from import_export import resources
from .models import Bill_Master_ADD_Advance,Bill_Master_ADD_Bill

class BillMasterADDAdvance(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Bill_Master_ADD_Advance

class BillMasterADDBill(resources.ModelResource):
    class Meta:
        # Specify the model to work with
        model = Bill_Master_ADD_Bill

