import re
from decimal import Decimal, InvalidOperation

from django.db import migrations

# Same normalization approach as Revenue's equivalent migration — strips
# thousands separators/whitespace before the schema migration changes
# these columns from CharField to DecimalField, defaulting anything still
# unparseable to '0' rather than blocking the change.
FIELDS = [
    ('Hotel_Cash_Withdrawal', 'Withdrawal_Hotel_Amount'),
    ('Food_Cash_Withdrawal', 'Withdrawal_Food_Amount'),
    ('Hotel_Cash_Miscellaneous_Expenses', 'Miscellaneous_Expenses_Hotel_Amount'),
    ('Food_Cash_Miscellaneous_Expenses', 'Miscellaneous_Expenses_Food_Amount'),
]


def normalize_amount_fields(apps, schema_editor):
    for model_name, field in FIELDS:
        model = apps.get_model('Expense', model_name)
        for row in model.objects.all():
            raw = getattr(row, field) or ''
            cleaned = re.sub(r'[,\s]', '', raw)
            try:
                Decimal(cleaned)
                normalized = cleaned
            except InvalidOperation:
                normalized = '0'
            if normalized != raw:
                setattr(row, field, normalized)
                row.save(update_fields=[field])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Expense', '0007_rename_miscellaneous_expenses_full_name_food_cash_miscellaneous_expenses_miscellaneous_expenses_food'),
    ]

    operations = [
        migrations.RunPython(normalize_amount_fields, noop_reverse),
    ]
