# UI migration — status

Source of the theme: `Mihir-Jungiwala/hotel-pallav-website`, specifically its
`admin/*` back-office skin (`includes/admin-layout-top.php`,
`includes/admin-nav.php`, `assets/css/site.css` tokens). That's the closer
analog to this app than the public guest-facing pages — both are internal
panels behind a login.

**Brand tokens carried over exactly:** the `pallav` violet scale
(`#F7F4FF`→`#4A1A8F`) and `gold` scale, Playfair Display for headings /
Inter for UI text, the हॉटेल पल्लव roundel mark, the glass sidebar with the
gradient active-indicator, the mobile clip-path drawer, `adminFadeIn` /
scroll-reveal motion.

## What's converted (this pass)

- `templates/base.html` — the shared shell: desktop sidebar, mobile drawer,
  flash messages wired to Django's `messages` framework, scroll-reveal JS.
- `templates/guest_base.html` — the centered-card shell for pages outside
  the sidebar (login, password reset).
- `Main/context_processors.py` — builds the sidebar's nav groups
  server-side from real `{% url %}` names, with active-state highlighting.
  Add a page to the nav by adding one line here, not by editing 48 files.
- `Authentication/templates/Login.html`
- `Dashboard/templates/Dashboard.html`
- `Authentication/templates/Authentication_User_Profile.html`

Also fixed in the process (both were blocking, not cosmetic):

- `Dashboard/views.py` rendered `"dashboard.html"`, a file that doesn't
  exist — the real one is `Dashboard.html`. That's a case-sensitivity bug
  that only shows up on Linux; it was silently crashing this exact page.
- Two URL patterns were both named `deleteUserprofile`
  (`Authentication`'s and `Staff_Profile`'s user-delete views). `{% url %}`
  resolves to whichever is registered last, so the Authentication page's
  delete button was one `{% url %}` conversion away from silently deleting
  Staff Profile records instead. Staff Profile's route is now named
  `StaffProfileUserDelete`.

## What's still on the old Bootstrap/dark-gradient skin

Everything else — 45 of 48 templates. They still work; they just don't
match yet: Revenue, Expense, Shift Handover, Bill Master (all of it),
Company Profile, Staff Profile, Reports, and the remaining Authentication
pages (Registration, Reset Password, Change Password, error page).

## Recommended order for the rest

Group by how much of the app each page's markup is shared with, largest
payoff first:

1. **Bill Master** (10 templates) — biggest, most form-heavy area; also
   the one with the money-calculation bugs flagged in the production
   review, so worth doing carefully rather than fast.
2. **Revenue / Expense** (11 templates) — same list+form+PDF-view pattern
   repeated per cash type; a shared partial for the list table and the
   PDF-view page pays for itself here.
3. **Shift Handover, Company, Staff Profile** (11 templates).
4. **Reports**, and the remaining **Authentication** pages (4 templates) —
   small, low-traffic, fine to leave for last.

Each page follows the same recipe used here: `{% extends "base.html" %}`
(or `guest_base.html` for logged-out pages), drop the inline `<style>`
block, replace the Bootstrap table/form classes with the Tailwind
equivalents already established in the three converted pages, keep every
`{% csrf_token %}`, form field name, and view-logic branch byte-for-byte
unchanged. This pass is UI only — no template here should change what a
form submits or what a view does with it.
