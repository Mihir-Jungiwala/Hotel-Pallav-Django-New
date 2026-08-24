from django.contrib import admin  # Importing Django's admin module for admin site management
from import_export.admin import ImportExportModelAdmin  # Importing the ImportExportModelAdmin class for import/export functionality
from .models import Shift_Handover  # Importing the Shift_Handover model to manage in the admin interface
from .resources import ShiftHandover  # Importing the resource class for Shift_Handover


class ShiftHandoverAdmin(ImportExportModelAdmin):
    # Associate the resource with the admin to enable import/export functionality
    resource_class = ShiftHandover  


# Register the Shift_Handover model with the custom admin
admin.site.register(Shift_Handover, ShiftHandoverAdmin)  
