from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Sum
from django.test import TestCase

from .models import Hotel_Cash_Deposite, Food_Cash_Deposite


class RevenueDepositTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='deposit_staff', password='Correct@1234')
        self.client.post('/', {'username': 'deposit_staff', 'password': 'Correct@1234'})

    def test_comma_formatted_amount_accepted_and_stored_clean(self):
        response = self.client.post('/Hotel-Revenue-Cash-Deposite/', {
            'hotel_deposite_date': '2026-08-24', 'hotel_deposite_time': '10:00',
            'hotel_deposite_depositer': 'Mr.Kishore Fichadiya', 'hotel_deposite_amount': '1,500',
        })
        self.assertEqual(response.status_code, 302)
        record = Hotel_Cash_Deposite.objects.get(Deposite_Hotel_Username=self.staff)
        self.assertEqual(record.Deposite_Hotel_Amount, 1500)

    def test_sql_sum_is_correct_across_mixed_formats(self):
        """Deposite_Hotel_Amount was a CharField; Sum() over it silently
        miscomputed whenever a value contained a comma (SQLite parses
        only the numeric prefix before the comma). Confirmed directly:
        Sum('1,500', '500') returned 501, not 2000. Now a DecimalField,
        so the same query is arithmetically correct by construction."""
        self.client.post('/Hotel-Revenue-Cash-Deposite/', {
            'hotel_deposite_date': '2026-08-24', 'hotel_deposite_time': '10:00', 'hotel_deposite_depositer': 'A', 'hotel_deposite_amount': '1,500',
        })
        self.client.post('/Hotel-Revenue-Cash-Deposite/', {
            'hotel_deposite_date': '2026-08-24', 'hotel_deposite_time': '11:00', 'hotel_deposite_depositer': 'B', 'hotel_deposite_amount': '500',
        })
        total = Hotel_Cash_Deposite.objects.filter(Deposite_Hotel_Username=self.staff).aggregate(t=Sum('Deposite_Hotel_Amount'))['t']
        self.assertEqual(total, 2000)

    def test_deposit_always_attributed_to_the_real_logged_in_user(self):
        other = User.objects.create_user(username='deposit_other', password='Correct@1234')
        self.client.post('/Hotel-Revenue-Cash-Deposite/', {
            'hotel_deposite_date': '2026-08-24', 'hotel_deposite_time': '10:00', 'hotel_deposite_username': 'deposit_other',
            'hotel_deposite_depositer': 'A', 'hotel_deposite_amount': '100',
        })
        record = Hotel_Cash_Deposite.objects.get(Deposite_Hotel_Withdrawer='A')
        self.assertEqual(record.Deposite_Hotel_Username, self.staff)
        self.assertNotEqual(record.Deposite_Hotel_Username, other)

    def test_non_numeric_amount_rejected_not_a_crash(self):
        response = self.client.post('/Hotel-Revenue-Cash-Deposite/', {
            'hotel_deposite_date': '2026-08-24', 'hotel_deposite_depositer': 'A', 'hotel_deposite_amount': 'garbage',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'valid deposit amount')
        self.assertFalse(Hotel_Cash_Deposite.objects.filter(Deposite_Hotel_Username=self.staff).exists())

    def test_blank_time_rejected_not_a_crash(self):
        """Deposite_Hotel_Time is a non-nullable TimeField; a blank time
        previously reached .save() and raised a raw ValidationError.
        Confirmed directly: Hotel_Cash_Deposite.objects.create(...,
        Deposite_Hotel_Time='') crashes. The form auto-fills this via JS
        so it's normally unreachable, but a direct POST must still be
        handled gracefully."""
        response = self.client.post('/Hotel-Revenue-Cash-Deposite/', {
            'hotel_deposite_date': '2026-08-24', 'hotel_deposite_depositer': 'A', 'hotel_deposite_amount': '500',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'valid time')
        self.assertFalse(Hotel_Cash_Deposite.objects.filter(Deposite_Hotel_Username=self.staff).exists())

    def test_negative_amount_rejected(self):
        response = self.client.post('/Hotel-Revenue-Cash-Deposite/', {
            'hotel_deposite_date': '2026-08-24', 'hotel_deposite_depositer': 'A', 'hotel_deposite_amount': '-500',
        }, follow=True)
        self.assertContains(response, 'valid deposit amount')
        self.assertFalse(Hotel_Cash_Deposite.objects.filter(Deposite_Hotel_Username=self.staff).exists())

    def test_food_deposit_same_fixes_apply(self):
        response = self.client.post('/Food-Revenue-Cash-Deposite/', {
            'food_deposite_date': '2026-08-24', 'food_deposite_time': '10:00', 'food_deposite_depositer': 'A', 'food_deposite_amount': '2,200',
        })
        self.assertEqual(response.status_code, 302)
        record = Food_Cash_Deposite.objects.get(Deposite_Food_Username=self.staff)
        self.assertEqual(record.Deposite_Food_Amount, 2200)


class RevenueDeleteOwnershipTests(TestCase):
    """Was: `hotel_cash_profile.Deposite_Hotel_Username != request.user.username`
    — comparing a User instance to a plain string, which is never equal
    regardless of actual ownership, so the true owner of a deposit could
    never delete their own record. Confirmed directly before fixing."""

    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username='hotel_dep_owner', password='Correct@1234')
        self.other = User.objects.create_user(username='hotel_dep_other', password='Correct@1234')
        self.superadmin = User.objects.create_user(username='SuperAdmin', password='Correct@1234', is_superuser=True)
        self.deposit = Hotel_Cash_Deposite.objects.create(
            Deposite_Hotel_Date='2026-08-24', Deposite_Hotel_Time='10:00',
            Deposite_Hotel_Username=self.owner, Deposite_Hotel_Withdrawer='Test', Deposite_Hotel_Amount=500,
            Deposite_Hotel_Amount_In_Words='Five Hundred',
        )

    def _login(self, username):
        self.client.post('/', {'username': username, 'password': 'Correct@1234'})

    def test_owner_can_now_delete_their_own_deposit(self):
        self._login('hotel_dep_owner')
        response = self.client.post(f'/Hotel-Revenue-Cash-Delete/{self.deposit.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Hotel_Cash_Deposite.objects.filter(id=self.deposit.id).exists())

    def test_non_owner_non_admin_still_blocked(self):
        self._login('hotel_dep_other')
        response = self.client.post(f'/Hotel-Revenue-Cash-Delete/{self.deposit.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Hotel_Cash_Deposite.objects.filter(id=self.deposit.id).exists())

    def test_superadmin_can_delete_anyone_s_deposit(self):
        self._login('SuperAdmin')
        response = self.client.post(f'/Hotel-Revenue-Cash-Delete/{self.deposit.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Hotel_Cash_Deposite.objects.filter(id=self.deposit.id).exists())

    def test_get_request_does_not_crash_and_does_not_delete(self):
        self._login('hotel_dep_owner')
        response = self.client.get(f'/Hotel-Revenue-Cash-Delete/{self.deposit.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Hotel_Cash_Deposite.objects.filter(id=self.deposit.id).exists())
