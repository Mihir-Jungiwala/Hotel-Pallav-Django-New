import re
from decimal import Decimal, InvalidOperation

from django.db import migrations


def normalize_amount_fields(apps, schema_editor):
    """Cleans up the free-form Deposite_*_Amount text before the next
    migration changes the column to a real DecimalField. Strips thousands
    separators (commas) and surrounding whitespace; anything left that
    still isn't parseable as a number is defaulted to '0' rather than
    left to fail the schema migration outright — a bad legacy value
    should not block the whole app from getting a correct, enforced
    numeric column going forward.
    """
    Hotel_Cash_Deposite = apps.get_model('Revenue', 'Hotel_Cash_Deposite')
    Food_Cash_Deposite = apps.get_model('Revenue', 'Food_Cash_Deposite')

    for model, field in ((Hotel_Cash_Deposite, 'Deposite_Hotel_Amount'), (Food_Cash_Deposite, 'Deposite_Food_Amount')):
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
    # Nothing to reverse: this only normalizes text that's about to
    # become a DecimalField in the next migration anyway.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Revenue', '0005_food_cash_deposite_deposite_food_full_name_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_amount_fields, noop_reverse),
    ]
