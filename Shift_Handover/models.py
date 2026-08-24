# Import necessary modules from Django
from django.db import models  # Importing Django's model module to define database models
from django.contrib.auth.models import User  # Importing the built-in User model for user authentication and management
from django.utils import timezone  # Importing timezone utilities for managing date and time operations

# Define the Shift_Handover model to represent shift handover records
class Shift_Handover(models.Model):
    # Field to store the date of the shift handover
    Shift_Handover_Date = models.DateField(null=True)
    
    # Field to store the time of the shift handover
    Shift_Handover_Time = models.TimeField(null=True)

    # ForeignKey field linking to the User model, representing the user who is handing over the shift
    Shift_Handover_Username = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Field to store the full name of the user handing over the shift
    Shift_Handover_Full_Name = models.CharField(max_length=20, null=True)
    
    # Field to store the shift type (e.g., morning, evening)
    Shift_Handover_Shift = models.CharField(max_length=20, null=True)
    
    # Text fields to store messages or notes during the shift handover process
    Shift_Handover_message_One = models.TextField(null=True)
    Shift_Handover_message_Two = models.TextField(null=True)
    Shift_Handover_message_Three = models.TextField(null=True)
    Shift_Handover_message_Four = models.TextField(null=True)
    Shift_Handover_message_Five = models.TextField(null=True)
    
    # Field for special instructions during the handover
    Shift_Handover_Special_Instruction = models.TextField(null=True)
    
    # Fields to count different denominations of currency and their total values
    Shift_Handover_Five_Hundred_Total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    Shift_Handover_Five_Hundred_Counts = models.CharField(max_length=10, default='0', null=True)
    
    Shift_Handover_Two_Hundred_Total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    Shift_Handover_Two_Hundred_Counts = models.CharField(max_length=10, default='0', null=True)
    
    Shift_Handover_One_Hundred_Total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    Shift_Handover_One_Hundred_Counts = models.CharField(max_length=10, default='0', null=True)
    
    Shift_Handover_Fifty_Total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    Shift_Handover_Fifty_Counts = models.CharField(max_length=10, default='0', null=True)
    
    Shift_Handover_Twenty_Total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    Shift_Handover_Twenty_Counts = models.CharField(max_length=10, default='0', null=True)
    
    Shift_Handover_Ten_Total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    Shift_Handover_Ten_Counts = models.CharField(max_length=10, default='0', null=True)
    
    Shift_Handover_Five_Total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    Shift_Handover_Five_Counts = models.CharField(max_length=10, default='0', null=True)
    
    Shift_Handover_Coins_Total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    Shift_Handover_Coins_Counts = models.CharField(max_length=10, default='0', null=True)
    
    # Field to store the total amount from the shift handover
    Shift_Handover_Total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True)
    
    # Field to store the total amount in words for better readability
    Shift_Handover_Total_Amount_In_Words = models.CharField(max_length=250)



