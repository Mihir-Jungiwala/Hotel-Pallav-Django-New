from django.db import models
from django.utils import timezone
from Company.models import Company_Profile

class Bill_Master_ADD_Advance(models.Model):
    Advance_Receipt_Number = models.CharField(max_length=100, unique=True, null=True) 
    Advance_Guest_Name = models.CharField(max_length=255, null=True)
    Advance_Mobile_Number = models.CharField(max_length=15, null=True)
    Advance_Bill_Company = models.ForeignKey(Company_Profile, on_delete=models.CASCADE, null=True)
    Advance_Payment_Date = models.DateField(null=True)
   
    Hotel_Advance_Amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    Food_Advance_Amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    Hotel_Advance_MOD = models.CharField(max_length=20, null=True) 
    Food_Advance_MOD = models.CharField(max_length=20, null=True)       
    Advance_Reference_Name = models.CharField(max_length=255, null=True)
    Advance_Reference_Mobile_Number = models.CharField(max_length=15, null=True)
    Advance_Instruction = models.CharField(max_length=255, null=True)
    Hotel_Balance_Amount = models.DecimalField(max_digits=50, decimal_places=2, null=True, default=0) 
    Food_Balance_Amount = models.DecimalField(max_digits=50, decimal_places=2, null=True, default=0) 
    Total = models.DecimalField(max_digits=50, decimal_places=2, null=True, default=0)     
    Hotel_Refund_Advance_Amount = models.DecimalField(max_digits=20, decimal_places=2, null=True) 
    Food_Refund_Advance_Amount = models.DecimalField(max_digits=20, decimal_places=2, null=True) 
    Hotel_Refund_MOD = models.CharField(max_length=20, null=True)
    Food_Refund_MOD = models.CharField(max_length=20, null=True)    
    Refund_Payment_Date = models.DateField(null=True)    
    Refund_Guest_Name = models.CharField(max_length=255, null=True)
    Refund_Mobile_Number = models.CharField(max_length=15, null=True)
    Refund_Instruction = models.CharField(max_length=255, null=True)



class Bill_Master_ADD_Bill(models.Model): 
    #Getting Advance  
    Bill_Master_Advance_Receipt_Number = models.CharField(max_length=100, blank=True, null=True)
    Bill_Master_Advance_Guest_Name = models.CharField(max_length=100, blank=True, null=True)
    Bill_Master_Hotel_Advance_Amounts = models.CharField(max_length=100, blank=True, null=True)
    Bill_Master_Advance_Date = models.CharField(max_length=100, blank=True, null=True)
    Bill_Master_Food_Advance_Amounts = models.CharField(max_length=100, blank=True, null=True)  
    Bill_Master_Advance_Company = models.CharField(max_length=100, blank=True, null=True) 
    Bill_Master_Bill_Number = models.CharField(max_length=100, null=True, unique=True)
    
    Bill_Master_Bill_Company = models.ForeignKey(Company_Profile, on_delete=models.CASCADE, null=True)
    Bill_Master_Bill_Date = models.DateField(null=True)
    Bill_Master_Guest_Name = models.CharField(max_length=255, null=True)
    Bill_Master_Mobile_Number = models.CharField(max_length=15, null=True)
    Bill_Master_Hotel_Plan = models.CharField(max_length=100, blank=True, null=True)    
    Bill_Master_Hotel_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Hotel_Plan_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Hotel_Laundry_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Hotel_GST = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Hotel_Mode_Of_Payment = models.CharField(max_length=100, blank=True, null=True)    
    Bill_Master_Food_Plan_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Food_Laundry_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Food_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)    
    Bill_Master_Food_GST = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Food_Mode_Of_Payment = models.CharField(max_length=100, blank=True, null=True)
    Bill_Master_Total_Hotel_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Total_Food_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)    
    Bill_Master_Reference_Name = models.CharField(max_length=100, blank=True, null=True)
    Bill_Master_Reference_Mobile_Number = models.CharField(max_length=15, blank=True, null=True)
    Bill_Master_Instruction = models.TextField(blank=True, null=True)
    Bill_Master_Debit_BIll_PDF = models.FileField(upload_to='Invoice_Debit_Bill/', null=True)

    Bill_Master_Balance_Hotel_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Balance_Food_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True) 

    Bill_Master_Advance_Hotel_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Advance_Food_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)



    Bill_Master_Advance_Delete_Hotel_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Advance_Delete_Food_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True) 

    Bill_Master_Formated_Advance_Receipt_Number  = models.CharField(max_length=255, null=True, blank=True)
    Bill_Master_Debit_Hotel_Advance = models.CharField(max_length=100, blank=True, null=True)   
    Bill_Master_Debit_Food_Advance = models.CharField(max_length=100, blank=True, null=True)   
    Bill_Master_Debit_Bill_Date = models.DateField(null=True)
    Bill_Master_Debit_Bill_Date_1 = models.DateField(null=True)
    Bill_Master_Debit_Bill_Date_2 = models.DateField(null=True)
    Bill_Master_Debit_Bill_Date_3 = models.DateField(null=True)
    Bill_Master_Debit_Bill_Date_4 = models.DateField(null=True)


    Bill_Master_Debit_Hotel_Mode_Of_Payment = models.CharField(max_length=100, blank=True, null=True)
    Bill_Master_Debit_Hotel_Mode_Of_Payment_1 = models.CharField(max_length=100, blank=True, null=True)   
    Bill_Master_Debit_Hotel_Mode_Of_Payment_2 = models.CharField(max_length=100, blank=True, null=True)   
    Bill_Master_Debit_Hotel_Mode_Of_Payment_3 = models.CharField(max_length=100, blank=True, null=True)   
    Bill_Master_Debit_Hotel_Mode_Of_Payment_4 = models.CharField(max_length=100, blank=True, null=True)   
    

    Bill_Master_Debit_Food_Mode_Of_Payment = models.CharField(max_length=100, blank=True, null=True) 
    Bill_Master_Debit_Food_Mode_Of_Payment_1 = models.CharField(max_length=100, blank=True, null=True)   
    Bill_Master_Debit_Food_Mode_Of_Payment_2 = models.CharField(max_length=100, blank=True, null=True)   
    Bill_Master_Debit_Food_Mode_Of_Payment_3 = models.CharField(max_length=100, blank=True, null=True)   
    Bill_Master_Debit_Food_Mode_Of_Payment_4 = models.CharField(max_length=100, blank=True, null=True)   
 

    Bill_Master_Debit_Hotel_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Debit_Hotel_Amount_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Debit_Hotel_Amount_2 = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Debit_Hotel_Amount_3= models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Debit_Hotel_Amount_4 = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    

    Bill_Master_Debit_Food_Amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Debit_Food_Amount_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Debit_Food_Amount_2 = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Debit_Food_Amount_3= models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    Bill_Master_Debit_Food_Amount_4 = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)
    

    Bill_Master_Debit_Reference_Name = models.CharField(max_length=100, blank=True, null=True)
    Bill_Master_Debit_Reference_Mobile_Number = models.CharField(max_length=15, blank=True, null=True)
    Bill_Master_Debit_Instruction = models.TextField(blank=True, null=True)

    