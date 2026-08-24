# Import necessary modules for view functions
from django.shortcuts import render, redirect  # For rendering templates and redirecting after form submission
from django.contrib import messages  # For displaying flash messages (e.g., success, error)
from django.contrib.auth.decorators import login_required  # To restrict access to views that require login
from .models import User_Profile  # Importing the User_Profile model from the current app's models
from datetime import datetime  # To work with date and time objects
from pytz import timezone  # For working with timezones in date and time operations
from django.db import transaction  # Import transaction for atomicity
from django.shortcuts import get_object_or_404, redirect  # For object retrieval and redirection

@login_required(login_url='Login_In')  # Ensures that the user is logged in to access this view
def Staff__Profile_User_Profile(request):
    # Start an atomic transaction to ensure that all database operations are completed successfully, or none at all
    try:
        with transaction.atomic():
            queryset = User_Profile.objects.all()  # Fetch all user profiles from the database
            context = {'user_profiles': queryset}  # Pass the fetched data to the template
            return render(request, "Staff__Profile_User_Profile.html", context)  # Render the template with the context data
    except Exception as e:
        # Log the exception and handle it by displaying an error page to the user
        print(e)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})  # Display an error page if an exception occurs



@login_required(login_url='Login_In')  # Ensures the user must be logged in to access this view
def Staff__Profile_Registration(request):
    try:
        # Start an atomic transaction to ensure data consistency
        with transaction.atomic():
            if request.method == 'POST':
                # Retrieve form data from POST request
                full_name = request.POST.get('full_name', '')
                address = request.POST.get('address', '')
                mobile_number = request.POST.get('mobile_number', '')
                date_of_birth_str = request.POST.get('date_of_birth', '')

                # Convert string date to date object
                if date_of_birth_str:
                    date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                else:
                    date_of_birth = None

                # Collect remaining form data
                email_id = request.POST.get('email_id', '')
                nationality = request.POST.get('nationality', '')
                country_and_pin_code = request.POST.get('country_and_pin_code', '')
                gender = request.POST.get('gender', '')
                job_title = request.POST.get('job_title', '')
                department = request.POST.get('department', '')
                qualification = request.POST.get('qualification', '')
                institution = request.POST.get('institution', '')
                skills = request.POST.get('skills', '')
                
                # Default salary to 0 if not provided
                salary = request.POST.get('salary', '0') if request.POST.get('salary', '') else '0'
                
                # Handle file uploads
                image = request.FILES.get('image', None)
                document_frontside_image = request.FILES.get('document_frontside_image', None)
                document_backside_image = request.FILES.get('document_backside_image', None)
                resume_pdf = request.FILES.get('resume_pdf', None)

                # Set timezone to 'Asia/Kolkata'
                tz = timezone('Asia/Kolkata')

                # Create the User_Profile object and save it to the database
                User_Profile.objects.create(
                    User_Full_Name=full_name,
                    User_Address=address,
                    User_Mobile_Number=mobile_number,
                    User_Date_Of_Birth=date_of_birth,
                    User_Email_ID=email_id,
                    User_Nationality=nationality,
                    User_Country_And_Pin_Code=country_and_pin_code,
                    User_Gender=gender,
                    User_Job_Title=job_title,
                    User_Department=department,
                    User_Qualification=qualification,
                    User_Qualification_Institution=institution,
                    User_Skills=skills,
                    User_Salary=salary,
                    User_Image=image,
                    User_Document_Frontside_Image=document_frontside_image,
                    User_Document_Backside_Image=document_backside_image,
                    User_Resume_PDF=resume_pdf,
                    created_by=request.user,  # Set the user who created the profile
                    created_at=datetime.now(tz),  # Set the creation time with the appropriate timezone
                )

                # Redirect to the user profile list page after successful registration
                return redirect('/Staff--Profile-User-Profile/')
    
    except Exception as e:
        # Log the exception and handle any errors that occur during profile creation
        print(e)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})  # Display an error page if an exception occurs


    # Render the registration page if the request is not a POST or an exception occurs
    return render(request, "Staff__Profile_User_Registration.html")



@login_required(login_url='Login_In')  # Ensure the user is logged in before accessing this view
def Staff__Profile_User_Update(request, id):
    try:
        # Start an atomic transaction to ensure that the update operation is fully consistent
        with transaction.atomic():
            # Retrieve the user profile that matches the provided id
            queryset = User_Profile.objects.get(id=id)
        
            # Check if the request method is POST (indicating form submission)
            if request.method == 'POST':
                # Retrieve form data from the POST request
                full_name = request.POST.get('full_name', '')
                address = request.POST.get('address', '')
                mobile_number = request.POST.get('mobile_number', '')
                date_of_birth_str = request.POST.get('date_of_birth', '')

                # Convert the date string to a date object if provided
                if date_of_birth_str:
                    date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                else:
                    date_of_birth = None  # Set to None if no date is provided

                email_id = request.POST.get('email_id', '')
                nationality = request.POST.get('nationality', '')
                country_and_pin_code = request.POST.get('country_and_pin_code', '')
                gender = request.POST.get('gender', '')
                job_title = request.POST.get('job_title', '')
                department = request.POST.get('department', '')
                qualification = request.POST.get('qualification', '')
                institution = request.POST.get('institution', '')
                skills = request.POST.get('skills', '')
                salary = request.POST.get('salary', '0') if request.POST.get('salary', '') else '0'
                image = request.FILES.get('image', None)
                document_frontside_image = request.FILES.get('document_frontside_image', None)
                document_backside_image = request.FILES.get('document_backside_image', None)
                resume_pdf = request.FILES.get('resume_pdf', None)

                # Update the fields of the User_Profile object
                queryset.User_Full_Name = full_name
                queryset.User_Address = address
                queryset.User_Mobile_Number = mobile_number
                queryset.User_Date_Of_Birth = date_of_birth
                queryset.User_Email_ID = email_id
                queryset.User_Nationality = nationality
                queryset.User_Country_And_Pin_Code = country_and_pin_code
                queryset.User_Gender = gender
                queryset.User_Job_Title = job_title
                queryset.User_Department = department
                queryset.User_Qualification = qualification
                queryset.User_Qualification_Institution = institution
                queryset.User_Skills = skills
                queryset.User_Salary = salary
                queryset.User_Image = image
                queryset.User_Document_Frontside_Image = document_frontside_image
                queryset.User_Document_Backside_Image = document_backside_image
                queryset.User_Resume_PDF = resume_pdf
                queryset.modified_by = request.user  # Record the current user as the modifier
                queryset.modified_at = datetime.now()  # Update the modification timestamp

                # Save the changes to the database
                queryset.save()

                # After saving, redirect to the user profile list page
                return redirect('/Staff--Profile-User-Profile/')
        
        # Prepare the context for the GET request, passing the current user profile to the template
        context = {'user': queryset}
        return render(request, 'Staff__Profile_User_Update.html', context)
    
    except Exception as e:
        print(e) 
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})  # Display an error page if an exception occurs
         # Log the exception for debugging purposes

        # Display an error message to the user in case of any issues during update
        messages.error(request, 'An error occurred while processing your update.')
        return render(request, 'error_page.html')



@login_required(login_url='Login_In')  # Ensure the user must be logged in to access this view
def Staff__Profile_User_Delete(request, id):
    try:
        # Start an atomic transaction to ensure the delete operation is consistent
        with transaction.atomic():
            if request.method == 'POST':
                # Retrieve the User_Profile object, return a 404 error if not found
                user_profile = get_object_or_404(User_Profile, id=id)
                
                # Delete the user profile
                user_profile.delete()
                
                # Redirect to the profile list after deletion
                return redirect('/Staff--Profile-User-Profile/')
    
    # Handle the case where the user profile does not exist
    except User_Profile.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': 'User Profile not found.'})
    
    # Catch all other exceptions and log them, then return an error page
    except Exception as e:
        print(e) 
         # Log the exception for debugging purposes
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})



@login_required(login_url='Login_In') # Ensure the user must be logged in to access this view
def User_Profile_Pause_Unpause(request, id):
    try:
        # Start a database transaction
        with transaction.atomic():
            # Retrieve the user profile by id or return 404 if not found
            user = get_object_or_404(User_Profile, id=id)

            if request.method == 'POST':
                # Toggle the user's active status (pause/unpause)
                user.is_active = not user.is_active
                user.save()  # Save the updated status in the database
                
                # Display a success message to the user
                messages.success(request, "User status updated successfully.")

    except Exception as e:
        # Handle any exceptions and display an error message
        messages.error(request, f"An error occurred: {str(e)}")

    # Redirect to the user profile list page after updating status
    return redirect('/Staff--Profile-User-Profile/')
