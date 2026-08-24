from datetime import timedelta
from venv import logger
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout 
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Authentication
from .Reset_Password_Email import Send_Reset_Password_Mail
import uuid
from django.utils import timezone
import pytz # type: ignore
import re        
from django.contrib.auth.hashers import check_password
from django.db import transaction
    

def Login_IN(request):
    try:
        # Using atomic transaction
        with transaction.atomic():
            if request.method == "POST":
                username = request.POST.get('username')
                password = request.POST.get('password')

                user = authenticate(request, username=username, password=password)

                if user is None:
                    messages.error(request, 'Invalid Username or Invalid Password')
                    return redirect('Login_In')
                
                login(request, user)

                current_time = timezone.now().astimezone(pytz.timezone('Asia/Kolkata'))
                Authentication.objects.create(
                    user=user,
                    activity_type='Login',
                    login_date=current_time.date(),
                    login_time=current_time.time()
                )

                return redirect('/Dashboard-Profile/') 

            return render(request, "Login.html")
    except Exception as e:
        print(e)
        return render(request, 'error_page.html')  # Render the error page in case of an une

@login_required(login_url='Login_In')
def Login_OUT(request):
    try:
        # Using atomic transaction
        with transaction.atomic():
            if request.user.is_authenticated:
                user = request.user

                latest_login = Authentication.objects.filter(user=user, activity_type='Login').order_by('-activity_time').first()

                if latest_login:
                    current_time = timezone.now().astimezone(pytz.timezone('Asia/Kolkata'))
                    latest_login.logout_date = current_time.date()
                    latest_login.logout_time = current_time.time()

                    latest_login.calculate_minutes_logged_in()
                    latest_login.save()

                logout(request)
                messages.success(request, 'You have been logged out successfully.')  # Display success message

        return redirect('Login_In')
    except Exception:
        return render(request, 'error_page.html')  # Render the error page in case of an unexpected error

@login_required(login_url='Login_In')
def Registration(request):
    try:
        # Using atomic transaction
        with transaction.atomic():
            if request.method == "POST":
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                username = request.POST.get('username')
                password = request.POST.get('password')
                confirm_password = request.POST.get('confirm_password')
                email = request.POST.get('email')
                role = request.POST.get('role')  # Added role field in the form

                # Password regex pattern
                password_pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+])[A-Za-z\d!@#$%^&*()_+]{8,}$'
                
                # Check if the password matches the pattern
                if not re.match(password_pattern, password):
                    return render(request, "Registration.html", {'error': 'Password does not meet requirements.'})
                
                # Check if passwords match
                if password != confirm_password:
                    return render(request, "Registration.html", {'error': 'Passwords do not match.'})
                
                # Create the user object
                user = User.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=email,
                )

                # Assign role based on selection
                if role == 'Admin':
                    user.is_staff = True
                    user.is_superuser = True
                elif role == 'Editor':
                    user.is_staff = True
                    user.is_superuser = False
                else: 
                    user.is_staff = False
                    user.is_superuser = False
                
                # Set password and save user
                user.set_password(password)
                user.save()

                return redirect('/Registration-User-Profile/')
            else:
                return render(request, "Registration.html")
    except Exception:
        messages.error(request, 'An error occurred while processing your registration.')
        return render(request, 'error_page.html')  # Render the error page in case of an unexpected error

@login_required(login_url='Login_In')
def Delete_User_Profile(request, id):
    try:
        # Using atomic transaction
        with transaction.atomic():
            # Try to get the User object with the given id
            user_obj = User.objects.get(id=id)
            # Delete the User object
            user_obj.delete()
            messages.success(request, 'User profile deleted successfully.')
    except User.DoesNotExist:
        # If the User object does not exist
        messages.error(request, 'User profile does not exist.')
    except Exception:
        # For other unexpected exceptions
        messages.error(request, 'An error occurred while deleting the user profile.')
        return render(request, 'error_page.html')  # Render the error page in case of an unexpected error

    return redirect('/Registration-User-Profile/')


@login_required(login_url='Login_In')
def Registration_User_Profile(request):
    try:
        # Using atomic transaction
        with transaction.atomic():
            # Check if the logged-in user is 'SuperAdmin'
            if request.user.username == 'SuperAdmin':
                queryset = User.objects.all()  # SuperAdmin can see all users
            else:
                queryset = User.objects.exclude(username='SuperAdmin')  # Other users cannot see SuperAdmin
            
            # Prepare context to be passed to the template
            context = {'users': queryset}  # Using 'users' instead of 'Authentication' for clarity
            
            # Render the 'Authentication_User_Profile.html' template with the context
            return render(request, "Authentication_User_Profile.html", context)
    
    except Exception:
        # Return a generic error page or redirect to a specific URL
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})


def Reset_Password(request):
    if request.method != "POST":
        return render(request, "Reset_Password.html")

    # Fetch the 'username' field from the form
    identifier = request.POST.get('username')  # Use 'username' to match the form field name
    print(f"Identifier: {identifier}")  # Debug print

    # Search for the user in the database
    user_obj = Authentication.objects.filter(user__username__iexact=identifier).first()
    print(f"User Object: {user_obj}")  # Debug print

    if not user_obj:
        messages.error(request, 'Invalid Username or Identifier')
        return redirect('/Reset-Password/')

    # Add new check for active user
    if not user_obj.user.is_active:
        messages.error(request, 'Invalid User')
        return redirect('/Reset-Password/')

    try:
        # Generate and update the token
        token = str(uuid.uuid4())
        user_obj.forgot_password_token = token
        user_obj.email_sent_time = timezone.now()
        user_obj.token_used = False
        user_obj.save()

        # Send the reset password email
        Send_Reset_Password_Mail(
            email=user_obj.user.email,
            first_name=user_obj.user.first_name,
            last_name=user_obj.user.last_name,
            token=token,
        )
        messages.success(request, 'An email has been sent to reset your password.')
        return redirect('Login_In')

    except Exception as e:
        logger.error(f'Error in Reset_Password: {str(e)}')
        return render(request, "error_page.html", {'error_message': f'An error occurred: {str(e)}'})

def Change_Password(request, token):
    try:
        print(f"Received token: {token}")  # Debug: Log the token

        # Use atomic transaction
        with transaction.atomic():
            # Get all ActivityLog objects based on the forgot_password_token
            activity_logs = Authentication.objects.filter(forgot_password_token=token)

            if not activity_logs:
                messages.error(request, 'Invalid or expired token.')
                return redirect('/Reset-Password/')

            # Iterate over all the activity logs for the given token
            for activity_log in activity_logs:
                # Check if the token is valid and has not expired
                expiration_time = activity_log.email_sent_time + timedelta(minutes=10)
                print(f"Expiration time: {expiration_time}, Current time: {timezone.now()}")  # Debug: Log expiration time and current time

                if timezone.now() > expiration_time:
                    messages.error(request, 'This link has expired. Please generate a new one.')
                    return redirect('/Reset-Password/')

                # Check if the token has already been used
                if activity_log.token_used:
                    messages.error(request, 'Sorry, but it seems that the link has already been used.')
                    return redirect('/Reset-Password/')

                if request.method == "POST":
                    new_password = request.POST.get('new_password')
                    confirm_password = request.POST.get('confirm_password')

                    # Ensure both passwords match
                    if new_password != confirm_password:
                        messages.error(request, 'Both passwords should be equal.')
                        return render(request, "Change_Password.html", {'user_id': activity_log.user.id})

                    # Validate password strength
                    if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+])[A-Za-z\d!@#$%^&*()_+]{8,}$', new_password):
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

                    messages.success(request, 'Password changed successfully.')
                    return redirect('Login_In')  # Redirect to login page after successful password change

            # If the request method is GET, render the page for the first matching activity log
            return render(request, "Change_Password.html", {'user_id': activity_logs[0].user.id})

    except Exception as e:
        messages.error(request, f'An error occurred: {e}. Please try again later.')
        return render(request, "Reset_Password.html")
def Error_Page(request):
    try:
        # Using atomic transaction
        with transaction.atomic():
            return render(request, 'error_page.html')
    except Exception:
        return render(request, 'error_page.html', {'error_message': 'An unexpected error occurred.'})

@login_required(login_url='Login_In')
def User_Active_Deactive_Status(request, id):
    try:
        with transaction.atomic():  # Begin a transaction
            # Retrieve the user by id
            user = get_object_or_404(User, id=id)

            if request.method == 'POST':
                # Handle the activation/deactivation logic
                user.is_active = not user.is_active  # Toggle the active status
                user.save()
                # Add a success message
                messages.success(request, "User status updated successfully.")

    except Exception as e:
        # Log the exception or handle it as necessary
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect('/Registration-User-Profile/')  # Redirect to the specified URL

@login_required(login_url='Login_In')
def Update_User_Role(request, id):
    try:
        user = get_object_or_404(User, id=id)  # Retrieve user by ID

        if request.method == "POST":
            new_role = request.POST.get('role')

            # Assign role based on selection
            if new_role == 'Admin':
                user.is_staff = True
                user.is_superuser = True
            elif new_role == 'Editor':
                user.is_staff = True
                user.is_superuser = False
            else: 
                user.is_staff = False
                user.is_superuser = False
            
            # Save the changes
            user.save()
            messages.success(request, 'User role updated successfully.')
            return redirect('/Registration-User-Profile/')  # Redirect after successful update

        else:
            # Render the update role form with the current role
            current_role = 'Admin' if user.is_superuser else 'Editor' if user.is_staff else 'Viewer'
            return render(request, "update_user_role.html", {'user': user, 'current_role': current_role})

    except Exception as e:
        messages.error(request, f'An error occurred while updating the user role: {str(e)}')
        return redirect('/Registration-User-Profile/')
