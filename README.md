# ARVEXA 2026 — Ready-to-Run Competition Portal

ARVEXA 2026 is a Django competition portal for three online arenas:

- APTIQ — 40 advanced questions / 50 minutes
- WEBPHOBIA — secure server-assigned creative wheel + submission evidence
- PROBLEM TO SOLUTION — theme → idea → final evidence, with no shortlist gate
- Separate organizer control room — no Django admin dependency

Event credit: **Conducted by Quadrafroyn Solutions.**

## 1. Local setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_questions
python manage.py collectstatic --noinput
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## 2. Organizer portal

Organizer is intentionally separated from Django administration.

URL:

`http://127.0.0.1:8000/organizer/`

Default development credentials:

- Email: `dhalak65@gmail.com`
- Password: `Dhan2005*`

For production, set:

```text
ORGANIZER_EMAIL=your-organizer-email
ORGANIZER_PASSWORD=your-strong-password
DJANGO_SECRET_KEY=your-long-random-secret
DEBUG=0
ALLOWED_HOSTS=your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
```

The code reads these values from environment variables, so production credentials do not need to be stored in source control.

## 3. Organizer capabilities

The control room provides:

- participant register and individual participant records
- APTIQ attempt and answer review
- automated score plus organizer manual score override
- review notes
- tab visibility / focus / fullscreen / copy / paste / context-menu monitoring signals
- Webphobia, idea and final evidence submissions
- submission status, score, maximum score and feedback
- direct download of uploaded participant files
- clean desktop-first white control-room interface

Browser monitoring is intentionally described as a **signal system**, not guaranteed surveillance. Browser APIs cannot prove every form of misconduct.

## 4. Competition flow changes

### Enter the Arena
Only these fields remain:

- Full name
- Email address
- Team name (optional)

College/institution and phone fields were removed.

### Webphobia
The wheel assignment is now server-side and locked to the participant session. The client animation is only the visual reveal. This prevents simply changing the topic in the URL.

### Problem to Solution
The shortlist / provisional-final language has been removed. The flow is:

1. Choose a theme
2. Submit the idea
3. Immediately continue to final evidence
4. Organizer reviews the submitted package

## 5. Deployment

For a basic Linux deployment:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_questions
python manage.py collectstatic --noinput
gunicorn core.wsgi:application
```

Set `DEBUG=0`, a strong `DJANGO_SECRET_KEY`, correct `ALLOWED_HOSTS`, and a persistent `MEDIA_ROOT` before going live.

## 6. Windows quick start

Double-click `run_windows.bat` after installing Python, or run it from Command Prompt.

## 7. Notes

- The included poster is displayed with `object-fit: contain` so the complete artwork remains visible.
- Remote editorial photography is used on the Problem to Solution experience from Unsplash image CDN URLs.
- The visual system intentionally avoids emoji-heavy / AI-template styling and uses a restrained editorial competition aesthetic.
