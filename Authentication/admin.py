from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Authentication
from .resources import AuthenticationResource

@admin.register(Authentication)
class AuthenticationAdmin(ImportExportModelAdmin):
    # Link the Authentication model with its resource class for import/export functionality
    resource_class = AuthenticationResource
    
    # Define the fields to be displayed in the admin list view
    list_display = ('user', 'activity_type',  'login_date', 'login_time', 'logout_date', 'logout_time', 'calculate_minutes_logged_in', 'email_sent_time', 'password_change_time', 'password_change_duration')  
    
    # Enable searching by specified fields
    search_fields = ('user__username', 'activity_type')
    
    # Enable filtering by specified fields
    list_filter = ('activity_type', 'activity_time')

    # Method to calculate and display the minutes logged in
    def calculate_minutes_logged_in(self, obj):
        """A method to display calculated minutes_logged_in in the admin list view."""
        return obj.minutes_logged_in

    # Set a custom column header for the calculated minutes logged in
    calculate_minutes_logged_in.short_description = 'Minutes Logged In'

    # Override save_model method to set created_by and modified_by fields
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
