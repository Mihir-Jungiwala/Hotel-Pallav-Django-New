import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction

from Staff_Profile.models import User_Profile
from .models import (
    Food_Cash_Miscellaneous_Expenses, Food_Cash_Withdrawal,
    Hotel_Cash_Miscellaneous_Expenses, Hotel_Cash_Withdrawal, Staff_Advance,
)
from Dashboard.views import numberToWords
from Reports.pdf import render_to_pdf

logger = logging.getLogger(__name__)


def _parse_amount(raw):
    """Same helper as Revenue._parse_amount: accepts a comma-formatted
    amount (e.g. "1,500") and returns a clean non-negative Decimal, or
    None if invalid. See docs/backend-hardening-log.md — this is what
    keeps Dashboard's Sum() queries over these fields arithmetically
    correct, now that the amount columns are DecimalFields."""
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


def _is_expense_admin(user):
    return user.username in ("SuperAdmin", "Admin")


def _full_name(user_instance):
    return f"{user_instance.first_name} {user_instance.last_name}".strip() or user_instance.username


@login_required(login_url='Login_In')
def Expense_Profile(request):
    try:
        context = {
            'hotel_withdrawals': Hotel_Cash_Withdrawal.objects.all(),
            'food_withdrawals': Food_Cash_Withdrawal.objects.all(),
            'staffadvance': Staff_Advance.objects.all(),
            'hotel_miscellaneous_expense_profile': Hotel_Cash_Miscellaneous_Expenses.objects.all(),
            'food_miscellaneous_expense_profile': Food_Cash_Miscellaneous_Expenses.objects.all(),
        }
        return render(request, "Expense_Profile.html", context)
    except Exception as e:
        logger.error(f"Unexpected error in Expense_Profile: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching expense records. Please try again later.'})


# ---------------------------------------------------------------------------
# Hotel / Food Cash Withdrawal
# ---------------------------------------------------------------------------

@login_required(login_url='Login_In')
def Hotel_Expense_Cash_Withdraw(request):
    if request.method != 'POST':
        return render(request, "Hotel_Cash_Withdraw.html")

    date_str = request.POST.get('Hotel_withdrawal_date', '')
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    time = request.POST.get('Hotel_withdrawal_time', '')
    withdrawer = request.POST.get('Hotel_withdrawal_withdrawer', '')
    if withdrawer == 'Other':
        withdrawer = request.POST.get('Hotel_withdrawal_other_person', '')

    amount = _parse_amount(request.POST.get('Hotel_withdrawal_amount', ''))
    if amount is None:
        messages.error(request, 'Please enter a valid withdrawal amount.')
        return render(request, "Hotel_Cash_Withdraw.html")
    if not time:
        messages.error(request, 'Please provide a valid time.')
        return render(request, "Hotel_Cash_Withdraw.html")

    try:
        with transaction.atomic():
            # Same "readonly is cosmetic" issue as Revenue/Shift_Handover
            # — always attribute the withdrawal to the real logged-in
            # user, never to a POSTed username field.
            user_instance = request.user
            amount_in_words = numberToWords(int(amount))

            Hotel_Cash_Withdrawal.objects.create(
                Withdrawal_Hotel_Date=date,
                Withdrawal_Hotel_Time=time,
                Withdrawal_Hotel_Username=user_instance,
                Withdrawal_Hotel_Full_Name=_full_name(user_instance),
                Withdrawal_Hotel_Withdrawer=withdrawer,
                Withdrawal_Hotel_Amount=amount,
                Withdrawal_Hotel_Amount_In_Words=amount_in_words,
            )
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Expense_Cash_Withdraw: {e}", exc_info=True)
        messages.error(request, 'An error occurred while recording the withdrawal.')
        return render(request, "Hotel_Cash_Withdraw.html")

    logger.info(f"User '{request.user.username}' recorded a hotel cash withdrawal of {amount}.")
    messages.success(request, 'Hotel cash withdrawal recorded successfully.')
    return redirect('/Expense-Profile/')


@login_required(login_url='Login_In')
def Food_Expense_Cash_Withdraw(request):
    if request.method != 'POST':
        return render(request, "Food_Cash_Withdraw.html")

    date_str = request.POST.get('Food_withdrawal_date', '')
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    time = request.POST.get('Food_withdrawal_time', '')
    withdrawer = request.POST.get('Food_withdrawal_withdrawer', '')
    if withdrawer == 'Other':
        withdrawer = request.POST.get('Food_withdrawal_other_person', '')

    amount = _parse_amount(request.POST.get('Food_withdrawal_amount', ''))
    if amount is None:
        messages.error(request, 'Please enter a valid withdrawal amount.')
        return render(request, "Food_Cash_Withdraw.html")
    if not time:
        messages.error(request, 'Please provide a valid time.')
        return render(request, "Food_Cash_Withdraw.html")

    try:
        with transaction.atomic():
            user_instance = request.user
            amount_in_words = numberToWords(int(amount))

            Food_Cash_Withdrawal.objects.create(
                Withdrawal_Food_Date=date,
                Withdrawal_Food_Time=time,
                Withdrawal_Food_Username=user_instance,
                Withdrawal_Food_Full_Name=_full_name(user_instance),
                Withdrawal_Food_Withdrawer=withdrawer,
                Withdrawal_Food_Amount=amount,
                Withdrawal_Food_Amount_In_Words=amount_in_words,
            )
    except Exception as e:
        logger.error(f"Unexpected error in Food_Expense_Cash_Withdraw: {e}", exc_info=True)
        messages.error(request, 'An error occurred while recording the withdrawal.')
        return render(request, "Food_Cash_Withdraw.html")

    logger.info(f"User '{request.user.username}' recorded a food cash withdrawal of {amount}.")
    messages.success(request, 'Food cash withdrawal recorded successfully.')
    return redirect('/Expense-Profile/')


@login_required(login_url='Login_In')
def Hotel_Expense_Cash_Delete(request, id):
    hotel_cash_profile = get_object_or_404(Hotel_Cash_Withdrawal, id=id)
    try:
        # Was: `hotel_cash_profile.Withdrawal_Hotel_Username != request.user.username`
        # — User instance compared to a plain string, always True
        # regardless of actual ownership. Same bug found and fixed
        # across Revenue's two delete views; confirmed the same way here.
        is_owner = hotel_cash_profile.Withdrawal_Hotel_Username == request.user
        if not _is_expense_admin(request.user) and not is_owner:
            messages.error(request, "You don't have permission to delete this record.")
            return redirect('/Expense-Profile/')

        if hotel_cash_profile.Withdrawal_Hotel_Username.username == "SuperAdmin" and request.user.username == "Admin":
            messages.error(request, "The SuperAdmin account's records can't be deleted.")
            return redirect('/Expense-Profile/')

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Expense-Profile/')

        with transaction.atomic():
            hotel_cash_profile.delete()

        logger.info(f"User '{request.user.username}' deleted hotel cash withdrawal id={id}.")
        messages.success(request, 'Hotel cash withdrawal deleted successfully.')
        return redirect('/Expense-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Expense_Cash_Delete: {e}", exc_info=True)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the record.'})


@login_required(login_url='Login_In')
def Food_Expense_Cash_Delete(request, id):
    food_cash_profile = get_object_or_404(Food_Cash_Withdrawal, id=id)
    try:
        is_owner = food_cash_profile.Withdrawal_Food_Username == request.user
        if not _is_expense_admin(request.user) and not is_owner:
            messages.error(request, "You don't have permission to delete this record.")
            return redirect('/Expense-Profile/')

        if food_cash_profile.Withdrawal_Food_Username.username == "SuperAdmin" and request.user.username == "Admin":
            messages.error(request, "The SuperAdmin account's records can't be deleted.")
            return redirect('/Expense-Profile/')

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Expense-Profile/')

        with transaction.atomic():
            food_cash_profile.delete()

        logger.info(f"User '{request.user.username}' deleted food cash withdrawal id={id}.")
        messages.success(request, 'Food cash withdrawal deleted successfully.')
        return redirect('/Expense-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Food_Expense_Cash_Delete: {e}", exc_info=True)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the record.'})


# ---------------------------------------------------------------------------
# Hotel / Food Miscellaneous Expense
# ---------------------------------------------------------------------------

@login_required(login_url='Login_In')
def Hotel_Cash_Miscellaneous_Expense(request):
    if request.method != 'POST':
        return render(request, "Hotel_Cash_Miscellaneous_Expense.html")

    date_str = request.POST.get('hotel_Cash_miscellaneous_expense_date', '')
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    time = request.POST.get('hotel_Cash_miscellaneous_expense_time', '')
    name = request.POST.get('hotel_Cash_miscellaneous_expense_name', '')
    instruction = request.POST.get('hotel_Cash_miscellaneous_expense_instruction', '')

    amount = _parse_amount(request.POST.get('hotel_Cash_miscellaneous_expense_amount', ''))
    if amount is None:
        messages.error(request, 'Please enter a valid expense amount.')
        return render(request, "Hotel_Cash_Miscellaneous_Expense.html")
    if not time:
        messages.error(request, 'Please provide a valid time.')
        return render(request, "Hotel_Cash_Miscellaneous_Expense.html")

    try:
        with transaction.atomic():
            user_instance = request.user
            amount_in_words = numberToWords(int(amount))

            Hotel_Cash_Miscellaneous_Expenses.objects.create(
                Miscellaneous_Expenses_Hotel_Date=date,
                Miscellaneous_Expenses_Hotel_Time=time,
                Miscellaneous_Expenses_Hotel_Username=user_instance,
                Miscellaneous_Expenses_Hotel_Full_Name=_full_name(user_instance),
                Miscellaneous_Expenses_Hotel_Expense_Name=name,
                Miscellaneous_Expenses_Hotel_Amount=amount,
                Miscellaneous_Expenses_Hotel_Amount_In_Words=amount_in_words,
                Miscellaneous_Expenses_Hotel_Instruction=instruction,
            )
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Cash_Miscellaneous_Expense: {e}", exc_info=True)
        messages.error(request, 'An error occurred while recording the expense.')
        return render(request, "Hotel_Cash_Miscellaneous_Expense.html")

    logger.info(f"User '{request.user.username}' recorded a hotel misc. expense of {amount}.")
    messages.success(request, 'Hotel miscellaneous expense recorded successfully.')
    return redirect('/Expense-Profile/')


@login_required(login_url='Login_In')
def Food_Cash_Miscellaneous_Expense(request):
    if request.method != 'POST':
        return render(request, "Food_Cash_Miscellaneous_Expense.html")

    date_str = request.POST.get('food_Cash_miscellaneous_expense_date', '')
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    time = request.POST.get('food_Cash_miscellaneous_expense_time', '')
    name = request.POST.get('food_Cash_miscellaneous_expense_name', '')
    instruction = request.POST.get('food_Cash_miscellaneous_expense_instruction', '')

    amount = _parse_amount(request.POST.get('food_Cash_miscellaneous_expense_amount', ''))
    if amount is None:
        messages.error(request, 'Please enter a valid expense amount.')
        return render(request, "Food_Cash_Miscellaneous_Expense.html")
    if not time:
        messages.error(request, 'Please provide a valid time.')
        return render(request, "Food_Cash_Miscellaneous_Expense.html")

    try:
        with transaction.atomic():
            user_instance = request.user
            amount_in_words = numberToWords(int(amount))

            Food_Cash_Miscellaneous_Expenses.objects.create(
                Miscellaneous_Expenses_Food_Date=date,
                Miscellaneous_Expenses_Food_Time=time,
                Miscellaneous_Expenses_Food_Username=user_instance,
                Miscellaneous_Expenses_Food_Full_Name=_full_name(user_instance),
                Miscellaneous_Expenses_Food_Expense_Name=name,
                Miscellaneous_Expenses_Food_Amount=amount,
                Miscellaneous_Expenses_Food_Amount_In_Words=amount_in_words,
                Miscellaneous_Expenses_Food_Instruction=instruction,
            )
    except Exception as e:
        logger.error(f"Unexpected error in Food_Cash_Miscellaneous_Expense: {e}", exc_info=True)
        messages.error(request, 'An error occurred while recording the expense.')
        return render(request, "Food_Cash_Miscellaneous_Expense.html")

    logger.info(f"User '{request.user.username}' recorded a food misc. expense of {amount}.")
    messages.success(request, 'Food miscellaneous expense recorded successfully.')
    return redirect('/Expense-Profile/')


@login_required(login_url='Login_In')
def Hotel_Cash_Miscellaneous_Expense_Delete(request, id):
    hotel_miscellaneous_expense = get_object_or_404(Hotel_Cash_Miscellaneous_Expenses, id=id)
    try:
        is_owner = hotel_miscellaneous_expense.Miscellaneous_Expenses_Hotel_Username == request.user
        if not _is_expense_admin(request.user) and not is_owner:
            messages.error(request, "You don't have permission to delete this record.")
            return redirect('/Expense-Profile/')

        if hotel_miscellaneous_expense.Miscellaneous_Expenses_Hotel_Username.username == "SuperAdmin" and request.user.username == "Admin":
            messages.error(request, "The SuperAdmin account's records can't be deleted.")
            return redirect('/Expense-Profile/')

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Expense-Profile/')

        with transaction.atomic():
            hotel_miscellaneous_expense.delete()

        logger.info(f"User '{request.user.username}' deleted hotel misc. expense id={id}.")
        messages.success(request, 'Hotel miscellaneous expense deleted successfully.')
        return redirect('/Expense-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Cash_Miscellaneous_Expense_Delete: {e}", exc_info=True)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the record.'})


@login_required(login_url='Login_In')
def Food_Cash_Miscellaneous_Expense_Delete(request, id):
    food_miscellaneous_expense = get_object_or_404(Food_Cash_Miscellaneous_Expenses, id=id)
    try:
        is_owner = food_miscellaneous_expense.Miscellaneous_Expenses_Food_Username == request.user
        if not _is_expense_admin(request.user) and not is_owner:
            messages.error(request, "You don't have permission to delete this record.")
            return redirect('/Expense-Profile/')

        if food_miscellaneous_expense.Miscellaneous_Expenses_Food_Username.username == "SuperAdmin" and request.user.username == "Admin":
            messages.error(request, "The SuperAdmin account's records can't be deleted.")
            return redirect('/Expense-Profile/')

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Expense-Profile/')

        with transaction.atomic():
            food_miscellaneous_expense.delete()

        logger.info(f"User '{request.user.username}' deleted food misc. expense id={id}.")
        messages.success(request, 'Food miscellaneous expense deleted successfully.')
        return redirect('/Expense-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Food_Cash_Miscellaneous_Expense_Delete: {e}", exc_info=True)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the record.'})


@login_required(login_url='Login_In')
def Hotel_Cash_Miscellaneous_Expense_Update(request, id):
    queryset = get_object_or_404(Hotel_Cash_Miscellaneous_Expenses, id=id)

    is_owner = queryset.Miscellaneous_Expenses_Hotel_Username.username == request.user.username
    if not _is_expense_admin(request.user) and not is_owner:
        messages.error(request, "You don't have permission to update this record.")
        return redirect('/Expense-Profile/')
    if queryset.Miscellaneous_Expenses_Hotel_Username.username == "SuperAdmin" and request.user.username == "Admin":
        messages.error(request, "The SuperAdmin account's records can't be updated.")
        return redirect('/Expense-Profile/')

    if request.method != 'POST':
        return render(request, 'Hotel_Cash_Miscellaneous_Expense_Update.html', {'hotel_cash_miscellaneous_expense_update': queryset})

    date_str = request.POST.get('hotel_Cash_miscellaneous_expense_date', '')
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    time = request.POST.get('hotel_Cash_miscellaneous_expense_time', '')
    name = request.POST.get('hotel_Cash_miscellaneous_expense_name', '')
    instruction = request.POST.get('hotel_Cash_miscellaneous_expense_instruction', '')

    amount = _parse_amount(request.POST.get('hotel_Cash_miscellaneous_expense_amount', ''))
    if amount is None:
        messages.error(request, 'Please enter a valid expense amount.')
        return render(request, 'Hotel_Cash_Miscellaneous_Expense_Update.html', {'hotel_cash_miscellaneous_expense_update': queryset})
    if not time:
        messages.error(request, 'Please provide a valid time.')
        return render(request, 'Hotel_Cash_Miscellaneous_Expense_Update.html', {'hotel_cash_miscellaneous_expense_update': queryset})

    try:
        with transaction.atomic():
            amount_in_words = numberToWords(int(amount))

            queryset.Miscellaneous_Expenses_Hotel_Date = date
            queryset.Miscellaneous_Expenses_Hotel_Time = time
            # Preserves the original behavior of reassigning ownership to
            # whoever saved the edit, except when SuperAdmin is editing —
            # but now attributes it to request.user instead of trusting a
            # readonly-but-forgeable POSTed username field (the form has
            # always submitted request.user.username here regardless, so
            # this closes an impersonation vector without changing any
            # legitimate outcome).
            if request.user.username != "SuperAdmin":
                queryset.Miscellaneous_Expenses_Hotel_Username = request.user
                queryset.Miscellaneous_Expenses_Hotel_Full_Name = _full_name(request.user)
            queryset.Miscellaneous_Expenses_Hotel_Amount_In_Words = amount_in_words
            queryset.Miscellaneous_Expenses_Hotel_Expense_Name = name
            queryset.Miscellaneous_Expenses_Hotel_Amount = amount
            queryset.Miscellaneous_Expenses_Hotel_Instruction = instruction
            queryset.save()
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Cash_Miscellaneous_Expense_Update: {e}", exc_info=True)
        messages.error(request, 'An error occurred while updating the record.')
        return render(request, 'Hotel_Cash_Miscellaneous_Expense_Update.html', {'hotel_cash_miscellaneous_expense_update': queryset})

    logger.info(f"User '{request.user.username}' updated hotel misc. expense id={id}.")
    messages.success(request, 'Hotel miscellaneous expense updated successfully.')
    return redirect('/Expense-Profile/')


@login_required(login_url='Login_In')
def Food_Cash_Miscellaneous_Expense_Update(request, id):
    queryset = get_object_or_404(Food_Cash_Miscellaneous_Expenses, id=id)

    is_owner = queryset.Miscellaneous_Expenses_Food_Username.username == request.user.username
    if not _is_expense_admin(request.user) and not is_owner:
        messages.error(request, "You don't have permission to update this record.")
        return redirect('/Expense-Profile/')
    if queryset.Miscellaneous_Expenses_Food_Username.username == "SuperAdmin" and request.user.username == "Admin":
        messages.error(request, "The SuperAdmin account's records can't be updated.")
        return redirect('/Expense-Profile/')

    if request.method != 'POST':
        return render(request, 'Food_Cash_Miscellaneous_Expense_Update.html', {'food_cash_miscellaneous_expense_update': queryset})

    date_str = request.POST.get('food_Cash_miscellaneous_expense_date', '')
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    time = request.POST.get('food_Cash_miscellaneous_expense_time', '')
    name = request.POST.get('food_Cash_miscellaneous_expense_name', '')
    instruction = request.POST.get('food_Cash_miscellaneous_expense_instruction', '')

    amount = _parse_amount(request.POST.get('food_Cash_miscellaneous_expense_amount', ''))
    if amount is None:
        messages.error(request, 'Please enter a valid expense amount.')
        return render(request, 'Food_Cash_Miscellaneous_Expense_Update.html', {'food_cash_miscellaneous_expense_update': queryset})
    if not time:
        messages.error(request, 'Please provide a valid time.')
        return render(request, 'Food_Cash_Miscellaneous_Expense_Update.html', {'food_cash_miscellaneous_expense_update': queryset})

    try:
        with transaction.atomic():
            amount_in_words = numberToWords(int(amount))

            queryset.Miscellaneous_Expenses_Food_Date = date
            queryset.Miscellaneous_Expenses_Food_Time = time
            if request.user.username != "SuperAdmin":
                queryset.Miscellaneous_Expenses_Food_Username = request.user
                queryset.Miscellaneous_Expenses_Food_Full_Name = _full_name(request.user)
            queryset.Miscellaneous_Expenses_Food_Amount_In_Words = amount_in_words
            queryset.Miscellaneous_Expenses_Food_Expense_Name = name
            queryset.Miscellaneous_Expenses_Food_Amount = amount
            queryset.Miscellaneous_Expenses_Food_Instruction = instruction
            queryset.save()
    except Exception as e:
        logger.error(f"Unexpected error in Food_Cash_Miscellaneous_Expense_Update: {e}", exc_info=True)
        messages.error(request, 'An error occurred while updating the record.')
        return render(request, 'Food_Cash_Miscellaneous_Expense_Update.html', {'food_cash_miscellaneous_expense_update': queryset})

    logger.info(f"User '{request.user.username}' updated food misc. expense id={id}.")
    messages.success(request, 'Food miscellaneous expense updated successfully.')
    return redirect('/Expense-Profile/')


# ---------------------------------------------------------------------------
# Staff Advance
# ---------------------------------------------------------------------------

@login_required(login_url='Login_In')
def Staff_Advance_Salaries(request):
    try:
        if request.method == "POST":
            date_str = request.POST.get('staff_advance__date')
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            time = request.POST.get('staff_advance__time')
            year_month = request.POST.get('staff_advance_year_month')
            staff_name_id = request.POST.get('staff_advance_name')
            instruction = request.POST.get('staff_advance_instruction')

            staff_name = get_object_or_404(User_Profile, pk=staff_name_id, is_active=True) if staff_name_id else None

            amount = _parse_amount(request.POST.get('advance_amount', ''))
            if amount is None:
                messages.error(request, 'Please enter a valid advance amount.')
                return render(request, "Staff_Advance_Salaries.html", {'user_profiles': User_Profile.objects.filter(is_active=True)})
            if not time:
                messages.error(request, 'Please provide a valid time.')
                return render(request, "Staff_Advance_Salaries.html", {'user_profiles': User_Profile.objects.filter(is_active=True)})

            with transaction.atomic():
                # Same impersonation gap as everywhere else in this app:
                # the readonly username field is cosmetic, so the record
                # is always attributed to the real logged-in user.
                user_instance = request.user
                amount_in_words = numberToWords(int(amount))

                Staff_Advance.objects.create(
                    Staff_Advance_date=date,
                    Staff_Advance_time=time,
                    Staff_Advance_username=user_instance,
                    Staff_Advance_Full_Name=_full_name(user_instance),
                    Staff_Advance_year_month=year_month,
                    Staff_Advance_name=staff_name,
                    Staff_Advance_amount=amount,
                    Staff_Advance_Amount_In_Words=amount_in_words,
                    Staff_Advance_instruction=instruction,
                )

            logger.info(f"User '{request.user.username}' recorded a staff advance of {amount} for profile id={staff_name_id}.")
            messages.success(request, 'Staff advance recorded successfully.')
            return redirect('/Expense-Profile/')

        return render(request, "Staff_Advance_Salaries.html", {'user_profiles': User_Profile.objects.filter(is_active=True)})
    except Exception as e:
        logger.error(f"Unexpected error in Staff_Advance_Salaries: {e}", exc_info=True)
        messages.error(request, 'An error occurred while recording the staff advance.')
        return render(request, "Staff_Advance_Salaries.html", {'user_profiles': User_Profile.objects.filter(is_active=True)})


@login_required(login_url='Login_In')
def Staff_Advance_Salaries_Delete(request, id):
    staffadvance = get_object_or_404(Staff_Advance, id=id)
    try:
        # Was: `staffadvance.Staff_Advance_username != request.user.username`
        # — the same User-vs-string comparison bug found across every
        # other Delete view in this app; confirmed the same way.
        is_owner = staffadvance.Staff_Advance_username == request.user
        if not _is_expense_admin(request.user) and not is_owner:
            messages.error(request, "You don't have permission to delete this record.")
            return redirect('/Expense-Profile/')

        if staffadvance.Staff_Advance_username.username == "SuperAdmin" and request.user.username == "Admin":
            messages.error(request, "The SuperAdmin account's records can't be deleted.")
            return redirect('/Expense-Profile/')

        if request.method != 'POST':
            messages.error(request, 'Invalid request.')
            return redirect('/Expense-Profile/')

        with transaction.atomic():
            staffadvance.delete()

        logger.info(f"User '{request.user.username}' deleted staff advance id={id}.")
        messages.success(request, 'Staff advance deleted successfully.')
        return redirect('/Expense-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Staff_Advance_Salaries_Delete: {e}", exc_info=True)
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the record.'})


@login_required(login_url='Login_In')
def Staff_Advance_Salaries_Update(request, id):
    queryset = get_object_or_404(Staff_Advance, id=id)

    is_owner = queryset.Staff_Advance_username.username == request.user.username
    if not _is_expense_admin(request.user) and not is_owner:
        messages.error(request, "You don't have permission to update this record.")
        return redirect('/Expense-Profile/')
    if queryset.Staff_Advance_username.username == "SuperAdmin" and request.user.username == "Admin":
        messages.error(request, "The SuperAdmin account's records can't be updated.")
        return redirect('/Expense-Profile/')

    if request.method != 'POST':
        return render(request, 'Staff_Advance_Salaries_Update.html', {
            'staff_advance_salaries_update': queryset,
            'user_profiles': User_Profile.objects.all(),
        })

    date_str = request.POST.get('staff_advance__date')
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    time = request.POST.get('staff_advance__time')
    year_month = request.POST.get('staff_advance_year_month')
    instruction = request.POST.get('staff_advance_instruction')

    amount = _parse_amount(request.POST.get('advance_amount', ''))
    error_context = {'staff_advance_salaries_update': queryset, 'user_profiles': User_Profile.objects.all()}
    if amount is None:
        messages.error(request, 'Please enter a valid advance amount.')
        return render(request, 'Staff_Advance_Salaries_Update.html', error_context)
    if not time:
        messages.error(request, 'Please provide a valid time.')
        return render(request, 'Staff_Advance_Salaries_Update.html', error_context)

    try:
        with transaction.atomic():
            amount_in_words = numberToWords(int(amount))

            queryset.Staff_Advance_date = date
            queryset.Staff_Advance_time = time
            queryset.Staff_Advance_Amount_In_Words = amount_in_words
            # Same fix as the misc-expense Update views: always the real
            # authenticated user, never a POSTed username field. Unlike
            # those two views, the original here had no SuperAdmin
            # exemption from reassignment — preserved that exact
            # (slightly inconsistent with the other two, but pre-existing)
            # behavior rather than introducing a new conditional.
            queryset.Staff_Advance_username = request.user
            queryset.Staff_Advance_Full_Name = _full_name(request.user)
            queryset.Staff_Advance_year_month = year_month
            queryset.Staff_Advance_amount = amount
            queryset.Staff_Advance_instruction = instruction
            queryset.save()
    except Exception as e:
        logger.error(f"Unexpected error in Staff_Advance_Salaries_Update: {e}", exc_info=True)
        messages.error(request, 'An error occurred while updating the record.')
        return render(request, 'Staff_Advance_Salaries_Update.html', error_context)

    logger.info(f"User '{request.user.username}' updated staff advance id={id}.")
    messages.success(request, 'Staff advance updated successfully.')
    return redirect('/Expense-Profile/')


# ---------------------------------------------------------------------------
# PDF receipts
# ---------------------------------------------------------------------------

@login_required(login_url='Login_In')
def Staff_Advance_Salaries_View(request, id):
    try:
        staff_advance_salaries_view = get_object_or_404(Staff_Advance, id=id)
        return render_to_pdf('StaffAdvanceSalariesView.html', {'staff_advance_salaries_view': staff_advance_salaries_view})
    except Exception as e:
        logger.error(f"Unexpected error in Staff_Advance_Salaries_View: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the staff advance. Please try again later.'})


@login_required(login_url='Login_In')
def Hotel_Expense_Cash_Withdraw_View(request, id):
    try:
        hotel_expense_cash_withdraw_view = get_object_or_404(Hotel_Cash_Withdrawal, id=id)
        return render_to_pdf('HotelExpenseCashWithdrawView.html', {'hotel_expense_cash_withdraw_view': hotel_expense_cash_withdraw_view})
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Expense_Cash_Withdraw_View: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the withdrawal. Please try again later.'})


@login_required(login_url='Login_In')
def Food_Expense_Cash_Withdraw_View(request, id):
    try:
        food_expense_cash_withdraw_view = get_object_or_404(Food_Cash_Withdrawal, id=id)
        return render_to_pdf('FoodExpenseCashWithdrawView.html', {'food_expense_cash_withdraw_view': food_expense_cash_withdraw_view})
    except Exception as e:
        logger.error(f"Unexpected error in Food_Expense_Cash_Withdraw_View: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the withdrawal. Please try again later.'})


@login_required(login_url='Login_In')
def Hotel_Cash_Miscellaneous_Expense_View(request, id):
    try:
        hotel_cash_miscellaneous_expense_view = get_object_or_404(Hotel_Cash_Miscellaneous_Expenses, id=id)
        return render_to_pdf('HotelCashMiscellaneousExpenseView.html', {'hotel_cash_miscellaneous_expense_view': hotel_cash_miscellaneous_expense_view})
    except Exception as e:
        logger.error(f"Unexpected error in Hotel_Cash_Miscellaneous_Expense_View: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the expense. Please try again later.'})


@login_required(login_url='Login_In')
def Food_Cash_Miscellaneous_Expense_View(request, id):
    try:
        food_cash_miscellaneous_expense_view = get_object_or_404(Food_Cash_Miscellaneous_Expenses, id=id)
        return render_to_pdf('FoodCashMiscellaneousExpenseView.html', {'food_cash_miscellaneous_expense_view': food_cash_miscellaneous_expense_view})
    except Exception as e:
        logger.error(f"Unexpected error in Food_Cash_Miscellaneous_Expense_View: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching the expense. Please try again later.'})
