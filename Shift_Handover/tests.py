from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from .models import Shift_Handover


class ShiftHandoverAddTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='staff_member', password='Correct@1234')
        self.client.post('/', {'username': 'staff_member', 'password': 'Correct@1234'})

    def test_amounts_are_recomputed_server_side_not_trusted_from_the_client(self):
        """The Add form marks the amount/total inputs readonly and
        computes them client-side in JS for display only — readonly is
        cosmetic, a raw POST can submit anything. The server must be the
        actual source of truth for quantity * denomination = amount."""
        response = self.client.post('/Shift-Handover-Add/', {
            'shift': 'Recompute Test',
            'five_hundred_quantity': '2', 'five_hundred_amount': '999999',
            'two_hundred_quantity': '3', 'two_hundred_amount': '1',
            'total': '1',
        })
        self.assertEqual(response.status_code, 302)
        record = Shift_Handover.objects.get(Shift_Handover_Shift='Recompute Test')
        self.assertEqual(record.Shift_Handover_Five_Hundred_Total, 1000)  # 2 * 500, not 999999
        self.assertEqual(record.Shift_Handover_Two_Hundred_Total, 600)    # 3 * 200, not 1
        self.assertEqual(record.Shift_Handover_Total, 1600)               # sum, not 1

    def test_record_always_attributed_to_the_real_logged_in_user(self):
        """The username field is readonly/pre-filled in the form but,
        again, readonly is cosmetic — a forged username in the POST body
        must not be able to attribute a shift handover to someone else."""
        other_user = User.objects.create_user(username='someone_else', password='Correct@1234')
        response = self.client.post('/Shift-Handover-Add/', {
            'shift': 'Impersonation Test', 'username': 'someone_else',
        })
        self.assertEqual(response.status_code, 302)
        record = Shift_Handover.objects.get(Shift_Handover_Shift='Impersonation Test')
        self.assertEqual(record.Shift_Handover_Username, self.staff)
        self.assertNotEqual(record.Shift_Handover_Username, other_user)

    def test_non_numeric_quantity_rejected_with_message_not_a_crash(self):
        response = self.client.post('/Shift-Handover-Add/', {
            'shift': 'Bad Qty', 'five_hundred_quantity': 'not-a-number',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'valid quantity')
        self.assertFalse(Shift_Handover.objects.filter(Shift_Handover_Shift='Bad Qty').exists())

    def test_negative_quantity_rejected(self):
        response = self.client.post('/Shift-Handover-Add/', {
            'shift': 'Negative Qty', 'five_hundred_quantity': '-5',
        }, follow=True)
        self.assertContains(response, 'cannot be negative')
        self.assertFalse(Shift_Handover.objects.filter(Shift_Handover_Shift='Negative Qty').exists())

    def test_coin_uses_face_value_one(self):
        response = self.client.post('/Shift-Handover-Add/', {
            'shift': 'Coin Test', 'coin_quantity': '75',
        })
        self.assertEqual(response.status_code, 302)
        record = Shift_Handover.objects.get(Shift_Handover_Shift='Coin Test')
        self.assertEqual(record.Shift_Handover_Coins_Total, 75)
        self.assertEqual(record.Shift_Handover_Total, 75)


class ShiftHandoverUpdatePermissionTests(TestCase):
    """The list page only shows the Update link/button to
    request.user.username == 'SuperAdmin' — previously the view itself
    had no permission check at all beyond @login_required, so any
    authenticated user could POST directly to this URL and rewrite
    another user's cash-count record. Confirmed directly before fixing."""

    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username='shift_owner', password='Correct@1234')
        self.superadmin = User.objects.create_user(username='SuperAdmin', password='Correct@1234', is_superuser=True)
        self.record = Shift_Handover.objects.create(
            Shift_Handover_Username=self.owner, Shift_Handover_Shift='Original', Shift_Handover_Total=0,
        )

    def _login(self, username):
        self.client.post('/', {'username': username, 'password': 'Correct@1234'})

    def test_non_admin_cannot_update_even_their_own_record(self):
        self._login('shift_owner')
        self.client.post(f'/Shift-Handover-Update/{self.record.id}/', {'shift': 'HACKED'})
        self.record.refresh_from_db()
        self.assertEqual(self.record.Shift_Handover_Shift, 'Original')

    def test_superadmin_can_update(self):
        self._login('SuperAdmin')
        response = self.client.post(f'/Shift-Handover-Update/{self.record.id}/', {
            'shift': 'Updated', 'ten_quantity': '4',
        })
        self.assertEqual(response.status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.Shift_Handover_Shift, 'Updated')
        self.assertEqual(self.record.Shift_Handover_Ten_Total, 40)

    def test_update_also_recomputes_totals_server_side(self):
        self._login('SuperAdmin')
        self.client.post(f'/Shift-Handover-Update/{self.record.id}/', {
            'shift': 'Original', 'fifty_quantity': '2', 'fifty_amount': '999999', 'total': '1',
        })
        self.record.refresh_from_db()
        self.assertEqual(self.record.Shift_Handover_Fifty_Total, 100)
        self.assertEqual(self.record.Shift_Handover_Total, 100)

    def test_get_on_update_shows_form_not_a_crash(self):
        self._login('SuperAdmin')
        response = self.client.get(f'/Shift-Handover-Update/{self.record.id}/')
        self.assertEqual(response.status_code, 200)


class ShiftHandoverDeleteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(username='shift_owner2', password='Correct@1234')
        self.other = User.objects.create_user(username='other_staff', password='Correct@1234')
        self.record = Shift_Handover.objects.create(Shift_Handover_Username=self.owner, Shift_Handover_Shift='Mine')

    def _login(self, username):
        self.client.post('/', {'username': username, 'password': 'Correct@1234'})

    def test_delete_via_get_does_not_crash_for_an_authorized_owner(self):
        """Previously: once the ownership/permission checks passed, a
        GET request fell through the function with no return statement
        at all — a hard 500, reproduced directly."""
        self._login('shift_owner2')
        response = self.client.get(f'/Shift-Handover-Delete/{self.record.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Shift_Handover.objects.filter(id=self.record.id).exists())

    def test_owner_can_delete_via_post(self):
        self._login('shift_owner2')
        response = self.client.post(f'/Shift-Handover-Delete/{self.record.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Shift_Handover.objects.filter(id=self.record.id).exists())

    def test_non_owner_non_admin_cannot_delete(self):
        self._login('other_staff')
        response = self.client.post(f'/Shift-Handover-Delete/{self.record.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Shift_Handover.objects.filter(id=self.record.id).exists())
