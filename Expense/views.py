from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from Staff_Profile.models import User_Profile
from .models import Food_Cash_Miscellaneous_Expenses, Food_Cash_Withdrawal, Hotel_Cash_Miscellaneous_Expenses, Hotel_Cash_Withdrawal, Staff_Advance
from datetime import datetime
from datetime import datetime
from django.shortcuts import render, redirect
from .models import Hotel_Cash_Miscellaneous_Expenses
from django.contrib.auth.models import User
from  Dashboard.views import numberToWords
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import User_Profile, Staff_Advance
from datetime import datetime
from Reports.pdf import render_to_pdf  # Import the render_to_pdf function



@login_required(login_url='Login_In')
def Expense_Profile(request):
    try:
        hotel_withdrawals = Hotel_Cash_Withdrawal.objects.all()
        staffadvance = Staff_Advance.objects.all()
        food_withdrawals = Food_Cash_Withdrawal.objects.all()
        hotel_miscellaneous_expense_profile = Hotel_Cash_Miscellaneous_Expenses.objects.all()
        food_miscellaneous_expense_profile = Food_Cash_Miscellaneous_Expenses.objects.all()
        context = {
            'hotel_withdrawals': hotel_withdrawals,
            'food_withdrawals': food_withdrawals,
            'staffadvance':staffadvance,
            'hotel_miscellaneous_expense_profile': hotel_miscellaneous_expense_profile,
            'food_miscellaneous_expense_profile': food_miscellaneous_expense_profile,
        }
        return render(request, "Expense_Profile.html", context)
    except Exception as e:
        print(e)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})

@login_required(login_url='Login_In')
def Hotel_Expense_Cash_Withdraw(request):
    try:
        if request.method == 'POST':
            Hotel_withdrawal_date_str = request.POST.get('Hotel_withdrawal_date', '') 

            if Hotel_withdrawal_date_str:
                Hotel_withdrawal_date = datetime.strptime(Hotel_withdrawal_date_str, '%Y-%m-%d').date()
            else:
                Hotel_withdrawal_date = None

            Hotel_withdrawal_time = request.POST.get('Hotel_withdrawal_time', '') 
            Hotel_withdrawal_username = request.POST.get('Hotel_withdrawal_username', '')
            Hotel_withdrawal_amount = request.POST.get('Hotel_withdrawal_amount', '')
            Hotel_withdrawal_withdrawer = request.POST.get('Hotel_withdrawal_withdrawer', '')

            # If "Other" option is selected, retrieve the value from the text input field
            if Hotel_withdrawal_withdrawer == 'Other':
                Hotel_withdrawal_withdrawer = request.POST.get('Hotel_withdrawal_other_person', '')

            user_instance = get_object_or_404(User, username=Hotel_withdrawal_username)
            full_name = f"{user_instance.first_name} {user_instance.last_name}"

            
            # Convert the amount to an integer (assuming the amount is in string format)
            amount_as_number = int(float(Hotel_withdrawal_amount))  # Convert string to float then to int

            # Convert the amount to words
            amount_in_words = numberToWords(amount_as_number)

            Hotel_Cash_Withdrawal.objects.create(
                Withdrawal_Hotel_Date=Hotel_withdrawal_date, 
                Withdrawal_Hotel_Time=Hotel_withdrawal_time, 
                Withdrawal_Hotel_Username=user_instance, 
                            
                Withdrawal_Hotel_Full_Name=full_name,

                Withdrawal_Hotel_Withdrawer=Hotel_withdrawal_withdrawer,
                Withdrawal_Hotel_Amount_In_Words=amount_in_words, 

                Withdrawal_Hotel_Amount=Hotel_withdrawal_amount, 
            )

            return redirect('/Expense-Profile/')

    except Exception as e:
        print(e)

    return render(request, "Hotel_Cash_Withdraw.html")

@login_required(login_url='Login_In')
def Food_Expense_Cash_Withdraw(request):
    if request.method == 'POST':
        try:
            Food_withdrawal_date_str = request.POST.get('Food_withdrawal_date', '') 
            Food_withdrawal_time = request.POST.get('Food_withdrawal_time', '') 
            Food_withdrawal_username = request.POST.get('Food_withdrawal_username', '')
            Food_withdrawal_amount = request.POST.get('Food_withdrawal_amount', '')
            Food_withdrawal_withdrawer = request.POST.get('Food_withdrawal_withdrawer', '')

            # If "Other" option is selected, retrieve the value from the text input field
            if Food_withdrawal_withdrawer == 'Other':
                Food_withdrawal_withdrawer = request.POST.get('Food_withdrawal_other_person', '')

            # Validate form input
            if Food_withdrawal_date_str and Food_withdrawal_time and Food_withdrawal_username and Food_withdrawal_amount and Food_withdrawal_withdrawer:
                Food_withdrawal_date = datetime.strptime(Food_withdrawal_date_str, '%Y-%m-%d').date()

                user_instance = get_object_or_404(User, username=Food_withdrawal_username)

                full_name = f"{user_instance.first_name} {user_instance.last_name}"

                 # Convert the amount to an integer (assuming the amount is in string format)
                amount_as_number = int(float(Food_withdrawal_amount))  # Convert string to float then to int

                # Convert the amount to words
                amount_in_words = numberToWords(amount_as_number)



                # Create the Cash Withdrawal object
                Food_Cash_Withdrawal.objects.create(
                    Withdrawal_Food_Date=Food_withdrawal_date, 
                    Withdrawal_Food_Time=Food_withdrawal_time, 
                    Withdrawal_Food_Username=user_instance, 
                               
                    Withdrawal_Food_Full_Name=full_name,

                    Withdrawal_Food_Withdrawer=Food_withdrawal_withdrawer, 
                    Withdrawal_Food_Amount=Food_withdrawal_amount,
                    Withdrawal_Food_Amount_In_Words=amount_in_words

                )
                return redirect('/Expense-Profile/')
            else:
                # Handle form validation errors
                return render(request, "Food_Cash_Withdraw.html", {'error_message': 'Please fill out all required fields.'})

        except Exception as e:
            # Log the exception or handle it appropriately
            print(e)
            return render(request, "Food_Cash_Withdraw.html", {'error_message': 'An error occurred while processing your request.'})

    return render(request, "Food_Cash_Withdraw.html")

@login_required(login_url='Login_In')
def Hotel_Expense_Cash_Delete(request, id):
    hotel_cash_profile = get_object_or_404(Hotel_Cash_Withdrawal, id=id)
    try:
        # Retrieve the specific hotel cash withdrawal entry or return a 404 if not found

        # Check if the user is allowed to delete
        if (
            request.user.username != "SuperAdmin" and
            request.user.username != "Admin" and 
            hotel_cash_profile.Withdrawal_Hotel_Username != request.user.username
        ):
            return redirect('/Expense-Profile/')  # Redirect if not authorized

        # Prevent Admin from deleting SuperAdmin's record
        if hotel_cash_profile.Withdrawal_Hotel_Username.username  == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Expense-Profile/')  # Redirect if Admin tries to delete SuperAdmin's record

        if request.method == 'POST':
            # Proceed to delete the record
            hotel_cash_profile.delete()
            return redirect('/Expense-Profile/')  # Redirect after deletion

        # Render a confirmation page for GET requests
        return render(request, 'confirm_delete.html', {'hotel_cash_profile': hotel_cash_profile})

    except Hotel_Cash_Withdrawal.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': 'User Profile not found.'})
    except Exception as e:
        print(e)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})


@login_required(login_url='Login_In')    
def Food_Expense_Cash_Delete(request, id):
    try:
        # Retrieve the specific food cash withdrawal entry or return a 404 if not found
        food_cash_profile = get_object_or_404(Food_Cash_Withdrawal, id=id)

        # Check if the user is allowed to delete the record
        if (
            request.user.username != "SuperAdmin" and 
            request.user.username != "Admin" and 
            food_cash_profile.Withdrawal_Food_Username != request.user.username
        ):
            return redirect('/Expense-Profile/')  # Redirect if not authorized

        # Prevent Admin from deleting SuperAdmin's record
        if food_cash_profile.Withdrawal_Food_Username.username == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Expense-Profile/')  # Redirect if Admin tries to delete SuperAdmin's record

        if request.method == 'POST':
            # Proceed to delete the record
            food_cash_profile.delete()
            return redirect('/Expense-Profile/')  # Redirect after deletion

        # Render a confirmation page for GET requests
        return render(request, 'confirm_delete.html', {'food_cash_profile': food_cash_profile})

    except Food_Cash_Withdrawal.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': 'User Profile not found.'})
    except Exception as e:
        print(e)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})


@login_required(login_url='Login_In')    
def Hotel_Cash_Miscellaneous_Expense(request):
    try:
        if request.method == 'POST':
            hotel_Cash_miscellaneous_expense_date_str = request.POST.get('hotel_Cash_miscellaneous_expense_date', '') 

            if hotel_Cash_miscellaneous_expense_date_str:
                hotel_Cash_miscellaneous_expense_date = datetime.strptime(hotel_Cash_miscellaneous_expense_date_str, '%Y-%m-%d').date()
            else:
                hotel_Cash_miscellaneous_expense_date = None

            hotel_Cash_miscellaneous_expense_time  = request.POST.get('hotel_Cash_miscellaneous_expense_time', '' )
            hotel_Cash_miscellaneous_expense_username  = request.POST.get('hotel_Cash_miscellaneous_expense_username', '' )
            hotel_Cash_miscellaneous_expense_name  = request.POST.get('hotel_Cash_miscellaneous_expense_name', '' )
            hotel_Cash_miscellaneous_expense_amount  = request.POST.get('hotel_Cash_miscellaneous_expense_amount', '' )
            hotel_Cash_miscellaneous_expense_instruction  = request.POST.get('hotel_Cash_miscellaneous_expense_instruction', '' )
                
            user_instance = get_object_or_404(User, username=hotel_Cash_miscellaneous_expense_username)
            full_name = f"{user_instance.first_name} {user_instance.last_name}"
            
              # Convert the amount to an integer (assuming the amount is in string format)
            amount_as_number = int(float(hotel_Cash_miscellaneous_expense_amount))  # Convert string to float then to int

                # Convert the amount to words
            amount_in_words = numberToWords(amount_as_number)

            Hotel_Cash_Miscellaneous_Expenses.objects.create(
                Miscellaneous_Expenses_Hotel_Date = hotel_Cash_miscellaneous_expense_date,
                Miscellaneous_Expenses_Hotel_Time = hotel_Cash_miscellaneous_expense_time,
                Miscellaneous_Expenses_Hotel_Username = user_instance,
                                
                Miscellaneous_Expenses_Hotel_Full_Name=full_name,

                Miscellaneous_Expenses_Hotel_Expense_Name = hotel_Cash_miscellaneous_expense_name,
                Miscellaneous_Expenses_Hotel_Amount = hotel_Cash_miscellaneous_expense_amount,
                Miscellaneous_Expenses_Hotel_Amount_In_Words = amount_in_words,

                Miscellaneous_Expenses_Hotel_Instruction = hotel_Cash_miscellaneous_expense_instruction,
            )
            

            return redirect('/Expense-Profile/')

    except Exception as e:
        print(e)

    return render (request, "Hotel_Cash_Miscellaneous_Expense.html")

@login_required(login_url='Login_In')
def Food_Cash_Miscellaneous_Expense(request):
    try:
        if request.method == 'POST':
            food_Cash_miscellaneous_expense_date_str = request.POST.get('food_Cash_miscellaneous_expense_date', '') 

            if food_Cash_miscellaneous_expense_date_str:
                food_Cash_miscellaneous_expense_date = datetime.strptime(food_Cash_miscellaneous_expense_date_str, '%Y-%m-%d').date()
            else:
                food_Cash_miscellaneous_expense_date = None

            food_Cash_miscellaneous_expense_time  = request.POST.get('food_Cash_miscellaneous_expense_time', '' )
            food_Cash_miscellaneous_expense_username  = request.POST.get('food_Cash_miscellaneous_expense_username', '' )
            food_Cash_miscellaneous_expense_name  = request.POST.get('food_Cash_miscellaneous_expense_name', '' )
            food_Cash_miscellaneous_expense_amount  = request.POST.get('food_Cash_miscellaneous_expense_amount', '' )
            food_Cash_miscellaneous_expense_instruction  = request.POST.get('food_Cash_miscellaneous_expense_instruction', '' )

            user_instance = get_object_or_404(User, username=food_Cash_miscellaneous_expense_username)

              # Extract the full name of the user from the instance
            full_name = f"{user_instance.first_name} {user_instance.last_name}"
            
              # Convert the amount to an integer (assuming the amount is in string format)
            amount_as_number = int(float(food_Cash_miscellaneous_expense_amount))  # Convert string to float then to int

                # Convert the amount to words
            amount_in_words = numberToWords(amount_as_number)

            Food_Cash_Miscellaneous_Expenses.objects.create(
                Miscellaneous_Expenses_Food_Date = food_Cash_miscellaneous_expense_date,
                Miscellaneous_Expenses_Food_Time = food_Cash_miscellaneous_expense_time,
                Miscellaneous_Expenses_Food_Username = user_instance,
                Miscellaneous_Expenses_Food_Full_Name=full_name,

                Miscellaneous_Expenses_Food_Expense_Name = food_Cash_miscellaneous_expense_name,
                Miscellaneous_Expenses_Food_Amount = food_Cash_miscellaneous_expense_amount,
                Miscellaneous_Expenses_Food_Amount_In_Words = amount_in_words,

                Miscellaneous_Expenses_Food_Instruction = food_Cash_miscellaneous_expense_instruction,
            )
            

            return redirect('/Expense-Profile/')

    except Exception as e:
        print(e)

    return render (request, "Food_Cash_Miscellaneous_Expense.html")

@login_required(login_url='Login_In')
def Hotel_Cash_Miscellaneous_Expense_Delete(request, id):
    try:
        # Retrieve the specific hotel miscellaneous expense entry or return a 404 if not found
        hotel_miscellaneous_expense = get_object_or_404(Hotel_Cash_Miscellaneous_Expenses, id=id)

        # Check if the user is allowed to delete the record
        if (
            request.user.username != "SuperAdmin" and 
            request.user.username != "Admin" and 
            hotel_miscellaneous_expense.Miscellaneous_Expenses_Hotel_Username != request.user.username
        ):
            return redirect('/Expense-Profile/')  # Redirect if not authorized

        # Prevent Admin from deleting SuperAdmin's record
        if hotel_miscellaneous_expense.Miscellaneous_Expenses_Hotel_Username.username == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Expense-Profile/')  # Redirect if Admin tries to delete SuperAdmin's record

        if request.method == 'POST':
            # Proceed to delete the record
            hotel_miscellaneous_expense.delete()
            return redirect('/Expense-Profile/')  # Redirect after deletion

        # Render a confirmation page for GET requests
        return render(request, 'confirm_delete.html', {'hotel_miscellaneous_expense': hotel_miscellaneous_expense})

    except Hotel_Cash_Miscellaneous_Expenses.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': 'User Profile not found.'})
    except Exception as e:
        print(e)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})


@login_required(login_url='Login_In')    
def Food_Cash_Miscellaneous_Expense_Delete(request, id):
    try:
        # Retrieve the specific food miscellaneous expense entry or return a 404 if not found
        food_miscellaneous_expense = get_object_or_404(Food_Cash_Miscellaneous_Expenses, id=id)

        # Check if the user is allowed to delete the record
        if (
            request.user.username != "SuperAdmin" and 
            request.user.username != "Admin" and 
            food_miscellaneous_expense.Miscellaneous_Expenses_Food_Username != request.user.username
        ):
            return redirect('/Expense-Profile/')  # Redirect if not authorized

        # Prevent Admin from deleting SuperAdmin's record
        if food_miscellaneous_expense.Miscellaneous_Expenses_Food_Username.username == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Expense-Profile/')  # Redirect if Admin tries to delete SuperAdmin's record

        if request.method == 'POST':
            # Proceed to delete the record
            food_miscellaneous_expense.delete()
            return redirect('/Expense-Profile/')  # Redirect after deletion

        # Render a confirmation page for GET requests
        return render(request, 'confirm_delete.html', {'food_miscellaneous_expense': food_miscellaneous_expense})

    except Food_Cash_Miscellaneous_Expenses.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': 'User Profile not found.'})
    except Exception as e:
        print(e)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})

@login_required(login_url='Login_In')
def Hotel_Cash_Miscellaneous_Expense_Update(request, id):
    try:
        # Retrieve the instance of Hotel Cash Miscellaneous Expense to be updated
        queryset = get_object_or_404(Hotel_Cash_Miscellaneous_Expenses, id=id)

        # Check if the logged-in user is SuperAdmin or the creator of the record
        if (
            request.user.username != "SuperAdmin" and 
            request.user.username != "Admin" and 
            queryset.Miscellaneous_Expenses_Hotel_Username.username != request.user.username
        ):
            return redirect('/Expense-Profile/')  # Redirect if the user is not allowed
        
        # Prevent Admin from updating SuperAdmin's record
        if queryset.Miscellaneous_Expenses_Hotel_Username.username == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Expense-Profile/')  # Redirect if Admin tries to update SuperAdmin's record

        if request.method == 'POST':
            # Retrieve form data from POST request
            hotel_Cash_miscellaneous_expense_date_str = request.POST.get('hotel_Cash_miscellaneous_expense_date', '') 
            hotel_Cash_miscellaneous_expense_time = request.POST.get('hotel_Cash_miscellaneous_expense_time', '')
            hotel_Cash_miscellaneous_expense_username = request.POST.get('hotel_Cash_miscellaneous_expense_username', '')
            hotel_Cash_miscellaneous_expense_name = request.POST.get('hotel_Cash_miscellaneous_expense_name', '')
            hotel_Cash_miscellaneous_expense_amount = request.POST.get('hotel_Cash_miscellaneous_expense_amount', '')
            hotel_Cash_miscellaneous_expense_instruction = request.POST.get('hotel_Cash_miscellaneous_expense_instruction', '')

            # Parse date string to datetime object
            hotel_Cash_miscellaneous_expense_date = datetime.strptime(hotel_Cash_miscellaneous_expense_date_str, '%Y-%m-%d').date() if hotel_Cash_miscellaneous_expense_date_str else None

            user_instance = get_object_or_404(User, username=hotel_Cash_miscellaneous_expense_username)
            full_name = f"{user_instance.first_name} {user_instance.last_name}"


            # Validate and convert amount to integer
            amount_as_number = int(hotel_Cash_miscellaneous_expense_amount) 
            
            # Convert the amount to words
            amount_in_words = numberToWords(amount_as_number)

            # Update instance with new data
            queryset.Miscellaneous_Expenses_Hotel_Date = hotel_Cash_miscellaneous_expense_date
            queryset.Miscellaneous_Expenses_Hotel_Time = hotel_Cash_miscellaneous_expense_time
            
            # Check if the user is SuperAdmin
            if request.user.username != "SuperAdmin":
                queryset.Miscellaneous_Expenses_Hotel_Username = user_instance
                queryset.Miscellaneous_Expenses_Hotel_Full_Name=full_name

            
            # Fixed the assignment to remove the comma
            queryset.Miscellaneous_Expenses_Hotel_Amount_In_Words = amount_in_words  
            queryset.Miscellaneous_Expenses_Hotel_Expense_Name = hotel_Cash_miscellaneous_expense_name
            queryset.Miscellaneous_Expenses_Hotel_Amount = hotel_Cash_miscellaneous_expense_amount
            queryset.Miscellaneous_Expenses_Hotel_Instruction = hotel_Cash_miscellaneous_expense_instruction

            # Save updated instance
            queryset.save()  

            # Redirect to expense profile page after successful update
            return redirect('/Expense-Profile/')

        # Prepare context to be passed to the template
        context = {'hotel_cash_miscellaneous_expense_update': queryset}

        # Render the update form template with context data
        return render(request, 'Hotel_Cash_Miscellaneous_Expense_Update.html', context)
    
    except Hotel_Cash_Miscellaneous_Expenses.DoesNotExist:
        # Handle the case where the requested object does not exist
        return render(request, 'error_template.html', {'error_message': 'Requested item does not exist.'})



@login_required(login_url='Login_In')
def Food_Cash_Miscellaneous_Expense_Update(request, id):
    try:
        # Retrieve the instance of Food Cash Miscellaneous Expense to be updated
        queryset = get_object_or_404(Food_Cash_Miscellaneous_Expenses, id=id)

        # Check if the logged-in user is SuperAdmin or the creator of the record
        if (
            request.user.username != "SuperAdmin" and 
            request.user.username != "Admin" and 
            queryset.Miscellaneous_Expenses_Food_Username.username  != request.user.username
        ):
            return redirect('/Expense-Profile/')  # Redirect if the user is not allowed
        
        # Prevent Admin from updating SuperAdmin's record
        if queryset.Miscellaneous_Expenses_Food_Username.username  == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Expense-Profile/')  # Redirect if Admin tries to update SuperAdmin's record

        if request.method == 'POST':
            # Retrieve form data from POST request
            food_Cash_miscellaneous_expense_date_str = request.POST.get('food_Cash_miscellaneous_expense_date', '') 
            food_Cash_miscellaneous_expense_time = request.POST.get('food_Cash_miscellaneous_expense_time', '' )
            food_Cash_miscellaneous_expense_username = request.POST.get('food_Cash_miscellaneous_expense_username', '' )
            food_Cash_miscellaneous_expense_name = request.POST.get('food_Cash_miscellaneous_expense_name', '' )
            food_Cash_miscellaneous_expense_amount = request.POST.get('food_Cash_miscellaneous_expense_amount', '' )
            food_Cash_miscellaneous_expense_instruction = request.POST.get('food_Cash_miscellaneous_expense_instruction', '' )

            # Parse date string to datetime object
            food_Cash_miscellaneous_expense_date = datetime.strptime(food_Cash_miscellaneous_expense_date_str, '%Y-%m-%d').date() if food_Cash_miscellaneous_expense_date_str else None

            user_instance = get_object_or_404(User, username=food_Cash_miscellaneous_expense_username)

            full_name = f"{user_instance.first_name} {user_instance.last_name}"

            # Validate and convert amount to integer
            amount_as_number = int(food_Cash_miscellaneous_expense_amount)  # Ensure total is used directly

            # Convert the amount to words
            amount_in_words = numberToWords(amount_as_number)

            # Update instance with new data
            queryset.Miscellaneous_Expenses_Food_Date = food_Cash_miscellaneous_expense_date
            queryset.Miscellaneous_Expenses_Food_Time = food_Cash_miscellaneous_expense_time
            
            # Check if the user is SuperAdmin
            if request.user.username != "SuperAdmin":
                queryset.Miscellaneous_Expenses_Food_Username = user_instance
                queryset.Miscellaneous_Expenses_Food_Full_Name=full_name
            
            # Fixed the assignment to remove the comma
            queryset.Miscellaneous_Expenses_Food_Amount_In_Words = amount_in_words  
            queryset.Miscellaneous_Expenses_Food_Expense_Name = food_Cash_miscellaneous_expense_name
            

            queryset.Miscellaneous_Expenses_Food_Amount = food_Cash_miscellaneous_expense_amount
            queryset.Miscellaneous_Expenses_Food_Instruction = food_Cash_miscellaneous_expense_instruction

            # Save updated instance
            queryset.save()  

            # Redirect to expense profile page after successful update
            return redirect('/Expense-Profile/')
        
        # Prepare context to be passed to the template
        context = {'food_cash_miscellaneous_expense_update': queryset}

        # Render the update form template with context data
        return render(request, 'Food_Cash_Miscellaneous_Expense_Update.html', context)
    
    except Food_Cash_Miscellaneous_Expenses.DoesNotExist:
        # Handle the case where the requested object does not exist
        return render(request, 'error_template.html', {'error_message': 'Requested item does not exist.'})











@login_required(login_url='Login_In')
def Staff_Advance_Salaries(request):
    try:
        if request.method == "POST":
            # Parse date from form input
            staff_advance_date_str = request.POST.get('staff_advance__date')
            if staff_advance_date_str:
                staff_advance__date = datetime.strptime(staff_advance_date_str, '%Y-%m-%d').date()
            else:
                staff_advance__date = None
            
            # Get other form inputs
            staff_advance__time = request.POST.get('staff_advance__time')
            staff_advance_username = request.POST.get('staff_advance_username')
            staff_advance_year_month = request.POST.get('staff_advance_year_month')
            staff_advance_name_id = request.POST.get('staff_advance_name')
            
            # Fetch user profile, ensure the user is active
            if staff_advance_name_id:
                staff_advance_name = get_object_or_404(User_Profile, pk=staff_advance_name_id, is_active=True)
            else:
                staff_advance_name = None
            
            advance_amount = request.POST.get('advance_amount')
            staff_advance_instruction = request.POST.get('staff_advance_instruction')
            
            user_instance = get_object_or_404(User, username=staff_advance_username)

            
            # Extract the full name of the user from the instance
            full_name = f"{user_instance.first_name} {user_instance.last_name}"

            
            # Convert the amount to an integer (assuming the amount is in string format)
            amount_as_number = int(float(advance_amount))  # Convert string to float then to int

            # Convert the amount to words
            amount_in_words = numberToWords(amount_as_number)

            # Create a new Staff_Advance instance
            Staff_Advance.objects.create(
                Staff_Advance_date=staff_advance__date,
                Staff_Advance_time=staff_advance__time,
                Staff_Advance_username=user_instance,
                Staff_Advance_Full_Name=full_name,

                Staff_Advance_year_month=staff_advance_year_month,
                Staff_Advance_name=staff_advance_name,
                Staff_Advance_amount=advance_amount,
                Staff_Advance_Amount_In_Words=amount_in_words,

                Staff_Advance_instruction=staff_advance_instruction
            )
            
            # Redirect to the desired URL
            return redirect('/Expense-Profile/')
        
        # Get active user profiles for dropdown
        user_profiles = User_Profile.objects.filter(is_active=True)
        
        # Context dictionary to pass data to the template
        context = {
            'user_profiles': user_profiles,
        }
        
        return render(request, "Staff_Advance_Salaries.html", context)
    
    except Exception as e:
        # Provide error information to the template
        context = {
            'error': f"An error occurred: {str(e)}",
            'user_profiles': User_Profile.objects.filter(is_active=True),  # Show only active users in case of error
        }
        return render(request, "Staff_Advance_Salaries.html", context)

@login_required(login_url='Login_In')
def Staff_Advance_Salaries_Delete(request, id):
    try:
        # Retrieve the specific staff advance entry or return a 404 if not found
        staffadvance = get_object_or_404(Staff_Advance, id=id)

        # Check if the user is allowed to delete the record
        if (
            request.user.username != "SuperAdmin" and 
            request.user.username != "Admin" and 
            staffadvance.Staff_Advance_username != request.user.username
        ):
            return redirect('/Expense-Profile/')  # Redirect if not authorized

        # Prevent Admin from deleting SuperAdmin's record
        if staffadvance.Staff_Advance_username.username == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Expense-Profile/')  # Redirect if Admin tries to delete SuperAdmin's record

        if request.method == 'POST':
            # Proceed to delete the record
            staffadvance.delete()
            return redirect('/Expense-Profile/')  # Redirect after deletion

        # Render a confirmation page for GET requests
        return render(request, 'confirm_delete.html', {'staffadvance': staffadvance})

    except Staff_Advance.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': 'User Profile not found.'})
    except Exception as e:
        print(e)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})

@login_required(login_url='Login_In')    
def Staff_Advance_Salaries_Update(request, id):
    try:
        # Retrieve the instance of Staff_Advance to be updated
        queryset = get_object_or_404(Staff_Advance, id=id)

        # Check if the logged-in user is allowed to update the record
        if (
            request.user.username != "SuperAdmin" and 
            request.user.username != "Admin" and 
            queryset.Staff_Advance_username.username != request.user.username
        ):
            return redirect('/Expense-Profile/')  # Redirect if the user is not allowed
        
        # Prevent Admin from updating SuperAdmin's record
        if queryset.Staff_Advance_username.username == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Expense-Profile/')  # Redirect if Admin tries to update SuperAdmin's record

        if request.method == "POST":
            print("POST request received.")
            staff_advance_date_str = request.POST.get('staff_advance__date')
            staff_advance__date = datetime.strptime(staff_advance_date_str, '%Y-%m-%d').date() if staff_advance_date_str else None
            
            staff_advance__time = request.POST.get('staff_advance__time')
            staff_advance_username = request.POST.get('staff_advance_username')
            staff_advance_year_month = request.POST.get('staff_advance_year_month')
         
            
           
            
            advance_amount = request.POST.get('advance_amount')
            staff_advance_instruction = request.POST.get('staff_advance_instruction')

            amount_as_number = int(advance_amount)  # Ensure total is used directly
            # Convert the amount to words
            amount_in_words = numberToWords(amount_as_number)
           
            # Update instance with new data
            queryset.Staff_Advance_date = staff_advance__date
            queryset.Staff_Advance_time = staff_advance__time
            queryset.Staff_Advance_Amount_In_Words=amount_in_words
            queryset.Staff_Advance_username = get_object_or_404(User, username=staff_advance_username)
            queryset.Staff_Advance_year_month = staff_advance_year_month
         
            queryset.Staff_Advance_amount = advance_amount
            queryset.Staff_Advance_instruction = staff_advance_instruction
            
            # Save the updated instance
            queryset.save()  
            print("Record updated successfully.")

            # Redirect to expense profile page after successful update
            return redirect('/Expense-Profile/')
        
        # Prepare context to be passed to the template
        context = {
            'staff_advance_salaries_update': queryset,
            'user_profiles': User_Profile.objects.all(),
        }

        # Render the update form template with context data
        return render(request, 'Staff_Advance_Salaries_Update.html', context)
    
    except Staff_Advance.DoesNotExist:
        return render(request, 'error_template.html', {'error_message': 'Requested item does not exist.'})
    
    except Exception as e:
        # Provide error information to the template
        context = {
            'error': f"An error occurred: {str(e)}",
            'user_profiles': User_Profile.objects.all(),
        }
        return render(request, "Staff_Advance_Salaries.html", context)























@login_required(login_url='Login_In')
def Staff_Advance_Salaries_View(request, id):
    try:
        # Fetch the specific hotel deposit using the provided id
        staff_advance_salaries_view = get_object_or_404(Staff_Advance, id=id)

        # Prepare context
        context = {
            'staff_advance_salaries_view': staff_advance_salaries_view,  # Use singular since we are fetching one record
        }
        return render_to_pdf('StaffAdvanceSalariesView.html', context)
    except Exception as e:
        print(e)  # Consider using logging instead of print for production code
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the hotel deposit. Please try again later.'})

@login_required(login_url='Login_In')
def Hotel_Expense_Cash_Withdraw_View(request, id):
    try:
        # Fetch the specific hotel deposit using the provided id
        hotel_expense_cash_withdraw_view = get_object_or_404(Hotel_Cash_Withdrawal, id=id)

        # Prepare context
        context = {
            'hotel_expense_cash_withdraw_view': hotel_expense_cash_withdraw_view,  # Use singular since we are fetching one record
        }
        return render_to_pdf('HotelExpenseCashWithdrawView.html', context)
    except Exception as e:
        print(e)  # Consider using logging instead of print for production code
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the hotel deposit. Please try again later.'})

@login_required(login_url='Login_In')
def Food_Expense_Cash_Withdraw_View(request, id):
    try:
        # Fetch the specific hotel deposit using the provided id
        food_expense_cash_withdraw_view = get_object_or_404(Food_Cash_Withdrawal, id=id)

        # Prepare context
        context = {
            'food_expense_cash_withdraw_view': food_expense_cash_withdraw_view,  # Use singular since we are fetching one record
        }
        return render_to_pdf('FoodExpenseCashWithdrawView.html', context)
    except Exception as e:
        print(e)  # Consider using logging instead of print for production code
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the hotel deposit. Please try again later.'})

@login_required(login_url='Login_In')
def Hotel_Cash_Miscellaneous_Expense_View(request, id):
    try:
        # Fetch the specific hotel deposit using the provided id
        hotel_cash_miscellaneous_expense_view = get_object_or_404(Hotel_Cash_Miscellaneous_Expenses, id=id)

        # Prepare context
        context = {
            'hotel_cash_miscellaneous_expense_view': hotel_cash_miscellaneous_expense_view,  # Use singular since we are fetching one record
        }
        return render_to_pdf('HotelCashMiscellaneousExpenseView.html', context)
    except Exception as e:
        print(e)  # Consider using logging instead of print for production code
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the hotel deposit. Please try again later.'})

@login_required(login_url='Login_In')
def Food_Cash_Miscellaneous_Expense_View(request, id):
    try:
        # Fetch the specific hotel deposit using the provided id
        food_cash_miscellaneous_expense_view = get_object_or_404(Food_Cash_Miscellaneous_Expenses, id=id)

        # Prepare context
        context = {
            'food_cash_miscellaneous_expense_view': food_cash_miscellaneous_expense_view,  # Use singular since we are fetching one record
        }
        return render_to_pdf('FoodCashMiscellaneousExpenseView.html', context)
    except Exception as e:
        print(e)  # Consider using logging instead of print for production code
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the hotel deposit. Please try again later.'})




