import csv
import json
import secrets
from functools import wraps
from vercel.blob import sync as blob
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Attempt, MonitorEvent, Participant, Question, Submission, Upload

TOPICS = [
    "AI-Powered Learning Studio",
    "Sustainable City Dashboard",
    "Future of Digital Healthcare",
    "Cybersecurity Awareness Hub",
    "Accessible Career Navigator",
    "Smart Agriculture Experience",
    "Space Exploration Portal",
    "Community Emergency Response",
    "Climate Action Tracker",
    "Local Business Digital Twin",
]

THEMES = [
    ("ARV-PTS-T01", "Education & Employability"),
    ("ARV-PTS-T02", "Public Services & Civic Life"),
    ("ARV-PTS-T03", "Health & Wellbeing"),
    ("ARV-PTS-T04", "Environment & Sustainability"),
    ("ARV-PTS-T05", "Small Business & Local Commerce"),
]

def person(request):
    token = request.session.get("participant_token")
    if not token:
        return None
    p = Participant.objects.filter(token=token).first()
    if p:
        Participant.objects.filter(pk=p.pk).update(last_seen=timezone.now())
    return p

def guard(request):
    return person(request)

def page(request, name, **context):
    return render(request, "page.html", {"page": name, "topics": TOPICS, "themes": THEMES, **context})

def home(request):
    return page(request, "home")

def join(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()[:140]
        email = request.POST.get("email", "").strip().lower()[:254]
        team = request.POST.get("team", "").strip()[:140]
        if not name or "@" not in email:
            return page(request, "join", error="Please enter a valid name and email address.")
        p, _ = Participant.objects.get_or_create(
            email=email,
            defaults={"name": name, "team": team, "token": secrets.token_hex(32)},
        )
        p.name = name
        p.team = team
        p.save(update_fields=["name", "team"])
        request.session["participant_token"] = p.token
        return redirect("arenas")
    return page(request, "join")

def arenas(request):
    p = guard(request)
    if not p:
        return redirect("join")
    return page(
        request,
        "arenas",
        p=p,
        attempt=Attempt.objects.filter(participant=p, ended__isnull=False).order_by("-id").first(),
        submitted=list(Submission.objects.filter(participant=p).values_list("arena", flat=True)),
    )

def aptiq(request):
    if not guard(request):
        return redirect("join")
    return page(request, "aptiq")

def start(request):
    p = guard(request)
    if not p or request.method != "POST":
        return redirect("aptiq")
    if not request.POST.get("agree"):
        return page(request, "aptiq", error="Please acknowledge the assessment rules.")
    attempt = Attempt.objects.filter(participant=p).order_by("-id").first()
    if attempt and attempt.ended:
        return redirect("arenas")
    if not attempt:
        attempt = Attempt.objects.create(participant=p)
    MonitorEvent.objects.create(participant=p, attempt=attempt, event_type="heartbeat", detail="Assessment started")
    return redirect("test")

def test(request):
    p = guard(request)
    if not p:
        return redirect("join")
    a = Attempt.objects.filter(participant=p).order_by("-id").first()
    if not a:
        return redirect("aptiq")
    if a.ended:
        return redirect("arenas")
    questions = list(Question.objects.values("id", "round", "prompt", "a", "b", "c", "d"))
    if len(questions) != 40:
        return page(request, "test_unavailable", count=len(questions))
    remaining = max(0, 3000 - int((timezone.now() - a.started).total_seconds()))
    return page(
        request, "test",
        questions=json.dumps(questions),
        answers=json.dumps(a.answers),
        remaining=remaining,
        attempt=a,
    )

@require_POST
def save(request):
    p = guard(request)
    if not p:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    a = Attempt.objects.filter(participant=p, ended__isnull=True).first()
    if not a:
        return JsonResponse({"error": "No active attempt"}, status=400)
    try:
        data = json.loads(request.body or "{}")
        ans = data.get("answers", {})
        violations = int(data.get("violations", 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Bad request"}, status=400)
    if not isinstance(ans, dict):
        return JsonResponse({"error": "Invalid answers"}, status=400)
    ids = {str(i) for i in Question.objects.values_list("id", flat=True)}
    a.answers = {k: v for k, v in ans.items() if k in ids and isinstance(v, str) and v in ["A", "B", "C", "D"]}
    a.violations = max(a.violations, min(violations, 999))
    a.save(update_fields=["answers", "violations"])
    return JsonResponse({"ok": True})

@require_POST
def finish(request):
    p = guard(request)
    if not p:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    a = Attempt.objects.filter(participant=p, ended__isnull=True).first()
    if not a:
        return JsonResponse({"ok": True, "url": "/arenas/"})
    try:
        data = json.loads(request.body or "{}")
        ans = data.get("answers", a.answers)
    except (ValueError, TypeError, json.JSONDecodeError):
        ans = a.answers
    if isinstance(ans, dict):
        a.answers = {k: v for k, v in ans.items() if isinstance(v, str) and v in "ABCD" and len(v) == 1}
    correct = {str(q.id): q.correct for q in Question.objects.all()}
    a.score = sum(a.answers.get(k) == v for k, v in correct.items())
    a.ended = timezone.now()
    a.save()
    MonitorEvent.objects.create(participant=p, attempt=a, event_type="heartbeat", detail="Assessment submitted")
    return JsonResponse({"ok": True, "url": "/arenas/"})

def web(request):
    if not guard(request):
        return redirect("join")
    return page(request, "web", assigned_topic=request.session.get("web_topic", ""))

@require_POST
def assign_web_topic(request):
    p = guard(request)
    if not p:
        return JsonResponse({"error": "Unauthorized"}, status=401)
    assigned = request.session.get("web_topic")
    if assigned not in TOPICS:
        import secrets as _secrets
        assigned = _secrets.choice(TOPICS)
        request.session["web_topic"] = assigned
        request.session.modified = True
    return JsonResponse({"topic": assigned})


def upload_submission(request, arena, topic, fields):
    p = guard(request)
    if not p:
        return redirect("join")
    if request.method != "POST":
        return None
    if not topic:
        return page(request, "error", error="Choose a valid topic or theme first.")
    if not all(request.FILES.get(k) for k in fields):
        return page(request, "error", error="All required files must be uploaded.")

    limits = {
        "video": 150 * 1024 * 1024,
        "code": 40 * 1024 * 1024,
        "ppt": 30 * 1024 * 1024,
        "prototype": 75 * 1024 * 1024,
        "architecture": 30 * 1024 * 1024,
        "solution": 30 * 1024 * 1024,
    }

    allowed = {
        "video": (".mp4", ".webm", ".mov"),
        "code": (".zip",),
        "ppt": (".ppt", ".pptx", ".pdf"),
        "prototype": (
            ".pdf", ".ppt", ".pptx", ".doc", ".docx",
            ".png", ".jpg", ".jpeg", ".mp4", ".webm", ".zip"
        ),
        "architecture": (
            ".pdf", ".ppt", ".pptx", ".doc", ".docx",
            ".png", ".jpg", ".jpeg", ".mp4", ".webm", ".zip"
        ),
        "solution": (
            ".pdf", ".ppt", ".pptx", ".doc", ".docx",
            ".png", ".jpg", ".jpeg", ".mp4", ".webm", ".zip"
        ),
    }

    for kind in fields:
        f = request.FILES[kind]
        if f.size > limits[kind] or not f.name.lower().endswith(allowed[kind]):
            return page(
                request,
                "error",
                error=f"Invalid file or file too large: {kind}."
            )

    with transaction.atomic():
        submission, _ = Submission.objects.update_or_create(
            participant=p,
            arena=arena,
            defaults={
                "topic": topic[:200],
                "description": request.POST.get("description", "")[:5000],
            },
        )

        submission.uploads.all().delete()

        for kind in fields:
            Upload.objects.create(
                submission=submission,
                kind=kind,
                file=request.FILES[kind],
            )

    return redirect("prototype" if arena == "pts1" else "arenas")

def submit_web(request):
    p = guard(request)
    if not p:
        return redirect("join")
    topic = request.POST.get("topic", "")
    if request.method == "POST":
        assigned = request.session.get("web_topic", "")
        if topic not in TOPICS or topic != assigned:
            return page(request, "error", error="This submission must use the topic assigned to your participant session.")
        return upload_submission(request, "web", topic, ["video", "code"])
    return page(request, "submit_web", topic=request.session.get("web_topic", ""))
def save_blob_upload(request):
    p = guard(request)

    if not p:
        return JsonResponse(
            {"error": "Participant session expired."},
            status=401,
        )

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST required."},
            status=405,
        )

    blob_url = request.POST.get("blob_url", "").strip()
    blob_path = request.POST.get("blob_path", "").strip()
    original_name = request.POST.get("original_name", "").strip()
    content_type = request.POST.get("content_type", "").strip()
    file_size = request.POST.get("file_size", "0").strip()

    if not blob_url or not blob_path or not original_name:
        return JsonResponse(
            {"error": "Missing Blob upload information."},
            status=400,
        )

    try:
        file_size = int(file_size)
    except (TypeError, ValueError):
        return JsonResponse(
            {"error": "Invalid file size."},
            status=400,
        )

    submission = Submission.objects.filter(
        participant=p,
        arena="pts1",
    ).first()

    if not submission:
        return JsonResponse(
            {"error": "Submit the Idea details first."},
            status=400,
        )

    submission.uploads.filter(kind="ppt").delete()

    Upload.objects.create(
        submission=submission,
        kind="ppt",
        blob_url=blob_url,
        blob_path=blob_path,
        original_name=original_name,
        content_type=content_type,
        file_size=file_size,
    )

    return JsonResponse({
        "success": True,
    })
def pts(request):
    if not guard(request):
        return redirect("join")
    return page(request, "pts")

def idea(request):
    if not guard(request):
        return redirect("join")

    if request.method == "POST":
        topic = request.POST.get("topic", "")

        valid = [
            f"{code} · {theme}"
            for code, theme in THEMES
        ]

        if topic not in valid:
            return page(
                request,
                "error",
                error="Select one official theme.",
            )

        submission, _ = Submission.objects.update_or_create(
            participant=guard(request),
            arena="pts1",
            defaults={
                "topic": topic[:200],
                "description": request.POST.get(
                    "description",
                    "",
                )[:5000],
            },
        )

        return redirect("prototype")

    return page(request, "idea")

def prototype(request):
    p = guard(request)
    if not p:
        return redirect("join")
    idea = Submission.objects.filter(participant=p, arena="pts1").first()
    if not idea:
        return redirect("idea")
    if request.method == "POST":
        return upload_submission(request, "pts2", idea.topic, ["prototype", "architecture", "solution"])
    return page(request, "prototype", idea=idea)

def complete(request):
    if not guard(request):
        return redirect("join")
    return page(request, "complete")

@require_POST
def heartbeat(request):
    p = guard(request)
    if not p:
        return JsonResponse({"ok": False}, status=401)
    try:
        data = json.loads(request.body or "{}")
    except (ValueError, TypeError, json.JSONDecodeError):
        data = {}
    attempt = Attempt.objects.filter(participant=p, ended__isnull=True).order_by("-id").first()
    event_type = data.get("event_type", "heartbeat")
    allowed = {x[0] for x in MonitorEvent.EVENT_TYPES}
    if event_type not in allowed:
        event_type = "heartbeat"
    detail = str(data.get("detail", ""))[:500]
    if event_type != "heartbeat" or data.get("record", False):
        MonitorEvent.objects.create(participant=p, attempt=attempt, event_type=event_type, detail=detail)
    Participant.objects.filter(pk=p.pk).update(last_seen=timezone.now())
    return JsonResponse({"ok": True})

# ---------------- Organizer portal ----------------

def organizer_guard(request):
    return request.session.get("organizer_authenticated") is True

def organizer_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not organizer_guard(request):
            return redirect("organizer_login")
        return view(request, *args, **kwargs)
    return wrapped

def organizer_login(request):
    if organizer_guard(request):
        return redirect("organizer_dashboard")
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        if email == settings.ORGANIZER_EMAIL and password == settings.ORGANIZER_PASSWORD:
            request.session["organizer_authenticated"] = True
            request.session.set_expiry(60 * 60 * 8)
            return redirect("organizer_dashboard")
        return page(request, "organizer_login", error="The organizer credentials could not be verified.")
    return page(request, "organizer_login")

def organizer_logout(request):
    request.session.pop("organizer_authenticated", None)
    return redirect("organizer_login")

@organizer_required
def organizer_dashboard(request):
    participants = Participant.objects.all().order_by("-last_seen")
    query = request.GET.get("q", "").strip()
    if query:
        from django.db.models import Q
        participants = participants.filter(Q(name__icontains=query) | Q(email__icontains=query) | Q(team__icontains=query))
    attempts = Attempt.objects.select_related("participant").order_by("-started")
    submissions = Submission.objects.select_related("participant").order_by("-created")
    recent_events = MonitorEvent.objects.select_related("participant").exclude(event_type="heartbeat").order_by("-created")[:35]
    flagged_events = MonitorEvent.objects.exclude(event_type="heartbeat").count()
    context = {
        "participants": participants,
        "attempts": attempts[:30],
        "submissions": submissions[:30],
        "recent_events": recent_events,
        "query": query,
        "stats": {
            "participants": Participant.objects.count(),
            "aptiq_completed": Attempt.objects.filter(ended__isnull=False).count(),
            "submissions": submissions.count(),
            "flagged": flagged_events,
        },
    }
    return page(request, "organizer_dashboard", **context)

@organizer_required
def organizer_export_participants(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="arvexa_participants.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Email", "Team", "Joined", "Last Active", "APTIQ Score", "APTIQ Flags", "Submissions"])
    for participant in Participant.objects.all().order_by("name"):
        attempt = participant.attempts.order_by("-id").first()
        writer.writerow([
            participant.name, participant.email, participant.team or "Individual",
            timezone.localtime(participant.created).strftime("%Y-%m-%d %H:%M"),
            timezone.localtime(participant.last_seen).strftime("%Y-%m-%d %H:%M"),
            attempt.final_score if attempt else "",
            attempt.violations if attempt else "",
            participant.submissions.count(),
        ])
    return response

@organizer_required
def organizer_participant(request, pk):
    participant = get_object_or_404(Participant, pk=pk)
    attempts = participant.attempts.order_by("-started")
    submissions = participant.submissions.prefetch_related("uploads").order_by("-created")
    events = participant.monitor_events.select_related("attempt").order_by("-created")[:120]
    return page(
        request, "organizer_participant",
        participant=participant, attempts=attempts, submissions=submissions, events=events,
    )

@organizer_required
def organizer_submission(request, pk):
    submission = get_object_or_404(Submission.objects.select_related("participant").prefetch_related("uploads"), pk=pk)
    if request.method == "POST":
        submission.status = request.POST.get("status", "Reviewed")[:30]
        raw = request.POST.get("score", "").strip()
        submission.score = int(raw) if raw.isdigit() else None
        raw_max = request.POST.get("max_score", "").strip()
        submission.max_score = int(raw_max) if raw_max.isdigit() else None
        submission.feedback = request.POST.get("feedback", "")[:8000]
        submission.save()
        messages.success(request, "Submission review saved.")
        return redirect("organizer_submission", pk=submission.pk)
    return page(request, "organizer_submission", submission=submission)

@organizer_required
def organizer_attempt(request, pk):
    attempt = get_object_or_404(Attempt.objects.select_related("participant"), pk=pk)
    questions = list(Question.objects.all())
    if request.method == "POST":
        raw = request.POST.get("manual_score", "").strip()
        attempt.manual_score = int(raw) if raw.isdigit() else None
        attempt.review_notes = request.POST.get("review_notes", "")[:8000]
        attempt.save(update_fields=["manual_score", "review_notes"])
        messages.success(request, "APTIQ review saved.")
        return redirect("organizer_attempt", pk=attempt.pk)
    return page(request, "organizer_attempt", attempt=attempt, questions=questions)

@organizer_required
def download_upload(request, pk):
    if not request.session.get("organizer"):
        return redirect("organizer_login")

    upload = get_object_or_404(Upload, pk=pk)

    if upload.blob_url:
        return redirect(upload.blob_url)

    if upload.file:
        return FileResponse(
            upload.file.open("rb"),
            as_attachment=True,
            filename=upload.file.name.split("/")[-1],
        )

    return page(request, "error", error="Uploaded file is unavailable.")

def logout_participant(request):
    request.session.pop("participant_token", None)
    return redirect("home")
