from django.shortcuts import get_object_or_404, redirect, render
from .models import Food_Cash_Deposite,Hotel_Cash_Deposite
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import render, redirect
from datetime import datetime
from .models import Hotel_Cash_Deposite
from django.shortcuts import render, redirect
from datetime import datetime
from .models import Hotel_Cash_Deposite
from  Dashboard.views import numberToWords
from Reports.pdf import render_to_pdf  # Import the render_to_pdf function




@login_required(login_url='Login_In')
def Revenue_Profile(request):
    try:
        hotel_deposite = Hotel_Cash_Deposite.objects.all()
        food_deposite = Food_Cash_Deposite.objects.all()
        context = {
            'hotel_deposite': hotel_deposite,
            'food_deposite': food_deposite
        }
        return render(request, "Revenue_Profile.html", context)
    except Exception as e:
        print(e)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})


@login_required(login_url='Login_In')
def Hotel_Revenue_View(request, id):
    try:
        # Fetch the specific hotel deposit using the provided id
        hotel_deposit_view = get_object_or_404(Hotel_Cash_Deposite, id=id)

        # Prepare context
        context = {
            'hotel_deposit_view': hotel_deposit_view,  # Use singular since we are fetching one record
        }
        return render_to_pdf('HotelRevenueView.html', context)
    except Exception as e:
        print(e)  # Consider using logging instead of print for production code
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the hotel deposit. Please try again later.'})


@login_required(login_url='Login_In')
def Food_Revenue_View(request, id):
    try:
        # Fetch the specific hotel deposit using the provided id
        food_deposit_view = get_object_or_404(Food_Cash_Deposite, id=id)

        # Prepare context
        context = {
            'food_deposit_view': food_deposit_view,  # Use singular since we are fetching one record
        }
        return render_to_pdf('FoodRevenueView.html', context)
    except Exception as e:
        print(e)  # Consider using logging instead of print for production code
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the hotel deposit. Please try again later.'})







@login_required(login_url='Login_In')
def Hotel_Revenue_Cash_Deposite(request):
    try:
        if request.method == 'POST':
            # Retrieve data from the POST request
            hotel_deposit_date_str = request.POST.get('hotel_deposite_date', '')

            # Convert date string to datetime object
            if hotel_deposit_date_str:
                hotel_deposit_date = datetime.strptime(hotel_deposit_date_str, '%Y-%m-%d').date()
            else:
                hotel_deposit_date = None

            # Retrieve other form fields from the POST request
            hotel_deposit_time = request.POST.get('hotel_deposite_time', '')
            hotel_deposit_username = request.POST.get('hotel_deposite_username', '')
            hotel_deposit_amount = request.POST.get('hotel_deposite_amount', '')
            hotel_deposit_depositer = request.POST.get('hotel_deposite_depositer', '')

            # If "Other" option is selected, retrieve the value from the text input field
            if hotel_deposit_depositer == 'Other':
                hotel_deposit_depositer = request.POST.get('hotel_deposite_other_person', '')

            user_instance = get_object_or_404(User, username=hotel_deposit_username)

            # Extract the full name of the user from the instance
            full_name = f"{user_instance.first_name} {user_instance.last_name}"

            # Convert the amount to an integer (assuming the amount is in string format)
            amount_as_number = int(float(hotel_deposit_amount))  # Convert string to float then to int

            # Convert the amount to words
            amount_in_words = numberToWords(amount_as_number)

            # Create a new instance of Hotel_Cash_Deposite model with retrieved data
            Hotel_Cash_Deposite.objects.create(
                Deposite_Hotel_Date=hotel_deposit_date,
                Deposite_Hotel_Time=hotel_deposit_time,
                Deposite_Hotel_Username=user_instance,
                Deposite_Hotel_Full_Name=full_name,
                Deposite_Hotel_Withdrawer=hotel_deposit_depositer,
                Deposite_Hotel_Amount=hotel_deposit_amount,
                Deposite_Hotel_Amount_In_Words=amount_in_words,
            )

            # Redirect to the revenue profile page after successful submission
            return redirect('/Revenue-Profile/')

    except Exception as e:
        print(e)  # Consider logging the error for better error handling

    # Render the Hotel_Cash_Deposite.html template
    return render(request, "Hotel_Cash_Deposite.html")


@login_required(login_url='Login_In')
def Food_Revenue_Cash_Deposite(request):
    try:
        if request.method == 'POST':
            # Retrieve data from the POST request
            food_deposit_date_str = request.POST.get('food_deposite_date', '') 

            # Convert date string to datetime object
            if food_deposit_date_str:
                food_deposit_date = datetime.strptime(food_deposit_date_str, '%Y-%m-%d').date()
            else:
                food_deposit_date = None

            # Retrieve other form fields from the POST refood
            food_deposit_time = request.POST.get('food_deposite_time', '') 
            food_deposit_username = request.POST.get('food_deposite_username', '')
            food_deposit_amount = request.POST.get('food_deposite_amount', '')
            food_deposit_depositer = request.POST.get('food_deposite_depositer', '')

            # If "Other" option is selected, retrieve the value from the text input field
            if food_deposit_depositer == 'Other':
                food_deposit_depositer = request.POST.get('food_deposite_other_person', '')

            user_instance = get_object_or_404(User, username=food_deposit_username)

            # Extract the full name of the user from the instance
            full_name = f"{user_instance.first_name} {user_instance.last_name}"

            # Convert the amount to an integer (assuming the amount is in string format)
            amount_as_number = int(float(food_deposit_amount))  # Convert string to float then to int

            # Convert the amount to words
            amount_in_words = numberToWords(amount_as_number)

            # Create a new instance of Hotel_Cash_Deposite model with retrieved data
            Food_Cash_Deposite.objects.create(
                Deposite_Food_Date=food_deposit_date, 
                Deposite_Food_Time=food_deposit_time, 
                Deposite_Food_Username=user_instance, 
                Deposite_Food_Full_Name=full_name,

                Deposite_Food_Withdrawer=food_deposit_depositer, 
                Deposite_Food_Amount=food_deposit_amount, 
                Deposite_Food_Amount_In_Words=amount_in_words, 

                 

            )

            # Redirect to the revenue profile page after successful submission
            return redirect('/Revenue-Profile/')

    except Exception as e:
        print(e)  # Consider logging the error for better error handling

    # Render the Hotel_Cash_Deposite.html template
    return render(request, "Food_Cash_Deposite.html")


@login_required(login_url='Login_In')
def Hotel_Revenue_Cash_Delete(request, id):
    # Retrieve the specific hotel cash deposit entry or return a 404 if not found
    hotel_cash_profile = get_object_or_404(Hotel_Cash_Deposite, id=id)

    try:
        # Check if the user is allowed to delete
        if (
            request.user.username != "SuperAdmin" and
            request.user.username != "Admin" and 
            hotel_cash_profile.Deposite_Hotel_Username != request.user.username
        ):
            return redirect('/Revenue-Profile/')  # Redirect if not authorized

        # Prevent Admin from deleting SuperAdmin's record
        if hotel_cash_profile.Deposite_Hotel_Username.username == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Revenue-Profile/')  # Redirect if Admin tries to delete SuperAdmin's record

        if request.method == 'POST':
            # Proceed to delete the record
            hotel_cash_profile.delete()
            return redirect('/Revenue-Profile/')  # Redirect after deletion

        # Render a confirmation page for GET requests
        return render(request, 'confirm_delete.html', {'hotel_cash_profile': hotel_cash_profile})

    except Hotel_Cash_Deposite.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': 'User Profile not found.'})
    except Exception as e:
        print(e)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})



@login_required(login_url='Login_In')
def Food_Revenue_Cash_Delete(request, id):
    # Retrieve the specific food cash deposit entry or return a 404 if not found
    food_cash_profile = get_object_or_404(Food_Cash_Deposite, id=id)

    try:
        # Check if the user is allowed to delete
        if (
            request.user.username != "SuperAdmin" and
            request.user.username != "Admin" and 
            food_cash_profile.Deposite_Food_Username != request.user.username
        ):
            return redirect('/Revenue-Profile/')  # Redirect if not authorized

        # Prevent Admin from deleting SuperAdmin's record
        if food_cash_profile.Deposite_Food_Username.username == "SuperAdmin" and request.user.username == "Admin":
            return redirect('/Revenue-Profile/')  # Redirect if Admin tries to delete SuperAdmin's record

        if request.method == 'POST':
            # Proceed to delete the record
            food_cash_profile.delete()
            return redirect('/Revenue-Profile/')  # Redirect after deletion

        # Render a confirmation page for GET requests
        return render(request, 'confirm_delete.html', {'food_cash_profile': food_cash_profile})

    except Food_Cash_Deposite.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': 'User Profile not found.'})
    except Exception as e:
        print(e)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})

