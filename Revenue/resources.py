# Import necessary modules from the import_export package
from import_export import resources  # Importing the resources module for handling import/export functionality
from .models import Hotel_Cash_Deposite, Food_Cash_Deposite  # Importing the models to be used in the resource classes

# Create a resource class for the Hotel_Cash_Deposite model
class HotelCashDeposite(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Hotel_Cash_Deposite  # Set the model for this resource class to Hotel_Cash_Deposite

# Create a resource class for the Food_Cash_Deposite model
class FoodCashDeposite(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Food_Cash_Deposite  # Set the model for this resource class to Food_Cash_Deposite
