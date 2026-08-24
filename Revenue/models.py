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
    # Was CharField(max_length=50) — storing money as free-form text meant
    # Dashboard.views' Sum('Deposite_Hotel_Amount') silently miscomputed
    # whenever a value contained a comma (e.g. "1,500" entered with an
    # Indian thousands separator): SQLite's loose typing parses only the
    # numeric prefix before the comma, so SUM('1,500', '500') returned
    # 501 instead of 2000. Confirmed directly against a real query. A
    # real DecimalField makes that class of silent corruption structurally
    # impossible instead of merely unlikely.
    Deposite_Hotel_Amount = models.DecimalField(max_digits=12, decimal_places=2)
    Deposite_Hotel_Amount_In_Words = models.CharField(max_length=250)  # Amount of cash in words (as a string)

# Define the Food_Cash_Deposite model to store food cash deposit records
class Food_Cash_Deposite(models.Model):
    Deposite_Food_Date = models.DateField()  # Field to store the date of the food cash deposit
    Deposite_Food_Time = models.TimeField()  # Field to store the time of the food cash deposit
    Deposite_Food_Username = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the User model
    Deposite_Food_Full_Name = models.CharField(max_length=20, null=True)  # Full name of the depositor (optional)
    Deposite_Food_Withdrawer = models.CharField(max_length=100)  # Name of the person withdrawing the deposit
    Deposite_Food_Amount = models.DecimalField(max_digits=12, decimal_places=2)  # See Hotel_Cash_Deposite.Deposite_Hotel_Amount above
    Deposite_Food_Amount_In_Words = models.CharField(max_length=250)  # Amount of food in words (as a string)
