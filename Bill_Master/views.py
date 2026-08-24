from decimal import Decimal, InvalidOperation
from datetime import datetime
from email.utils import parsedate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone
import logging
from .models import Bill_Master_ADD_Advance, Bill_Master_ADD_Bill, Company_Profile
from Company.models import Company_Profile
from django.shortcuts import get_object_or_404

@login_required(login_url='Login_In') 
def Bill_Master_Advance_Delete(request, id):
    try:
        if request.method == 'POST':  # Check if the request method is POST (form submission)
            # Retrieve the bill master record to be deleted
            bill_master = Bill_Master_ADD_Advance.objects.get(id=id)

            # Check if Hotel_Advance_Amount equals Hotel_Balance_Amount and Food_Advance_Amount equals Food_Balance_Amount
            if bill_master.Hotel_Advance_Amount == bill_master.Hotel_Balance_Amount and bill_master.Food_Advance_Amount == bill_master.Food_Balance_Amount:
                bill_master.delete()  # Delete the retrieved bill master record
                return redirect('/Bill-Master-Advance-Profile/')  # Redirect to the advance profile page after deletion
            else:
                return redirect('/Bill-Master-Advance-Profile/')  # Redirect to the same page if conditions are not met

    except Bill_Master_ADD_Advance.DoesNotExist:
        return render(request, 'error_page.html', {'error_message': 'User Profile not found.'})
    except Exception as e:
        print(e)  # Print any error that occurs for debugging purposes
        return render(request, 'error_page.html', {'error_message': 'An error occurred while deleting the user profile.'})

@login_required(login_url='Login_In') 
def Bill_Master_Advance_Profile(request):
    try:
        # Retrieve all bill master records from the database
        queryset = Bill_Master_ADD_Advance.objects.all()
        
        context = {'advance_profiles': queryset}  # Create context containing the retrieved bill master records
        return render(request, "Bill_Master_Advance_Profile.html", context)  # Render the profile template with context data
    except Exception as e:
        print(e)  # Print any error that occurs for debugging purposes
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})

logger = logging.getLogger(__name__)
@login_required(login_url='Login_In')
def Bill_Master_Advance_Add(request):
    try:
        # Fetch all company details from the Company_Profile model for rendering in the form
        companies = Company_Profile.objects.all()

        if request.method == 'POST':  # Check if the request method is POST (form submission)
            try:
                with transaction.atomic():  # Ensure atomic transaction
                    # Retrieve form data
                    advance_Receipt_Number = request.POST.get('advance_Receipt_Number', '')
                    advance_Guest_Name = request.POST.get('advance_Guest_Name', '')
                    advance_Mobile_Number = request.POST.get('advance_Mobile_Number', '')
                    advance_Payment_Date_str = request.POST.get('advance_Payment_Date', '') 

                    # Parse the payment date if provided
                    if advance_Payment_Date_str:
                        advance_Payment_Date = datetime.strptime(advance_Payment_Date_str, '%Y-%m-%d').date()
                    else:
                        advance_Payment_Date = None

                    hotel_advance_amount = Decimal(request.POST.get('hotel_advance_amount', '0')) if request.POST.get('hotel_advance_amount', '') else Decimal('0')
                    hotel_advance_mod = request.POST.get('hotel_advance_mod', '')
                    food_advance_amount = Decimal(request.POST.get('food_advance_amount', '0')) if request.POST.get('food_advance_amount', '') else Decimal('0')
                    food_advance_mod = request.POST.get('food_advance_mod', '')
                    total =Decimal(request.POST.get('total', '0')) if request.POST.get('total', '') else Decimal('0')
                    advance_Reference_Name = request.POST.get('advance_Reference_Name', '')
                    advance_Reference_Mobile_Number = request.POST.get('advance_Reference_Mobile_Number', '')
                    advance_Instruction = request.POST.get('advance_Instruction', '')
                    select_company_id = request.POST.get('select_company', None)
                
                    # Check if a company was selected
                    select_company = None
                    if select_company_id:
                        try:
                            select_company = Company_Profile.objects.get(pk=select_company_id)
                        except Company_Profile.DoesNotExist:
                            logger.error(f"Company with id {select_company_id} does not exist")
                            return render(request, "Bill_Master_Advance_Add.html", {"companies": companies, "error": "Selected company does not exist."})

                    # Get the current year
                    current_year = datetime.now().year

                    # Format the advance receipt number
                    formatted_advance_Receipt_Number = f"{current_year} / {advance_Receipt_Number}"

                    # Create a new Bill_Master_ADD_Advance object with the provided data
                    Bill_Master_ADD_Advance.objects.create(
                        Advance_Receipt_Number=formatted_advance_Receipt_Number,
                        Advance_Guest_Name=advance_Guest_Name,
                        Advance_Mobile_Number=advance_Mobile_Number,
                        Advance_Bill_Company=select_company,
                        Advance_Payment_Date=advance_Payment_Date,
                        Hotel_Advance_Amount=hotel_advance_amount,
                        Hotel_Advance_MOD=hotel_advance_mod,
                        Food_Advance_Amount=food_advance_amount,
                        Food_Advance_MOD=food_advance_mod,
                        Total=total,
                        Hotel_Balance_Amount=hotel_advance_amount,
                        Food_Balance_Amount=food_advance_amount,
                        Advance_Reference_Name=advance_Reference_Name,
                        Advance_Reference_Mobile_Number=advance_Reference_Mobile_Number,
                        Advance_Instruction=advance_Instruction,
                    )

                    # Redirect to the advance profile page after adding
                    return redirect('/Bill-Master-Advance-Profile/')
            except Exception as e:
                logger.error(f"Error adding Bill Master Advance: {e}")  # Log any error that occurs for debugging purposes

        # Render the form template for adding a new bill master record
        return render(request, "Bill_Master_Advance_Add.html", {"companies": companies})
    except Exception as e:
        logger.error(f"Error fetching company profiles: {e}")
        return render(request, "Bill_Master_Advance_Add.html", {"error": "Error fetching company profiles."})

@login_required(login_url='Login_In')
def Bill_Master_Advance_Update(request, id):
    context = {}

    try:
        # Fetch all company details from the Company_Profile model for rendering in the form
        companies = Company_Profile.objects.all()
        # Retrieve the bill master record to be updated
        queryset = Bill_Master_ADD_Advance.objects.get(id=id)
        
        # Check if Hotel_Advance_Amount equals Hotel_Balance_Amount and Food_Advance_Amount equals Food_Balance_Amount
        if queryset.Hotel_Advance_Amount != queryset.Hotel_Balance_Amount or queryset.Food_Advance_Amount != queryset.Food_Balance_Amount:
            messages.warning(request, 'Cannot update the record. Advance amount does not match balance amount.')
            return redirect('/Bill-Master-Advance-Profile/')
        
        # Check if a refund has been done
        if queryset.Refund_Payment_Date:
            messages.warning(request, 'Cannot update the record. Refund has already been done.')
            return redirect('/Bill-Master-Advance-Profile/')
        
        if request.method == 'POST':
            # Retrieve form data
            advance_Guest_Name = request.POST.get('advance_Guest_Name', '')
            advance_Mobile_Number = request.POST.get('advance_Mobile_Number', '')
            advance_Payment_Date_str = request.POST.get('advance_Payment_Date', '')
            hotel_advance_amount = Decimal(request.POST.get('hotel_advance_amount', '0')) if request.POST.get('hotel_advance_amount', '') else Decimal('0')
            hotel_advance_mod = request.POST.get('hotel_advance_mod', '')
            food_advance_amount = Decimal(request.POST.get('food_advance_amount', '0')) if request.POST.get('food_advance_amount', '') else Decimal('0')
            food_advance_mod = request.POST.get('food_advance_mod', '')
            total = Decimal(request.POST.get('total', '0'))
            advance_Reference_Name = request.POST.get('advance_Reference_Name', '')
            advance_Reference_Mobile_Number = request.POST.get('advance_Reference_Mobile_Number', '')
            advance_Instruction = request.POST.get('advance_Instruction', '')

            # Parse the payment date if provided
            advance_Payment_Date = None
            if advance_Payment_Date_str:
                advance_Payment_Date = timezone.datetime.strptime(advance_Payment_Date_str, '%Y-%m-%d').date()
                
            select_company_id = request.POST.get('select_company', None)
            
            # Check if a company was selected
            select_company = None
            if select_company_id:
                try:
                    select_company = Company_Profile.objects.get(pk=select_company_id)
                except Company_Profile.DoesNotExist:
                    messages.error(request, f"Company with id {select_company_id} does not exist.")
                    return redirect('/Bill-Master-Advance-Profile/')

            # Update the retrieved bill master record with the new data
            queryset.Advance_Guest_Name = advance_Guest_Name
            queryset.Advance_Mobile_Number = advance_Mobile_Number
            queryset.Advance_Payment_Date = advance_Payment_Date
            queryset.Hotel_Advance_Amount = hotel_advance_amount
            queryset.Hotel_Advance_MOD = hotel_advance_mod
            queryset.Food_Advance_Amount = food_advance_amount
            queryset.Food_Advance_MOD = food_advance_mod
            queryset.Hotel_Balance_Amount = hotel_advance_amount
            queryset.Food_Balance_Amount = food_advance_amount
            queryset.Total = total
            queryset.Advance_Reference_Name = advance_Reference_Name
            queryset.Advance_Reference_Mobile_Number = advance_Reference_Mobile_Number
            queryset.Advance_Instruction = advance_Instruction
            queryset.Advance_Bill_Company = select_company

            # Save the updated bill master record
            queryset.save()
            
            # Display success message
            messages.success(request, 'Bill master record updated successfully.')
            
            # Redirect to the bill master profile page
            return redirect('/Bill-Master-Advance-Profile/')
        
        context['bill_master'] = queryset
        context['companies'] = companies
    
    except Bill_Master_ADD_Advance.DoesNotExist:
        # Handle case where the bill master record does not exist
        messages.error(request, 'Bill master record not found.')
        return redirect('/Bill-Master-Advance-Profile/')
    
    except ValueError:
        # Handle invalid values
        messages.error(request, 'Invalid input values.')
    
    except Exception as e:
        # Handle other exceptions
        messages.error(request, f'An error occurred while updating the bill master record: {str(e)}')
    
    # Render the update form template with the bill master data
    return render(request, "Bill_Master_Advance_Update.html", context)

@login_required(login_url='Login_In')
def Bill_Master_Advance_Refund(request, id):
    try:
        # Retrieve the bill master record
        bill_master = Bill_Master_ADD_Advance.objects.get(id=id)

        # Check if refund details are already present
        if bill_master.Refund_Payment_Date is not None:
            # If refund details are present, redirect to the bill master profile page
            return redirect('/Bill-Master-Advance-Profile/')

        if request.method == 'POST':
            # Retrieve form data
            refund_payment_date_str = request.POST.get('refund_Payment_Date', '')
            hotel_refund_amount_str = request.POST.get('hotel_refund_amount', '')
            refund_hotel_mod = request.POST.get('refund_hotel_mod', '')
            food_refund_amount_str = request.POST.get('food_refund_amount', '')
            refund_food_mod = request.POST.get('refund_food_mod', '')
            refund_guest_name = request.POST.get('refund_guest_name', '')
            refund_mobile_number = request.POST.get('refund_Mobile_Number', '')
            refund_instruction = request.POST.get('refund_Instruction', '')
            refund_total_amount_str = request.POST.get('refund_total_amount', '')

            # Parse the payment date if provided
            if refund_payment_date_str:
                refund_payment_date = datetime.strptime(refund_payment_date_str, '%Y-%m-%d').date()
            else:
                refund_payment_date = None

            # Convert refund amounts to Decimal
            hotel_refund_amount = Decimal(hotel_refund_amount_str) if hotel_refund_amount_str else Decimal(0)
            food_refund_amount = Decimal(food_refund_amount_str) if food_refund_amount_str else Decimal(0)
            refund_total_amount = Decimal(refund_total_amount_str) if refund_total_amount_str else Decimal(0)
            # Check if refund amount exceeds advance amount
            if hotel_refund_amount > bill_master.Hotel_Advance_Amount or food_refund_amount > bill_master.Food_Advance_Amount:
                # If refund amount exceeds advance amount, redirect back to the same page
                messages.error(request, 'Refund amount cannot exceed advance amount.')
                return redirect(request.path_info)

            # Calculate balance amount
            hotel_balance_amount = bill_master.Hotel_Balance_Amount - hotel_refund_amount
            food_balance_amount = bill_master.Food_Balance_Amount - food_refund_amount
            

            # Update the existing bill master record with the new refund details
            bill_master.Refund_Payment_Date = refund_payment_date
            bill_master.Hotel_Refund_Advance_Amount = hotel_refund_amount
            bill_master.Food_Refund_Advance_Amount = food_refund_amount
            bill_master.Hotel_Refund_MOD = refund_hotel_mod
            bill_master.Food_Refund_MOD = refund_food_mod
            bill_master.Refund_Guest_Name = refund_guest_name
            bill_master.Refund_Mobile_Number = refund_mobile_number
            bill_master.Refund_Instruction = refund_instruction
            bill_master.Total= refund_total_amount


            # Update balance amount based on refund amount
            bill_master.Hotel_Balance_Amount = hotel_balance_amount
            bill_master.Food_Balance_Amount = food_balance_amount

            # Save the updated bill master record
            bill_master.save()

            # Display success message
            messages.success(request, 'Refund details added successfully.')

            # Redirect to the bill master profile page
            return redirect('/Bill-Master-Advance-Profile/')

    except Bill_Master_ADD_Advance.DoesNotExist:
        # Handle case where the bill master record does not exist
        return render(request, 'error_page.html', {'error_message': 'Bill master record not found.'})

    except Exception as e:
        # Handle other exceptions
        print(e)  # Print any error that occurs for debugging purposes
        messages.error(request, 'An error occurred while adding refund details.')

    # Render the template with the bill master data
    return render(request, "Bill_Master_Advance_Refund.html", {'bill_master': bill_master})



@login_required(login_url='Login_In')
def Bill_Master_Advance_Refund_Delete(request, id):
    try:
        bill_master = get_object_or_404(Bill_Master_ADD_Advance, id=id)

        if request.method == 'POST':
            # Check if refund details are present
            if bill_master.Refund_Payment_Date is not None:
                # Capture current balance amounts
                original_hotel_balance = bill_master.Hotel_Balance_Amount
                original_food_balance = bill_master.Food_Balance_Amount

                # Update balance amounts to include refunded amounts
                bill_master.Hotel_Balance_Amount = original_hotel_balance + bill_master.Hotel_Refund_Advance_Amount
                bill_master.Food_Balance_Amount = original_food_balance + bill_master.Food_Refund_Advance_Amount
                bill_master.Total = bill_master.Hotel_Balance_Amount + bill_master.Food_Balance_Amount

                # Clear the refund details
                bill_master.Refund_Payment_Date = None
                bill_master.Hotel_Refund_Advance_Amount = None
                bill_master.Food_Refund_Advance_Amount = None
                bill_master.Hotel_Refund_MOD = ''
                bill_master.Food_Refund_MOD = ''
                bill_master.Refund_Guest_Name = ''
                bill_master.Refund_Mobile_Number = ''
                bill_master.Refund_Instruction = ''

                # Save the updated bill master record
                bill_master.save()

                # Display success message
                messages.success(request, 'Refund details deleted successfully.')

            else:
                # Display an error message if refund details are not present
                messages.error(request, 'No refund details to delete.')

            # Redirect to the bill master profile page
            return redirect('/Bill-Master-Advance-Profile/')  # Replace with your desired URL

    except Bill_Master_ADD_Advance.DoesNotExist:
        # Handle case where the bill master record does not exist
        return render(request, 'error_page.html', {'error_message': 'Bill master record not found.'})

    except Exception as e:
        # Log and handle other exceptions
        messages.error(request, 'An error occurred while deleting the refund details.')
        logger.error(f'Error deleting refund details: {e}')

    # Redirect to the bill master profile page in case of errors
    return redirect('/Bill-Master-Advance-Profile/')  # Replace with your desired URL

@login_required(login_url='Login_In') 
def Bill_Master_Bill_Profile(request):
    try:
        # Retrieve all bill master records from the database
        queryset = Bill_Master_ADD_Bill.objects.all()
        context = {'bill_profiles': queryset}  # Create context containing the retrieved bill master records
        return render(request, "Bill_Master_Bill_Profile.html", context)  # Render the profile template with context data
    except Exception as e:
        print(e)  # Print any error that occurs for debugging purposes
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})

















@login_required(login_url='Login_In')
def Bill_Master_Bill_Delete(request, advance_id):
    try:
        if request.method == 'POST':
            # Retrieve the bill master record to be deleted
            bill_delete = get_object_or_404(Bill_Master_ADD_Bill, id=advance_id)
              # Check if refund details are already present
            if bill_delete.Bill_Master_Debit_Bill_Date is not None:
                # If refund details are present, redirect to the bill master profile page
                return redirect('/Bill-Master-Bill-Profile/')
            
            # Retrieve the advance delete hotel and food amounts directly from the bill record
            hotel_advance_delete_amount = Decimal(bill_delete.Bill_Master_Advance_Delete_Hotel_Amount)
            food_advance_delete_amount = Decimal(bill_delete.Bill_Master_Advance_Delete_Food_Amount)

            # Check if the deleted bill record is associated with an advance
            if bill_delete.Bill_Master_Advance_Receipt_Number:
                advance_record = Bill_Master_ADD_Advance.objects.filter(Advance_Receipt_Number=bill_delete.Bill_Master_Advance_Receipt_Number).first()

                if advance_record:
                    # Calculate the new hotel and food balance amounts for the advance record
                    new_hotel_balance = hotel_advance_delete_amount 
                    new_food_balance = food_advance_delete_amount 

                    # Update the balance amounts in the advance record  
                    advance_record.Hotel_Balance_Amount = new_hotel_balance
                    advance_record.Food_Balance_Amount = new_food_balance
                    advance_record.Total = new_hotel_balance + new_food_balance
                    advance_record.save()

            # Delete the bill record
            bill_delete.delete()

            # Redirect to the bill profile page
            return redirect('/Bill-Master-Bill-Profile/')

    except Bill_Master_ADD_Bill.DoesNotExist:
        # Log an error and return an error page if the bill record does not exist
        logging.error(f"Bill record with id {advance_id} not found.")
        return render(request, 'error_page.html', {'error_message': f"Bill record with id {advance_id} not found."})

    except Exception as e:
        # Log any other exceptions and return an error page
        logging.error(f"Error deleting bill record with id {advance_id}: {e}")
        return render(request, 'error_page.html', {'error_message': f"An error occurred while deleting the bill record with id {advance_id}."})










logger = logging.getLogger(__name__)

@login_required(login_url='Login_In')
def Bill_Master_Bill_Add(request, advance_id=None):
    try:
        advance_records = Bill_Master_ADD_Advance.objects.all()
        companies = Company_Profile.objects.all()

        if request.method == 'POST':
            with transaction.atomic():  # Start a transaction block
                advance_receipt_number = request.POST.get('advance_receipt_number', '')
                paid_by = request.POST.get('paid_by', '')
                company_name = request.POST.get('company_name', '')
                advance_date = request.POST.get('advance_date', '')
                hotel_advance_amount = Decimal(request.POST.get('hotel_advance_amount', '')) if request.POST.get('hotel_advance_amount', '') else Decimal('0')
                food_advance_amount = Decimal(request.POST.get('food_advance_amount', '')) if request.POST.get('food_advance_amount', '') else Decimal('0')
                bill_Number = request.POST.get('bill_Number', '')
                bill_date_str = request.POST.get('bill_date', '')

                # Handle bill date
                bill_date = timezone.datetime.strptime(bill_date_str, '%Y-%m-%d').date() if bill_date_str else None

                bill_master_Guest_Name = request.POST.get('bill_master_Guest_Name', '')
                bill_master_Mobile_Number = request.POST.get('bill_master_Mobile_Number', '')
                select_company_id = request.POST.get('select_company', None)

                # Check selected company
                select_company = None
                if select_company_id:
                    try:
                        select_company = Company_Profile.objects.get(pk=select_company_id)
                    except Company_Profile.DoesNotExist:
                        logger.error(f"Company with id {select_company_id} does not exist")
                        return render(request, "Bill_Master_Bill_Add.html", {"companies": companies, "error": "Selected company does not exist."})

                Plan = request.POST.get('Plan', '')
                bill_master_hotel_amount = Decimal(request.POST.get('bill_master_hotel_amount', '')) if request.POST.get('bill_master_hotel_amount', '') else Decimal('0')
                bill_master_hotel_plan_amount = Decimal(request.POST.get('bill_master_hotel_plan_amount', '')) if request.POST.get('bill_master_hotel_plan_amount', '') else Decimal('0')
                bill_master_hotel_laundry_amount = Decimal(request.POST.get('bill_master_hotel_laundry_amount', '')) if request.POST.get('bill_master_hotel_laundry_amount', '') else Decimal('0')
                bill_master_hotel_gst = Decimal(request.POST.get('bill_master_hotel_gst', '')) if request.POST.get('bill_master_hotel_gst', '') else Decimal('0')
                bill_master_hotel_mod = request.POST.get('bill_master_hotel_mod', '')
                bill_master_food_amount = Decimal(request.POST.get('bill_master_food_amount', '')) if request.POST.get('bill_master_food_amount', '') else Decimal('0')
                bill_master_food_plan_amount = Decimal(request.POST.get('bill_master_food_plan_amount', '')) if request.POST.get('bill_master_food_plan_amount', '') else Decimal('0')
                bill_master_food_laundry_amount = Decimal(request.POST.get('bill_master_food_laundry_amount', '')) if request.POST.get('bill_master_food_laundry_amount', '') else Decimal('0')
                bill_master_food_gst = Decimal(request.POST.get('bill_master_food_gst', '')) if request.POST.get('bill_master_food_gst', '') else Decimal('0')
                bill_master_food_mod = request.POST.get('bill_master_food_mod', '')
                bill_master_hotel_total_amount = Decimal(request.POST.get('bill_master_hotel_total_amount', '')) if request.POST.get('bill_master_hotel_total_amount', '') else Decimal('0')
                bill_master_food_total_amount = Decimal(request.POST.get('bill_master_food_total_amount', '')) if request.POST.get('bill_master_food_total_amount', '') else Decimal('0')
                bill_master_name = request.POST.get('bill_master_name', '')
                bill_master_Number = request.POST.get('bill_master_Number', '')
                bill_master_instruction = request.POST.get('bill_master_instruction', '')
                upload_invoice_PDF = request.FILES.get('upload_invoice_PDF', '')

                # Format the bill number
                current_year = datetime.now().year
                formatted_bill_Number = f"{current_year} / {bill_Number}"

                # Calculate advance hotel balance amount
                if hotel_advance_amount > abs(bill_master_hotel_total_amount):
                    advance_hotel_balance_amount = hotel_advance_amount - abs(bill_master_hotel_total_amount)
                else:
                    advance_hotel_balance_amount = bill_master_hotel_total_amount - hotel_advance_amount


                # Calculate advance hotel balance amount
                if food_advance_amount > abs(bill_master_food_total_amount):
                    advance_food_balance_amount = food_advance_amount - abs(bill_master_hotel_total_amount)
                else:
                    advance_food_balance_amount = bill_master_food_total_amount - food_advance_amount


                            # Compute Bill_Master_Advance_Delete_Hotel_Amount before calling create()
                if bill_master_hotel_total_amount < 0:
                    Bill_Master_Advance_Delete_Hotel_Amount = advance_hotel_balance_amount + abs(bill_master_hotel_total_amount)
                else:
                    Bill_Master_Advance_Delete_Hotel_Amount = bill_master_hotel_total_amount - advance_hotel_balance_amount
                
                             # Compute Bill_Master_Advance_Delete_Hotel_Amount before calling create()
                if bill_master_food_total_amount < 0:
                    Bill_Master_Advance_Delete_Food_Amount = advance_food_balance_amount + abs(bill_master_food_total_amount)
                else:
                    Bill_Master_Advance_Delete_Food_Amount = bill_master_food_total_amount - advance_food_balance_amount


                # Create Bill_Master_ADD_Bill object
                Bill_Master_ADD_Bill.objects.create(
                    Bill_Master_Advance_Receipt_Number=advance_receipt_number,
                    Bill_Master_Advance_Guest_Name=paid_by,
                    Bill_Master_Advance_Company=company_name,
                    Bill_Master_Advance_Date=advance_date,
                    Bill_Master_Hotel_Advance_Amounts=hotel_advance_amount,
                    Bill_Master_Food_Advance_Amounts=food_advance_amount,
                    Bill_Master_Bill_Number=formatted_bill_Number,
                    Bill_Master_Bill_Company=select_company,
                    Bill_Master_Bill_Date=bill_date,
                    Bill_Master_Guest_Name=bill_master_Guest_Name,
                    Bill_Master_Mobile_Number=bill_master_Mobile_Number,
                    Bill_Master_Hotel_Plan=Plan,
                    Bill_Master_Hotel_Amount=bill_master_hotel_amount,
                    Bill_Master_Hotel_Plan_Amount=bill_master_hotel_plan_amount,
                    Bill_Master_Hotel_Laundry_Amount=bill_master_hotel_laundry_amount,
                    Bill_Master_Hotel_GST=bill_master_hotel_gst,
                    Bill_Master_Hotel_Mode_Of_Payment=bill_master_hotel_mod,
                    Bill_Master_Food_Amount=bill_master_food_amount,
                    Bill_Master_Food_Plan_Amount=bill_master_food_plan_amount,
                    Bill_Master_Food_Laundry_Amount=bill_master_food_laundry_amount,
                    Bill_Master_Food_GST=bill_master_food_gst,
                    Bill_Master_Food_Mode_Of_Payment=bill_master_food_mod,
                    Bill_Master_Total_Hotel_Amount=bill_master_hotel_total_amount,
                    Bill_Master_Total_Food_Amount=bill_master_food_total_amount,
                    Bill_Master_Reference_Name=bill_master_name,
                    Bill_Master_Reference_Mobile_Number=bill_master_Number,
                    Bill_Master_Instruction=bill_master_instruction,
                    Bill_Master_Debit_BIll_PDF=upload_invoice_PDF,
                    Bill_Master_Balance_Hotel_Amount=bill_master_hotel_total_amount if bill_master_hotel_mod == 'Debit' else 0,
                    Bill_Master_Balance_Food_Amount=bill_master_food_total_amount if bill_master_food_mod == 'Debit' else 0,
                    Bill_Master_Advance_Hotel_Amount=advance_hotel_balance_amount,
                    Bill_Master_Advance_Food_Amount=advance_food_balance_amount,

                    Bill_Master_Advance_Delete_Hotel_Amount=Bill_Master_Advance_Delete_Hotel_Amount,
                    Bill_Master_Advance_Delete_Food_Amount=Bill_Master_Advance_Delete_Food_Amount,  # Pass computed value
                        # Pass computed value
                )


                # Handle advance record
                if advance_receipt_number:
                    try:
                        advance_record = Bill_Master_ADD_Advance.objects.get(Advance_Receipt_Number=advance_receipt_number)
                    except Bill_Master_ADD_Advance.DoesNotExist:
                        logger.error(f"Advance record with receipt number {advance_receipt_number} does not exist")
                        return render(request, "Bill_Master_Bill_Add.html", {"advance_records": advance_records, "companies": companies, "error": "Advance record does not exist."})
                else:
                    advance_record = None

                if advance_record:
                    advance_record.Hotel_Balance_Amount = Decimal('0') if bill_master_hotel_total_amount >= 0 else abs(bill_master_hotel_total_amount)
                    advance_record.Food_Balance_Amount = Decimal('0') if bill_master_food_total_amount >= 0 else abs(bill_master_food_total_amount)
                    advance_record.Total = advance_record.Hotel_Balance_Amount + advance_record.Food_Balance_Amount
                    advance_record.save()

                return redirect('/Bill-Master-Bill-Profile/')  # Redirect if successful

        # Handle advance ID
        selected_advance_record = Bill_Master_ADD_Advance.objects.get(id=advance_id) if advance_id else None

        return render(request, "Bill_Master_Bill_Add.html", {"advance_records": advance_records, "companies": companies, "selected_advance_record": selected_advance_record})

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return render(request, "error_page.html", {"error_message": "An unexpected error occurred."})

logger = logging.getLogger(__name__)
@login_required(login_url='Login_In')
def Bill_Master_Bill_Update(request, id):
    try:
        
        # Retrieve the bill master record to be updated
        queryset = get_object_or_404(Bill_Master_ADD_Bill, id=id)

         # Check if refund details are already present
        if queryset.Bill_Master_Debit_Bill_Date is not None:
            # If refund details are present, redirect to the bill master profile page
            return redirect('/Bill-Master-Bill-Profile/')

        # Initialize the context dictionary
        context = {
            'bill_master_bill_update': queryset,
            'companies': Company_Profile.objects.all()
        }

        if request.method == 'POST':
            select_company_id = request.POST.get('select_company', None)

            # Fetch the selected company if provided
            select_company = None
            if select_company_id:
                try:
                    select_company = Company_Profile.objects.get(pk=select_company_id)
                except Company_Profile.DoesNotExist:
                    # Handle the case where the company is not found
                    messages.error(request, "Company not found.")
                    return redirect("/Bill-Master-Bill-Profile/")

            # Parse bill date
            bill_date_str = request.POST.get('bill_date', '')
            bill_date = datetime.strptime(bill_date_str, '%Y-%m-%d').date() if bill_date_str else None

            # Extract the remaining form data
            bill_master_Guest_Name = request.POST.get('bill_master_Guest_Name', '')
            bill_master_Mobile_Number = request.POST.get('bill_master_Mobile_Number', '')
            Plan = request.POST.get('Plan', '')

            bill_master_hotel_amount = Decimal(request.POST.get('bill_master_hotel_amount', '')) if request.POST.get('bill_master_hotel_amount', '') else Decimal('0')
            bill_master_hotel_plan_amount = Decimal(request.POST.get('bill_master_hotel_plan_amount', '')) if request.POST.get('bill_master_hotel_plan_amount', '') else Decimal('0')
            bill_master_hotel_laundry_amount = Decimal(request.POST.get('bill_master_hotel_laundry_amount', '')) if request.POST.get('bill_master_hotel_laundry_amount', '') else Decimal('0')
            bill_master_hotel_gst = Decimal(request.POST.get('bill_master_hotel_gst', '')) if request.POST.get('bill_master_hotel_gst', '') else Decimal('0')
            bill_master_hotel_mod = request.POST.get('bill_master_hotel_mod', '')

            bill_master_food_amount = Decimal(request.POST.get('bill_master_food_amount', '')) if request.POST.get('bill_master_food_amount', '') else Decimal('0')
            bill_master_food_plan_amount = Decimal(request.POST.get('bill_master_food_plan_amount', '')) if request.POST.get('bill_master_food_plan_amount', '') else Decimal('0')
            bill_master_food_laundry_amount = Decimal(request.POST.get('bill_master_food_laundry_amount', '')) if request.POST.get('bill_master_food_laundry_amount', '') else Decimal('0')
            bill_master_food_gst = Decimal(request.POST.get('bill_master_food_gst', '')) if request.POST.get('bill_master_food_gst', '') else Decimal('0')
            bill_master_food_mod = request.POST.get('bill_master_food_mod', '')
            
            bill_master_hotel_total_amount = Decimal(request.POST.get('bill_master_hotel_total_amount', '')) if request.POST.get('bill_master_hotel_total_amount', '') else Decimal('0')
            bill_master_food_total_amount = Decimal(request.POST.get('bill_master_food_total_amount', '')) if request.POST.get('bill_master_food_total_amount', '') else Decimal('0')

            bill_master_name = request.POST.get('bill_master_name', '')
            bill_master_Number = request.POST.get('bill_master_Number', '')
            bill_master_instruction = request.POST.get('bill_master_instruction', '')
            upload_invoice_PDF = request.FILES.get('upload_invoice_PDF', None)

            # Update the queryset fields
            queryset.Bill_Master_Bill_Company = select_company
            queryset.Bill_Master_Bill_Date = bill_date
            queryset.Bill_Master_Guest_Name = bill_master_Guest_Name
            queryset.Bill_Master_Mobile_Number = bill_master_Mobile_Number
            queryset.Bill_Master_Hotel_Plan = Plan
            queryset.Bill_Master_Hotel_Amount = bill_master_hotel_amount
            queryset.Bill_Master_Hotel_Plan_Amount = bill_master_hotel_plan_amount
            queryset.Bill_Master_Hotel_Laundry_Amount = bill_master_hotel_laundry_amount
            queryset.Bill_Master_Hotel_GST = bill_master_hotel_gst
            queryset.Bill_Master_Hotel_Mode_Of_Payment = bill_master_hotel_mod
            queryset.Bill_Master_Food_Amount = bill_master_food_amount
            queryset.Bill_Master_Food_Plan_Amount = bill_master_food_plan_amount
            queryset.Bill_Master_Food_Laundry_Amount = bill_master_food_laundry_amount
            queryset.Bill_Master_Food_GST = bill_master_food_gst
            queryset.Bill_Master_Food_Mode_Of_Payment = bill_master_food_mod
            queryset.Bill_Master_Total_Hotel_Amount = bill_master_hotel_total_amount
            queryset.Bill_Master_Total_Food_Amount = bill_master_food_total_amount

            queryset.Bill_Master_Balance_Hotel_Amount = bill_master_hotel_total_amount if bill_master_hotel_mod == 'Debit' else 0


            queryset.Bill_Master_Balance_Food_Amount = bill_master_food_total_amount if bill_master_hotel_mod == 'Debit' else 0

            queryset.Bill_Master_Reference_Name = bill_master_name
            queryset.Bill_Master_Reference_Mobile_Number = bill_master_Number
            queryset.Bill_Master_Instruction = bill_master_instruction

            if upload_invoice_PDF:
                queryset.Bill_Master_Debit_BIll_PDF = upload_invoice_PDF

            # Save the queryset
            queryset.save()

            messages.success(request, "Bill updated successfully.")
            return redirect('/Bill-Master-Bill-Profile/')

        # If not POST request, render the form template with the context data
        return render(request, "Bill_Master_Bill_Add_Update.html", context)

    except Bill_Master_ADD_Bill.DoesNotExist:
        # Handle the case where the bill master record does not exist
        messages.error(request, 'Bill master record not found.')
        return redirect('/Bill-Master-Bill-Profile/')

    except Exception as e:
        # Log any exception that may occur
        logger.error(f"An error occurred: {str(e)}")
        # Optionally, you can return an error response or render an error page
        return render(request, "error_page.html", {"error_message": "An unexpected error occurred."})

@login_required(login_url='Login_In')
def Bill_Master_Debit_Bill_Profile(request):
    try:
        # Filter the queryset to only include bills with a mode of payment set to debit for either food or hotel
        queryset = Bill_Master_ADD_Bill.objects.filter(
            Bill_Master_Food_Mode_Of_Payment__iexact='debit',
        ) | Bill_Master_ADD_Bill.objects.filter(
            Bill_Master_Hotel_Mode_Of_Payment__iexact='debit',
        )

        # Prepare the context dictionary with the filtered queryset
        context = {
            'debit_bill_profiles': queryset
        }

        # Render the profile template with the context data
        return render(request, "Bill_Master_Debit_Bill_Profile.html", context)

    except Exception as e:
        # Print the exception and render an error page if an exception occurs
        print(e)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})












@login_required(login_url='Login_In')
def Bill_Master_Debit_Bill_Add(request, id):
    try:
        queryset = get_object_or_404(Bill_Master_ADD_Bill, id=id)
        companies = Company_Profile.objects.all()

        if queryset.Bill_Master_Debit_Bill_Date is not None:
            messages.warning(request, 'A debit bill has already been generated. If you need to make changes, please delete the existing bill and re-enter the details.')
            return redirect('/Bill-Master-Debit-Bill-Profile/')

       

        bill_master_hotel_total_amount = queryset.Bill_Master_Total_Hotel_Amount if queryset.Bill_Master_Hotel_Mode_Of_Payment == "Debit" else Decimal(0)
        bill_master_food_total_amount = queryset.Bill_Master_Total_Food_Amount if queryset.Bill_Master_Food_Mode_Of_Payment == "Debit" else Decimal(0)

        context = {
            'bill_master_bill_update': queryset,
            'companies': companies,
            'bill_master_hotel_total_amount': bill_master_hotel_total_amount,
            'bill_master_food_total_amount': bill_master_food_total_amount,
        }

        if request.method == 'POST':
            try:
                debit_bill_date_str = request.POST.get('debit_bill_date', '')
                debit_bill_date = timezone.datetime.strptime(debit_bill_date_str, '%Y-%m-%d').date() if debit_bill_date_str else None
                debit_bill_date_str_1 = request.POST.get('debit_bill_date_1', '')
                debit_bill_date_1 = timezone.datetime.strptime(debit_bill_date_str_1, '%Y-%m-%d').date() if debit_bill_date_str_1 else None
                debit_bill_date_str_2 = request.POST.get('debit_bill_date_2', '')
                debit_bill_date_2 = timezone.datetime.strptime(debit_bill_date_str_2, '%Y-%m-%d').date() if debit_bill_date_str_2 else None
                debit_bill_date_str_3 = request.POST.get('debit_bill_date_3', '')
                debit_bill_date_3 = timezone.datetime.strptime(debit_bill_date_str_3, '%Y-%m-%d').date() if debit_bill_date_str_3 else None
                debit_bill_date_str_4 = request.POST.get('debit_bill_date_4', '')
                debit_bill_date_4 = timezone.datetime.strptime(debit_bill_date_str_4, '%Y-%m-%d').date() if debit_bill_date_str_4 else None



                bill_master_debit_hotel_amount = Decimal(request.POST.get('bill_master_debit_hotel_amount', '0')) if request.POST.get('bill_master_debit_hotel_amount', '') else Decimal('0')
                bill_master_debit_hotel_amount_1 = Decimal(request.POST.get('bill_master_debit_hotel_amount_1', '0')) if request.POST.get('bill_master_debit_hotel_amount', '') else Decimal('0')
                bill_master_debit_hotel_amount_2 = Decimal(request.POST.get('bill_master_debit_hotel_amount_2', '0')) if request.POST.get('bill_master_debit_hotel_amount', '') else Decimal('0')
                bill_master_debit_hotel_amount_3= Decimal(request.POST.get('bill_master_debit_hotel_amount_3', '0')) if request.POST.get('bill_master_debit_hotel_amount', '') else Decimal('0')
                bill_master_debit_hotel_amount_4 = Decimal(request.POST.get('bill_master_debit_hotel_amount_4', '0')) if request.POST.get('bill_master_debit_hotel_amount', '') else Decimal('0')
        

                bill_master_debit_hotel_mod = request.POST.get('bill_master_debit_hotel_mod', '')
                bill_master_debit_hotel_mod_1 = request.POST.get('bill_master_debit_hotel_mod_1', '')
                bill_master_debit_hotel_mod_2 = request.POST.get('bill_master_debit_hotel_mod_2', '')
                bill_master_debit_hotel_mod_3 = request.POST.get('bill_master_debit_hotel_mod_3', '')
                bill_master_debit_hotel_mod_4 = request.POST.get('bill_master_debit_hotel_mod_4', '')
              


                select_company_id = request.POST.get('select_company_id', None)

                bill_Number = request.POST.get('bill_Number', '')                     
                bill_master_debit_food_amount = Decimal(request.POST.get('bill_master_debit_food_amount', '0')) if request.POST.get('bill_master_debit_food_amount', '') else Decimal('0')
                bill_master_debit_food_amount_1 = Decimal(request.POST.get('bill_master_debit_food_amount_1', '0')) if request.POST.get('bill_master_debit_food_amount', '') else Decimal('0')
                bill_master_debit_food_amount_2 = Decimal(request.POST.get('bill_master_debit_food_amount_2', '0')) if request.POST.get('bill_master_debit_food_amount', '') else Decimal('0')
                bill_master_debit_food_amount_3 = Decimal(request.POST.get('bill_master_debit_food_amount_3', '0')) if request.POST.get('bill_master_debit_food_amount', '') else Decimal('0')
                bill_master_debit_food_amount_4 = Decimal(request.POST.get('bill_master_debit_food_amount_4', '0')) if request.POST.get('bill_master_debit_food_amount', '') else Decimal('0')
       
                bill_master_debit_food_mod = request.POST.get('bill_master_debit_food_mod', '')
                bill_master_debit_food_mod_1 = request.POST.get('bill_master_debit_food_mod_1', '')
                bill_master_debit_food_mod_2 = request.POST.get('bill_master_debit_food_mod_2', '')
                bill_master_debit_food_mod_3 = request.POST.get('bill_master_debit_food_mod_3', '')
                bill_master_debit_food_mod_4 = request.POST.get('bill_master_debit_food_mod_4', '')
         

                bill_master_hotel_remaining_balance = Decimal(request.POST.get('bill_master_hotel_remaining_balance', '0')) if request.POST.get('bill_master_hotel_remaining_balance', '') else Decimal('0')
                bill_master_food_remaining_balance = Decimal(request.POST.get('bill_master_food_remaining_balance', '0')) if request.POST.get('bill_master_food_remaining_balance', '') else Decimal('0')
                bill_master_debit_name = request.POST.get('bill_master_debit_name', '')
                bill_master_debit_Number = request.POST.get('bill_master_debit_Number', '')
                bill_master_debit_instruction = request.POST.get('bill_master_debit_instruction', '')

                queryset.Bill_Master_Debit_Bill_Date = debit_bill_date
                queryset.Bill_Master_Debit_Bill_Date_1 = debit_bill_date_1
                queryset.Bill_Master_Debit_Bill_Date_2 = debit_bill_date_2
                queryset.Bill_Master_Debit_Bill_Date_3 = debit_bill_date_3
                queryset.Bill_Master_Debit_Bill_Date_4 = debit_bill_date_4
               
                
                queryset.Bill_Master_Debit_Hotel_Amount = bill_master_debit_hotel_amount
                queryset.Bill_Master_Debit_Hotel_Amount_1 = bill_master_debit_hotel_amount_1
                queryset.Bill_Master_Debit_Hotel_Amount_2 = bill_master_debit_hotel_amount_2
                queryset.Bill_Master_Debit_Hotel_Amount_3 = bill_master_debit_hotel_amount_3
                queryset.Bill_Master_Debit_Hotel_Amount_4 = bill_master_debit_hotel_amount_4
              

                queryset.Bill_Master_Debit_Hotel_Mode_Of_Payment = bill_master_debit_hotel_mod
                queryset.Bill_Master_Debit_Hotel_Mode_Of_Payment_1 = bill_master_debit_hotel_mod_1
                queryset.Bill_Master_Debit_Hotel_Mode_Of_Payment_2 = bill_master_debit_hotel_mod_2
                queryset.Bill_Master_Debit_Hotel_Mode_Of_Payment_3 = bill_master_debit_hotel_mod_3
                queryset.Bill_Master_Debit_Hotel_Mode_Of_Payment_4 = bill_master_debit_hotel_mod_4
                

                queryset.Bill_Master_Debit_Food_Amount = bill_master_debit_food_amount
                queryset.Bill_Master_Debit_Food_Amount_1 = bill_master_debit_food_amount_1
                queryset.Bill_Master_Debit_Food_Amount_2 = bill_master_debit_food_amount_2
                queryset.Bill_Master_Debit_Food_Amount_3 = bill_master_debit_food_amount_3
                queryset.Bill_Master_Debit_Food_Amount_4 = bill_master_debit_food_amount_4
              

                queryset.Bill_Master_Debit_Food_Mode_Of_Payment = bill_master_debit_food_mod
                queryset.Bill_Master_Debit_Food_Mode_Of_Payment_1 = bill_master_debit_food_mod_1
                queryset.Bill_Master_Debit_Food_Mode_Of_Payment_2 = bill_master_debit_food_mod_2
                queryset.Bill_Master_Debit_Food_Mode_Of_Payment_3 = bill_master_debit_food_mod_3
                queryset.Bill_Master_Debit_Food_Mode_Of_Payment_4 = bill_master_debit_food_mod_4
              

                queryset.Bill_Master_Debit_Reference_Name = bill_master_debit_name
                queryset.Bill_Master_Debit_Reference_Mobile_Number = bill_master_debit_Number
                queryset.Bill_Master_Debit_Instruction = bill_master_debit_instruction
                queryset.Bill_Master_Debit_Hotel_Advance = max(0, bill_master_hotel_remaining_balance)
                queryset.Bill_Master_Debit_Food_Advance = max(0, bill_master_food_remaining_balance)

                queryset.Bill_Master_Balance_Hotel_Amount = max(0, -bill_master_hotel_remaining_balance)
                queryset.Bill_Master_Balance_Food_Amount = max(0, -bill_master_food_remaining_balance)

                if select_company_id:
                    try:
                        select_company = Company_Profile.objects.get(pk=select_company_id)
                    except Company_Profile.DoesNotExist:
                        logging.error(f"Company with id {select_company_id} does not exist")
                        return render(request, "Bill_Master_Advance_Add.html", {"companies": companies, "error": "Selected company does not exist."})

                    if bill_master_hotel_remaining_balance > 0 or bill_master_food_remaining_balance > 0:
                        formatted_advance_Receipt_Number = f"Excessive / {bill_Number}"
                        hotel_advance_amount = max(0, bill_master_hotel_remaining_balance)
                        food_advance_amount = max(0, bill_master_food_remaining_balance)

                        # Set Hotel_Advance_MOD and Food_Advance_MOD to None if the corresponding balance is not positive
                        hotel_advance_mod = bill_master_debit_hotel_mod if bill_master_hotel_remaining_balance > 0 else None
                        food_advance_mod = bill_master_debit_food_mod if bill_master_food_remaining_balance > 0 else None

                        # Set the balance amounts to 0 if they are negative
                        hotel_balance_amount = max(0, bill_master_hotel_remaining_balance)
                        food_balance_amount = max(0, bill_master_food_remaining_balance)

                        # Create the new advance record only if at least one of the amounts is positive
                        if hotel_advance_amount > 0 or food_advance_amount > 0:
                            new_advance = Bill_Master_ADD_Advance.objects.create(
                                Advance_Receipt_Number=formatted_advance_Receipt_Number,
                                Advance_Guest_Name=select_company.Company_Name if select_company else '',
                                Advance_Mobile_Number=bill_master_debit_Number,
                                Advance_Bill_Company=select_company,
                                Advance_Payment_Date=debit_bill_date,
                                Hotel_Advance_Amount=hotel_advance_amount,
                                Hotel_Advance_MOD=hotel_advance_mod,
                                Food_Advance_Amount=food_advance_amount,
                                Food_Advance_MOD=food_advance_mod,
                                Total=hotel_advance_amount + food_advance_amount,
                                Hotel_Balance_Amount=hotel_balance_amount,
                                Food_Balance_Amount=food_balance_amount,
                                Advance_Reference_Name=bill_master_debit_name,
                                Advance_Reference_Mobile_Number=bill_master_debit_Number,
                                Advance_Instruction=bill_master_debit_instruction,
                            )

                            queryset.Bill_Master_Formated_Advance_Receipt_Number=formatted_advance_Receipt_Number

                            logging.info(f"New advance record created: {new_advance}")

                queryset.save()
                return redirect("/Bill-Master-Debit-Bill-Profile/")

            except Exception as e:
                logging.error(f"Error processing form: {str(e)}")
                messages.error(request, 'An error occurred while processing the form.')
                return render(request, "Bill_Master_Debit_Bill_Add.html", context)

        return render(request, "Bill_Master_Debit_Bill_Add.html", context)

    except Bill_Master_ADD_Bill.DoesNotExist:
        messages.error(request, 'Bill master record not found.')
        return redirect("/Bill-Master-Debit-Bill-Profile/")
    
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return render(request, "error_page.html", {"error_message": "An unexpected error occurred."})


@login_required(login_url='Login_In')
def Bill_Master_Debit_Bill_Delete(request, id):
    try:
        if request.method == 'POST':
            with transaction.atomic():
                # Retrieve the bill master record to be deleted
                bill_master_debit = Bill_Master_ADD_Bill.objects.get(id=id)

                # Get the formatted advance receipt number from the bill master record
                formatted_advance_receipt_number = bill_master_debit.Bill_Master_Formated_Advance_Receipt_Number

                # Check if an advance exists with the same advance receipt number
                bill_master_debit_advance = Bill_Master_ADD_Advance.objects.filter(
                    Advance_Receipt_Number=formatted_advance_receipt_number
                ).first()

                # If an advance record is found, delete it
                if bill_master_debit_advance:
                    bill_master_debit_advance.delete()

                # Clear the refund details by setting them to None or empty values
                bill_master_debit.Bill_Master_Debit_Bill_Date = None
                bill_master_debit.Bill_Master_Debit_Bill_Date_1 = None
                bill_master_debit.Bill_Master_Debit_Bill_Date_2 = None
                bill_master_debit.Bill_Master_Debit_Bill_Date_3 = None
                bill_master_debit.Bill_Master_Debit_Bill_Date_4 = None

                bill_master_debit.Bill_Master_Debit_Hotel_Amount = None
                bill_master_debit.Bill_Master_Debit_Hotel_Amount_1 = None
                bill_master_debit.Bill_Master_Debit_Hotel_Amount_2 = None
                bill_master_debit.Bill_Master_Debit_Hotel_Amount_3 = None
                bill_master_debit.Bill_Master_Debit_Hotel_Amount_4 = None

                bill_master_debit.Bill_Master_Debit_Food_Amount = None
                bill_master_debit.Bill_Master_Debit_Food_Amount_1 = None
                bill_master_debit.Bill_Master_Debit_Food_Amount_2 = None
                bill_master_debit.Bill_Master_Debit_Food_Amount_3 = None
                bill_master_debit.Bill_Master_Debit_Food_Amount_4 = None

                bill_master_debit.Bill_Master_Debit_Hotel_Mode_Of_Payment = ''
                bill_master_debit.Bill_Master_Debit_Hotel_Mode_Of_Payment_1 = ''
                bill_master_debit.Bill_Master_Debit_Hotel_Mode_Of_Payment_2 = ''
                bill_master_debit.Bill_Master_Debit_Hotel_Mode_Of_Payment_3 = ''
                bill_master_debit.Bill_Master_Debit_Hotel_Mode_Of_Payment_4 = ''

                bill_master_debit.Bill_Master_Debit_Food_Mode_Of_Payment = ''
                bill_master_debit.Bill_Master_Debit_Food_Mode_Of_Payment_1 = ''
                bill_master_debit.Bill_Master_Debit_Food_Mode_Of_Payment_2 = ''
                bill_master_debit.Bill_Master_Debit_Food_Mode_Of_Payment_3 = ''
                bill_master_debit.Bill_Master_Debit_Food_Mode_Of_Payment_4 = ''

                bill_master_debit.Bill_Master_Debit_Reference_Name = ''
                bill_master_debit.Bill_Master_Debit_Reference_Mobile_Number = ''
                bill_master_debit.Bill_Master_Debit_Instruction = ''
                bill_master_debit.Bill_Master_Debit_Hotel_Advance = ''
                bill_master_debit.Bill_Master_Debit_Food_Advance = ''

                # Update balance amount to be equal to total amount
                bill_master_debit.Bill_Master_Balance_Hotel_Amount = bill_master_debit.Bill_Master_Total_Hotel_Amount
                bill_master_debit.Bill_Master_Balance_Food_Amount = bill_master_debit.Bill_Master_Total_Food_Amount

                # Save the updated bill master record
                bill_master_debit.save()

        else:
            messages.warning(request, 'Invalid request method.')
    except Bill_Master_ADD_Bill.DoesNotExist:
        messages.error(request, 'Bill master debit record not found.')
    except Exception as e:
        print(e)  # Print any error that occurs for debugging purposes
        messages.error(request, 'An error occurred while deleting the refund details.')

    return redirect('/Bill-Master-Debit-Bill-Profile/')
