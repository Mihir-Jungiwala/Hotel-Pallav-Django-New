import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, render, redirect

from .models import Company_Profile

logger = logging.getLogger(__name__)

# Every POST key a company form submits, alongside the model field it maps
# to. Shared by Add and Update instead of duplicated field-by-field in
# each view — the previous duplication is exactly how the Add view ended
# up reading 'company_assitant_hr_mobile_number' (missing an 's') while
# both templates have only ever submitted 'company_assistant_hr_mobile_number':
# every company ever registered through Add has silently had a blank
# Assistant HR mobile number regardless of what was typed in, since the
# Update view (which reads the correct key) was never compared against it.
COMPANY_FIELD_MAP = [
    ('company_name', 'Company_Name'),
    ('company_address', 'Company_Address'),
    ('company_email', 'Company_Email'),
    ('company_country', 'Company_Country'),
    ('company_pincode', 'Company_Pincode'),
    ('company_nationality', 'Company_Nationality'),
    ('company_mobile_number', 'Company_Mobile_Number'),
    ('company_phone_number', 'Company_Phone_Number'),
    ('company_instruction', 'Company_Instruction'),
    ('company_gst_number', 'Company_GST_Number'),
    ('company_md_one_name', 'Company_MD_One_Name'),
    ('company_md_one_email', 'Company_MD_One_Email'),
    ('company_md_one_mobile_number', 'Company_MD_One_Mobile_Number'),
    ('company_md_second_name', 'Company_MD_Second_Name'),
    ('company_md_second_email', 'Company_MD_Second_Email'),
    ('company_md_second_mobile_number', 'Company_MD_Second_Mobile_Number'),
    ('company_hr_head_name', 'Company_HR_Head_Name'),
    ('company_hr_head_email', 'Company_HR_Head_Email'),
    ('company_hr_head_mobile_number', 'Company_HR_Head_Mobile_Number'),
    ('company_assitant_hr_name', 'Company_Assitant_HR_Name'),
    ('company_assitant_hr_email', 'Company_Assitant_HR_Email'),
    ('company_assistant_hr_mobile_number', 'Company_Assitant_HR_Mobile_Number'),
    ('company_accountant_head_name', 'Company_Accountant_Head_Name'),
    ('company_accountant_head_email', 'Company_Accountant_Head_Email'),
    ('company_accountant_head_mobile_number', 'Company_Accountant_Head_Mobile_Number'),
    ('company_accountant_assistant_one_name', 'Company_Accountant_Assistant_One_Name'),
    ('company_accountant_assistant_one_email', 'Company_Accountant_Assistant_One_Email'),
    ('company_accountant_assistant_one_mobile_number', 'Company_Accountant_Assistant_One_Mobile_Number'),
    ('company_accountant_assistant_two_name', 'Company_Accountant_Assistant_Two_Name'),
    ('company_accountant_assistant_two_email', 'Company_Accountant_Assistant_Two_Email'),
    ('company_accountant_assistant_two_mobile_number', 'Company_Accountant_Assistant_Two_Mobile_Number'),
]

# These four are DecimalFields — POSTed as text and defaulted to '0'
# when blank, same as the original Add view.
# The original Update view instead defaulted them to '' when blank; that
# looks harmless but DecimalField.to_python('') raises ValidationError
# on save (confirmed directly: Company_Profile.objects.first() with
# Company_Discount_Percentage = '' then .save() crashes). That was a real
# crash on any Update submission that cleared one of these fields;
# defaulting to '0' consistently (matching Add) fixes it without changing
# behavior for the
# non-blank case.
COMPANY_DECIMAL_FIELDS = [
    ('company_discount_percentage', 'Company_Discount_Percentage'),
    ('company_gst_percentage', 'Company_GST_Percentage'),
    ('company_tcs_percentage', 'Company_TCS_Percentage'),
    ('company_tds_percentage', 'Company_TDS_Percentage'),
]


def _extract_company_fields(request):
    data = {}
    for post_key, model_field in COMPANY_FIELD_MAP:
        data[model_field] = (request.POST.get(post_key) or '').strip()
    for post_key, model_field in COMPANY_DECIMAL_FIELDS:
        raw = request.POST.get(post_key, '')
        data[model_field] = raw if raw else '0'
    return data


def _validate_company_fields(data):
    """Returns an error message string, or None if the submission is valid."""
    if not data['Company_Name']:
        return 'Company name is required.'

    for email_field in ('Company_Email', 'Company_MD_One_Email', 'Company_MD_Second_Email',
                         'Company_HR_Head_Email', 'Company_Assitant_HR_Email',
                         'Company_Accountant_Head_Email', 'Company_Accountant_Assistant_One_Email',
                         'Company_Accountant_Assistant_Two_Email'):
        value = data.get(email_field)
        if value:
            try:
                validate_email(value)
            except ValidationError:
                return f"'{value}' is not a valid email address."

    for post_key, model_field in COMPANY_DECIMAL_FIELDS:
        try:
            value = float(data[model_field])
        except ValueError:
            return f"'{data[model_field]}' is not a valid percentage for {model_field.replace('_', ' ')}."
        if not (0 <= value <= 100):
            return f"{model_field.replace('_', ' ').title()} must be between 0 and 100."

    return None


@login_required(login_url='Login_In')
def Company_User_Profile(request):
    try:
        queryset = Company_Profile.objects.all()
        return render(request, "Company_User_Profile.html", {'company_profiles': queryset})
    except Exception as e:
        logger.error(f"Unexpected error in Company_User_Profile: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching company profiles. Please try again later.'})


@login_required(login_url='Login_In')
def Company__Profile_Registration(request):
    if request.method != 'POST':
        return render(request, "Company_User_Registration.html")

    data = _extract_company_fields(request)

    error = _validate_company_fields(data)
    if error:
        messages.error(request, error)
        return render(request, "Company_User_Registration.html")

    try:
        with transaction.atomic():
            Company_Profile.objects.create(**data)
    except IntegrityError:
        # The DB-level constraints (Company_Name unique, and the
        # conditional unique constraint on Company_GST_Number added in
        # this hardening pass) are the actual guarantee — this catches
        # both a name collision and a GST-number collision (including
        # the race-condition case two concurrent submissions with the
        # same GST number can hit) with one friendly message instead of
        # a raw database error string.
        logger.info(f"Company registration rejected: duplicate name or GST number ('{data['Company_Name']}').")
        messages.error(request, f"A company named \"{data['Company_Name']}\" or with that GST number already exists.")
        return render(request, "Company_User_Registration.html")
    except Exception as e:
        logger.error(f"Unexpected error in Company__Profile_Registration: {e}", exc_info=True)
        messages.error(request, 'An error occurred while processing your registration.')
        return render(request, "Company_User_Registration.html")

    logger.info(f"User '{request.user.username}' registered company '{data['Company_Name']}'.")
    messages.success(request, 'Company profile registered successfully.')
    return redirect('/Company-User-Profile/')


@login_required(login_url='Login_In')
def Company_Profile__Update(request, id):
    queryset = get_object_or_404(Company_Profile, id=id)

    if request.method != 'POST':
        return render(request, "Company_User_Registration_Update.html", {'companyprofile': queryset})

    data = _extract_company_fields(request)

    error = _validate_company_fields(data)
    if error:
        messages.error(request, error)
        return render(request, "Company_User_Registration_Update.html", {'companyprofile': queryset})

    try:
        with transaction.atomic():
            for field, value in data.items():
                setattr(queryset, field, value)
            queryset.save()
    except IntegrityError:
        logger.info(f"Company update rejected for id={id}: duplicate name or GST number.")
        messages.error(request, f"A company named \"{data['Company_Name']}\" or with that GST number already exists.")
        return render(request, "Company_User_Registration_Update.html", {'companyprofile': queryset})
    except Exception as e:
        logger.error(f"Unexpected error in Company_Profile__Update: {e}", exc_info=True)
        messages.error(request, 'An error occurred while processing your update.')
        return render(request, "Company_User_Registration_Update.html", {'companyprofile': queryset})

    logger.info(f"User '{request.user.username}' updated company id={id} ('{data['Company_Name']}').")
    messages.success(request, 'Company profile updated successfully.')
    return redirect('/Company-User-Profile/')


@login_required(login_url='Login_In')
def Company_Profile_User_Delete(request, id):
    try:
        company_profile = get_object_or_404(Company_Profile, id=id)

        if request.method != 'POST':
            # Previously fell through with no return at all on a GET
            # request — Django raised "didn't return an HttpResponse"
            # (a hard 500) for any GET to this URL, e.g. a stray link,
            # crawler, or a browser prefetch.
            messages.error(request, 'Invalid request.')
            return redirect('/Company-User-Profile/')

        with transaction.atomic():
            deleted_name = company_profile.Company_Name
            company_profile.delete()

        logger.info(f"User '{request.user.username}' deleted company '{deleted_name}' (id={id}).")
        messages.success(request, 'Company profile deleted successfully.')
        return redirect('/Company-User-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Company_Profile_User_Delete: {e}", exc_info=True)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the company profile.'})
