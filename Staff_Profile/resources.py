# Import necessary modules
from import_export import resources  # Importing resources from the django-import-export library
from .models import User_Profile  # Importing the User_Profile model from the current app's models

# Create a resource class for User_Profile model to handle import/export functionality
class UserProfile(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = User_Profile  # This resource will work with the User_Profile model for importing/exporting data
