# Import necessary modules for view functions
from django.shortcuts import render, redirect, get_object_or_404  # For rendering templates and redirecting after form submission
from django.contrib.auth.models import User  # For accessing User model
from django.contrib import messages  # For displaying messages to users
from .models import Shift_Handover  # Importing the Shift_Handover model from the current app's models
from decimal import Decimal  # For handling decimal numbers
from Dashboard.views import numberToWords  # For converting numbers to words
from django.db import transaction  # Import transaction for atomicity
from Reports.pdf import render_to_pdf  # Import the render_to_pdf function
from django.contrib.auth.decorators import login_required  # For login-required decorators



@login_required(login_url='Login_In')
def Shift_Handover_Profile(request):
   
    try:
        # Start an atomic transaction
        with transaction.atomic():
            # Retrieve all company profiles from the database
            queryset = Shift_Handover.objects.all()
            # Prepare the context dictionary to pass company profiles to the template
            context = {'shift_handover_profile': queryset}
            # Render the company profile list page with the context
            return render(request, "Shift_Handover_Profile.html", context)
    except Exception as e:
        # Print the exception for debugging purposes
        print(e)
        # Render an error page if an exception occurs while fetching company profiles
        return render(request, "error_page.html", {"error": str(e)})
     
   



@login_required(login_url='Login_In')
def Shift_Handover_Add(request):
    # Check if the request method is POST to process the form submission
    if request.method == 'POST':
        try:
            # Start an atomic transaction
            with transaction.atomic():
                # Retrieve form data
                date = request.POST.get('date', '')
                time = request.POST.get('time', '')
                username = request.POST.get('username', '')
                shift = request.POST.get('shift', '')
                message_one = request.POST.get('message_one', '')
                message_two = request.POST.get('message_two', '')
                message_three = request.POST.get('message_three', '')
                message_four = request.POST.get('message_four', '')
                message_five = request.POST.get('message_five', '')

                # Retrieve quantities and amounts, with default values
                five_hundred_quantity = int(request.POST.get('five_hundred_quantity', '0')) if request.POST.get('five_hundred_quantity', '') else 0
                five_hundred_amount = Decimal(request.POST.get('five_hundred_amount', '0')) if request.POST.get('five_hundred_amount', '') else Decimal('0')
                two_hundred_quantity = int(request.POST.get('two_hundred_quantity', '0')) if request.POST.get('two_hundred_quantity', '') else 0
                two_hundred_amount = Decimal(request.POST.get('two_hundred_amount', '0')) if request.POST.get('two_hundred_amount', '') else Decimal('0')
                one_hundred_quantity = int(request.POST.get('one_hundred_quantity', '0')) if request.POST.get('one_hundred_quantity', '') else 0
                one_hundred_amount = Decimal(request.POST.get('one_hundred_amount', '0')) if request.POST.get('one_hundred_amount', '') else Decimal('0')
                fifty_quantity = int(request.POST.get('fifty_quantity', '0')) if request.POST.get('fifty_quantity', '') else 0
                fifty_amount = Decimal(request.POST.get('fifty_amount', '0')) if request.POST.get('fifty_amount', '') else Decimal('0')
                twenty_quantity = int(request.POST.get('twenty_quantity', '0')) if request.POST.get('twenty_quantity', '') else 0
                twenty_amount = Decimal(request.POST.get('twenty_amount', '0')) if request.POST.get('twenty_amount', '') else Decimal('0')
                ten_quantity = int(request.POST.get('ten_quantity', '0')) if request.POST.get('ten_quantity', '') else 0
                ten_amount = Decimal(request.POST.get('ten_amount', '0')) if request.POST.get('ten_amount', '') else Decimal('0')
                five_quantity = int(request.POST.get('five_quantity', '0')) if request.POST.get('five_quantity', '') else 0
                five_amount = Decimal(request.POST.get('five_amount', '0')) if request.POST.get('five_amount', '') else Decimal('0')
                coin_quantity = int(request.POST.get('coin_quantity', '0')) if request.POST.get('coin_quantity', '') else 0
                coin_amount = Decimal(request.POST.get('coin_amount', '0')) if request.POST.get('coin_amount', '') else Decimal('0')
                total = Decimal(request.POST.get('total', '0')) if request.POST.get('total', '') else Decimal('0')
                instruction = request.POST.get('instruction', '')

                # Fetch the User instance using the username
                user_instance = get_object_or_404(User, username=username)

                # Extract the full name of the user from the instance
                full_name = f"{user_instance.first_name} {user_instance.last_name}"

                # Convert the total amount to an integer
                amount_as_number = int(float(total))  # Convert string to float then to int

                # Convert the total amount to words
                amount_in_words = numberToWords(amount_as_number)

                # Create the Shift_Handover object
                Shift_Handover.objects.create(
                    Shift_Handover_Date=date,
                    Shift_Handover_Time=time,
                    Shift_Handover_Username=user_instance,  # Save the User instance
                    Shift_Handover_Full_Name=full_name,  # Save the full name as a separate field
                    Shift_Handover_Shift=shift,
                    Shift_Handover_message_One=message_one,
                    Shift_Handover_message_Two=message_two,
                    Shift_Handover_message_Three=message_three,
                    Shift_Handover_message_Four=message_four,
                    Shift_Handover_message_Five=message_five,
                    Shift_Handover_Five_Hundred_Counts=five_hundred_quantity,
                    Shift_Handover_Two_Hundred_Counts=two_hundred_quantity,
                    Shift_Handover_One_Hundred_Counts=one_hundred_quantity,
                    Shift_Handover_Fifty_Counts=fifty_quantity,
                    Shift_Handover_Twenty_Counts=twenty_quantity,
                    Shift_Handover_Ten_Counts=ten_quantity,
                    Shift_Handover_Five_Counts=five_quantity,
                    Shift_Handover_Coins_Counts=coin_quantity,
                    Shift_Handover_Five_Hundred_Total=five_hundred_amount,
                    Shift_Handover_Two_Hundred_Total=two_hundred_amount,
                    Shift_Handover_One_Hundred_Total=one_hundred_amount,
                    Shift_Handover_Fifty_Total=fifty_amount,
                    Shift_Handover_Twenty_Total=twenty_amount,
                    Shift_Handover_Ten_Total=ten_amount,
                    Shift_Handover_Five_Total=five_amount,
                    Shift_Handover_Coins_Total=coin_amount,
                    Shift_Handover_Total=total,
                    Shift_Handover_Total_Amount_In_Words=amount_in_words,
                    Shift_Handover_Special_Instruction=instruction
                )

                # Redirect to the Shift Handover Profile page after successful creation
                return redirect('/Shift-Handover-Profile/')
        except Exception as e:
            # Print the exception for debugging purposes
            print(e)
            # Optionally, add error handling here (e.g., flash messages, logging, etc.)

    # If not a POST request, render the form for adding a new shift handover
    return render(request, "shift_handover_add.html")



@login_required(login_url='Login_In')
def Shift_Handover_Update(request, id):
    # Retrieve the shift handover record to be updated
    shift_handover = get_object_or_404(Shift_Handover, id=id)

    if request.method == 'POST':
        try:
            with transaction.atomic():  # Start a transaction
                # Process the form submission
                shift = request.POST.get('shift', '')
                message_one = request.POST.get('message_one', '')
                message_two = request.POST.get('message_two', '')
                message_three = request.POST.get('message_three', '')
                message_four = request.POST.get('message_four', '')
                message_five = request.POST.get('message_five', '')

                # Convert string inputs to integers (except for total)
                five_hundred_quantity = int(request.POST.get('five_hundred_quantity', '0'))
                five_hundred_amount = Decimal(request.POST.get('five_hundred_amount', '0'))
                two_hundred_quantity = int(request.POST.get('two_hundred_quantity', '0'))
                two_hundred_amount = Decimal(request.POST.get('two_hundred_amount', '0'))
                one_hundred_quantity = int(request.POST.get('one_hundred_quantity', '0'))
                one_hundred_amount = Decimal(request.POST.get('one_hundred_amount', '0'))
                fifty_quantity = int(request.POST.get('fifty_quantity', '0'))
                fifty_amount = Decimal(request.POST.get('fifty_amount', '0'))
                twenty_quantity = int(request.POST.get('twenty_quantity', '0'))
                twenty_amount = Decimal(request.POST.get('twenty_amount', '0'))
                ten_quantity = int(request.POST.get('ten_quantity', '0'))
                ten_amount = Decimal(request.POST.get('ten_amount', '0'))
                five_quantity = int(request.POST.get('five_quantity', '0'))
                five_amount = Decimal(request.POST.get('five_amount', '0'))
                coin_quantity = int(request.POST.get('coin_quantity', '0'))
                coin_amount = Decimal(request.POST.get('coin_amount', '0'))
                total = Decimal(request.POST.get('total', '0'))
                instruction = request.POST.get('instruction', '')

                # Validate and convert amount to integer
                amount_as_number = int(total)

                # Convert the amount to words (assuming you have this function defined)
                amount_in_words = numberToWords(amount_as_number)

                # Update the shift handover record
                shift_handover.Shift_Handover_Shift = shift
                shift_handover.Shift_Handover_message_One = message_one
                shift_handover.Shift_Handover_message_Two = message_two
                shift_handover.Shift_Handover_message_Three = message_three
                shift_handover.Shift_Handover_message_Four = message_four
                shift_handover.Shift_Handover_message_Five = message_five

                shift_handover.Shift_Handover_Five_Hundred_Counts = five_hundred_quantity
                shift_handover.Shift_Handover_Two_Hundred_Counts = two_hundred_quantity
                shift_handover.Shift_Handover_One_Hundred_Counts = one_hundred_quantity
                shift_handover.Shift_Handover_Fifty_Counts = fifty_quantity
                shift_handover.Shift_Handover_Twenty_Counts = twenty_quantity
                shift_handover.Shift_Handover_Ten_Counts = ten_quantity
                shift_handover.Shift_Handover_Five_Counts = five_quantity
                shift_handover.Shift_Handover_Coins_Counts = coin_quantity

                shift_handover.Shift_Handover_Five_Hundred_Total = five_hundred_amount
                shift_handover.Shift_Handover_Two_Hundred_Total = two_hundred_amount
                shift_handover.Shift_Handover_One_Hundred_Total = one_hundred_amount
                shift_handover.Shift_Handover_Fifty_Total = fifty_amount
                shift_handover.Shift_Handover_Twenty_Total = twenty_amount
                shift_handover.Shift_Handover_Ten_Total = ten_amount
                shift_handover.Shift_Handover_Five_Total = five_amount
                shift_handover.Shift_Handover_Coins_Total = coin_amount
                shift_handover.Shift_Handover_Total = total
                shift_handover.Shift_Handover_Total_Amount_In_Words = amount_in_words

                shift_handover.Shift_Handover_Special_Instruction = instruction

                # Save the updated shift handover record
                shift_handover.save()

                # Display success message
                messages.success(request, "Shift handover record updated successfully.")
                
                # Redirect to the shift handover profile list page after update
                return redirect('/Shift-Handover-Profile/')

        except Exception as e:
            # Handle exceptions
            messages.error(request, f"An error occurred while updating: {str(e)}")
            return redirect(request.path)  # Redirect back to the form with an error message
    
    # Prepare the context with the shift handover record to be updated
    context = {'Shift_Handover_Update': shift_handover}
    
    # Render the update form template with the shift handover record data
    return render(request, "Shift_Handover_Update.html", context)



@login_required(login_url='Login_In')
def Shift_Handover_Delete(request, id):
    # Retrieve the specific shift handover entry or return a 404 if not found
    shift_handover = get_object_or_404(Shift_Handover, id=id)

    try:
        # Start an atomic transaction to ensure the delete operation is atomic
        with transaction.atomic():  # Start a transaction
            # Check if the user is allowed to delete
            if (
                request.user.username != "SuperAdmin" and
                request.user.username != "Admin" and 
                shift_handover.Shift_Handover_Username != request.user
            ):
                return redirect('/Shift-Handover-Profile/')  # Redirect if not authorized

            # Prevent Admin from deleting SuperAdmin's record
            if shift_handover.Shift_Handover_Username.username == "SuperAdmin" and request.user.username == "Admin":
                return redirect('/Shift-Handover-Profile/')  # Redirect if Admin tries to delete SuperAdmin's record

            if request.method == 'POST':
                # Proceed to delete the record
                shift_handover.delete()  # Delete the shift handover entry
                messages.success(request, 'Shift handover entry deleted successfully.')  # Success message
                return redirect('/Shift-Handover-Profile/')  # Redirect after deletion

    except Exception as e:
        # Handle any unexpected errors
        print(e)  # Log the exception for debugging purposes
        messages.error(request, 'An error occurred during deletion.')  # Error message
        return render(request, 'error_page.html', {'error_message': 'An error occurred during deletion.'})  # Render error page



@login_required(login_url='Login_In')
def Shift_Handover_View(request, id):
    try:
        with transaction.atomic():  # Start a transaction
            # Fetch the specific shift handover using the provided id
            shift_handover = get_object_or_404(Shift_Handover, id=id)

            # Prepare context
            context = {
                'shift_handover_view': shift_handover,
            }

            # Render the context to PDF
            return render_to_pdf('ShiftHandoverView.html', context)
    
    except Exception as e:
        # Log the exception for debugging purposes
        print(e)  # Optionally, log this to a logging system
        messages.error(request, 'An error occurred while trying to fetch the shift handover details.')  # Error message
        return redirect('/Shift-Handover-Profile/')  # Redirect to a relevant page on error
