from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def is_admin_user(user):
    """The app's one definition of "admin" — used consistently across
    templates (nav visibility), the SuperAdminOnlyMiddleware admin-panel
    gate, and now every admin-only view. A single source of truth here
    means a future role change only has to happen in one place."""
    return user.is_authenticated and (user.is_superuser or user.username == 'SuperAdmin')


def admin_required(view_func):
    """Blocks a view at the server, not just at the template.

    Several admin actions (register a user, delete a user, change a
    user's role, activate/deactivate a user) were previously gated only
    by hiding the button in the template for non-admins — the views
    themselves had no permission check beyond @login_required, so any
    authenticated user (including the lowest-privilege "Viewer" role)
    could reach them directly with a raw POST request and, for example,
    promote their own account to Admin via Update-User-Role. This
    decorator closes that gap.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_admin_user(request.user):
            messages.error(request, "You don't have permission to do that.")
            return redirect('/Dashboard-Profile/')
        return view_func(request, *args, **kwargs)

    return _wrapped


def protect_superadmin_account(target_user, request, action_description):
    """Returns True (and sets an error message) if `target_user` is the
    SuperAdmin account and the action should be blocked. The SuperAdmin
    account is the one account that must always exist, always be active,
    and always keep its role — losing it locks the whole app's admin
    tooling out from under every other admin.
    """
    if target_user.username == 'SuperAdmin':
        messages.error(request, f"The SuperAdmin account can't be {action_description}.")
        return True
    return False
