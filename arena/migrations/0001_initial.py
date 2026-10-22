from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Participant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=140)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("team", models.CharField(blank=True, max_length=140)),
                ("token", models.CharField(max_length=64, unique=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("round", models.IntegerField(choices=[(1, "AI Awareness"), (2, "Logic & Aptitude")])),
                ("prompt", models.TextField()),
                ("a", models.CharField(max_length=500)),
                ("b", models.CharField(max_length=500)),
                ("c", models.CharField(max_length=500)),
                ("d", models.CharField(max_length=500)),
                ("correct", models.CharField(choices=[("A","A"),("B","B"),("C","C"),("D","D")], max_length=1)),
                ("order", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["round", "order", "id"]},
        ),
        migrations.CreateModel(
            name="Attempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started", models.DateTimeField(default=django.utils.timezone.now)),
                ("ended", models.DateTimeField(blank=True, null=True)),
                ("answers", models.JSONField(default=dict)),
                ("score", models.PositiveIntegerField(default=0)),
                ("manual_score", models.PositiveIntegerField(blank=True, null=True)),
                ("violations", models.PositiveIntegerField(default=0)),
                ("review_notes", models.TextField(blank=True)),
                ("participant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="arena.participant")),
            ],
        ),
        migrations.CreateModel(
            name="Submission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("arena", models.CharField(choices=[("web","Webphobia"),("pts1","Problem to Solution · Idea"),("pts2","Problem to Solution · Prototype")], max_length=10)),
                ("topic", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("created", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(default="Submitted", max_length=30)),
                ("feedback", models.TextField(blank=True)),
                ("score", models.PositiveIntegerField(blank=True, null=True)),
                ("max_score", models.PositiveIntegerField(blank=True, null=True)),
                ("participant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="arena.participant")),
            ],
            options={"constraints":[models.UniqueConstraint(fields=("participant","arena"), name="one_submission_per_arena")]},
        ),
        migrations.CreateModel(
            name="Upload",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="submissions/%Y/%m/")),
                ("kind", models.CharField(max_length=50)),
                ("submission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="uploads", to="arena.submission")),
            ],
        ),
        migrations.CreateModel(
            name="MonitorEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[
                    ("tab_hidden","Tab / window hidden"),("tab_visible","Returned to assessment"),
                    ("fullscreen_exit","Fullscreen exited"),("window_blur","Window lost focus"),
                    ("copy_attempt","Copy attempted"),("paste_attempt","Paste attempted"),
                    ("context_menu","Context menu attempted"),("heartbeat","Heartbeat")
                ], max_length=40)),
                ("detail", models.CharField(blank=True, max_length=500)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("attempt", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="monitor_events", to="arena.attempt")),
                ("participant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="monitor_events", to="arena.participant")),
            ],
            options={"ordering":["-created"]},
        ),
    ]
