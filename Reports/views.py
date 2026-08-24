from django.shortcuts import render
from datetime import datetime
import pytz
from django.contrib.auth.decorators import login_required
from Bill_Master.models import Bill_Master_ADD_Advance, Bill_Master_ADD_Bill

@login_required(login_url='Login_In')
def Reports_Profile(request):
    try:
        # Set the timezone to Indian Standard Time (IST)
        ist_timezone = pytz.timezone('Asia/Kolkata')
        
        # Get the current date and time in IST timezone
        now = datetime.now(ist_timezone)
        
        # Retrieve all Bill_Master_BillADD objects
        bill_maters = Bill_Master_ADD_Bill.objects.all()
        
        # Prepare the context dictionary with the formatted date, time, and day
        context = {
            'current_date': now.strftime('%d %B %Y'),  # Formatted date (e.g., 20 April 2024)
            'current_time': now.strftime('%I:%M %p'),  # Formatted time (e.g., 03:30 PM)
            'current_day': now.strftime('%A'),  # Full name of the day (e.g., Saturday)
            'bill_maters': bill_maters,
        }
        
        # Render the 'Reports.html' template with the context
        return render(request, "Reports.html", context)
    
    except Exception as e:
        print(e)
        return render(request, "error_page.html", {'error_message': 'An error occurred while fetching user profiles. Please try again later.'})
