# Deploying Hotel Pallav

> Deploying to **Vercel**? Use `VERCEL_DEPLOYMENT.md` instead — Vercel is
> serverless, so gunicorn/the `Procfile` below don't apply there, and
> Postgres + S3 storage are mandatory rather than optional. This document
> is for a traditional host (a VPS, Render, Railway, etc.) that runs
> gunicorn as a long-lived process.

This app is now set up to run behind a real WSGI server with production
security settings, collected static files served by whitenoise, and
optional Postgres/S3 backing — but every one of those is opt-in via
environment variables. Nothing here provisions actual infrastructure
(a database, a bucket, a domain, TLS) — that's still a decision only you
can make and a step only you can carry out. This document is the exact
sequence of steps once you have.

## 1. Set environment variables

Copy `.env.example`, fill in real values, and set them in your hosting
platform's environment (Heroku config vars, Render/Railway env settings,
a systemd `EnvironmentFile=`, etc.) — do not commit a filled-in `.env`.

At minimum, set:
- `DJANGO_SECRET_KEY` — generate with the command in `.env.example`
- `DJANGO_DEBUG=False` (this is already the default if unset, but set it
  explicitly so it's visible in your platform's config)
- `DJANGO_ALLOWED_HOSTS` — your real domain(s); Django will reject every
  request with a 400 if this is empty while DEBUG=False
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` — needed for password reset
  emails to actually send

Decide on the database and media storage (see `.env.example` for the
Postgres and S3 variable sets) — SQLite and local-disk media both work for
a single always-on server with modest traffic, but SQLite serializes
writes at the file level (unsafe for multiple gunicorn workers under
real concurrent load) and local-disk media is lost on every
deploy/restart on an ephemeral filesystem (most PaaS/containers).

## 2. Install dependencies

```
pip install -r requirements.txt
```

## 3. Run migrations

```
python manage.py migrate
```

(The `Procfile`'s `release: python manage.py migrate --noinput` line does
this automatically on platforms that support a release phase, e.g. Heroku.)

## 4. Collect static files

```
python manage.py collectstatic --noinput
```

This writes into `STATIC_ROOT` (`staticfiles/`), which whitenoise then
serves directly from the WSGI process — no separate nginx/CDN static
config needed for a first deployment.

## 5. Create an admin/SuperAdmin account

```
python manage.py createsuperuser
```

Then log in and use the app's own Registration flow (admin-only, per the
Authentication hardening pass) to create the SuperAdmin-role user the app
itself expects — a Django superuser and this app's "SuperAdmin" role are
two different things; see `Authentication/decorators.py`.

## 6. Start the server

```
gunicorn Main.wsgi:application --bind 0.0.0.0:$PORT --workers 3
```

(Already wired up as the `web:` line in `Procfile` for platforms that
read one.) Put a real reverse proxy or platform load balancer in front of
this for TLS termination — gunicorn itself does not terminate HTTPS.
`SECURE_PROXY_SSL_HEADER` is already configured in `settings.py` to trust
`X-Forwarded-Proto` from that proxy.

## 7. Verify before declaring it live

- Load the app over HTTPS and confirm you're redirected from HTTP
  (`DJANGO_SECURE_SSL_REDIRECT`).
- Log in, hit a few pages from each app (Dashboard, Bill_Master, Revenue,
  Expense) and confirm no 500s.
- **Generate an actual PDF** (a Bill_Master/Revenue/Expense receipt or the
  Shift_Handover report) and open it. This could not be verified
  end-to-end in the development sandbox this app was hardened in, due to
  a broken `xhtml2pdf`/`pyhanko` dependency chain unrelated to this
  codebase — confirm it works in your real environment before relying on
  it.
- If you enabled S3 media storage, upload a staff photo or resume and
  confirm it round-trips (uploads, then displays/downloads correctly).
- Check `logs/app.log` and `logs/error.log` are being written and rotate
  as expected.

## What this repo does NOT do for you

- Provision a database, S3 bucket, domain, or TLS certificate
- Configure a reverse proxy (nginx, Caddy, your platform's load balancer)
- Set up backups, monitoring, or alerting
- Scale gunicorn worker count for your actual traffic (3 is a reasonable
  small-deployment starting point, not a measured number)

See `docs/backend-hardening-log.md` for the full record of every backend
change made to get the application code itself to this point.
