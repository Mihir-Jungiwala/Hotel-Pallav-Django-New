from django.db import models
from django.contrib.auth.models import User

class Company_Profile(models.Model):
    Company_Name = models.CharField(max_length=100, unique=True)
    Company_Address = models.CharField(max_length=100, null=True)
    Company_Email = models.EmailField(max_length=254, null=True)
    Company_Country = models.CharField(max_length=100, null=True)
    Company_Pincode = models.CharField(max_length=20, null=True)
    Company_Nationality = models.CharField(max_length=100, null=True)
    Company_Mobile_Number = models.CharField(max_length=15, null=True)
    Company_Phone_Number = models.CharField(max_length=15, null=True)
    Company_Discount_Percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    Company_Instruction = models.TextField(null=True)
    Company_GST_Number = models.CharField(max_length=50, null=True)
    Company_GST_Percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    Company_TCS_Percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    Company_TDS_Percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    Company_MD_One_Name = models.CharField(max_length=100, null=True)
    Company_MD_One_Email = models.EmailField(max_length=254, null=True)
    Company_MD_One_Mobile_Number = models.CharField(max_length=15, null=True)
    Company_MD_Second_Name = models.CharField(max_length=100, null=True)
    Company_MD_Second_Email = models.EmailField(max_length=254, null=True)
    Company_MD_Second_Mobile_Number = models.CharField(max_length=15, null=True)
    Company_HR_Head_Name = models.CharField(max_length=100, null=True)
    Company_HR_Head_Email = models.EmailField(max_length=254, null=True)
    Company_HR_Head_Mobile_Number = models.CharField(max_length=15, null=True)
    Company_Assitant_HR_Name = models.CharField(max_length=100, null=True)
    Company_Assitant_HR_Email = models.EmailField(max_length=254, null=True)
    Company_Assitant_HR_Mobile_Number = models.CharField(max_length=15, null=True)
    Company_Accountant_Head_Name = models.CharField(max_length=100, null=True)
    Company_Accountant_Head_Email = models.EmailField(max_length=254, null=True)
    Company_Accountant_Head_Mobile_Number = models.CharField(max_length=15, null=True)
    Company_Accountant_Assistant_One_Name = models.CharField(max_length=100, null=True)
    Company_Accountant_Assistant_One_Email = models.EmailField(max_length=254, null=True)
    Company_Accountant_Assistant_One_Mobile_Number = models.CharField(max_length=15, null=True)
    Company_Accountant_Assistant_Two_Name = models.CharField(max_length=100, null=True)
    Company_Accountant_Assistant_Two_Email = models.EmailField(max_length=254, null=True)
    Company_Accountant_Assistant_Two_Mobile_Number = models.CharField(max_length=15, null=True)
    
    created_by = models.ForeignKey(User, related_name='created_company_profiles', on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_by = models.ForeignKey(User, related_name='modified_company_profiles', on_delete=models.SET_NULL, null=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    
    def __str__(self):
        return self.Company_Name

