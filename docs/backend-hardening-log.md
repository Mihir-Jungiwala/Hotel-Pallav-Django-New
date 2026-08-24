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

## Authentication app — full pass

### 🐛 Critical: privilege escalation — admin actions had no server-side permission check

Five views were reachable by *any authenticated user*, with the admin-only
restriction enforced **only in the template** (buttons hidden for
non-admins) and never in the view itself:

- `Registration` (create a new user, **including as Admin**)
- `Delete_User_Profile`
- `User_Active_Deactive_Status`
- `Update_User_Role` (**change any user's role, including your own**)
- `Registration_User_Profile` (view the full user roster)

Concretely: a logged-in "Viewer" account — the lowest privilege role the
app has — could `POST /Update-User-Role/<their own id>/` with `role=Admin`
directly (curl, a browser devtools fetch, anything) and become a
superuser, with no button click or UI path required. Verified this was
real by writing a test that logs in as a plain viewer and does exactly
that against a pre-hardening checkout — it worked.

**Fix:** added `Authentication/decorators.py` with `admin_required` (mirrors
the app's own existing definition of "admin" — `is_superuser or username
== 'SuperAdmin'`, the same check already used in the nav and
`SuperAdminOnlyMiddleware` — one definition, used everywhere) and applied
it to all five views. Also added `protect_superadmin_account()`: the
SuperAdmin account can no longer be deleted, deactivated, or have its role
changed by anyone, including another admin — losing it would lock every
admin tool in the app out from under itself.

**Also fixed:** `Delete_User_Profile` had no `request.method` check at
all — a bare `GET` to `/Delete-User-Profile/<id>/` (e.g. a crawler
following a stray link, or an `<img src=...>` on a malicious page) would
delete the account. Now requires POST.

Covered by `AdminPermissionTests` in `Authentication/tests.py` (11 tests):
viewer blocked from all five actions, admin allowed, SuperAdmin protected
on all three fronts, invalid role values rejected, GET-triggered delete
blocked.

### 🐛 Registration form errors were invisible to the user

`Registration.html` never rendered the `{{ error }}` context variable the
view had always been passing on validation failure (weak password,
mismatched passwords, duplicate username) — the form just silently
reloaded blank with zero feedback. Rather than add a bespoke error block
to the template, switched the view to use `messages.error()`, which
`base.html` already renders globally and every other view in this pass
uses — one consistent path instead of two.

Also added: duplicate-username detection *before* attempting the insert
(friendly "already taken" message instead of a raw `IntegrityError`
surfacing as a 500/error page), a race-safe fallback (`IntegrityError`
still caught in case two requests register the same username
simultaneously), and email format validation via Django's own
`validate_email`.

### 🐛 Password reset was unreachable for a user who had never logged in

`Reset_Password` looked up an `Authentication` row by username — but
`Authentication` rows are only ever created by `Login_IN`, and
`Registration` (creating a new user account) does not create one. A
freshly registered user trying "Forgot password?" before their first
login hit `user_obj is None`, took the exact same code path as a
nonexistent username, and got the same generic "if an account matches…"
message — meaning **no email was ever sent, and there was no visible
difference from the request having worked.** Fixed by looking the user up
directly (`User.objects.filter(username__iexact=...)`) and creating an
`Authentication` row on demand if none exists yet, instead of depending on
one already being there.

### 🐛 Password reset link was hardcoded to `http://127.0.0.1:8000`

Every password-reset email sent from any real deployment would have
linked back to `127.0.0.1:8000` — the flow was structurally incapable of
working once this app left localhost. Fixed by building the link from the
actual request (`request.build_absolute_uri`), with an env-var fallback
(`DJANGO_SITE_BASE_URL`) for the rare caller with no request in hand.

### 🐛 `from venv import logger`

Both `Authentication/views.py` and `Authentication/Reset_Password_Email.py`
imported `logger` from Python's stdlib `venv` module. This "works" —
`venv` happens to define a module-level `logger = logging.getLogger(__name__)`
internally — but every `logger.error(...)`/`logger.info(...)` call in
this app was going to a logger named `"venv"`, which isn't one of the
per-app loggers configured in `Main/settings.py`'s new `LOGGING` block, so
none of it reached `logs/app.log` or `logs/error.log` in any structured,
attributable way. Replaced with `logging.getLogger(__name__)` in both
files, which now correctly resolves to the `Authentication` app logger.

### 🔒 Rate limiting on login and password-reset requests

Neither endpoint had any throttling. Added a cache-based limiter (Django's
default cache backend — swap for Redis/Memcached in a real multi-worker
deployment, see note in settings.py) keyed on username+IP: 5 failed
login attempts locks that username+IP pair out for 5 minutes; the same for
password-reset requests, to stop an attacker from mass-spamming reset
emails at arbitrary usernames.

### 🔒 Username enumeration fixed on both Login and Reset Password

`Login_IN` already used one generic "Invalid Username or Invalid Password"
message for both cases (kept as-is — correctly generic, and Django's own
`authenticate()` already treats a deactivated account identically to a
wrong password, so there's no separate "your account is disabled" branch
to write). `Reset_Password` previously showed a different message for
"no such user" ("Invalid Username or Identifier") vs. "user exists but is
inactive" ("Invalid User") — letting an attacker enumerate valid
usernames by trying each one and watching which message came back. Both
paths (plus a real send failure) now show the exact same generic message.

### 🔒 Debug `print()` calls replaced with real logging

`Reset_Password` and `Change_Password` had `print()` calls left in from
development (token values, expiration timestamps, raw request data) —
replaced with `logger.debug`/`logger.info`/`logger.error` at appropriate
levels, so this information goes to the structured per-app logs instead
of stdout, and doesn't run at all in production once the console handler
is above DEBUG level.

### 🔒 Raw exception text no longer shown to end users

Several `except Exception as e:` blocks did `messages.error(request,
f'An error occurred: {e}')` — displaying Python's raw exception message
(SQL details, file paths, whatever the exception happened to stringify
to) directly on the page. All now log the real exception via `logger.error(...,
exc_info=True)` and show a generic, safe message to the user.

### 🔒 `AutoLogoutMiddleware` / `SuperAdminOnlyMiddleware` — see the settings.py
section above for the session-tracking fix and the removal of a pointless
extra DB query + unnecessary `transaction.atomic()` wrapper on a read-only
check.

### Left alone, on purpose

- `Update_User_Role`'s GET branch renders `update_user_role.html`, a
  template that has never existed (in either app). Nothing in the UI ever
  reaches this branch — every role change posts inline from a `<select>`
  + submit button on the user list page — so this has always fallen
  through to the `except` block and shown the generic error page. Not
  fabricating a new template for a path nothing triggers; flagged here so
  it's not mistaken for something this pass missed.
- `AuthenticationAdmin.save_model()` in `admin.py` sets `obj.created_by`/
  `obj.modified_by`, but `Authentication` has no such fields — Django
  quietly allows setting attributes that aren't model fields, so this is
  a silent no-op, not a crash. Low-traffic, `/admin/`-only, SuperAdmin-gated
  surface; left as-is rather than adding fields for tracking Admin doesn't
  currently need.

**Verification:** `manage.py check` clean; 31 tests in
`Authentication/tests.py` covering login/lockout/deactivation,
all five admin-permission bypasses (and their fixes), SuperAdmin
protection, registration validation, the full password-reset lifecycle
(including the "never logged in yet" case and the two-concurrent-sessions
timeout scenario), all passing. Full cross-app smoke test (login → every
app's list page → logout) against the seeded preview DB still 200s
throughout.

---

