from import_export import resources
from .models import Hotel_Cash_Withdrawal, Food_Cash_Withdrawal, Hotel_Cash_Miscellaneous_Expenses, Food_Cash_Miscellaneous_Expenses, Staff_Advance

class HotelCashWithdrawal(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Hotel_Cash_Withdrawal

class FoodCashWithdrawal(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Food_Cash_Withdrawal

class HotelCashMiscellaneousExpenses(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Hotel_Cash_Miscellaneous_Expenses

class FoodCashMiscellaneousExpenses(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Food_Cash_Miscellaneous_Expenses

class StaffAdvance(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Staff_Advance