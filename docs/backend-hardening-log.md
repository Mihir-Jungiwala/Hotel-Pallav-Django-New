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

## Company app — full pass

### 🐛 Confirmed crash: updating a company by an invalid id → hard 500

`Company_Profile__Update` did `queryset = Company_Profile.objects.get(id=id)`
as the first line inside a `try`, then — outside the try/except entirely —
`return render(request, "...", {'companyprofile': queryset})`. A
nonexistent id raises `DoesNotExist`, caught by the generic `except
Exception`, which logs a friendly message... and then execution falls
through to that final `render()`, which references `queryset` — never
assigned. Reproduced directly: `GET /Company--Profile-Update/999999/`
raised `UnboundLocalError: cannot access local variable 'queryset'`,
an unhandled 500. Fixed with `get_object_or_404`, which now correctly
returns a real 404 instead.

### 🐛 Confirmed crash: any GET request to the delete URL → hard 500

`Company_Profile_User_Delete` only had a body inside `if request.method ==
'POST':` with no `else`. A GET request (a stray link, a crawler, a
browser link-prefetch) fell through the entire function with no `return`
statement reached at all. Reproduced directly: `GET
/Company--Profile-User-Delete/23/` raised `ValueError: The view ...
didn't return an HttpResponse object. It returned None instead.` — also
an unhandled 500. Fixed: GET now redirects back to the list with an
"Invalid request" message instead of crashing.

### 🐛 Assistant HR mobile number silently dropped on every new company

The Add view read `request.POST.get('company_assitant_hr_mobile_number')`
(missing an "s") — but both the original Add *and* Update templates have
only ever submitted `company_assistant_hr_mobile_number` (correct
spelling). Confirmed by diffing the original app's two templates: both
already used the correct spelling; only the Add view's Python read the
wrong key. Every company ever registered through "Add Company" has had a
blank Assistant HR Mobile Number regardless of what was actually typed
into that field — a pure silent data-loss bug, invisible unless someone
went looking at the raw column. Fixed by extracting both Add and Update
field-handling into one shared `COMPANY_FIELD_MAP`/`_extract_company_fields()`
(see "Also: large de-duplication" below), which uses the one correct spelling.

### 🐛 Clearing a percentage field on Update crashed the request

The Add view defaults Discount/GST/TCS/TDS percentage to `'0'` when
blank; the Update view instead defaulted them to `''`. Confirmed directly
against a real row: assigning `''` to a `DecimalField` attribute and
calling `.save()` raises `ValidationError` — not caught by the update
view's `except IntegrityError` clause, only by the broader
`except Exception`, which then re-rendered the form... but the field on
the in-memory object was already `''`, so the same crash would recur on
the next save attempt unless the user re-typed a number into that field.
Fixed by unifying both views to the same `'0'`-when-blank default.

### 🔒 GST-number uniqueness — check-then-create race fixed with a real DB constraint

`Company_GST_Number` had no `unique=True` and no way to have one, since a
plain unique constraint on a nullable-but-not-blank-safe field would wrongly
reject a second company with a blank GST number (Django/most DBs treat
`NULL` as "never equal," but every call site actually stores `''`, not
`NULL`, when the field is left blank). The registration/update views
enforced uniqueness only with a `.filter(...).exists()` check followed by
`.create()`/`.save()` in separate statements — two concurrent submissions
with the same GST number could both pass the check before either write
landed. Added a conditional `UniqueConstraint` (`Company_GST_Number` unique
only when non-null and non-empty) via migration
`0005_company_profile_unique_company_gst_number_when_set`, and both views
now catch the resulting `IntegrityError` with a friendly message instead
of relying solely on the pre-check. `test_two_companies_can_both_have_blank_gst_number`
confirms the constraint doesn't over-apply.

### 🔒 Raw database error text no longer shown to users

Both views caught `IntegrityError` and did `messages.error(request,
str(e))` — showing a raw SQLite constraint-violation string (or, for the
manually-`raise`d GST case, the literal Python exception text) directly on
the page. Now shows one consistent, friendly message
(`A company named "X" or with that GST number already exists.`) and logs
the real exception server-side.

### 🔒 Basic server-side validation added

Company name is now required (previously: no check at all — an empty
name could be submitted, and would only ever collide with a second empty
name thanks to `Company_Name`'s existing `unique=True`). Email fields
(company + every contact role) are validated with Django's own
`validate_email`. Percentage fields are validated as numbers in [0, 100]
before hitting the database, instead of only being caught if they happen
to be non-numeric text (silently accepted otherwise, even at 9999%).

### Also: large de-duplication

Both the registration and update views had ~30 nearly-identical
`request.POST.get('company_x', '')` lines each, and the registration view
had two entire duplicate `Company_Profile.objects.create(...)` call
blocks (one for "GST number provided," one for "not provided" — both
blocks were otherwise identical, since the GST field is passed through in
both anyway). Collapsed into a shared `COMPANY_FIELD_MAP` +
`_extract_company_fields()` + `_validate_company_fields()`, used by both
views. Also removed doubled/redundant imports (`IntegrityError` and
`messages` were each imported twice in the original file, once above and
once below a stray mid-file `@login_required`/import block).

**Verification:** `manage.py check` clean; 16 tests in `Company/tests.py`
covering both crash reproductions and their fixes, the typo-field fix,
duplicate name/GST rejection (with a check that the friendly message
replaces the raw SQL string), the blank-GST-doesn't-collide case, the
decimal-crash fix, invalid-email and out-of-range-percentage rejection,
and that updating a company without changing its own GST number doesn't
reject itself as a false duplicate. Full cross-app smoke test still 200s
throughout.

---

## Staff_Profile app — full pass

### 🐛 Confirmed crash: any GET request to Delete or Pause/Unpause → hard 500

Same pattern as Company's delete bug: `Staff__Profile_User_Delete` only
had a body inside `if request.method == 'POST':`, no `else`, no trailing
return. Reproduced directly: `GET /Staff--Profile-User-Delete/<id>/`
raised `ValueError: ... didn't return an HttpResponse object. It
returned None instead.` `User_Profile_Pause_Unpause` didn't crash (it has
an unconditional `return redirect(...)` after the try/except, outside the
POST check) but silently no-op'd on GET with no feedback; given
`Staff__Profile_User_Delete` needed an explicit non-POST branch anyway,
added the same one to `User_Profile_Pause_Unpause` for consistency and a
real "Invalid request" message instead of a silent no-op.

### 🐛 Confirmed crash: a non-numeric or unset-looking salary → hard 500

`User_Salary` is an `IntegerField`; the view passed the raw POST string
straight through to `.create()`/`.save()`. Reproduced directly against a
real row: `User_Profile.objects.create(User_Salary='not-a-number')`
raises `ValueError: Field 'User_Salary' expected a number but got
'not-a-number'.` — uncaught by the surrounding `except Exception`
correctly catching the crash and showing an error page, but that meant
*any* typo in the salary field on Add or Update always dumped the user to
a generic error page. Now validated as a non-negative integer before
touching the database, with a specific message on failure.

### 🐛 Updating any field silently deleted the staff member's photo/documents/resume — behavior change, called out explicitly

This is the most consequential fix in this app's pass, and unlike
everything else in this log it's a **behavior change on a working path**,
not just a crash fix — read carefully.

The Update view always did `image = request.FILES.get('image', None)`
then unconditionally `queryset.User_Image = image`. An HTML file input
that the user doesn't touch submits nothing, so `request.FILES.get(...)`
returns `None` on every update where the photo/front-ID/back-ID/resume
wasn't re-selected — and assigning `None` to a `FileField` clears it.
**In the original app, editing a staff member's job title (or any other
single field) deletes their profile photo and both ID document images
and their resume unless all four files are re-uploaded on every single
save.** Confirmed directly: uploaded a photo, updated an unrelated field
without re-attaching it, and the photo was gone.

Fixed: each file field is now only overwritten when a new file is
actually present in the request; otherwise the existing file is left
alone. Confirmed the reverse case still works too — re-uploading a new
photo does replace the old one.

**Why this is called out this prominently:** if this repo has any
existing staff profiles with photos/documents that were uploaded once
and have survived any subsequent edit, this fix doesn't touch them. But
if the deployed instance has been hit by this bug already (any profile
where a field was edited after the photo was set), those files are
already gone from the *old* app and this fix only prevents it from
happening again going forward — it cannot recover files that were
already wiped before this pass. Worth a quick manual check of whether any
currently-live staff profiles are missing photos/documents that should be
there.

### 🔒 Basic validation added

Full name is now required (previously: no check — an entirely blank
profile could be created). Email format validated via
`validate_email`. Salary validated as a non-negative integer (see
above). Uploaded images capped at 5MB and the resume PDF at 10MB —
previously no size limit at all on any of the four file uploads, so a
single request could write an arbitrarily large file to disk.

### Also: de-duplication

Add and Update had ~20 near-identical `request.POST.get(...)` lines each;
collapsed into shared `_extract_staff_fields()` / `_extract_staff_files()`
/ `_validate_staff_fields()`, used by both views — the same pattern used
for Company in this pass.

**Verification:** `manage.py check` clean; 17 tests in
`Staff_Profile/tests.py`, including direct reproductions of both crashes
and the file-wipe bug before their fixes (with an explicit test that a
photo *does* still get replaced when a new one is uploaded, so the fix
isn't just "never touch files again"). Full cross-app smoke test still
200s throughout.

---

## Shift_Handover app — full pass

This app tracks cash-count reconciliation at shift changeover — real
money accounting, so the two fixes below are the most consequential in
this pass so far after Authentication's privilege escalation.

### 🐛 The server never verified the cash-count arithmetic — took the client's numbers as-is

`Shift_Handover_Add.html` computes each denomination's amount
(`quantity × face value`) and the grand total in JavaScript
(`calculateAmount`/`calculateTotal`) purely for the live on-screen
display, and marks those `<input>` fields `readonly`. But `readonly` is
a client-side HTML attribute only — it does nothing to what a raw POST
request can contain. The view took `five_hundred_amount`, `total`, etc.
directly from `request.POST` and stored them as submitted, with **no
server-side check that amount actually equals quantity × denomination,
or that total actually equals the sum of the eight line amounts.**

Confirmed directly: POSTed `five_hundred_quantity=2` with
`five_hundred_amount=999999` and `total=1` — the record saved with
those forged values, no error, no rejection. A cash-count reconciliation
record — the entire point of which is catching discrepancies between
counted cash and expected cash — could contain **arbitrary, internally
inconsistent numbers with no relationship to what was actually counted.**

Fixed: `_compute_denominations()` now recomputes every denomination's
total, and the grand total, from the submitted *quantities* server-side
(the one number a `readonly` amount field can't fake as directly — it's
still client input, but the arithmetic connecting it to money is now
authoritative, not merely displayed). The client-submitted
`*_amount`/`total` fields are no longer read at all. Applied to both Add
and Update.

### 🐛 Any authenticated user could rewrite anyone's shift handover record — same class of bug as Authentication's privilege escalation

`Shift_Handover_Update` had no permission check beyond `@login_required`
— but `Shift_Handover_Profile.html` only shows the "Update" link to
`request.user.username == 'SuperAdmin'`. Confirmed directly: logged in
as a plain non-admin account and POSTed to
`/Shift-Handover-Update/<id>/` for a record it didn't own, setting
`shift=HACKED` and (before the fix above) `total=99999` — it worked, no
error, no permission denial. Added the same
`is_superuser or username == 'SuperAdmin'` check used everywhere else in
this pass. (`Shift_Handover_Delete` already had a real ownership/admin
check — that one was fine.)

### 🐛 Confirmed crash: GET on Delete, once authorized, → hard 500

`Shift_Handover_Delete`'s ownership checks each `return redirect(...)`
on failure, but the actual delete only happens inside
`if request.method == 'POST':` with nothing after it — an authorized
user (owner or admin) hitting the URL with a plain GET fell through with
no return statement at all. Reproduced directly: `ValueError: ... didn't
return an HttpResponse object.` Fixed with an explicit non-POST branch.

### 🔒 A "readonly" username field doesn't stop a forged POST from impersonating someone else

Same `readonly`-is-cosmetic issue as the amount fields: the Add form's
username input is pre-filled with `request.user.username` and marked
readonly for display, but the view read it from `request.POST` — a
forged `username` value in a raw POST could attribute a shift handover
to a different user entirely. Fixed: the record is now always attributed
to `request.user`, the field is no longer read from POST data at all.

### 🔒 Silent failure on Add; raw exception text shown on Update

`Shift_Handover_Add` caught exceptions with a bare `print(e)` and no
`messages.error()` at all — a failed submission (e.g. an unparseable
date) silently reloaded a blank form with zero feedback, same pattern
fixed elsewhere in this session. `Shift_Handover_Update` did
`messages.error(request, f"An error occurred: {str(e)}")`, showing raw
exception text. Both now log the real error and show a generic, safe
message.

**Verification:** `manage.py check` clean; 12 tests in
`Shift_Handover/tests.py` covering the forged-amount recomputation (Add
and Update), the impersonation fix, the privilege-escalation fix (both
the negative case and that SuperAdmin retains access), the delete
permission matrix (owner/admin/neither), and the GET-crash
reproduction. PDF receipt template (`ShiftHandoverView.html`) verified to
still render correctly via direct template rendering (this sandbox's
`xhtml2pdf` is broken for unrelated reasons — see earlier session notes —
so PDF views are checked by rendering the template directly rather than
through the full `render_to_pdf()` call). Full cross-app smoke test still
200s throughout.

---

## Revenue app — full pass

### 🐛 Critical, confirmed: money stored as free text silently corrupted the Dashboard's revenue totals

`Deposite_Hotel_Amount` and `Deposite_Food_Amount` were `CharField(max_length=50)`
— and `Dashboard/views.py` runs `Sum('Deposite_Hotel_Amount')` /
`Sum('Deposite_Food_Amount')` directly over them for the dashboard's
revenue figures. Confirmed directly: created two hotel deposits, `'1,500'`
and `'500'` (a comma-formatted amount — an entirely normal way to type
money, especially with Indian thousands-separator conventions) —
`Sum()` returned **501**, not 2000. SQLite's loose typing parses only the
numeric *prefix* of a text value before the first non-numeric character,
so `'1,500'` contributed `1`, not `1500`, to the sum. On a stricter
production database engine (Postgres/MySQL) the same query would likely
have raised a hard error instead of silently returning a wrong number —
either way, this was never safe.

This is a data-modeling problem, not a narrow view-level bug, so it's
fixed at the model level: `Deposite_Hotel_Amount`/`Deposite_Food_Amount`
are now `DecimalField(max_digits=12, decimal_places=2)`. Two migrations:
`0006_normalize_amount_text_before_decimal` (a data migration that strips
commas/whitespace from every existing value first, defaulting anything
still unparseable to `'0'` rather than blocking the schema change) then
`0007_...` (the actual `AlterField` to `DecimalField`). Existing preview
data (`'12500'`, `'500'`) converted cleanly to `Decimal('12500.00')` /
`Decimal('500.00')`.

The views now parse submitted amounts through `_parse_amount()`, which
still *accepts* a comma-formatted amount (stripping it before parsing —
no reason to reject normal typing) but always stores a clean `Decimal`,
so `Sum()` over the column is arithmetically correct by construction
going forward, not just for the values that happen not to contain a
comma.

### 🐛 Confirmed: the actual owner of a deposit could never delete their own record

Both delete views checked `hotel_cash_profile.Deposite_Hotel_Username !=
request.user.username` — comparing a `User` model instance
(`Deposite_Hotel_Username` is a ForeignKey) to a plain string. A `User`
instance is never `==` to a string, so this comparison was always `True`
regardless of actual ownership, meaning the "not authorized" branch
always fired for anyone whose username wasn't literally "SuperAdmin" or
"Admin" — **the true owner of a deposit could never delete their own
entry.** Confirmed directly: logged in as the actual owner, POSTed the
delete, record remained. Fixed by comparing `User` to `User`
(`hotel_cash_profile.Deposite_Hotel_Username == request.user`).

### 🔒 Same "readonly is cosmetic" impersonation gap as Shift_Handover

Both deposit forms pre-fill a readonly `username` field with
`request.user.username` for display; the views read it from
`request.POST` anyway. Fixed the same way as Shift_Handover: the record
is always attributed to `request.user`, the POSTed username is no longer
read.

### 🐛 Confirmed: a blank submitted time crashed the request

`Deposite_Hotel_Time`/`Deposite_Food_Time` are non-nullable `TimeField`s;
the views passed `request.POST.get('..._time', '')` straight through.
Confirmed directly: `Hotel_Cash_Deposite.objects.create(...,
Deposite_Hotel_Time='')` raises `ValidationError` at save time. The form
auto-fills this field via JS on page load, so it's normally unreachable
from the real UI — but a direct POST (or a JS-disabled browser) hit it.
Now validated up front with a friendly message instead of a raw crash.

### 🔒 Silent failure replaced with real feedback; raw exceptions no longer shown

Both deposit views caught exceptions with a bare `print(e)` and no
`messages.error()` — a failed submission silently reloaded a blank form.
Both delete views' non-POST branch rendered `confirm_delete.html`, a
template that has never existed in either app (same class of gap noted
for `update_user_role.html` in the Authentication pass) — always fell
through to the generic error page. Since this branch is unreachable from
the UI (both delete actions are POST-only forms) fixing it changes no
visible behavior; replaced with a proper redirect + message instead of
leaving a reference to a nonexistent template in place.

**Verification:** `manage.py check` clean; both migrations applied
cleanly to the seeded preview DB (existing amounts converted correctly);
11 tests in `Revenue/tests.py` covering the `Sum()` corruption
reproduction and fix, the ownership-comparison bug reproduction and fix,
the impersonation fix, the blank-time crash reproduction and fix, and the
delete permission matrix (owner/non-owner/SuperAdmin/GET-doesn't-crash).
PDF receipt templates verified via direct rendering. Full cross-app smoke
test still 200s throughout.

---

