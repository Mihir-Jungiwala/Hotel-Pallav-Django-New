# Deploying Hotel Pallav to Vercel

Vercel now has first-class Django support (auto-detects `manage.py`,
reads `WSGI_APPLICATION`, runs `collectstatic` automatically). That
changes a few things from the general `DEPLOYMENT.md` in this repo:
**gunicorn and the `Procfile` are not used at all on Vercel** — Vercel
runs your Django app as a single serverless Function directly. Ignore
those two files for this path; they exist for other hosts (Render,
Railway, a plain VPS).

Vercel's serverless model also makes two things that were *optional* in
`DEPLOYMENT.md` **mandatory** here, because a Vercel Function's
filesystem is ephemeral and mostly read-only:

1. **You cannot use SQLite.** Not "not recommended" — there is nowhere
   for it to durably write. You must attach a real Postgres database.
2. **You cannot store uploaded files on local disk.** Staff photos,
   resumes, and invoice scans written to `media/` would vanish (or fail
   to write at all) between requests. You must configure S3-compatible
   storage.

Both are already built into this codebase (`DJANGO_DB_ENGINE`/
`DATABASE_URL` and `DJANGO_USE_S3` in `Main/settings.py`) — you just have
to actually turn them on before this app will function on Vercel, not
just before it performs well.

## 1. Attach a Postgres database

In the Vercel dashboard, add a Postgres integration to the project —
Vercel Postgres, or a marketplace integration like Neon or Supabase all
work. Attaching one automatically sets a `DATABASE_URL` environment
variable on the project. `Main/settings.py` already checks for
`DATABASE_URL` first (via `dj-database-url`, added to `requirements.txt`)
and uses it if present — no further database configuration needed.

## 2. Set up S3-compatible media storage

Vercel Blob (Vercel's own object storage) has no mainstream Django
storage backend, so this app uses `django-storages`' S3 backend instead
— point it at any S3-API-compatible bucket: AWS S3, Cloudflare R2, or
similar. Provision the bucket first, then set in Vercel's project
environment variables:

```
DJANGO_USE_S3=True
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
AWS_S3_REGION_NAME=...          # leave blank for R2
AWS_S3_ENDPOINT_URL=...         # required for R2/non-AWS providers; blank for AWS S3
AWS_S3_CUSTOM_DOMAIN=...        # optional, if you've mapped a CDN domain to the bucket
```

Without this, `Staff__Profile_Registration`/`_Update` (photo, resume) and
`Bill_Master_Bill_Add`/`Bill_Master_Bill_Update` (invoice PDF upload)
will either fail to save the file or silently lose it on the next
deploy/cold start.

## 3. Set the remaining required environment variables

`Main/settings.py` auto-detects Vercel's own domain (via the `VERCEL_URL`/
`VERCEL_PROJECT_PRODUCTION_URL`/`VERCEL_BRANCH_URL` variables Vercel sets
automatically) and uses it for both `ALLOWED_HOSTS` and
`CSRF_TRUSTED_ORIGINS` when you haven't set those explicitly — so a plain
`*.vercel.app` deployment works with no host configuration at all. You
only need to set `DJANGO_ALLOWED_HOSTS`/`DJANGO_CSRF_TRUSTED_ORIGINS`
yourself if you're serving from a **custom domain** (they're not
detectable automatically), in which case setting either one disables the
auto-detection entirely for that variable — set both together, not just
one, once you do.

In the Vercel dashboard, Project Settings → Environment Variables, set:

- `DJANGO_SECRET_KEY` — generate with
  `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS` — only if using a
  custom domain, e.g. `hotelpallav.example.com` /
  `https://hotelpallav.example.com`
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` — for password reset emails

`DJANGO_DEBUG` should stay unset or `False` — Vercel is production, and
the codebase now defaults to `False` when unset (see
`docs/backend-hardening-log.md`, "Deployment readiness pass").

## 4. Static files — no action needed

Vercel detects `STATIC_ROOT` in `settings.py` and runs `collectstatic`
automatically during the build, serving the result from Vercel's CDN.
The `whitenoise` middleware already in `MIDDLEWARE` stays useful for
local development (`vercel dev` / `manage.py runserver`) but is inactive
in Vercel's actual production serving path — nothing to configure here.

## 5. Deploy

```
npm i -g vercel   # if you don't already have the CLI
vercel link       # connect this directory to a Vercel project
vercel deploy --prod
```

Or connect the GitHub repo in the Vercel dashboard and push to the
branch Vercel is watching — either path auto-detects Django via
`manage.py` and `Main/wsgi.py` (already exposes the required top-level
`application` name).

`vercel.json` in this repo sets `maxDuration: 30` for the Django
function — bump it further if a specific request (a heavy Dashboard
aggregation, a large PDF) needs more headroom; check your Vercel plan's
maximum first.

## 6. Run migrations

Vercel has no automatic post-deploy hook that runs arbitrary commands
(no Heroku-style release phase), so run migrations yourself against the
now-live database:

```
vercel pull                 # writes the project's env vars to .env.local
export $(grep -v '^#' .env.local | xargs)   # or use python-dotenv/django-environ
python manage.py migrate
python manage.py createsuperuser
```

Do this once after the first deploy, and again after any deploy that
includes new migrations.

## 7. Verify before declaring it live

Same checklist as `DEPLOYMENT.md`, plus two Vercel-specific checks:

- Upload a staff photo or resume and confirm it round-trips through your
  S3 bucket (not local disk).
- Confirm a page that fires several queries at once (Dashboard) returns
  well within the `maxDuration` you set.
- **Generate an actual PDF** (a Bill_Master/Revenue/Expense receipt or
  the Shift_Handover report) and open it — this still could not be
  verified end-to-end in the development sandbox this app was hardened
  in, due to a broken `xhtml2pdf`/`pyhanko` dependency chain unrelated to
  this codebase.

## What this repo does NOT do for you

- Provision the Postgres database or the S3-compatible bucket
- Set the real secret values in Vercel's environment variable UI
- Guarantee the deployment stays under Vercel's 500 MB Function bundle
  size limit — this app's dependency list includes some heavier native
  packages (`lxml`, `Pillow`, `pyHanko`/`cryptography`, `reportlab`,
  `xhtml2pdf`). It's likely fine, but this could not be measured without
  an actual Vercel deploy from this environment; watch the build output
  the first time you deploy.

See `docs/backend-hardening-log.md` for the full record of every backend
change made to get the application code itself to this point, and
`DEPLOYMENT.md` for the equivalent instructions on a traditional
(non-serverless) host.
