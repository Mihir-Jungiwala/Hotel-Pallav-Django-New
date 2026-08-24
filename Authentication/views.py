import logging
from datetime import timedelta
from django.core.cache import cache
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import Authentication
from .decorators import admin_required, protect_superadmin_account
from .Reset_Password_Email import Send_Reset_Password_Mail
import uuid
from django.utils import timezone
import pytz # type: ignore
import re
from django.contrib.auth.hashers import check_password
from django.db import transaction

logger = logging.getLogger(__name__)

PASSWORD_PATTERN = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+])[A-Za-z\d!@#$%^&*()_+]{8,}$'

LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300  # 5 minutes


def _login_attempts_key(username, ip):
    # Keyed on username+IP together: keeps one attacker guessing a single
    # username from locking out that username for everyone else on a
    # shared IP (e.g. an office), while still throttling a single source.
    return f"login_attempts:{username.lower()}:{ip}"


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def Login_IN(request):
    try:
        if request.method == "POST":
            username = (request.POST.get('username') or '').strip()
            password = request.POST.get('password') or ''
            ip = _client_ip(request)

            if not username or not password:
                messages.error(request, 'Please enter both a username and a password.')
                return redirect('Login_In')

            attempts_key = _login_attempts_key(username, ip)
            attempts = cache.get(attempts_key, 0)
            if attempts >= LOGIN_MAX_ATTEMPTS:
                logger.warning(f"Login locked out for '{username}' from {ip}: too many failed attempts.")
                messages.error(request, 'Too many failed login attempts. Please try again in a few minutes.')
                return redirect('Login_In')

            with transaction.atomic():
                # authenticate() already rejects a deactivated user by
                # returning None (Django's ModelBackend checks is_active
                # internally), so a deactivated account and a wrong
                # password are indistinguishable here — same as a wrong
                # username. That's the correct security posture (no
                # "your account is disabled" oracle for an attacker to
                # probe), so there's no separate is_active branch to
                # write; user is never None-but-inactive by this point.
                user = authenticate(request, username=username, password=password)

                if user is None:
                    cache.set(attempts_key, attempts + 1, timeout=LOGIN_LOCKOUT_SECONDS)
                    logger.info(f"Failed login for '{username}' from {ip} (attempt {attempts + 1}).")
                    messages.error(request, 'Invalid Username or Invalid Password')
                    return redirect('Login_In')

                login(request, user)
                cache.delete(attempts_key)

                # login() cycles the session key; make sure it's persisted
                # before we read it so this row is tied to the real key.
                if not request.session.session_key:
                    request.session.save()

                current_time = timezone.now().astimezone(pytz.timezone('Asia/Kolkata'))
                Authentication.objects.create(
                    user=user,
                    activity_type='Login',
                    login_date=current_time.date(),
                    login_time=current_time.time(),
                    session_key=request.session.session_key,
                )

            logger.info(f"User '{username}' logged in from {ip}.")
            return redirect('/Dashboard-Profile/')

        return render(request, "Login.html")
    except Exception as e:
        logger.error(f"Unexpected error in Login_IN: {e}", exc_info=True)
        return render(request, 'error_page.html')

@login_required(login_url='Login_In')
def Login_OUT(request):
    try:
        with transaction.atomic():
            user = request.user
            session_key = request.session.session_key

            # Prefer the row for *this* session; only fall back to
            # "most recent login row for this user" for legacy rows that
            # predate session_key tracking (see Authentication/models.py).
            login_record = None
            if session_key:
                login_record = Authentication.objects.filter(
                    user=user, activity_type='Login', session_key=session_key,
                ).order_by('-activity_time').first()
            if login_record is None:
                login_record = Authentication.objects.filter(
                    user=user, activity_type='Login',
                ).order_by('-activity_time').first()

            if login_record:
                current_time = timezone.now().astimezone(pytz.timezone('Asia/Kolkata'))
                login_record.logout_date = current_time.date()
                login_record.logout_time = current_time.time()
                login_record.calculate_minutes_logged_in()
                login_record.save()

            logout(request)
            messages.success(request, 'You have been logged out successfully.')

        return redirect('Login_In')
    except Exception:
        return render(request, 'error_page.html')  # Render the error page in case of an unexpected error

@login_required(login_url='Login_In')
@admin_required
def Registration(request):
    try:
        if request.method != "POST":
            return render(request, "Registration.html")

        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        confirm_password = request.POST.get('confirm_password') or ''
        email = (request.POST.get('email') or '').strip()
        role = request.POST.get('role')

        # Uses messages.error() (rendered globally by base.html) rather
        # than a template-context 'error' variable — Registration.html
        # never actually displayed that variable, so every validation
        # failure here previously just reloaded a blank form with no
        # feedback at all. See docs/backend-hardening-log.md.
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, "Registration.html")

        if not re.match(PASSWORD_PATTERN, password):
            messages.error(
                request,
                'Password must be at least 8 characters and include an uppercase letter, '
                'a lowercase letter, a digit, and a special character.',
            )
            return render(request, "Registration.html")

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, "Registration.html")

        if email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Please enter a valid email address.')
                return render(request, "Registration.html")

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, f'The username "{username}" is already taken.')
            return render(request, "Registration.html")

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=email,
                )

                if role == 'Admin':
                    user.is_staff = True
                    user.is_superuser = True
                elif role == 'Editor':
                    user.is_staff = True
                    user.is_superuser = False
                else:
                    user.is_staff = False
                    user.is_superuser = False

                user.set_password(password)
                user.save()
        except IntegrityError:
            # Race: two requests created the same username between the
            # exists() check above and the insert. The unique constraint
            # is the real guard; the exists() check above is just a
            # friendlier first line of defense for the common case.
            messages.error(request, f'The username "{username}" is already taken.')
            return render(request, "Registration.html")

        logger.info(f"User '{request.user.username}' registered new account '{username}' with role '{role}'.")
        messages.success(request, f'User "{username}" created successfully.')
        return redirect('/Registration-User-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Registration: {e}", exc_info=True)
        messages.error(request, 'An error occurred while processing your registration.')
        return render(request, 'error_page.html')

@login_required(login_url='Login_In')
@admin_required
def Delete_User_Profile(request, id):
    try:
        user_obj = get_object_or_404(User, id=id)

        if protect_superadmin_account(user_obj, request, 'deleted'):
            return redirect('/Registration-User-Profile/')

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Registration-User-Profile/')

        with transaction.atomic():
            deleted_username = user_obj.username
            user_obj.delete()

        logger.info(f"User '{request.user.username}' deleted account '{deleted_username}'.")
        messages.success(request, 'User profile deleted successfully.')
    except Exception as e:
        logger.error(f"Unexpected error in Delete_User_Profile: {e}", exc_info=True)
        messages.error(request, 'An error occurred while deleting the user profile.')

    return redirect('/Registration-User-Profile/')


@login_required(login_url='Login_In')
@admin_required
def Registration_User_Profile(request):
    # Previously only @login_required — the full user roster (usernames,
    # roles) was readable by any authenticated user, including the
    # lowest-privilege "Viewer" role, even though the sidebar only shows
    # this link to admins. @admin_required makes the view match what the
    # nav already implies.
    try:
        if request.user.username == 'SuperAdmin':
            queryset = User.objects.all()
        else:
            queryset = User.objects.exclude(username='SuperAdmin')

        return render(request, "Authentication_User_Profile.html", {'users': queryset})
    except Exception as e:
        logger.error(f"Unexpected error in Registration_User_Profile: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})


RESET_PASSWORD_MAX_ATTEMPTS = 5
RESET_PASSWORD_LOCKOUT_SECONDS = 300  # 5 minutes


def Reset_Password(request):
    if request.method != "POST":
        return render(request, "Reset_Password.html")

    identifier = (request.POST.get('username') or '').strip()
    ip = _client_ip(request)

    # One generic outcome message regardless of whether the username
    # exists, is inactive, or the email send fails — the previous version
    # showed a different message for "no such user" vs "inactive user",
    # which lets an attacker enumerate valid usernames by watching which
    # message comes back. Same behavior, same UX, one message.
    generic_response = redirect('/Reset-Password/')
    generic_success_message = (
        "If an account matches that username, we've sent password reset instructions to its email address."
    )

    if not identifier:
        messages.error(request, 'Please enter a username.')
        return generic_response

    throttle_key = f"reset_password_attempts:{identifier.lower()}:{ip}"
    attempts = cache.get(throttle_key, 0)
    if attempts >= RESET_PASSWORD_MAX_ATTEMPTS:
        logger.warning(f"Reset-password request throttled for '{identifier}' from {ip}.")
        messages.error(request, 'Too many reset requests. Please try again in a few minutes.')
        return generic_response
    cache.set(throttle_key, attempts + 1, timeout=RESET_PASSWORD_LOCKOUT_SECONDS)

    target_user = User.objects.filter(username__iexact=identifier).first()

    if not target_user or not target_user.is_active or not target_user.email:
        logger.info(f"Reset-password requested for unknown/inactive/emailless identifier '{identifier}' from {ip}.")
        messages.success(request, generic_success_message)
        return generic_response

    # Password-reset needs *a* row to hold the token, but Authentication
    # rows are otherwise only created by Login_IN — meaning a user who
    # registered but has never logged in yet had no row to attach a
    # token to, so Reset_Password always silently no-op'd for them (the
    # generic response looks identical whether or not an email actually
    # went out, so this was invisible unless you checked the outbox).
    # Reusing their most recent row when one exists keeps existing
    # behavior; creating one on demand is the fix for the "never logged
    # in yet" case.
    user_obj = Authentication.objects.filter(user=target_user).order_by('-activity_time').first()
    if user_obj is None:
        user_obj = Authentication.objects.create(user=target_user, activity_type='Login')

    try:
        token = str(uuid.uuid4())
        user_obj.forgot_password_token = token
        user_obj.email_sent_time = timezone.now()
        user_obj.token_used = False
        user_obj.save(update_fields=['forgot_password_token', 'email_sent_time', 'token_used'])

        Send_Reset_Password_Mail(
            email=user_obj.user.email,
            first_name=user_obj.user.first_name,
            last_name=user_obj.user.last_name,
            token=token,
            request=request,
        )
        logger.info(f"Password reset email sent for '{identifier}'.")
        messages.success(request, generic_success_message)
        return redirect('Login_In')

    except Exception as e:
        # Do not leak whether the user exists even on send failure —
        # log the real error, show the same generic message.
        logger.error(f"Error sending reset-password email for '{identifier}': {e}", exc_info=True)
        messages.success(request, generic_success_message)
        return generic_response

def Change_Password(request, token):
    try:
        logger.debug(f"Change_Password requested with token {token}")

        # Use atomic transaction
        with transaction.atomic():
            # Get all ActivityLog objects based on the forgot_password_token
            activity_logs = Authentication.objects.filter(forgot_password_token=token)

            if not activity_logs:
                messages.error(request, 'Invalid or expired token.')
                return redirect('/Reset-Password/')

            # Iterate over all the activity logs for the given token
            for activity_log in activity_logs:
                # A row can only carry a non-null forgot_password_token if
                # Reset_Password set it, and that always sets
                # email_sent_time in the same save() — but guard anyway
                # rather than trust that invariant holds for every row.
                if not activity_log.email_sent_time:
                    messages.error(request, 'Invalid or expired token.')
                    return redirect('/Reset-Password/')

                # Check if the token is valid and has not expired
                expiration_time = activity_log.email_sent_time + timedelta(minutes=10)

                if timezone.now() > expiration_time:
                    messages.error(request, 'This link has expired. Please generate a new one.')
                    return redirect('/Reset-Password/')

                # Check if the token has already been used
                if activity_log.token_used:
                    messages.error(request, 'Sorry, but it seems that the link has already been used.')
                    return redirect('/Reset-Password/')

                if request.method == "POST":
                    new_password = request.POST.get('new_password') or ''
                    confirm_password = request.POST.get('confirm_password') or ''

                    # Ensure both passwords match
                    if new_password != confirm_password:
                        messages.error(request, 'Both passwords should be equal.')
                        return render(request, "Change_Password.html", {'user_id': activity_log.user.id})

                    # Validate password strength
                    if not re.match(PASSWORD_PATTERN, new_password):
                        messages.error(request, 'Password does not meet the complexity requirements.')
                        return render(request, "Change_Password.html", {'user_id': activity_log.user.id})

                    user_obj = activity_log.user

                    # Ensure the new password is different from the old password
                    if user_obj.check_password(new_password):
                        messages.error(request, 'New password must be different from the old password.')
                        return render(request, "Change_Password.html", {'user_id': activity_log.user.id})

                    # Set the new password
                    user_obj.set_password(new_password)
                    user_obj.save()

                    # Update the ActivityLog to indicate the token has been used
                    activity_log.password_change_time = timezone.now()
                    activity_log.password_change_duration = (activity_log.password_change_time - activity_log.email_sent_time).total_seconds() // 60
                    activity_log.token_used = True
                    activity_log.save()

                    logger.info(f"Password changed via reset token for user '{user_obj.username}'.")
                    messages.success(request, 'Password changed successfully.')
                    return redirect('Login_In')  # Redirect to login page after successful password change

            # If the request method is GET, render the page for the first matching activity log
            return render(request, "Change_Password.html", {'user_id': activity_logs[0].user.id})

    except Exception as e:
        logger.error(f"Unexpected error in Change_Password: {e}", exc_info=True)
        messages.error(request, 'An error occurred. Please try again later.')
        return render(request, "Reset_Password.html")
def Error_Page(request):
    # A plain render — nothing here writes to the database, so the
    # transaction.atomic() wrapper was pure overhead on every hit of
    # this page.
    return render(request, 'error_page.html')

@login_required(login_url='Login_In')
@admin_required
def User_Active_Deactive_Status(request, id):
    try:
        user = get_object_or_404(User, id=id)

        if protect_superadmin_account(user, request, 'deactivated'):
            return redirect('/Registration-User-Profile/')

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Registration-User-Profile/')

        with transaction.atomic():
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])

        logger.info(f"User '{request.user.username}' set '{user.username}' active={user.is_active}.")
        messages.success(request, "User status updated successfully.")
    except Exception as e:
        logger.error(f"Unexpected error in User_Active_Deactive_Status: {e}", exc_info=True)
        messages.error(request, "An error occurred while updating the user's status.")

    return redirect('/Registration-User-Profile/')

VALID_ROLES = {'Admin', 'Editor', 'Viewer'}


@login_required(login_url='Login_In')
@admin_required
def Update_User_Role(request, id):
    # Previously reachable by any authenticated user with no permission
    # check at all — meaning a "Viewer" account could POST directly to
    # this URL for their own id with role=Admin and self-promote to
    # superuser. @admin_required closes that; protect_superadmin_account
    # additionally stops anyone (including another admin) from demoting
    # the one account the app's own admin tooling depends on.
    try:
        user = get_object_or_404(User, id=id)

        if request.method == "POST":
            new_role = request.POST.get('role')
            if new_role not in VALID_ROLES:
                messages.error(request, 'Please select a valid role.')
                return redirect('/Registration-User-Profile/')

            if protect_superadmin_account(user, request, 'changed'):
                return redirect('/Registration-User-Profile/')

            with transaction.atomic():
                if new_role == 'Admin':
                    user.is_staff = True
                    user.is_superuser = True
                elif new_role == 'Editor':
                    user.is_staff = True
                    user.is_superuser = False
                else:
                    user.is_staff = False
                    user.is_superuser = False
                user.save(update_fields=['is_staff', 'is_superuser'])

            logger.info(f"User '{request.user.username}' set '{user.username}' role to '{new_role}'.")
            messages.success(request, 'User role updated successfully.')
            return redirect('/Registration-User-Profile/')

        else:
            # Dead branch, kept exactly as it was: no link or form in the
            # app ever GETs this URL (Registration_User_Profile.html
            # posts the role change inline with a <select> + submit
            # button), and 'update_user_role.html' has never existed as
            # a template — so this has always fallen through to the
            # except block below and rendered the generic error page.
            # See docs/backend-hardening-log.md for why this is left
            # alone rather than fabricated: preserving unreachable
            # pre-existing behavior, not inventing a new page for a path
            # nothing in the UI triggers.
            current_role = 'Admin' if user.is_superuser else 'Editor' if user.is_staff else 'Viewer'
            return render(request, "update_user_role.html", {'user': user, 'current_role': current_role})

    except Exception as e:
        logger.error(f"Unexpected error in Update_User_Role: {e}", exc_info=True)
        messages.error(request, 'An error occurred while updating the user role.')
        return redirect('/Registration-User-Profile/')
