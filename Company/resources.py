# Import necessary modules
from import_export import resources
from .models import Company_Profile


class CompanyProfile(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Company_Profile
