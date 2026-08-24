from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Sum
from django.test import TestCase

from .models import (
    Food_Cash_Miscellaneous_Expenses, Food_Cash_Withdrawal,
    Hotel_Cash_Miscellaneous_Expenses, Hotel_Cash_Withdrawal, Staff_Advance,
)
from Staff_Profile.models import User_Profile


class WithdrawalTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='withdraw_staff', password='Correct@1234')
        self.client.post('/', {'username': 'withdraw_staff', 'password': 'Correct@1234'})

    def test_sql_sum_correct_across_comma_and_plain_amounts(self):
        """Withdrawal_Hotel_Amount was CharField; Sum() over it silently
        miscomputed for comma-formatted values, same as Revenue's
        Deposite_Hotel_Amount bug. Now DecimalField."""
        self.client.post('/Hotel-Expense-Cash-Withdraw/', {
            'Hotel_withdrawal_date': '2026-08-24', 'Hotel_withdrawal_time': '10:00',
            'Hotel_withdrawal_withdrawer': 'A', 'Hotel_withdrawal_amount': '1,500',
        })
        self.client.post('/Hotel-Expense-Cash-Withdraw/', {
            'Hotel_withdrawal_date': '2026-08-24', 'Hotel_withdrawal_time': '11:00',
            'Hotel_withdrawal_withdrawer': 'B', 'Hotel_withdrawal_amount': '500',
        })
        total = Hotel_Cash_Withdrawal.objects.filter(Withdrawal_Hotel_Username=self.staff).aggregate(t=Sum('Withdrawal_Hotel_Amount'))['t']
        self.assertEqual(total, 2000)

    def test_withdrawal_attributed_to_real_user_not_forged_field(self):
        other = User.objects.create_user(username='withdraw_other', password='Correct@1234')
        self.client.post('/Hotel-Expense-Cash-Withdraw/', {
            'Hotel_withdrawal_date': '2026-08-24', 'Hotel_withdrawal_time': '10:00',
            'Hotel_withdrawal_username': 'withdraw_other',
            'Hotel_withdrawal_withdrawer': 'A', 'Hotel_withdrawal_amount': '100',
        })
        record = Hotel_Cash_Withdrawal.objects.get(Withdrawal_Hotel_Withdrawer='A')
        self.assertEqual(record.Withdrawal_Hotel_Username, self.staff)
        self.assertNotEqual(record.Withdrawal_Hotel_Username, other)

    def test_non_numeric_amount_rejected_not_a_crash(self):
        response = self.client.post('/Hotel-Expense-Cash-Withdraw/', {
            'Hotel_withdrawal_date': '2026-08-24', 'Hotel_withdrawal_time': '10:00',
            'Hotel_withdrawal_withdrawer': 'A', 'Hotel_withdrawal_amount': 'garbage',
        }, follow=True)
        self.assertContains(response, 'valid withdrawal amount')
        self.assertEqual(Hotel_Cash_Withdrawal.objects.filter(Withdrawal_Hotel_Username=self.staff).count(), 0)

    def test_food_withdrawal_same_fixes(self):
        response = self.client.post('/Food-Expense-Cash-Withdraw/', {
            'Food_withdrawal_date': '2026-08-24', 'Food_withdrawal_time': '10:00',
            'Food_withdrawal_withdrawer': 'A', 'Food_withdrawal_amount': '3,300',
        })
        self.assertEqual(response.status_code, 302)
        record = Food_Cash_Withdrawal.objects.get(Withdrawal_Food_Username=self.staff)
        self.assertEqual(record.Withdrawal_Food_Amount, 3300)


class WithdrawalDeleteOwnershipTests(TestCase):
    """Was: `hotel_cash_profile.Withdrawal_Hotel_Username != request.user.username`
    — a User instance compared to a plain string, never equal regardless
    of ownership. Confirmed the owner could never delete their own
    withdrawal before this fix."""

    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username='hotel_wd_owner', password='Correct@1234')
        self.other = User.objects.create_user(username='hotel_wd_other', password='Correct@1234')
        self.withdrawal = Hotel_Cash_Withdrawal.objects.create(
            Withdrawal_Hotel_Date='2026-08-24', Withdrawal_Hotel_Time='10:00',
            Withdrawal_Hotel_Username=self.owner, Withdrawal_Hotel_Withdrawer='Test',
            Withdrawal_Hotel_Amount=500, Withdrawal_Hotel_Amount_In_Words='Five Hundred',
        )

    def _login(self, username):
        self.client.post('/', {'username': username, 'password': 'Correct@1234'})

    def test_owner_can_now_delete_own_withdrawal(self):
        self._login('hotel_wd_owner')
        response = self.client.post(f'/Hotel-Expense-Cash-Delete/{self.withdrawal.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Hotel_Cash_Withdrawal.objects.filter(id=self.withdrawal.id).exists())

    def test_non_owner_still_blocked(self):
        self._login('hotel_wd_other')
        response = self.client.post(f'/Hotel-Expense-Cash-Delete/{self.withdrawal.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Hotel_Cash_Withdrawal.objects.filter(id=self.withdrawal.id).exists())

    def test_get_request_does_not_crash_or_delete(self):
        self._login('hotel_wd_owner')
        response = self.client.get(f'/Hotel-Expense-Cash-Delete/{self.withdrawal.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Hotel_Cash_Withdrawal.objects.filter(id=self.withdrawal.id).exists())


class MiscellaneousExpenseTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='misc_staff', password='Correct@1234')
        self.client.post('/', {'username': 'misc_staff', 'password': 'Correct@1234'})

    def test_add_and_delete_own_record(self):
        self.client.post('/Hotel-Cash-Miscellaneous-Expense/', {
            'hotel_Cash_miscellaneous_expense_date': '2026-08-24', 'hotel_Cash_miscellaneous_expense_time': '10:00',
            'hotel_Cash_miscellaneous_expense_name': 'Repairs', 'hotel_Cash_miscellaneous_expense_amount': '2,000',
        })
        record = Hotel_Cash_Miscellaneous_Expenses.objects.get(Miscellaneous_Expenses_Hotel_Username=self.staff)
        self.assertEqual(record.Miscellaneous_Expenses_Hotel_Amount, 2000)

        response = self.client.post(f'/Hotel-Cash-Miscellaneous-Expense-Delete/{record.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Hotel_Cash_Miscellaneous_Expenses.objects.filter(id=record.id).exists())

    def test_update_with_decimal_amount_does_not_crash(self):
        """Update used int(amount_string) directly, which raises
        ValueError for a decimal string ('500.50') — the Add view used
        int(float(amount_string)) instead. Confirmed directly:
        int('500.50') crashes. Both paths now go through the same
        _parse_amount() helper, which returns a Decimal."""
        self.client.post('/Hotel-Cash-Miscellaneous-Expense/', {
            'hotel_Cash_miscellaneous_expense_date': '2026-08-24', 'hotel_Cash_miscellaneous_expense_time': '10:00',
            'hotel_Cash_miscellaneous_expense_name': 'Original', 'hotel_Cash_miscellaneous_expense_amount': '500',
        })
        record = Hotel_Cash_Miscellaneous_Expenses.objects.get(Miscellaneous_Expenses_Hotel_Username=self.staff)

        response = self.client.post(f'/Hotel-Cash-Miscellaneous-Expense-Update/{record.id}/', {
            'hotel_Cash_miscellaneous_expense_date': '2026-08-24', 'hotel_Cash_miscellaneous_expense_time': '10:00',
            'hotel_Cash_miscellaneous_expense_name': 'Updated', 'hotel_Cash_miscellaneous_expense_amount': '500.50',
        })
        self.assertEqual(response.status_code, 302)
        record.refresh_from_db()
        self.assertEqual(str(record.Miscellaneous_Expenses_Hotel_Amount), '500.50')

    def test_food_misc_expense_same_fixes(self):
        response = self.client.post('/Food-Cash-Miscellaneous-Expense/', {
            'food_Cash_miscellaneous_expense_date': '2026-08-24', 'food_Cash_miscellaneous_expense_time': '10:00',
            'food_Cash_miscellaneous_expense_name': 'Vegetables', 'food_Cash_miscellaneous_expense_amount': '1,200',
        })
        self.assertEqual(response.status_code, 302)
        record = Food_Cash_Miscellaneous_Expenses.objects.get(Miscellaneous_Expenses_Food_Username=self.staff)
        self.assertEqual(record.Miscellaneous_Expenses_Food_Amount, 1200)


class StaffAdvanceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='advance_staff', password='Correct@1234')
        self.client.post('/', {'username': 'advance_staff', 'password': 'Correct@1234'})
        self.profile = User_Profile.objects.create(User_Full_Name='Advance Recipient', is_active=True)

    def test_add_advance_and_delete_own_record(self):
        self.client.post('/Staff-Advance-Salaries/', {
            'staff_advance__date': '2026-08-24', 'staff_advance__time': '10:00',
            'staff_advance_year_month': '2026 - August', 'staff_advance_name': self.profile.id,
            'advance_amount': '1,000', 'staff_advance_instruction': 'test',
        })
        record = Staff_Advance.objects.get(Staff_Advance_username=self.staff)
        self.assertEqual(record.Staff_Advance_amount, 1000)

        response = self.client.post(f'/Staff-Advance-Salaries-Delete/{record.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Staff_Advance.objects.filter(id=record.id).exists())

    def test_delete_ownership_bug_fixed(self):
        """Was: `staffadvance.Staff_Advance_username != request.user.username`
        — same User-vs-string comparison bug as every other Delete view
        in this app."""
        other_owner = User.objects.create_user(username='advance_owner2', password='Correct@1234')
        record = Staff_Advance.objects.create(
            Staff_Advance_date='2026-08-24', Staff_Advance_time='10:00',
            Staff_Advance_username=other_owner, Staff_Advance_year_month='2026 - August',
            Staff_Advance_amount=500, Staff_Advance_Amount_In_Words='Five Hundred',
        )
        self.client.post('/', {'username': 'advance_owner2', 'password': 'Correct@1234'})
        response = self.client.post(f'/Staff-Advance-Salaries-Delete/{record.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Staff_Advance.objects.filter(id=record.id).exists())
