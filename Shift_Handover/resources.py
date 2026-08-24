# Import necessary modules
from import_export import resources  # Importing resources from django-import-export for data handling
from .models import Shift_Handover  # Importing the Shift_Handover model to work with

class ShiftHandover(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Shift_Handover
