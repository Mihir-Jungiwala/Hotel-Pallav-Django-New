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
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the user is authenticated
        if request.user.is_authenticated:
            try:
                # Get the latest authentication record for the user
                auth_record = Authentication.objects.filter(user=request.user).order_by('-activity_time').first()

                if auth_record:
                    # Calculate the time difference since the last activity
                    time_since_last_activity = timezone.now() - auth_record.activity_time

                    # If the user has been inactive for more than 10 minutes, log them out
                    if time_since_last_activity.total_seconds() > 600:  # 10 minutes in seconds
                        logout(request)
                        return redirect('Login_In')  # Redirect to login page or another appropriate view

            except Authentication.DoesNotExist:
                pass  # No activity record found, continue with the request

        # Process the request
        response = self.get_response(request)

        # Update the activity time in the auth record
        if request.user.is_authenticated:
            auth_record = Authentication.objects.filter(user=request.user).order_by('-activity_time').first()
            if auth_record:
                auth_record.activity_time = timezone.now()
                auth_record.save()

        return response


