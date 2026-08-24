# Import necessary modules
from django.contrib import admin  # Importing Django's admin module
from import_export.admin import ImportExportModelAdmin  # Importing ImportExportModelAdmin to enable import/export features
from .models import User_Profile  # Importing the User_Profile model from the current app's models
from .resources import UserProfile  # Import the resource class for User_Profile

# Create a custom admin class for User_Profile model with import/export functionality
class UserProfileAdmin(ImportExportModelAdmin):
    resource_class = UserProfile  # Associate the resource class (UserProfile) with the admin for import/export functionality

# Register the User_Profile model with the custom admin class
admin.site.register(User_Profile, UserProfileAdmin)
