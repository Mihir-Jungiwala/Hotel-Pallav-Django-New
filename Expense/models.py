
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from Staff_Profile.models import User_Profile



class Hotel_Cash_Withdrawal(models.Model):
  
    
    Withdrawal_Hotel_Date = models.DateField()  
    Withdrawal_Hotel_Time = models.TimeField()
    Withdrawal_Hotel_Username =  models.ForeignKey(User, on_delete=models.CASCADE)
    Withdrawal_Hotel_Full_Name = models.CharField(max_length=20, null=True)

    Withdrawal_Hotel_Withdrawer = models.CharField(max_length=100)
    Withdrawal_Hotel_Amount = models.CharField(max_length=50)
    Withdrawal_Hotel_Amount_In_Words = models.CharField(max_length=250)

    

class Food_Cash_Withdrawal(models.Model):
    

    Withdrawal_Food_Date = models.DateField()
    Withdrawal_Food_Time = models.TimeField()
    Withdrawal_Food_Username =  models.ForeignKey(User, on_delete=models.CASCADE)
    Withdrawal_Food_Full_Name = models.CharField(max_length=20, null=True)

    Withdrawal_Food_Withdrawer = models.CharField(max_length=100)
    Withdrawal_Food_Amount = models.CharField(max_length=50)
    Withdrawal_Food_Amount_In_Words = models.CharField(max_length=250)


class Hotel_Cash_Miscellaneous_Expenses(models.Model):
    

    Miscellaneous_Expenses_Hotel_Date = models.DateField()
    Miscellaneous_Expenses_Hotel_Time = models.TimeField()
    Miscellaneous_Expenses_Hotel_Username =  models.ForeignKey(User, on_delete=models.CASCADE)
    Miscellaneous_Expenses_Hotel_Full_Name = models.CharField(max_length=20, null=True)

    Miscellaneous_Expenses_Hotel_Expense_Name = models.CharField(max_length=100)
    Miscellaneous_Expenses_Hotel_Amount = models.CharField(max_length=50)
    Miscellaneous_Expenses_Hotel_Instruction = models.CharField(max_length=500)
    Miscellaneous_Expenses_Hotel_Amount_In_Words = models.CharField(max_length=250)


class Food_Cash_Miscellaneous_Expenses(models.Model):
    

    Miscellaneous_Expenses_Food_Date = models.DateField()
    Miscellaneous_Expenses_Food_Time = models.TimeField()
    Miscellaneous_Expenses_Food_Username =  models.ForeignKey(User, on_delete=models.CASCADE)
    Miscellaneous_Expenses_Food_Full_Name = models.CharField(max_length=20, null=True)

    Miscellaneous_Expenses_Food_Expense_Name = models.CharField(max_length=100)
    Miscellaneous_Expenses_Food_Amount = models.CharField(max_length=50)
    Miscellaneous_Expenses_Food_Instruction = models.CharField(max_length=500)
    Miscellaneous_Expenses_Food_Amount_In_Words = models.CharField(max_length=250)



class Staff_Advance(models.Model):  # Renamed class according to Python naming conventions
    

    Staff_Advance_date = models.DateField()
    Staff_Advance_time = models.TimeField()
    Staff_Advance_username = models.ForeignKey(User, on_delete=models.CASCADE)
    Staff_Advance_Full_Name = models.CharField(max_length=20, null=True)

    Staff_Advance_year_month = models.CharField(max_length=7)  # Assuming format: "YYYY-MM"
    Staff_Advance_name = models.ForeignKey(User_Profile, on_delete=models.CASCADE, null=True) 
    Staff_Advance_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Adjust max_digits and decimal_places as needed
    Staff_Advance_instruction = models.TextField(blank=True)  
    Staff_Advance_Amount_In_Words = models.CharField(max_length=250)
    # Allow blank fields



        
