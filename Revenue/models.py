# Import necessary modules from Django
from django.db import models  # Importing the models module to define database models
from django.contrib.auth.models import User  # Importing the User model for user-related fields

# Define the Hotel_Cash_Deposite model to store hotel cash deposit records
class Hotel_Cash_Deposite(models.Model):
    Deposite_Hotel_Date = models.DateField()  # Field to store the date of the cash deposit
    Deposite_Hotel_Time = models.TimeField()  # Field to store the time of the cash deposit
    Deposite_Hotel_Username = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the User model
    Deposite_Hotel_Full_Name = models.CharField(max_length=20, null=True)  # Full name of the depositor (optional)
    Deposite_Hotel_Withdrawer = models.CharField(max_length=100)  # Name of the person withdrawing the deposit
    Deposite_Hotel_Amount = models.CharField(max_length=50)  # Amount of cash deposited (as a string)
    Deposite_Hotel_Amount_In_Words = models.CharField(max_length=250)  # Amount of cash in words (as a string)

# Define the Food_Cash_Deposite model to store food cash deposit records
class Food_Cash_Deposite(models.Model):
    Deposite_Food_Date = models.DateField()  # Field to store the date of the food cash deposit
    Deposite_Food_Time = models.TimeField()  # Field to store the time of the food cash deposit
    Deposite_Food_Username = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the User model
    Deposite_Food_Full_Name = models.CharField(max_length=20, null=True)  # Full name of the depositor (optional)
    Deposite_Food_Withdrawer = models.CharField(max_length=100)  # Name of the person withdrawing the deposit
    Deposite_Food_Amount = models.CharField(max_length=50)  # Amount of food deposited (as a string)
    Deposite_Food_Amount_In_Words = models.CharField(max_length=250)  # Amount of food in words (as a string)
