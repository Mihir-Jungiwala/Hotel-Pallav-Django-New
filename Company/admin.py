from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Company_Profile
from .resources import CompanyProfile # Import the resource


class CompanyProfileAdmin(ImportExportModelAdmin):
    resource_class = CompanyProfile # Associate the resource with the admin


# Register the CompanyProfile model with the custom admin
admin.site.register(Company_Profile, CompanyProfileAdmin)
