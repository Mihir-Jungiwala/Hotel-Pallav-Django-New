# Import necessary modules
from import_export import resources
from .models import Authentication

# Define a resource class for exporting and importing Authentication data
class AuthenticationResource(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Authentication
