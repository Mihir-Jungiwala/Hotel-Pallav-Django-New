import logging
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone as dj_timezone
from pytz import timezone

from .models import User_Profile

logger = logging.getLogger(__name__)

# Files this app accepts get a hard size ceiling before touching the
# filesystem — previously unbounded, so a single request could write an
# arbitrarily large file to disk (a storage-exhaustion DoS, accidental or
# not). Images and the resume PDF have separate ceilings since a resume
# legitimately needs more headroom than a profile photo.
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024   # 5 MB
MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _extract_staff_fields(request):
    date_of_birth_str = request.POST.get('date_of_birth', '')
    date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date() if date_of_birth_str else None

    return {
        'User_Full_Name': (request.POST.get('full_name') or '').strip(),
        'User_Address': (request.POST.get('address') or '').strip(),
        'User_Mobile_Number': (request.POST.get('mobile_number') or '').strip(),
        'User_Date_Of_Birth': date_of_birth,
        'User_Email_ID': (request.POST.get('email_id') or '').strip(),
        'User_Nationality': (request.POST.get('nationality') or '').strip(),
        'User_Country_And_Pin_Code': (request.POST.get('country_and_pin_code') or '').strip(),
        'User_Gender': (request.POST.get('gender') or '').strip(),
        'User_Job_Title': (request.POST.get('job_title') or '').strip(),
        'User_Department': (request.POST.get('department') or '').strip(),
        'User_Qualification': (request.POST.get('qualification') or '').strip(),
        'User_Qualification_Institution': (request.POST.get('institution') or '').strip(),
        'User_Skills': (request.POST.get('skills') or '').strip(),
        'User_Salary': (request.POST.get('salary') or '0').strip() or '0',
    }


def _extract_staff_files(request):
    return {
        'User_Image': request.FILES.get('image'),
        'User_Document_Frontside_Image': request.FILES.get('document_frontside_image'),
        'User_Document_Backside_Image': request.FILES.get('document_backside_image'),
        'User_Resume_PDF': request.FILES.get('resume_pdf'),
    }


def _validate_staff_fields(data, files):
    if not data['User_Full_Name']:
        return 'Full name is required.'

    if data['User_Email_ID']:
        try:
            validate_email(data['User_Email_ID'])
        except ValidationError:
            return f"'{data['User_Email_ID']}' is not a valid email address."

    try:
        salary = int(data['User_Salary'])
    except ValueError:
        return f"'{data['User_Salary']}' is not a valid salary amount."
    if salary < 0:
        return 'Salary cannot be negative.'
    data['User_Salary'] = salary  # normalized in place for the caller

    for field_name in ('User_Image', 'User_Document_Frontside_Image', 'User_Document_Backside_Image'):
        f = files.get(field_name)
        if f and f.size > MAX_IMAGE_SIZE_BYTES:
            return f"{field_name.replace('User_', '').replace('_', ' ')} must be under {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB."

    resume = files.get('User_Resume_PDF')
    if resume and resume.size > MAX_RESUME_SIZE_BYTES:
        return f"Resume must be under {MAX_RESUME_SIZE_BYTES // (1024 * 1024)}MB."

    return None


@login_required(login_url='Login_In')
def Staff__Profile_User_Profile(request):
    try:
        queryset = User_Profile.objects.all()
        return render(request, "Staff__Profile_User_Profile.html", {'user_profiles': queryset})
    except Exception as e:
        logger.error(f"Unexpected error in Staff__Profile_User_Profile: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})


@login_required(login_url='Login_In')
def Staff__Profile_Registration(request):
    if request.method != 'POST':
        return render(request, "Staff__Profile_User_Registration.html")

    data = _extract_staff_fields(request)
    files = _extract_staff_files(request)

    error = _validate_staff_fields(data, files)
    if error:
        messages.error(request, error)
        return render(request, "Staff__Profile_User_Registration.html")

    try:
        with transaction.atomic():
            User_Profile.objects.create(
                **data,
                **files,
                created_by=request.user,
                created_at=dj_timezone.now().astimezone(timezone('Asia/Kolkata')),
            )
    except Exception as e:
        logger.error(f"Unexpected error in Staff__Profile_Registration: {e}", exc_info=True)
        messages.error(request, 'An error occurred while creating the staff profile.')
        return render(request, "Staff__Profile_User_Registration.html")

    logger.info(f"User '{request.user.username}' created staff profile '{data['User_Full_Name']}'.")
    messages.success(request, 'Staff profile created successfully.')
    return redirect('/Staff--Profile-User-Profile/')


@login_required(login_url='Login_In')
def Staff__Profile_User_Update(request, id):
    queryset = get_object_or_404(User_Profile, id=id)

    if request.method != 'POST':
        return render(request, 'Staff__Profile_User_Registration_Update.html', {'user': queryset})

    data = _extract_staff_fields(request)
    files = _extract_staff_files(request)

    error = _validate_staff_fields(data, files)
    if error:
        messages.error(request, error)
        return render(request, 'Staff__Profile_User_Registration_Update.html', {'user': queryset})

    try:
        with transaction.atomic():
            for field, value in data.items():
                setattr(queryset, field, value)
            # Only replace a file if a new one was actually uploaded —
            # the original view did the same (an untouched file input
            # POSTs nothing, so request.FILES.get(...) is None here, and
            # setting these attributes to None would have wiped an
            # existing photo/document/resume just by opening the form
            # and saving without re-attaching a file. Explicit is safer
            # than relying on that being the case by accident.
            for field, value in files.items():
                if value is not None:
                    setattr(queryset, field, value)
            queryset.modified_by = request.user
            queryset.modified_at = dj_timezone.now()
            queryset.save()
    except Exception as e:
        logger.error(f"Unexpected error in Staff__Profile_User_Update: {e}", exc_info=True)
        messages.error(request, 'An error occurred while processing your update.')
        return render(request, 'Staff__Profile_User_Registration_Update.html', {'user': queryset})

    logger.info(f"User '{request.user.username}' updated staff profile id={id} ('{data['User_Full_Name']}').")
    messages.success(request, 'Staff profile updated successfully.')
    return redirect('/Staff--Profile-User-Profile/')


@login_required(login_url='Login_In')
def Staff__Profile_User_Delete(request, id):
    try:
        user_profile = get_object_or_404(User_Profile, id=id)

        if request.method != 'POST':
            # Previously no else-branch at all for a non-POST request —
            # a bare GET fell through the whole function with no return,
            # and Django raised "didn't return an HttpResponse" (a hard
            # 500) for any GET to this URL.
            messages.error(request, 'Invalid request.')
            return redirect('/Staff--Profile-User-Profile/')

        with transaction.atomic():
            deleted_name = user_profile.User_Full_Name
            user_profile.delete()

        logger.info(f"User '{request.user.username}' deleted staff profile '{deleted_name}' (id={id}).")
        messages.success(request, 'Staff profile deleted successfully.')
        return redirect('/Staff--Profile-User-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Staff__Profile_User_Delete: {e}", exc_info=True)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})


@login_required(login_url='Login_In')
def User_Profile_Pause_Unpause(request, id):
    try:
        user = get_object_or_404(User_Profile, id=id)

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Staff--Profile-User-Profile/')

        with transaction.atomic():
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])

        logger.info(f"User '{request.user.username}' set staff profile id={id} active={user.is_active}.")
        messages.success(request, "User status updated successfully.")
    except Exception as e:
        logger.error(f"Unexpected error in User_Profile_Pause_Unpause: {e}", exc_info=True)
        messages.error(request, "An error occurred while updating the user's status.")

    return redirect('/Staff--Profile-User-Profile/')
