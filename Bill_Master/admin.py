from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Bill_Master_ADD_Advance,Bill_Master_ADD_Bill
from .resources import BillMasterADDAdvance,BillMasterADDBill

class  BillMasterADDAdvanceAdmin(ImportExportModelAdmin):
    resource_class = BillMasterADDAdvance

class BillMasterADDBillAdmin(ImportExportModelAdmin):
    resource_class = BillMasterADDBill


# Register the models with the custom admin
admin.site.register(Bill_Master_ADD_Advance,  BillMasterADDAdvanceAdmin)
admin.site.register(Bill_Master_ADD_Bill, BillMasterADDBillAdmin)

