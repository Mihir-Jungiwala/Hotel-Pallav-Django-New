from decimal import Decimal

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from .models import Bill_Master_ADD_Advance, Bill_Master_ADD_Bill


class AdvanceAddUpdateTotalTests(TestCase):
    """Was: `total` read directly from the client-submitted 'total' field
    on both Add and Update, so a stale or forged value could be stored.
    Now always recomputed as hotel_advance_amount + food_advance_amount."""

    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='bm_staff', password='Correct@1234')
        self.client.post('/', {'username': 'bm_staff', 'password': 'Correct@1234'})

    def test_add_recomputes_total_server_side(self):
        self.client.post('/Bill-Master-Advance-Add/', {
            'advance_Receipt_Number': 'T1', 'advance_Guest_Name': 'Guest',
            'advance_Mobile_Number': '9999999999', 'advance_Payment_Date': '2026-08-24',
            'hotel_advance_amount': '1000', 'hotel_advance_mod': 'Cash',
            'food_advance_amount': '500', 'food_advance_mod': 'Cash',
            'total': '999999',
        })
        adv = Bill_Master_ADD_Advance.objects.get(Advance_Receipt_Number__contains='T1')
        self.assertEqual(adv.Total, Decimal('1500.00'))

    def test_update_recomputes_total_server_side(self):
        adv = Bill_Master_ADD_Advance.objects.create(
            Advance_Receipt_Number='T2', Advance_Guest_Name='Guest',
            Hotel_Advance_Amount=Decimal('100'), Food_Advance_Amount=Decimal('100'),
            Hotel_Balance_Amount=Decimal('100'), Food_Balance_Amount=Decimal('100'), Total=Decimal('200'),
        )
        self.client.post(f'/Bill-Master-Advance-Update/{adv.id}/', {
            'advance_Guest_Name': 'Guest', 'advance_Mobile_Number': '9999999999',
            'advance_Payment_Date': '2026-08-24', 'hotel_advance_amount': '2000',
            'hotel_advance_mod': 'Cash', 'food_advance_amount': '700', 'food_advance_mod': 'Cash',
            'total': '1',
        })
        adv.refresh_from_db()
        self.assertEqual(adv.Total, Decimal('2700.00'))

    def test_negative_advance_amount_rejected(self):
        response = self.client.post('/Bill-Master-Advance-Add/', {
            'advance_Receipt_Number': 'T3', 'advance_Guest_Name': 'Guest',
            'hotel_advance_amount': '-100', 'food_advance_amount': '0',
        }, follow=True)
        self.assertContains(response, 'cannot be negative')
        self.assertFalse(Bill_Master_ADD_Advance.objects.filter(Advance_Receipt_Number__contains='T3').exists())


class AdvanceDeleteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='bm_del_staff', password='Correct@1234')
        self.client.post('/', {'username': 'bm_del_staff', 'password': 'Correct@1234'})

    def test_get_request_does_not_crash(self):
        """Was: no non-POST branch at all, so a GET request fell through
        with an implicit `return None`, which Django turns into a hard
        ValueError."""
        adv = Bill_Master_ADD_Advance.objects.create(
            Advance_Receipt_Number='D1', Hotel_Advance_Amount=Decimal('0'),
            Food_Advance_Amount=Decimal('0'), Hotel_Balance_Amount=Decimal('0'),
            Food_Balance_Amount=Decimal('0'),
        )
        response = self.client.get(f'/Bill-Master-Advance-Delete/{adv.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Bill_Master_ADD_Advance.objects.filter(id=adv.id).exists())


class AdvanceRefundTests(TestCase):
    """Was: bill_master.Total set directly from the client-submitted
    'refund_total_amount' field. Now derived from the balance amounts
    actually being saved, matching the convention used elsewhere in this
    app (e.g. Bill_Master_Bill_Add's advance_record.Total)."""

    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='bm_refund_staff', password='Correct@1234')
        self.client.post('/', {'username': 'bm_refund_staff', 'password': 'Correct@1234'})
        self.adv = Bill_Master_ADD_Advance.objects.create(
            Advance_Receipt_Number='R1', Advance_Guest_Name='Guest',
            Hotel_Advance_Amount=Decimal('1000'), Food_Advance_Amount=Decimal('500'),
            Hotel_Balance_Amount=Decimal('1000'), Food_Balance_Amount=Decimal('500'), Total=Decimal('1500'),
        )

    def test_total_recomputed_from_balances_not_trusted_from_client(self):
        self.client.post(f'/Bill-Master-Advance-Refund/{self.adv.id}/', {
            'refund_Payment_Date': '2026-08-24', 'hotel_refund_amount': '200',
            'refund_hotel_mod': 'Cash', 'food_refund_amount': '100', 'refund_food_mod': 'Cash',
            'refund_guest_name': 'Guest', 'refund_Mobile_Number': '9999999999',
            'refund_total_amount': '999999',
        })
        self.adv.refresh_from_db()
        self.assertEqual(self.adv.Total, Decimal('1200.00'))
        self.assertEqual(self.adv.Hotel_Balance_Amount, Decimal('800.00'))
        self.assertEqual(self.adv.Food_Balance_Amount, Decimal('400.00'))

    def test_negative_refund_amount_rejected(self):
        response = self.client.post(f'/Bill-Master-Advance-Refund/{self.adv.id}/', {
            'refund_Payment_Date': '2026-08-24', 'hotel_refund_amount': '-50',
            'food_refund_amount': '0',
        }, follow=True)
        self.assertContains(response, 'cannot be negative')
        self.adv.refresh_from_db()
        self.assertIsNone(self.adv.Refund_Payment_Date)


class BillAddCalculationTests(TestCase):
    """Was: `advance_food_balance_amount = food_advance_amount -
    abs(bill_master_hotel_total_amount)` — a copy-paste bug that subtracted
    the HOTEL total from the food advance amount instead of the FOOD total.
    Confirmed by reading the code (matched the production-readiness audit's
    flagged bug) and reproduced here: with different hotel/food totals, the
    food balance must be computed purely from food-side numbers."""

    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='bm_add_staff', password='Correct@1234')
        self.client.post('/', {'username': 'bm_add_staff', 'password': 'Correct@1234'})

    def test_food_advance_balance_uses_food_total_not_hotel_total(self):
        self.client.post('/Bill-Master-Bill-Add/', {
            'bill_Number': 'B1', 'bill_date': '2026-08-24',
            'bill_master_Guest_Name': 'Guest', 'bill_master_Mobile_Number': '9999999999',
            'Plan': 'EP',
            'bill_master_hotel_amount': '0', 'bill_master_hotel_plan_amount': '0',
            'bill_master_hotel_laundry_amount': '0', 'bill_master_hotel_gst': '0',
            'bill_master_hotel_mod': 'Cash', 'bill_master_hotel_total_amount': '100',
            'bill_master_food_amount': '0', 'bill_master_food_plan_amount': '0',
            'bill_master_food_laundry_amount': '0', 'bill_master_food_gst': '0',
            'bill_master_food_mod': 'Cash', 'bill_master_food_total_amount': '50',
            'hotel_advance_amount': '2000', 'food_advance_amount': '700',
        })
        bill = Bill_Master_ADD_Bill.objects.get(Bill_Master_Bill_Number__contains='B1')
        self.assertEqual(bill.Bill_Master_Advance_Food_Amount, Decimal('650.00'))
        self.assertEqual(bill.Bill_Master_Advance_Hotel_Amount, Decimal('1900.00'))


class BillUpdateCalculationTests(TestCase):
    """Was: `Bill_Master_Balance_Food_Amount` decided by
    `bill_master_hotel_mod == 'Debit'` instead of `bill_master_food_mod`
    — a copy-paste bug that made the food balance track the HOTEL mode of
    payment."""

    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='bm_upd_staff', password='Correct@1234')
        self.client.post('/', {'username': 'bm_upd_staff', 'password': 'Correct@1234'})
        self.bill = Bill_Master_ADD_Bill.objects.create(Bill_Master_Bill_Number='U1')

    def test_food_balance_driven_by_food_mod_not_hotel_mod(self):
        self.client.post(f'/Bill-Master-Bill-Update/{self.bill.id}/', {
            'bill_date': '2026-08-24', 'bill_master_Guest_Name': 'Guest',
            'bill_master_Mobile_Number': '9999999999', 'Plan': 'EP',
            'bill_master_hotel_amount': '0', 'bill_master_hotel_plan_amount': '0',
            'bill_master_hotel_laundry_amount': '0', 'bill_master_hotel_gst': '0',
            'bill_master_hotel_mod': 'Debit',
            'bill_master_food_amount': '0', 'bill_master_food_plan_amount': '0',
            'bill_master_food_laundry_amount': '0', 'bill_master_food_gst': '0',
            'bill_master_food_mod': 'Cash',
            'bill_master_hotel_total_amount': '100', 'bill_master_food_total_amount': '50',
        })
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.Bill_Master_Balance_Hotel_Amount, Decimal('100.00'))
        self.assertEqual(self.bill.Bill_Master_Balance_Food_Amount, Decimal('0.00'))


class BillDeleteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='bm_bdel_staff', password='Correct@1234')
        self.client.post('/', {'username': 'bm_bdel_staff', 'password': 'Correct@1234'})

    def test_get_request_does_not_crash(self):
        """Was: no non-POST branch at all, so a GET request fell through
        with an implicit `return None`."""
        bill = Bill_Master_ADD_Bill.objects.create(Bill_Master_Bill_Number='D1')
        response = self.client.get(f'/Bill-Master-Bill-Delete/{bill.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Bill_Master_ADD_Bill.objects.filter(id=bill.id).exists())

    def test_null_advance_delete_amount_does_not_crash(self):
        """Was: `Decimal(bill_delete.Bill_Master_Advance_Delete_Hotel_Amount)`
        with no guard — the field is nullable, so a None value would raise
        decimal.InvalidOperation/TypeError. Now guarded with `or 0`."""
        bill = Bill_Master_ADD_Bill.objects.create(
            Bill_Master_Bill_Number='D2',
            Bill_Master_Advance_Delete_Hotel_Amount=None,
            Bill_Master_Advance_Delete_Food_Amount=None,
        )
        response = self.client.post(f'/Bill-Master-Bill-Delete/{bill.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Bill_Master_ADD_Bill.objects.filter(id=bill.id).exists())


class DebitBillAddInstallmentTests(TestCase):
    """Was: every `_1`..`_4` installment field's guard checked the
    truthiness of the base (unsuffixed) amount field instead of its own
    field, e.g. the 3rd hotel installment's guard read
    `request.POST.get('bill_master_debit_hotel_amount', '')`. If the first
    installment was left blank while a later one had a real value, that
    value was silently discarded and stored as 0. Confirmed across all
    four hotel and all four food installments; fixed identically."""

    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='bm_debit_staff', password='Correct@1234')
        self.client.post('/', {'username': 'bm_debit_staff', 'password': 'Correct@1234'})
        self.bill = Bill_Master_ADD_Bill.objects.create(
            Bill_Master_Bill_Number='DB1',
            Bill_Master_Hotel_Mode_Of_Payment='Debit', Bill_Master_Food_Mode_Of_Payment='Debit',
            Bill_Master_Total_Hotel_Amount=Decimal('1000'), Bill_Master_Total_Food_Amount=Decimal('500'),
        )

    def test_later_installment_saved_even_when_first_is_blank(self):
        self.client.post(f'/Bill-Master-Debit-Bill-Add/{self.bill.id}/', {
            'debit_bill_date': '2026-08-24',
            'bill_master_debit_hotel_amount_3': '250',
            'bill_master_debit_hotel_mod_3': 'Cash',
            'bill_master_debit_food_amount_2': '150',
            'bill_master_debit_food_mod_2': 'Cash',
            'bill_Number': 'DB1',
            'bill_master_hotel_remaining_balance': '0', 'bill_master_food_remaining_balance': '0',
        })
        self.bill.refresh_from_db()
        self.assertEqual(self.bill.Bill_Master_Debit_Hotel_Amount_3, Decimal('250.00'))
        self.assertEqual(self.bill.Bill_Master_Debit_Food_Amount_2, Decimal('150.00'))
