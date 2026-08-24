# Backend Hardening Log

This document tracks every backend change made during the production-hardening
pass (as distinct from the earlier UI-only reskin pass). Read this top to
bottom to see exactly what changed and why — nothing here is silent.

Each entry states: **what was wrong**, **what changed**, and **whether it
alters stored data or calculated output** (i.e. whether old and new numbers
can differ for the same input).

---

## Legend

- 🐛 **Bug fix** — corrects wrong behavior. May change output vs. the old app.
- 🔒 **Hardening** — validation, transactions, race-condition guards. Should
  not change correct-input output, but will reject or safely handle bad
  input that the old app accepted silently.
- 📝 **Logging/observability** — no behavior change, just visibility.
- 🧪 **Tests** — no behavior change, adds coverage.
- ⚙️ **Config/infra** — settings, deployment posture.

---

## Main/settings.py

⚙️ **SECRET_KEY / DEBUG / ALLOWED_HOSTS now read from environment
variables** (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`),
falling back to the existing dev-only values only when those variables are
unset. Deploying now means setting three env vars — no code change, no
committed production secret. `DJANGO_DEBUG` defaults to the current `True`
so nothing breaks for anyone still running this locally without env vars set.

⚙️ **Added `CSRF_TRUSTED_ORIGINS`** (env-driven, empty by default) for
deployments that sit behind a proxy/custom domain and need CSRF to trust
that origin.

⚙️ **When `DJANGO_DEBUG=False`, a block of production security settings
now activates automatically**: forced HTTPS redirect, secure/HttpOnly
session & CSRF cookies, HSTS (1 year, includeSubDomains, preload),
`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`. Verified with
`manage.py check --deploy` — went from a settings file that would fail
every deploy check to zero warnings when the env vars are set.

⚙️ **`DATABASES` is now env-overridable** (`DJANGO_DB_ENGINE` +
`DJANGO_DB_NAME/USER/PASSWORD/HOST/PORT`) without hardcoding a specific
engine or adding a new dependency — falls back to SQLite for local dev.
Also added `OPTIONS.timeout: 20` to the SQLite config so a request that
hits SQLite's single-writer lock waits up to 20s instead of immediately
raising "database is locked" — matters once more than one worker process
is writing concurrently (this is a mitigation, not a fix: SQLite is still
not safe for real concurrent-write production load; the code doesn't
force a database engine choice, but a Postgres/MySQL move needs its
driver added to requirements.txt and is a deployment decision, not
something silently changed here).

📝 **Added a real `LOGGING` config** — console output plus two rotating
log files (`logs/app.log` for INFO+, `logs/error.log` for ERROR+, 10MB ×
5–10 backups), with one logger per app (`Bill_Master`, `Revenue`, etc.) so
`logging.getLogger(__name__)` calls inside each app's `views.py`
propagate to a named, filterable logger instead of Python's default
"logging configured? not really" behavior. This is what the subsequent
per-app passes plug into when replacing `print(e)` with real logging.
`logs/` is already covered by the existing `*.log` gitignore rule.

**Verification:** `manage.py check` clean with no env vars (dev defaults);
`manage.py check --deploy` clean with `DJANGO_DEBUG=False` +
`DJANGO_SECRET_KEY` + `DJANGO_ALLOWED_HOSTS` set; full login → page-render
smoke test against the seeded preview DB still passes.

---

## Authentication/middleware.py — AutoLogoutMiddleware

🔒 **Halved the DB round-trips per authenticated request.** The middleware
was querying `Authentication.objects.filter(...).first()` twice per
request — once before the view ran (idle-timeout check), once after
(activity-time stamp) — as two independent queries. Now fetched once and
reused for both.

🔒 **Throttled the activity-time write to once per 30 seconds per session**
instead of writing on literally every request. Under normal use (a user
clicking through several pages within a few seconds) this is a large
write-volume cut with no effect on the 10-minute timeout itself, since 30s
≪ 600s.

🐛 **Found, not yet fixed here (see Authentication app pass below): the
underlying session-tracking design is unsound.** `Authentication.objects.create(...)`
inserts a brand-new row on every login instead of updating one record per
active session, and `AutoLogoutMiddleware` picks "whichever row for this
user has the most recent `activity_time`" rather than the row belonging to
*this* browser session. Verified experimentally: log the same user in
twice in quick succession and the idle-timeout check for session A silently
reads session B's activity — meaning two simultaneous logins (or even just
leftover historical rows) make the timeout unreliable in both directions
(a session that should time out doesn't, or one that shouldn't does). This
needs a `session_key` column tying each `Authentication` row to its actual
Django session; fixing it here would touch the login/logout views too, so
it's tracked as the first item in the Authentication app pass, not folded
into this settings-focused commit.

---

