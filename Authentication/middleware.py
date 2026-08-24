from django.shortcuts import redirect
from django.utils import timezone
from django.contrib.auth import logout
from .models import Authentication  
from datetime import timedelta # Import timedelta for time calculations
import logging  # Import the logging module for logging messages and errors
from django.db import transaction  # Import transaction management for atomic database operations
from django.shortcuts import redirect  # Import redirect function for redirecting HTTP requests
from django.contrib.auth import logout  # Import logout function to log users out
from django.utils import timezone  # Import timezone for handling date and time



# Set up logging for this module
logger = logging.getLogger(__name__)

class SuperAdminOnlyMiddleware:
    def __init__(self, get_response):
        # Store the get_response callable for later use
        self.get_response = get_response

    def __call__(self, request):
        # Begin atomic transaction to ensure database operations are safe
        with transaction.atomic():
            # Check if the request is targeting the admin panel and if the user is authenticated
            if request.path.startswith('/admin/') and request.user.is_authenticated:
                try:
                    # Get the latest authentication record for the user
                    user_profile = Authentication.objects.filter(user=request.user).order_by('-id').first()

                    # If no profile exists, redirect to the dashboard
                    if not user_profile:
                        logger.error(f"User {request.user.username} does not have a profile assigned.")
                        return redirect('/Dashboard-Profile/')  

                    # Allow only the user with username 'SuperAdmin' to access the admin panel
                    if user_profile.user.username != 'SuperAdmin':
                        logger.warning(f"User {request.user.username} attempted to access the admin panel without the Superadmin role.")
                        return redirect('/Dashboard-Profile/')  

                except Exception as e:
                    # Log any unexpected exceptions that occur during the process
                    logger.error(f"An unexpected error occurred for user {request.user.username}: {str(e)}")
                    return redirect('/Error/')  

        # If all checks pass, process the request normally and return the response
        response = self.get_response(request)
        return response


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
    """

    ACTIVITY_WRITE_THROTTLE_SECONDS = 30

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_record = None

        if request.user.is_authenticated:
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


