
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Company_Profile

from django.contrib.auth.decorators import login_required

@login_required(login_url='Login_In')
def Company_User_Profile(request):
    """
    View function to display all company profiles.
    """
    try:
        # Retrieve all company profiles
        queryset = Company_Profile.objects.all()
        # Pass the company profiles to the template context
        context = {'company_profiles': queryset}
        # Render the company profile list page
        return render(request, "Company_User_Profile.html", context)
    except Exception as e:
        print(e)
        # Render error page if an exception occurs while fetching company profiles
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching company profiles. Please try again later.'})


@login_required(login_url='Login_In')
def Company__Profile_Registration(request):
    """
    View function to register a new company profile.
    """
    if request.method == 'POST':
        # Retrieve form data from POST request
        company_name = request.POST.get('company_name', '')
        company_address = request.POST.get('company_address', '')
        company_email = request.POST.get('company_email', '')
        company_country = request.POST.get('company_country', '')
        company_pincode = request.POST.get('company_pincode', '')
        company_nationality = request.POST.get('company_nationality', '')
        company_mobile_number = request.POST.get('company_mobile_number', '')
        company_phone_number = request.POST.get('company_phone_number', '')
        company_discount_percentage = request.POST.get('company_discount_percentage', '0') if request.POST.get('company_discount_percentage', '') else '0'
        company_instruction = request.POST.get('company_instruction', '')
        company_gst_number = request.POST.get('company_gst_number', '')
        company_gst_percentage = request.POST.get('company_gst_percentage', '0') if request.POST.get('company_gst_percentage', '') else '0'
        company_tcs_percentage = request.POST.get('company_tcs_percentage', '0') if request.POST.get('company_tcs_percentage', '') else '0'
        company_tds_percentage = request.POST.get('company_tds_percentage', '0') if request.POST.get('company_tds_percentage', '') else '0'
        company_md_one_name = request.POST.get('company_md_one_name', '')
        company_md_one_email = request.POST.get('company_md_one_email', '')
        company_md_one_mobile_number = request.POST.get('company_md_one_mobile_number', '')
        company_md_second_name = request.POST.get('company_md_second_name', '')
        company_md_second_email = request.POST.get('company_md_second_email', '')
        company_md_second_mobile_number = request.POST.get('company_md_second_mobile_number', '')
        company_hr_head_name = request.POST.get('company_hr_head_name', '')
        company_hr_head_email = request.POST.get('company_hr_head_email', '')
        company_hr_head_mobile_number = request.POST.get('company_hr_head_mobile_number', '')
        company_assitant_hr_name = request.POST.get('company_assitant_hr_name', '')
        company_assitant_hr_email = request.POST.get('company_assitant_hr_email', '')
        company_assitant_hr_mobile_number = request.POST.get('company_assitant_hr_mobile_number', '')
        company_accountant_head_name = request.POST.get('company_accountant_head_name', '')
        company_accountant_head_email = request.POST.get('company_accountant_head_email', '')
        company_accountant_head_mobile_number = request.POST.get('company_accountant_head_mobile_number', '')
        company_accountant_assistant_one_name = request.POST.get('company_accountant_assistant_one_name', '')
        company_accountant_assistant_one_email = request.POST.get('company_accountant_assistant_one_email', '')
        company_accountant_assistant_one_mobile_number = request.POST.get('company_accountant_assistant_one_mobile_number', '')
        company_accountant_assistant_two_name = request.POST.get('company_accountant_assistant_two_name', '')
        company_accountant_assistant_two_email = request.POST.get('company_accountant_assistant_two_email', '')
        company_accountant_assistant_two_mobile_number = request.POST.get('company_accountant_assistant_two_mobile_number', '')

        try:
            # If GST number is provided, enforce uniqueness
            if company_gst_number:
                if Company_Profile.objects.filter(Company_GST_Number=company_gst_number).exists():
                    raise IntegrityError('Company with this GST number already exists.')
                else:
                    Company_Profile.objects.create(
                        Company_Name=company_name,
                        Company_Address=company_address,
                        Company_Email=company_email,
                        Company_Country=company_country,
                        Company_Pincode=company_pincode,
                        Company_Nationality=company_nationality,
                        Company_Mobile_Number=company_mobile_number,
                        Company_Phone_Number=company_phone_number,
                        Company_Discount_Percentage=company_discount_percentage,
                        Company_Instruction=company_instruction,
                        Company_GST_Number=company_gst_number,
                        Company_GST_Percentage=company_gst_percentage,
                        Company_TCS_Percentage=company_tcs_percentage,
                        Company_TDS_Percentage=company_tds_percentage,
                        Company_MD_One_Name=company_md_one_name,
                        Company_MD_One_Email=company_md_one_email,
                        Company_MD_One_Mobile_Number=company_md_one_mobile_number,
                        Company_MD_Second_Name=company_md_second_name,
                        Company_MD_Second_Email=company_md_second_email,
                        Company_MD_Second_Mobile_Number=company_md_second_mobile_number,
                        Company_HR_Head_Name=company_hr_head_name,
                        Company_HR_Head_Email=company_hr_head_email,
                        Company_HR_Head_Mobile_Number=company_hr_head_mobile_number,
                        Company_Assitant_HR_Name=company_assitant_hr_name,
                        Company_Assitant_HR_Email=company_assitant_hr_email,
                        Company_Assitant_HR_Mobile_Number=company_assitant_hr_mobile_number,
                        Company_Accountant_Head_Name=company_accountant_head_name,
                        Company_Accountant_Head_Email=company_accountant_head_email,
                        Company_Accountant_Head_Mobile_Number=company_accountant_head_mobile_number,
                        Company_Accountant_Assistant_One_Name=company_accountant_assistant_one_name,
                        Company_Accountant_Assistant_One_Email=company_accountant_assistant_one_email,
                        Company_Accountant_Assistant_One_Mobile_Number=company_accountant_assistant_one_mobile_number,
                        Company_Accountant_Assistant_Two_Name=company_accountant_assistant_two_name,
                        Company_Accountant_Assistant_Two_Email=company_accountant_assistant_two_email,
                        Company_Accountant_Assistant_Two_Mobile_Number=company_accountant_assistant_two_mobile_number
                    )
                    messages.success(request, 'Company profile registered successfully.')
                    return redirect('/Company-User-Profile/')
            else:
                # If GST number is not provided, allow saving without uniqueness check
                Company_Profile.objects.create(
                    Company_Name=company_name,
                    Company_Address=company_address,
                    Company_Email=company_email,
                    Company_Country=company_country,
                    Company_Pincode=company_pincode,
                    Company_Nationality=company_nationality,
                    Company_Mobile_Number=company_mobile_number,
                    Company_Phone_Number=company_phone_number,
                    Company_Discount_Percentage=company_discount_percentage,
                    Company_Instruction=company_instruction,
                    Company_GST_Number=company_gst_number,
                    Company_GST_Percentage=company_gst_percentage,
                    Company_TCS_Percentage=company_tcs_percentage,
                    Company_TDS_Percentage=company_tds_percentage,
                    Company_MD_One_Name=company_md_one_name,
                    Company_MD_One_Email=company_md_one_email,
                    Company_MD_One_Mobile_Number=company_md_one_mobile_number,
                    Company_MD_Second_Name=company_md_second_name,
                    Company_MD_Second_Email=company_md_second_email,
                    Company_MD_Second_Mobile_Number=company_md_second_mobile_number,
                    Company_HR_Head_Name=company_hr_head_name,
                    Company_HR_Head_Email=company_hr_head_email,
                    Company_HR_Head_Mobile_Number=company_hr_head_mobile_number,
                    Company_Assitant_HR_Name=company_assitant_hr_name,
                    Company_Assitant_HR_Email=company_assitant_hr_email,
                    Company_Assitant_HR_Mobile_Number=company_assitant_hr_mobile_number,
                    Company_Accountant_Head_Name=company_accountant_head_name,
                    Company_Accountant_Head_Email=company_accountant_head_email,
                    Company_Accountant_Head_Mobile_Number=company_accountant_head_mobile_number,
                    Company_Accountant_Assistant_One_Name=company_accountant_assistant_one_name,
                    Company_Accountant_Assistant_One_Email=company_accountant_assistant_one_email,
                    Company_Accountant_Assistant_One_Mobile_Number=company_accountant_assistant_one_mobile_number,
                    Company_Accountant_Assistant_Two_Name=company_accountant_assistant_two_name,
                    Company_Accountant_Assistant_Two_Email=company_accountant_assistant_two_email,
                    Company_Accountant_Assistant_Two_Mobile_Number=company_accountant_assistant_two_mobile_number
            )
            messages.success(request, 'Company profile registered successfully.')
            return redirect('/Company-User-Profile/')
        except IntegrityError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'An error occurred while processing your registration.')
            print(e)
    
    return render(request, "Company_User_Registration.html")



from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError
from .models import Company_Profile
from django.db import IntegrityError
from django.contrib import messages

@login_required(login_url='Login_In')
def Company_Profile__Update(request, id):
    """
    View function to update a company profile.
    """
    try:
        # Retrieve the company profile to be updated
        queryset = Company_Profile.objects.get(id=id)
        
        if request.method == 'POST':
            # Retrieve form data from POST request
            company_name = request.POST.get('company_name', '')
            company_address = request.POST.get('company_address', '')
            company_email = request.POST.get('company_email', '')
            company_country = request.POST.get('company_country', '')
            company_pincode = request.POST.get('company_pincode', '')
            company_nationality = request.POST.get('company_nationality', '')
            company_mobile_number = request.POST.get('company_mobile_number', '')
            company_phone_number = request.POST.get('company_phone_number', '')
            company_discount_percentage = request.POST.get('company_discount_percentage', '')
            company_instruction = request.POST.get('company_instruction', '')
            company_gst_number = request.POST.get('company_gst_number', '')
            company_gst_percentage = request.POST.get('company_gst_percentage', '')
            company_tcs_percentage = request.POST.get('company_tcs_percentage', '')
            company_tds_percentage = request.POST.get('company_tds_percentage', '')
            company_md_one_name = request.POST.get('company_md_one_name', '')
            company_md_one_email = request.POST.get('company_md_one_email', '')
            company_md_one_mobile_number = request.POST.get('company_md_one_mobile_number', '')
            company_md_second_name = request.POST.get('company_md_second_name', '')
            company_md_second_email = request.POST.get('company_md_second_email', '')
            company_md_second_mobile_number = request.POST.get('company_md_second_mobile_number', '')
            company_hr_head_name = request.POST.get('company_hr_head_name', '')
            company_hr_head_email = request.POST.get('company_hr_head_email', '')
            company_hr_head_mobile_number = request.POST.get('company_hr_head_mobile_number', '')
            company_assitant_hr_name = request.POST.get('company_assitant_hr_name', '')
            company_assitant_hr_email = request.POST.get('company_assitant_hr_email', '')
            company_assistant_hr_mobile_number = request.POST.get('company_assistant_hr_mobile_number', '')
            company_accountant_head_name = request.POST.get('company_accountant_head_name', '')
            company_accountant_head_email = request.POST.get('company_accountant_head_email', '')
            company_accountant_head_mobile_number = request.POST.get('company_accountant_head_mobile_number', '')
            company_accountant_assistant_one_name = request.POST.get('company_accountant_assistant_one_name', '')
            company_accountant_assistant_one_email = request.POST.get('company_accountant_assistant_one_email', '')
            company_accountant_assistant_one_mobile_number = request.POST.get('company_accountant_assistant_one_mobile_number', '')
            company_accountant_assistant_two_name = request.POST.get('company_accountant_assistant_two_name', '')
            company_accountant_assistant_two_email = request.POST.get('company_accountant_assistant_two_email', '')
            company_accountant_assistant_two_mobile_number = request.POST.get('company_accountant_assistant_two_mobile_number', '')

            # Check for duplicate GST number if provided
            if company_gst_number:
                if Company_Profile.objects.filter(Company_GST_Number=company_gst_number).exclude(id=id).exists():
                    raise IntegrityError('Company with this GST number already exists.')

            # Update the company profile object with the retrieved data
            queryset.Company_Name = company_name
            queryset.Company_Address = company_address
            queryset.Company_Email = company_email
            queryset.Company_Country = company_country
            queryset.Company_Pincode = company_pincode
            queryset.Company_Nationality = company_nationality
            queryset.Company_Mobile_Number = company_mobile_number
            queryset.Company_Phone_Number = company_phone_number
            queryset.Company_Discount_Percentage = company_discount_percentage
            queryset.Company_Instruction = company_instruction
            queryset.Company_GST_Number = company_gst_number
            queryset.Company_GST_Percentage = company_gst_percentage
            queryset.Company_TCS_Percentage = company_tcs_percentage
            queryset.Company_TDS_Percentage = company_tds_percentage
            queryset.Company_MD_One_Name = company_md_one_name
            queryset.Company_MD_One_Email = company_md_one_email
            queryset.Company_MD_One_Mobile_Number = company_md_one_mobile_number
            queryset.Company_MD_Second_Name = company_md_second_name
            queryset.Company_MD_Second_Email = company_md_second_email
            queryset.Company_MD_Second_Mobile_Number = company_md_second_mobile_number
            queryset.Company_HR_Head_Name = company_hr_head_name
            queryset.Company_HR_Head_Email = company_hr_head_email
            queryset.Company_HR_Head_Mobile_Number = company_hr_head_mobile_number
            queryset.Company_Assitant_HR_Name = company_assitant_hr_name
            queryset.Company_Assitant_HR_Email = company_assitant_hr_email
            queryset.Company_Assitant_HR_Mobile_Number = company_assistant_hr_mobile_number
            queryset.Company_Accountant_Head_Name = company_accountant_head_name
            queryset.Company_Accountant_Head_Email = company_accountant_head_email
            queryset.Company_Accountant_Head_Mobile_Number = company_accountant_head_mobile_number
            queryset.Company_Accountant_Assistant_One_Name = company_accountant_assistant_one_name
            queryset.Company_Accountant_Assistant_One_Email = company_accountant_assistant_one_email
            queryset.Company_Accountant_Assistant_One_Mobile_Number = company_accountant_assistant_one_mobile_number
            queryset.Company_Accountant_Assistant_Two_Name = company_accountant_assistant_two_name
            queryset.Company_Accountant_Assistant_Two_Email = company_accountant_assistant_two_email
            queryset.Company_Accountant_Assistant_Two_Mobile_Number = company_accountant_assistant_two_mobile_number

            queryset.save()  # Save the updated company profile object
            # Redirect to the company profile list page after update
            return redirect('/Company-User-Profile/')
        
    except IntegrityError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, 'An error occurred while processing your update.')
        print(e)
    
    # Render the update form template with the company profile data
    return render(request, "Company_User_Registration_Update.html", {'companyprofile': queryset})



@login_required(login_url='Login_In')
def Company_Profile_User_Delete(request, id):
    """
    View function to delete a company profile.
    """
    try:
        if request.method == 'POST':
            # Retrieve the company profile to be deleted
            company_profile = Company_Profile.objects.get(id=id)
            # Delete the company profile
            company_profile.delete()
            # Redirect to the company profile list page after deletion
            return redirect('/Company-User-Profile/')
    except Company_Profile.DoesNotExist:
        # Render error page if the company profile doesn't exist
        return render(request, 'error_page.html', {'error_message': 'Company Profile not found.'})
    except Exception as e:
        print(e)
        # Render error page if an exception occurs while deleting the company profile
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the company profile.'})
