import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from Bill_Master.models import Bill_Master_ADD_Bill


class DashboardDebitInstallmentIncomeTests(TestCase):
    """Was: 'today's cash income from debit settlements' only summed the
    base (1st installment) amount field. A debit bill can be settled in up
    to 5 installments (base + _1.._4), each with its own date and mode of
    payment (see Bill_Master_Debit_Bill_Add) — a cash payment recorded
    against installment 2, 3, or 4 was silently excluded from the
    dashboard's daily income figure."""

    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='dash_staff', password='Correct@1234')
        self.client.post('/', {'username': 'dash_staff', 'password': 'Correct@1234'})
        self.today = datetime.date.today()

    def test_later_installment_counted_in_hotel_income(self):
        Bill_Master_ADD_Bill.objects.create(
            Bill_Master_Bill_Number='DASH-H1',
            Bill_Master_Hotel_Mode_Of_Payment='Debit',
            Bill_Master_Debit_Bill_Date=self.today - datetime.timedelta(days=5),
            Bill_Master_Debit_Hotel_Mode_Of_Payment='Cash',
            Bill_Master_Debit_Hotel_Amount=Decimal('100'),
            Bill_Master_Debit_Bill_Date_3=self.today,
            Bill_Master_Debit_Hotel_Mode_Of_Payment_3='Cash',
            Bill_Master_Debit_Hotel_Amount_3=Decimal('777'),
        )
        response = self.client.get('/Dashboard-Profile/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context['total_hotel_income'], Decimal('777'))

    def test_later_installment_counted_in_food_income(self):
        Bill_Master_ADD_Bill.objects.create(
            Bill_Master_Bill_Number='DASH-F1',
            Bill_Master_Food_Mode_Of_Payment='Debit',
            Bill_Master_Debit_Bill_Date=self.today - datetime.timedelta(days=5),
            Bill_Master_Debit_Food_Mode_Of_Payment='Cash',
            Bill_Master_Debit_Food_Amount=Decimal('50'),
            Bill_Master_Debit_Bill_Date_2=self.today,
            Bill_Master_Debit_Food_Mode_Of_Payment_2='Cash',
            Bill_Master_Debit_Food_Amount_2=Decimal('333'),
        )
        response = self.client.get('/Dashboard-Profile/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context['total_food_income'], Decimal('333'))


class DashboardResilienceTests(TestCase):
    """Was: no try/except at all on this view, even though it's the
    landing page shown right after login. Any query failure crashed the
    whole app with a raw 500 instead of the friendly error page every
    other view in the codebase falls back to."""

    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='dash_resilience_staff', password='Correct@1234')
        self.client.post('/', {'username': 'dash_resilience_staff', 'password': 'Correct@1234'})

    def test_dashboard_loads_with_no_data(self):
        response = self.client.get('/Dashboard-Profile/')
        self.assertEqual(response.status_code, 200)
