"""
URL configuration for Main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Authentication.views import *
from Dashboard.views import *
from Revenue.views import *
from Expense.views import *
from Shift_Handover.views import *
from Bill_Master.views import *
from Company.views import *
from Staff_Profile.views import *
from Reports.views import *


urlpatterns = [

    #Authnetication
    path('', Login_IN, name='Login_In'),
    path('Logout/', Login_OUT, name='loginout'),
    path('User-Registration/', Registration, name='registration'),
    path('Registration-User-Profile/', Registration_User_Profile, name='userprofile'),
    path('Delete-User-Profile/<id>/', Delete_User_Profile, name ='deleteUserprofile'),
    path('Reset-Password/', Reset_Password , name ='resetpassword'),
    path('Change-Password/<token>/', Change_Password, name ='changepassword'),
    path('Update-User-Role/<int:id>/', Update_User_Role, name ='UpdateUserRole'),
    path('User-Active-Deactive-Status/<int:id>/', User_Active_Deactive_Status, name ='useractivedeactivestatus'),
    path('Error/', Error_Page, name=' Error_Page'),

    #Dashboard
    path('Dashboard-Profile/', Dashboard_Profile, name = 'DashboardProfile'),

    #Revenue
    path('Revenue-Profile/', Revenue_Profile, name = 'RevenueProfile'),
    path('Hotel-Revenue-Cash-Deposite/', Hotel_Revenue_Cash_Deposite, name = 'HotelRevenueCashDeposite'),
    path('Hotel-Revenue-Cash-Delete/<id>/', Hotel_Revenue_Cash_Delete, name ='HotelRevenueCashDelete'),
    path('Hotel-Revenue-View/<id>/', Hotel_Revenue_View, name = 'HotelRevenueView'),
    path('Food-Revenue-Cash-Deposite/', Food_Revenue_Cash_Deposite, name = 'FoodRevenueCashDeposite'),
    path('Food-Revenue-Cash-Delete/<id>/', Food_Revenue_Cash_Delete, name ='FoodRevenueCashDelete'),
    path('Food-Revenue-View/<id>/', Food_Revenue_View, name = 'FoodRevenueView'),
   
    #Expense    
    path('Expense-Profile/', Expense_Profile, name = 'ExpenseProfile'),
    path('Hotel-Expense-Cash-Withdraw/', Hotel_Expense_Cash_Withdraw, name = 'HotelExpenseCashWithdraw'),
    path('Hotel-Expense-Cash-Withdraw-View/<id>/', Hotel_Expense_Cash_Withdraw_View, name = 'HotelExpenseCashWithdrawView'),
    path('Hotel-Expense-Cash-Delete/<id>/', Hotel_Expense_Cash_Delete, name ='HotelExpenseCashDelete'),  
    path('Hotel-Cash-Miscellaneous-Expense/', Hotel_Cash_Miscellaneous_Expense, name = 'HotelCashMiscellaneousExpense'),
    path('Hotel-Cash-Miscellaneous-Expense-Update/<id>/', Hotel_Cash_Miscellaneous_Expense_Update, name ='HotelCashMiscellaneousExpenseUpdate'),
    path('Hotel-Cash-Miscellaneous-Expense-Delete/<id>/', Hotel_Cash_Miscellaneous_Expense_Delete, name ='HotelCashMiscellaneousExpenseDelete'),
    path('Hotel-Cash-Miscellaneous-Expense-View/<id>/', Hotel_Cash_Miscellaneous_Expense_View, name = 'HotelCashMiscellaneousExpenseView'),
    path('Food-Expense-Cash-Withdraw/', Food_Expense_Cash_Withdraw, name = 'FoodExpenseCashWithdraw'),
    path('Food-Expense-Cash-Delete/<id>/', Food_Expense_Cash_Delete, name ='FoodExpenseCashDelete'),
    path('Food-Expense-Cash-Withdraw-View/<id>/', Food_Expense_Cash_Withdraw_View, name = 'FoodExpenseCashWithdrawView'),   
    path('Food-Cash-Miscellaneous-Expense/', Food_Cash_Miscellaneous_Expense, name = 'FoodCashMiscellaneousExpense'),
    path('Food-Cash-Miscellaneous-Expense-Update/<id>/', Food_Cash_Miscellaneous_Expense_Update, name ='FoodCashMiscellaneousExpenseUpdate'),
    path('Food-Cash-Miscellaneous-Expense-Delete/<id>/', Food_Cash_Miscellaneous_Expense_Delete, name ='FoodCashMiscellaneousExpenseDelete'),
    path('Food-Cash-Miscellaneous-Expense-View/<id>/', Food_Cash_Miscellaneous_Expense_View, name = 'FoodCashMiscellaneousExpenseView'),
    path('Staff-Advance-Salaries/', Staff_Advance_Salaries, name = 'StaffAdvanceSalaries'),
    path('Staff-Advance-Salaries-Update/<id>/', Staff_Advance_Salaries_Update, name = 'StaffAdvanceSalariesUpdate'),
    path('Staff-Advance-Salaries-Delete/<id>/', Staff_Advance_Salaries_Delete, name = 'StaffAdvanceSalariesDelete'),
    path('Staff-Advance-Salaries-View/<id>/', Staff_Advance_Salaries_View, name = 'StaffAdvanceSalariesView'),
    path('User-Profile-Pause-Unpause/<int:id>/', User_Profile_Pause_Unpause, name ='UserProfilePauseUnpause'),

    #Shift Handover
    path('Shift-Handover-Profile/', Shift_Handover_Profile ,  name = 'ShiftHandoverProfile'),
    path('Shift-Handover-Add/', Shift_Handover_Add, name = 'ShiftHandoverAdd'),
    path('Shift-Handover-Update/<id>/', Shift_Handover_Update, name ='ShiftHandoverUpdate'),
    path('Shift-Handover-Delete/<id>/', Shift_Handover_Delete, name ='ShiftHandoverDelete'),
    path('Shift_Handover_View/<int:id>/', Shift_Handover_View, name='Shift_Handover_View'),
    
    #Bill Master 
    #Advance   
    path('Bill-Master-Advance-Profile/', Bill_Master_Advance_Profile, name = 'BillMasterAdvanceProfile'),
    path('Bill-Master-Advance-Add/', Bill_Master_Advance_Add, name = 'BillMasterAdvanceAdd'),
    path('Bill-Master-Advance-Update/<id>/', Bill_Master_Advance_Update, name ='BillMasterAdvanceUpdate'),
    path('Bill-Master-Advance-Delete/<id>/', Bill_Master_Advance_Delete, name ='BillMasterAdvanceDelete'),
    path('Bill-Master-Advance-Refund/<id>/', Bill_Master_Advance_Refund, name ='BillMasterAdvanceRefund'),
    path('Bill-Master-Advance-Refund-Delete/<id>/', Bill_Master_Advance_Refund_Delete, name ='BillMasterAdvanceRefundDelete'),
    #Bill 
    path('Bill-Master-Debit-Bill-Profile/', Bill_Master_Debit_Bill_Profile, name = 'BillMasterDebitBillProfile'),
    path('Bill-Master-Bill-Add/', Bill_Master_Bill_Add, name = 'BillMasterBillAdd'),
    path('Bill-Master-Bill-Update/<id>/', Bill_Master_Bill_Update, name ='BillMasterBillUpdate'),
    path('Bill-Master-Bill-Delete/<int:advance_id>/', Bill_Master_Bill_Delete, name ='BillMasterBillDelete'),
    #Debit Bill 
    path('Bill-Master-Bill-Profile/', Bill_Master_Bill_Profile, name = 'BillMasterBillProfile'),
    path('Bill-Master-Debit-Bill-Add/<id>/', Bill_Master_Debit_Bill_Add, name = 'BillMasterDebitBillAdd'),
    #path('Bill-Master-Debit-Bill-Update/<id>/', Bill_Master_Debit_Bill_Update, name = 'BillMasterDebitBillUpdate'),
    path('Bill-Master-Debit-Bill-Delete/<id>/', Bill_Master_Debit_Bill_Delete, name = 'BillMasterDebitBillDelete'),   
    
    #Company Profile
    path('Company-User-Profile/', Company_User_Profile, name = 'CompanyProfile'),
    path('Company--Profile-Registration/', Company__Profile_Registration, name = 'CompanyProfileRegistration'),
    path('Company--Profile-Update/<id>/', Company_Profile__Update, name = 'CompanyProfileUpdate'),
    path('Company--Profile-User-Delete/<id>/', Company_Profile_User_Delete, name ='CompanyProfileUserDelete'),

    #Staff Profile 
    path('Staff--Profile-User-Profile/', Staff__Profile_User_Profile, name = 'StaffProfileUserProfile'),    
    path('Staff--Profile-Registration/', Staff__Profile_Registration, name = 'StaffProfileRegistration'), 
    path('Staff--Profile-User-Update/<id>/', Staff__Profile_User_Update, name = 'StaffProfileUserUpdate'),
    path('Staff--Profile-User-Delete/<id>/', Staff__Profile_User_Delete, name ='StaffProfileUserDelete'),
 
    #Reports
    path('Reports-Profile/', Reports_Profile, name = 'ReportsProfile'),
    
    #Admin Panel
    path('admin/', admin.site.urls),
]
