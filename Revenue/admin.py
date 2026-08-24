# Import necessary modules for the Django admin interface
from django.contrib import admin  # Importing Django's admin module
from import_export.admin import ImportExportModelAdmin  # Importing ImportExportModelAdmin to enable import/export features
from .models import Hotel_Cash_Deposite, Food_Cash_Deposite  # Importing the models that will be managed through the admin interface
from .resources import HotelCashDeposite, FoodCashDeposite  # Importing the resource classes for handling import/export logic

# Create a custom admin class for the Hotel_Cash_Deposite model with import/export functionality
class HotelCashDepositeAdmin(ImportExportModelAdmin):
    resource_class = HotelCashDeposite  # Associate the resource class (HotelCashDeposite) with the admin for import/export functionality

# Create a custom admin class for the Food_Cash_Deposite model with import/export functionality
class FoodCashDepositeAdmin(ImportExportModelAdmin):
    resource_class = FoodCashDeposite  # Associate the resource class (FoodCashDeposite) with the admin for import/export functionality

# Register the Hotel_Cash_Deposite model with the custom admin class
admin.site.register(Hotel_Cash_Deposite, HotelCashDepositeAdmin)
# Register the Food_Cash_Deposite model with the custom admin class
admin.site.register(Food_Cash_Deposite, FoodCashDepositeAdmin)
