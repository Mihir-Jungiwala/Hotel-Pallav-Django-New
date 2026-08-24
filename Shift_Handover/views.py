import logging
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Shift_Handover
from Dashboard.views import numberToWords
from django.db import transaction
from Reports.pdf import render_to_pdf
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

# denomination key -> (POST quantity key, model Counts field, model Total field, face value)
# 'coin' has a face value of 1 because the form doesn't collect a coin
# denomination breakdown, just a total coin value in rupees directly —
# matches Shift_Handover_Add.html's calculateAmount('coin') using
# denominationValue = 1.
DENOMINATIONS = [
    ('five_hundred', 'Shift_Handover_Five_Hundred_Counts', 'Shift_Handover_Five_Hundred_Total', Decimal('500')),
    ('two_hundred', 'Shift_Handover_Two_Hundred_Counts', 'Shift_Handover_Two_Hundred_Total', Decimal('200')),
    ('one_hundred', 'Shift_Handover_One_Hundred_Counts', 'Shift_Handover_One_Hundred_Total', Decimal('100')),
    ('fifty', 'Shift_Handover_Fifty_Counts', 'Shift_Handover_Fifty_Total', Decimal('50')),
    ('twenty', 'Shift_Handover_Twenty_Counts', 'Shift_Handover_Twenty_Total', Decimal('20')),
    ('ten', 'Shift_Handover_Ten_Counts', 'Shift_Handover_Ten_Total', Decimal('10')),
    ('five', 'Shift_Handover_Five_Counts', 'Shift_Handover_Five_Total', Decimal('5')),
    ('coin', 'Shift_Handover_Coins_Counts', 'Shift_Handover_Coins_Total', Decimal('1')),
]


def _compute_denominations(request):
    """Recomputes every denomination's total (and the grand total) from
    the submitted *quantities* server-side, instead of trusting the
    client-submitted amount/total fields directly.

    The Add/Update forms compute these client-side in JS
    (calculateAmount/calculateTotal in Shift_Handover_Add.html) purely
    for the live on-screen display — the amount/total <input>s are
    marked readonly, but readonly is cosmetic only; a raw POST (or a
    modified request from browser devtools) can submit any value for
    them completely decoupled from the quantities. For a cash-count
    reconciliation record this matters: the server is now the actual
    source of truth for the arithmetic, not just a passthrough for
    whatever numbers the client happened to send. Returns
    (model_field_values, grand_total, error_message_or_None).
    """
    values = {}
    grand_total = Decimal('0')

    for key, counts_field, total_field, face_value in DENOMINATIONS:
        raw_quantity = request.POST.get(f'{key}_quantity', '0')
        try:
            quantity = int(raw_quantity) if raw_quantity else 0
        except ValueError:
            return None, None, f"'{raw_quantity}' is not a valid quantity for {key.replace('_', ' ')} notes."
        if quantity < 0:
            return None, None, f"Quantity for {key.replace('_', ' ')} notes cannot be negative."

        line_total = face_value * quantity
        values[counts_field] = quantity
        values[total_field] = line_total
        grand_total += line_total

    return values, grand_total, None


@login_required(login_url='Login_In')
def Shift_Handover_Profile(request):
    try:
        queryset = Shift_Handover.objects.all()
        return render(request, "Shift_Handover_Profile.html", {'shift_handover_profile': queryset})
    except Exception as e:
        logger.error(f"Unexpected error in Shift_Handover_Profile: {e}", exc_info=True)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching shift handover records. Please try again later.'})


@login_required(login_url='Login_In')
def Shift_Handover_Add(request):
    if request.method != 'POST':
        return render(request, "Shift_Handover_Add.html")

    date = request.POST.get('date', '')
    time = request.POST.get('time', '')
    shift = request.POST.get('shift', '')
    message_one = request.POST.get('message_one', '')
    message_two = request.POST.get('message_two', '')
    message_three = request.POST.get('message_three', '')
    message_four = request.POST.get('message_four', '')
    message_five = request.POST.get('message_five', '')
    instruction = request.POST.get('instruction', '')

    denom_values, total, error = _compute_denominations(request)
    if error:
        messages.error(request, error)
        return render(request, "Shift_Handover_Add.html")

    try:
        with transaction.atomic():
            # The form's username field is marked readonly and pre-filled
            # with request.user.username for display, but readonly is
            # cosmetic — a raw POST could submit a different username and
            # attribute the handover to someone else. Always using the
            # actual authenticated user makes that impossible rather than
            # merely discouraged by the UI.
            user_instance = request.user
            full_name = f"{user_instance.first_name} {user_instance.last_name}".strip() or user_instance.username

            amount_as_number = int(total)
            amount_in_words = numberToWords(amount_as_number)

            Shift_Handover.objects.create(
                Shift_Handover_Date=date or None,
                Shift_Handover_Time=time or None,
                Shift_Handover_Username=user_instance,
                Shift_Handover_Full_Name=full_name,
                Shift_Handover_Shift=shift,
                Shift_Handover_message_One=message_one,
                Shift_Handover_message_Two=message_two,
                Shift_Handover_message_Three=message_three,
                Shift_Handover_message_Four=message_four,
                Shift_Handover_message_Five=message_five,
                Shift_Handover_Total=total,
                Shift_Handover_Total_Amount_In_Words=amount_in_words,
                Shift_Handover_Special_Instruction=instruction,
                **denom_values,
            )
    except Exception as e:
        # Previously: print(e) with no messages.error() at all -- a
        # failed submission (bad date, etc.) silently reloaded a blank
        # form with zero feedback.
        logger.error(f"Unexpected error in Shift_Handover_Add: {e}", exc_info=True)
        messages.error(request, 'An error occurred while creating the shift handover record. Please check the date/time and try again.')
        return render(request, "Shift_Handover_Add.html")

    logger.info(f"User '{request.user.username}' created shift handover record (total={total}).")
    messages.success(request, 'Shift handover record created successfully.')
    return redirect('/Shift-Handover-Profile/')


def _is_shift_handover_admin(user):
    return user.is_superuser or user.username == 'SuperAdmin'


@login_required(login_url='Login_In')
def Shift_Handover_Update(request, id):
    shift_handover = get_object_or_404(Shift_Handover, id=id)

    # Previously had no permission check at all beyond @login_required —
    # but the list page only ever shows the "Update" link/button to
    # request.user.username == 'SuperAdmin', so any other authenticated
    # user could still POST directly to this URL and rewrite someone
    # else's cash-count reconciliation record. Confirmed directly: a
    # plain non-admin account could set Shift_Handover_Total to an
    # arbitrary value via a raw POST. Matches the template's own
    # SuperAdmin-only intent instead of leaving it enforced only by
    # hiding a button.
    if not _is_shift_handover_admin(request.user):
        messages.error(request, "You don't have permission to update shift handover records.")
        return redirect('/Shift-Handover-Profile/')

    if request.method != 'POST':
        return render(request, "Shift_Handover_Update.html", {'Shift_Handover_Update': shift_handover})

    shift = request.POST.get('shift', '')
    message_one = request.POST.get('message_one', '')
    message_two = request.POST.get('message_two', '')
    message_three = request.POST.get('message_three', '')
    message_four = request.POST.get('message_four', '')
    message_five = request.POST.get('message_five', '')
    instruction = request.POST.get('instruction', '')

    denom_values, total, error = _compute_denominations(request)
    if error:
        messages.error(request, error)
        return render(request, "Shift_Handover_Update.html", {'Shift_Handover_Update': shift_handover})

    try:
        with transaction.atomic():
            amount_as_number = int(total)
            amount_in_words = numberToWords(amount_as_number)

            shift_handover.Shift_Handover_Shift = shift
            shift_handover.Shift_Handover_message_One = message_one
            shift_handover.Shift_Handover_message_Two = message_two
            shift_handover.Shift_Handover_message_Three = message_three
            shift_handover.Shift_Handover_message_Four = message_four
            shift_handover.Shift_Handover_message_Five = message_five
            shift_handover.Shift_Handover_Special_Instruction = instruction
            shift_handover.Shift_Handover_Total = total
            shift_handover.Shift_Handover_Total_Amount_In_Words = amount_in_words
            for field, value in denom_values.items():
                setattr(shift_handover, field, value)

            shift_handover.save()
    except Exception as e:
        logger.error(f"Unexpected error in Shift_Handover_Update: {e}", exc_info=True)
        messages.error(request, 'An error occurred while updating the shift handover record.')
        return render(request, "Shift_Handover_Update.html", {'Shift_Handover_Update': shift_handover})

    logger.info(f"User '{request.user.username}' updated shift handover record id={id} (total={total}).")
    messages.success(request, "Shift handover record updated successfully.")
    return redirect('/Shift-Handover-Profile/')


@login_required(login_url='Login_In')
def Shift_Handover_Delete(request, id):
    shift_handover = get_object_or_404(Shift_Handover, id=id)

    try:
        is_admin = request.user.username in ("SuperAdmin", "Admin")
        is_owner = shift_handover.Shift_Handover_Username == request.user

        if not is_admin and not is_owner:
            messages.error(request, "You don't have permission to delete this record.")
            return redirect('/Shift-Handover-Profile/')

        if shift_handover.Shift_Handover_Username.username == "SuperAdmin" and request.user.username == "Admin":
            messages.error(request, "The SuperAdmin account's records can't be deleted.")
            return redirect('/Shift-Handover-Profile/')

        if request.method != 'POST':
            # Previously: no branch at all for a non-POST request once
            # the permission checks passed — an authorized user hitting
            # this URL with a plain GET got "didn't return an
            # HttpResponse" (a hard 500), reproduced directly.
            messages.error(request, 'Invalid request.')
            return redirect('/Shift-Handover-Profile/')

        with transaction.atomic():
            shift_handover.delete()

        logger.info(f"User '{request.user.username}' deleted shift handover record id={id}.")
        messages.success(request, 'Shift handover entry deleted successfully.')
        return redirect('/Shift-Handover-Profile/')
    except Exception as e:
        logger.error(f"Unexpected error in Shift_Handover_Delete: {e}", exc_info=True)
        messages.error(request, 'An error occurred during deletion.')
        return render(request, 'error_page.html', {'error_message': 'An error occurred during deletion.'})


@login_required(login_url='Login_In')
def Shift_Handover_View(request, id):
    try:
        shift_handover = get_object_or_404(Shift_Handover, id=id)
        return render_to_pdf('ShiftHandoverView.html', {'shift_handover_view': shift_handover})
    except Exception as e:
        logger.error(f"Unexpected error in Shift_Handover_View: {e}", exc_info=True)
        messages.error(request, 'An error occurred while trying to fetch the shift handover details.')
        return redirect('/Shift-Handover-Profile/')
