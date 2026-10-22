from django.db import models
from django.utils import timezone


class Participant(models.Model):
    name = models.CharField(max_length=140)
    email = models.EmailField(unique=True)
    team = models.CharField(max_length=140, blank=True)
    token = models.CharField(max_length=64, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Attempt(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="attempts")
    started = models.DateTimeField(default=timezone.now)
    ended = models.DateTimeField(null=True, blank=True)
    answers = models.JSONField(default=dict)
    score = models.PositiveIntegerField(default=0)
    manual_score = models.PositiveIntegerField(null=True, blank=True)
    violations = models.PositiveIntegerField(default=0)
    review_notes = models.TextField(blank=True)

    @property
    def final_score(self):
        return self.manual_score if self.manual_score is not None else self.score

    def __str__(self):
        return f"{self.participant} · {self.final_score}/40"


class Submission(models.Model):
    ARENAS = [
        ("web", "Webphobia"),
        ("pts1", "Problem to Solution · Idea"),
        ("pts2", "Problem to Solution · Prototype"),
    ]
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="submissions")
    arena = models.CharField(max_length=10, choices=ARENAS)
    topic = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=30, default="Submitted")
    feedback = models.TextField(blank=True)
    score = models.PositiveIntegerField(null=True, blank=True)
    max_score = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["participant", "arena"], name="one_submission_per_arena")]

    def __str__(self):
        return f"{self.participant} · {self.get_arena_display()}"


class Upload(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="uploads")
    file = models.FileField(upload_to="submissions/%Y/%m/")
    kind = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.kind}: {self.file.name}"


class Question(models.Model):
    ROUND = [(1, "AI Awareness"), (2, "Logic & Aptitude")]
    round = models.IntegerField(choices=ROUND)
    prompt = models.TextField()
    a = models.CharField(max_length=500)
    b = models.CharField(max_length=500)
    c = models.CharField(max_length=500)
    d = models.CharField(max_length=500)
    correct = models.CharField(max_length=1, choices=[(x, x) for x in "ABCD"])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["round", "order", "id"]

    def __str__(self):
        return f"R{self.round}: {self.prompt[:55]}"


class MonitorEvent(models.Model):
    EVENT_TYPES = [
        ("tab_hidden", "Tab / window hidden"),
        ("tab_visible", "Returned to assessment"),
        ("fullscreen_exit", "Fullscreen exited"),
        ("window_blur", "Window lost focus"),
        ("copy_attempt", "Copy attempted"),
        ("paste_attempt", "Paste attempted"),
        ("context_menu", "Context menu attempted"),
        ("heartbeat", "Heartbeat"),
    ]
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="monitor_events")
    attempt = models.ForeignKey(Attempt, on_delete=models.SET_NULL, null=True, blank=True, related_name="monitor_events")
    event_type = models.CharField(max_length=40, choices=EVENT_TYPES)
    detail = models.CharField(max_length=500, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.participant} · {self.event_type}"
