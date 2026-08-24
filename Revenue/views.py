import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .models import Food_Cash_Deposite, Hotel_Cash_Deposite
from Dashboard.views import numberToWords
from Reports.pdf import render_to_pdf

logger = logging.getLogger(__name__)


def _parse_amount(raw):
    """Accepts a thousands-separator-formatted amount (e.g. "1,500",
    common with Indian currency entry) and returns a clean Decimal, or
    None if it isn't a valid amount. Being forgiving of commas on input
    while always storing a clean Decimal is what keeps
    Sum('Deposite_Hotel_Amount') correct — see Revenue/models.py."""
    if raw is None:
        return None
    cleaned = re.sub(r'[,\s]', '', raw)
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None
    if value < 0:
        return None
    return value


def _is_deposit_admin(user):
    return user.username in ("SuperAdmin", "Admin")


@login_required(login_url='Login_In')
def Revenue_Profile(request):
    try:
        hotel_deposite = Hotel_Cash_Deposite.objects.all()
        food_deposite = Food_Cash_Deposite.objects.all()
        return render(request, "Revenue_Profile.html", {
            'hotel_deposite': hotel_deposite,
            'food_deposite': food_deposite,
        })
    except Exception as e:
        logger.error(f"Unexpected error in Revenue_Profile: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching revenue records. Please try again later.'})


@login_required(login_url='Login_In')
def Hotel_Revenue_View(request, id):
    try:
        hotel_deposit_view = get_object_or_404(Hotel_Cash_Deposite, id=id)
        return render_to_pdf('HotelRevenueView.html', {'hotel_deposit_view': hotel_deposit_view})
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Revenue_View: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the hotel deposit. Please try again later.'})


@login_required(login_url='Login_In')
def Food_Revenue_View(request, id):
    try:
        food_deposit_view = get_object_or_404(Food_Cash_Deposite, id=id)
        return render_to_pdf('FoodRevenueView.html', {'food_deposit_view': food_deposit_view})
    except Exception as e:
        logger.error(f"Unexpected error in Food_Revenue_View: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the food deposit. Please try again later.'})


@login_required(login_url='Login_In')
def Hotel_Revenue_Cash_Deposite(request):
    if request.method != 'POST':
        return render(request, "Hotel_Cash_Deposite.html")

    hotel_deposit_date_str = request.POST.get('hotel_deposite_date', '')
    hotel_deposit_date = datetime.strptime(hotel_deposit_date_str, '%Y-%m-%d').date() if hotel_deposit_date_str else None

    hotel_deposit_time = request.POST.get('hotel_deposite_time', '')
    hotel_deposit_depositer = request.POST.get('hotel_deposite_depositer', '')
    if hotel_deposit_depositer == 'Other':
        hotel_deposit_depositer = request.POST.get('hotel_deposite_other_person', '')

    amount = _parse_amount(request.POST.get('hotel_deposite_amount', ''))
    if amount is None:
        messages.error(request, 'Please enter a valid deposit amount.')
        return render(request, "Hotel_Cash_Deposite.html")

    if not hotel_deposit_time:
        # Deposite_Hotel_Time is a non-nullable TimeField; the form
        # auto-fills it via JS on load so this is normally unreachable
        # from the real UI, but a direct POST (or JS-disabled browser)
        # with a blank time previously crashed at .save() with a raw
        # ValidationError. Confirmed directly. Validate up front instead.
        messages.error(request, 'Please provide a valid time.')
        return render(request, "Hotel_Cash_Deposite.html")

    try:
        with transaction.atomic():
            # The form's username field is readonly/pre-filled for
            # display, same as Shift_Handover's — always use the real
            # authenticated user rather than trusting POST data, so a
            # forged field can't attribute a deposit to someone else.
            user_instance = request.user
            full_name = f"{user_instance.first_name} {user_instance.last_name}".strip() or user_instance.username

            amount_in_words = numberToWords(int(amount))

            Hotel_Cash_Deposite.objects.create(
                Deposite_Hotel_Date=hotel_deposit_date,
                Deposite_Hotel_Time=hotel_deposit_time,
                Deposite_Hotel_Username=user_instance,
                Deposite_Hotel_Full_Name=full_name,
                Deposite_Hotel_Withdrawer=hotel_deposit_depositer,
                Deposite_Hotel_Amount=amount,
                Deposite_Hotel_Amount_In_Words=amount_in_words,
            )
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Revenue_Cash_Deposite: {e}", exc_info=True)
        messages.error(request, 'An error occurred while recording the deposit. Please check the date/time and try again.')
        return render(request, "Hotel_Cash_Deposite.html")

    logger.info(f"User '{request.user.username}' recorded a hotel cash deposit of {amount}.")
    messages.success(request, 'Hotel cash deposit recorded successfully.')
    return redirect('/Revenue-Profile/')


@login_required(login_url='Login_In')
def Food_Revenue_Cash_Deposite(request):
    if request.method != 'POST':
        return render(request, "Food_Cash_Deposite.html")

    food_deposit_date_str = request.POST.get('food_deposite_date', '')
    food_deposit_date = datetime.strptime(food_deposit_date_str, '%Y-%m-%d').date() if food_deposit_date_str else None

    food_deposit_time = request.POST.get('food_deposite_time', '')
    food_deposit_depositer = request.POST.get('food_deposite_depositer', '')
    if food_deposit_depositer == 'Other':
        food_deposit_depositer = request.POST.get('food_deposite_other_person', '')

    amount = _parse_amount(request.POST.get('food_deposite_amount', ''))
    if amount is None:
        messages.error(request, 'Please enter a valid deposit amount.')
        return render(request, "Food_Cash_Deposite.html")

    if not food_deposit_time:
        messages.error(request, 'Please provide a valid time.')
        return render(request, "Food_Cash_Deposite.html")

    try:
        with transaction.atomic():
            user_instance = request.user
            full_name = f"{user_instance.first_name} {user_instance.last_name}".strip() or user_instance.username

            amount_in_words = numberToWords(int(amount))

            Food_Cash_Deposite.objects.create(
                Deposite_Food_Date=food_deposit_date,
                Deposite_Food_Time=food_deposit_time,
                Deposite_Food_Username=user_instance,
                Deposite_Food_Full_Name=full_name,
                Deposite_Food_Withdrawer=food_deposit_depositer,
                Deposite_Food_Amount=amount,
                Deposite_Food_Amount_In_Words=amount_in_words,
            )
    except Exception as e:
        logger.error(f"Unexpected error in Food_Revenue_Cash_Deposite: {e}", exc_info=True)
        messages.error(request, 'An error occurred while recording the deposit. Please check the date/time and try again.')
        return render(request, "Food_Cash_Deposite.html")

    logger.info(f"User '{request.user.username}' recorded a food cash deposit of {amount}.")
    messages.success(request, 'Food cash deposit recorded successfully.')
    return redirect('/Revenue-Profile/')


@login_required(login_url='Login_In')
def Hotel_Revenue_Cash_Delete(request, id):
    hotel_cash_profile = get_object_or_404(Hotel_Cash_Deposite, id=id)

    try:
        # Was: `hotel_cash_profile.Deposite_Hotel_Username != request.user.username`
        # — comparing a User instance to a plain string, which is never
        # equal regardless of actual ownership. Confirmed directly: the
        # true owner of a deposit could never delete their own record,
        # only accounts literally named "SuperAdmin"/"Admin" could ever
        # reach the delete branch. Comparing User to User fixes it.
        is_owner = hotel_cash_profile.Deposite_Hotel_Username == request.user
        if not _is_deposit_admin(request.user) and not is_owner:
            messages.error(request, "You don't have permission to delete this record.")
            return redirect('/Revenue-Profile/')

        if hotel_cash_profile.Deposite_Hotel_Username.username == "SuperAdmin" and request.user.username == "Admin":
            messages.error(request, "The SuperAdmin account's records can't be deleted.")
            return redirect('/Revenue-Profile/')

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Revenue-Profile/')

        with transaction.atomic():
            hotel_cash_profile.delete()

        logger.info(f"User '{request.user.username}' deleted hotel cash deposit id={id}.")
        messages.success(request, 'Hotel cash deposit deleted successfully.')
        return redirect('/Revenue-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Revenue_Cash_Delete: {e}", exc_info=True)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the record.'})


@login_required(login_url='Login_In')
def Food_Revenue_Cash_Delete(request, id):
    food_cash_profile = get_object_or_404(Food_Cash_Deposite, id=id)

    try:
        is_owner = food_cash_profile.Deposite_Food_Username == request.user
        if not _is_deposit_admin(request.user) and not is_owner:
            messages.error(request, "You don't have permission to delete this record.")
            return redirect('/Revenue-Profile/')

        if food_cash_profile.Deposite_Food_Username.username == "SuperAdmin" and request.user.username == "Admin":
            messages.error(request, "The SuperAdmin account's records can't be deleted.")
            return redirect('/Revenue-Profile/')

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Revenue-Profile/')

        with transaction.atomic():
            food_cash_profile.delete()

        logger.info(f"User '{request.user.username}' deleted food cash deposit id={id}.")
        messages.success(request, 'Food cash deposit deleted successfully.')
        return redirect('/Revenue-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Food_Revenue_Cash_Delete: {e}", exc_info=True)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the record.'})
