from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Food_Cash_Withdrawal, Hotel_Cash_Withdrawal, Hotel_Cash_Miscellaneous_Expenses, Food_Cash_Miscellaneous_Expenses, Staff_Advance
from .resources import HotelCashWithdrawal, FoodCashWithdrawal, HotelCashMiscellaneousExpenses, FoodCashMiscellaneousExpenses, StaffAdvance

class HotelCashWithdrawalAdmin(ImportExportModelAdmin):
    resource_class = HotelCashWithdrawal

class FoodCashWithdrawalAdmin(ImportExportModelAdmin):
    resource_class = FoodCashWithdrawal

class HotelCashMiscellaneousExpensesAdmin(ImportExportModelAdmin):
    resource_class = HotelCashMiscellaneousExpenses

class FoodCashMiscellaneousExpensesAdmin(ImportExportModelAdmin):
    resource_class = FoodCashMiscellaneousExpenses

class StaffAdvanceAdmin(ImportExportModelAdmin):
    resource_class = StaffAdvance

# Register the models with the custom admin
admin.site.register(Hotel_Cash_Withdrawal, HotelCashWithdrawalAdmin)
admin.site.register(Food_Cash_Withdrawal, FoodCashWithdrawalAdmin)
admin.site.register(Hotel_Cash_Miscellaneous_Expenses, HotelCashMiscellaneousExpensesAdmin)
admin.site.register(Food_Cash_Miscellaneous_Expenses, FoodCashMiscellaneousExpensesAdmin)
admin.site.register(Staff_Advance, StaffAdvanceAdmin)
