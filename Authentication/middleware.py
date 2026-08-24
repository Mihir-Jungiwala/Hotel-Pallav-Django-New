import logging

from django.shortcuts import redirect
from django.utils import timezone
from django.contrib.auth import logout
from .models import Authentication

logger = logging.getLogger(__name__)

class SuperAdminOnlyMiddleware:
    """Restricts /admin/ to the SuperAdmin account.

    Hardening note: this previously queried Authentication.objects.filter(
    user=request.user).order_by('-id').first() on every /admin/ request
    just to read that row's .user.username — which is always just
    request.user.username, so the query was both pointless (an extra DB
    round trip returning data the request already has) and fragile (a
    user with zero Authentication rows — e.g. one created directly via
    `manage.py createsuperuser` who never logged in through Login_IN —
    would read as "no profile assigned" and get redirected away from
    /admin/ even if they *are* SuperAdmin). Checking request.user.username
    directly avoids both problems, and there's nothing here that writes
    to the database, so the transaction.atomic() wrapper it had was
    pure overhead — removed along with it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/') and request.user.is_authenticated:
            if request.user.username != 'SuperAdmin':
                logger.warning(f"User {request.user.username} attempted to access the admin panel without the SuperAdmin role.")
                return redirect('/Dashboard-Profile/')

        return self.get_response(request)


class AutoLogoutMiddleware:
    """Enforces a 10-minute inactivity timeout and stamps the user's last
    activity time on every request.

    Hardening notes (see docs/backend-hardening-log.md):
    - The record is fetched once per request and reused for both the
      timeout check and the post-response stamp, instead of two separate
      queries — halves the DB round-trips this middleware makes per
      authenticated request.
    - The activity-time write is throttled to once every ACTIVITY_WRITE_
      THROTTLE_SECONDS: under normal browsing (rapid page-to-page
      navigation) this cuts write volume substantially without weakening
      the 10-minute timeout, since the timeout window is far larger than
      the throttle window.
    - Looked up by session_key first (this session's own record), falling
      back to "most recent row for this user" only for legacy rows that
      predate session_key tracking. Previously this always used the
      user-wide "most recent" lookup, so a second concurrent login (or
      even just old leftover rows) for the same user could make one
      session's idle timeout read a completely different session's
      activity — a session that should time out silently never did, or
      one that shouldn't could get logged out by an unrelated session
      going idle. Tying the check to the actual browser session that
      Django's own session framework already identifies fixes this at
      the source rather than papering over it.
    """

    ACTIVITY_WRITE_THROTTLE_SECONDS = 30

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_record = None

        if request.user.is_authenticated:
            session_key = request.session.session_key
            if session_key:
                auth_record = Authentication.objects.filter(
                    user=request.user, session_key=session_key,
                ).order_by('-activity_time').first()
            if auth_record is None:
                auth_record = Authentication.objects.filter(user=request.user).order_by('-activity_time').first()

            if auth_record:
                time_since_last_activity = timezone.now() - auth_record.activity_time
                if time_since_last_activity.total_seconds() > 600:  # 10 minutes
                    logout(request)
                    return redirect('Login_In')

        response = self.get_response(request)

        if request.user.is_authenticated and auth_record:
            now = timezone.now()
            if (now - auth_record.activity_time).total_seconds() >= self.ACTIVITY_WRITE_THROTTLE_SECONDS:
                auth_record.activity_time = now
                auth_record.save(update_fields=['activity_time'])

        return response


