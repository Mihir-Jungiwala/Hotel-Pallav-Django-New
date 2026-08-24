from datetime import timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from .models import Authentication


class LoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='alice', password='Correct@1234')

    def test_valid_login_redirects_to_dashboard_and_creates_session_row(self):
        response = self.client.post('/', {'username': 'alice', 'password': 'Correct@1234'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/Dashboard-Profile/')

        record = Authentication.objects.filter(user=self.user).order_by('-id').first()
        self.assertIsNotNone(record)
        self.assertEqual(record.session_key, self.client.session.session_key)

    def test_invalid_password_rejected(self):
        response = self.client.post('/', {'username': 'alice', 'password': 'wrong'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_missing_credentials_rejected_without_500(self):
        response = self.client.post('/', {'username': '', 'password': ''})
        self.assertEqual(response.status_code, 302)

    def test_lockout_after_repeated_failures(self):
        for _ in range(5):
            self.client.post('/', {'username': 'alice', 'password': 'wrong'})

        # Even the correct password is now rejected until the lockout window passes.
        response = self.client.post('/', {'username': 'alice', 'password': 'Correct@1234'}, follow=True)
        self.assertContains(response, 'Too many failed login attempts')

    def test_deactivated_account_cannot_log_in(self):
        # Django's authenticate() rejects a deactivated user by returning
        # None, indistinguishable from a wrong password — intentionally:
        # no "your account is disabled" oracle for an attacker probing
        # usernames. So this looks exactly like any other failed login.
        self.user.is_active = False
        self.user.save()
        response = self.client.post('/', {'username': 'alice', 'password': 'Correct@1234'}, follow=True)
        self.assertContains(response, 'Invalid Username or Invalid Password')
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class AdminPermissionTests(TestCase):
    """Every one of these previously had no server-side permission check
    at all — only the template hid the button/link for non-admins. See
    docs/backend-hardening-log.md."""

    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user(username='admin_user', password='Correct@1234', is_superuser=True)
        self.viewer = User.objects.create_user(username='viewer_user', password='Correct@1234')
        self.target = User.objects.create_user(username='target_user', password='Correct@1234')
        self.superadmin = User.objects.create_user(username='SuperAdmin', password='Correct@1234', is_superuser=True)

    def _login(self, username):
        self.client.post('/', {'username': username, 'password': 'Correct@1234'})

    def test_viewer_cannot_view_user_roster(self):
        self._login('viewer_user')
        response = self.client.get('/Registration-User-Profile/')
        self.assertEqual(response.status_code, 302)

    def test_admin_can_view_user_roster(self):
        self._login('admin_user')
        response = self.client.get('/Registration-User-Profile/')
        self.assertEqual(response.status_code, 200)

    def test_viewer_cannot_register_new_user(self):
        self._login('viewer_user')
        self.client.post('/User-Registration/', {
            'first_name': 'x', 'last_name': 'y', 'username': 'new_sneaky_user',
            'password': 'Correct@1234', 'confirm_password': 'Correct@1234',
            'email': 'x@example.com', 'role': 'Viewer',
        })
        self.assertFalse(User.objects.filter(username='new_sneaky_user').exists())

    def test_viewer_cannot_self_promote_via_update_role(self):
        self._login('viewer_user')
        self.client.post(f'/Update-User-Role/{self.viewer.id}/', {'role': 'Admin'})
        self.viewer.refresh_from_db()
        self.assertFalse(self.viewer.is_superuser)

    def test_admin_can_change_another_users_role(self):
        self._login('admin_user')
        self.client.post(f'/Update-User-Role/{self.target.id}/', {'role': 'Admin'})
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_superuser)

    def test_invalid_role_value_rejected(self):
        self._login('admin_user')
        self.client.post(f'/Update-User-Role/{self.target.id}/', {'role': 'Nonsense'})
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_superuser)
        self.assertFalse(self.target.is_staff)

    def test_viewer_cannot_deactivate_users(self):
        self._login('viewer_user')
        self.client.post(f'/User-Active-Deactive-Status/{self.target.id}/')
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_viewer_cannot_delete_users(self):
        self._login('viewer_user')
        self.client.post(f'/Delete-User-Profile/{self.target.id}/')
        self.assertTrue(User.objects.filter(id=self.target.id).exists())

    def test_delete_requires_post(self):
        self._login('admin_user')
        self.client.get(f'/Delete-User-Profile/{self.target.id}/')
        self.assertTrue(User.objects.filter(id=self.target.id).exists())

    def test_superadmin_cannot_be_deleted_even_by_admin(self):
        self._login('admin_user')
        self.client.post(f'/Delete-User-Profile/{self.superadmin.id}/')
        self.assertTrue(User.objects.filter(username='SuperAdmin').exists())

    def test_superadmin_role_cannot_be_changed(self):
        self._login('admin_user')
        self.client.post(f'/Update-User-Role/{self.superadmin.id}/', {'role': 'Viewer'})
        self.superadmin.refresh_from_db()
        self.assertTrue(self.superadmin.is_superuser)

    def test_superadmin_cannot_be_deactivated(self):
        self._login('admin_user')
        self.client.post(f'/User-Active-Deactive-Status/{self.superadmin.id}/')
        self.superadmin.refresh_from_db()
        self.assertTrue(self.superadmin.is_active)


class RegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user(username='admin_user', password='Correct@1234', is_superuser=True)
        self.client.post('/', {'username': 'admin_user', 'password': 'Correct@1234'})

    def test_duplicate_username_rejected_with_visible_message(self):
        response = self.client.post('/User-Registration/', {
            'first_name': 'a', 'last_name': 'b', 'username': 'admin_user',
            'password': 'Another@1234', 'confirm_password': 'Another@1234',
            'email': 'dup@example.com', 'role': 'Viewer',
        }, follow=True)
        self.assertContains(response, 'already taken')
        self.assertEqual(User.objects.filter(username='admin_user').count(), 1)

    def test_weak_password_rejected_with_visible_message(self):
        response = self.client.post('/User-Registration/', {
            'first_name': 'a', 'last_name': 'b', 'username': 'weakpass_user',
            'password': 'weak', 'confirm_password': 'weak',
            'email': 'weak@example.com', 'role': 'Viewer',
        }, follow=True)
        self.assertContains(response, 'Password must be at least 8 characters')
        self.assertFalse(User.objects.filter(username='weakpass_user').exists())

    def test_mismatched_passwords_rejected(self):
        response = self.client.post('/User-Registration/', {
            'first_name': 'a', 'last_name': 'b', 'username': 'mismatch_user',
            'password': 'Correct@1234', 'confirm_password': 'Different@1234',
            'email': 'mismatch@example.com', 'role': 'Viewer',
        }, follow=True)
        self.assertContains(response, 'do not match')
        self.assertFalse(User.objects.filter(username='mismatch_user').exists())

    def test_valid_registration_succeeds(self):
        response = self.client.post('/User-Registration/', {
            'first_name': 'New', 'last_name': 'User', 'username': 'brand_new_user',
            'password': 'Correct@1234', 'confirm_password': 'Correct@1234',
            'email': 'new@example.com', 'role': 'Editor',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='brand_new_user')
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)


class PasswordResetTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='reset_user', password='Old@1234', email='reset@example.com',
        )

    def test_reset_request_for_unknown_username_shows_generic_success(self):
        """Guards against username enumeration: an unknown username gets
        the exact same response as a real one."""
        response = self.client.post('/Reset-Password/', {'username': 'does_not_exist'}, follow=True)
        self.assertContains(response, "If an account matches")

    def test_reset_request_for_known_username_shows_same_generic_success(self):
        response = self.client.post('/Reset-Password/', {'username': 'reset_user'}, follow=True)
        self.assertContains(response, "If an account matches")

    def test_reset_creates_usable_token_for_known_user(self):
        self.client.post('/Reset-Password/', {'username': 'reset_user'})
        record = Authentication.objects.filter(user=self.user).exclude(forgot_password_token__isnull=True).first()
        self.assertIsNotNone(record)
        self.assertFalse(record.token_used)

    def test_change_password_with_valid_token_succeeds(self):
        self.client.post('/Reset-Password/', {'username': 'reset_user'})
        record = Authentication.objects.filter(user=self.user).exclude(forgot_password_token__isnull=True).first()

        response = self.client.post(f'/Change-Password/{record.forgot_password_token}/', {
            'new_password': 'BrandNew@1234', 'confirm_password': 'BrandNew@1234',
        })
        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('BrandNew@1234'))

        record.refresh_from_db()
        self.assertTrue(record.token_used)

    def test_change_password_token_cannot_be_reused(self):
        self.client.post('/Reset-Password/', {'username': 'reset_user'})
        record = Authentication.objects.filter(user=self.user).exclude(forgot_password_token__isnull=True).first()

        self.client.post(f'/Change-Password/{record.forgot_password_token}/', {
            'new_password': 'BrandNew@1234', 'confirm_password': 'BrandNew@1234',
        })
        response = self.client.post(f'/Change-Password/{record.forgot_password_token}/', {
            'new_password': 'AnotherOne@1234', 'confirm_password': 'AnotherOne@1234',
        }, follow=True)
        self.assertContains(response, 'already been used')

    def test_change_password_expired_token_rejected(self):
        self.client.post('/Reset-Password/', {'username': 'reset_user'})
        record = Authentication.objects.filter(user=self.user).exclude(forgot_password_token__isnull=True).first()
        record.email_sent_time = timezone.now() - timedelta(minutes=11)
        record.save()

        response = self.client.post(f'/Change-Password/{record.forgot_password_token}/', {
            'new_password': 'BrandNew@1234', 'confirm_password': 'BrandNew@1234',
        }, follow=True)
        self.assertContains(response, 'expired')

    def test_change_password_invalid_token_rejected(self):
        response = self.client.post('/Change-Password/not-a-real-token/', {
            'new_password': 'BrandNew@1234', 'confirm_password': 'BrandNew@1234',
        }, follow=True)
        self.assertContains(response, 'Invalid or expired token')


class AutoLogoutMiddlewareTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='idle_user', password='Correct@1234')

    def test_idle_session_beyond_timeout_gets_logged_out(self):
        self.client.post('/', {'username': 'idle_user', 'password': 'Correct@1234'})
        record = Authentication.objects.filter(user=self.user).order_by('-id').first()
        record.activity_time = timezone.now() - timedelta(minutes=15)
        record.save()

        response = self.client.get('/Dashboard-Profile/', follow=True)
        self.assertRedirects(response, '/')  # bounced to Login.html, not the dashboard

    def test_active_session_within_timeout_stays_logged_in(self):
        self.client.post('/', {'username': 'idle_user', 'password': 'Correct@1234'})
        response = self.client.get('/Dashboard-Profile/')
        self.assertEqual(response.status_code, 200)

    def test_two_concurrent_sessions_for_same_user_time_out_independently(self):
        """This is the exact bug found while testing this pass: before
        session_key tracking, checking session A's idle time could read
        session B's (fresher) activity_time and never time out A."""
        client_a = self.client_class()
        client_b = self.client_class()

        client_a.post('/', {'username': 'idle_user', 'password': 'Correct@1234'})
        client_b.post('/', {'username': 'idle_user', 'password': 'Correct@1234'})

        record_a = Authentication.objects.get(session_key=client_a.session.session_key)
        record_a.activity_time = timezone.now() - timedelta(minutes=15)
        record_a.save()

        # Session B stays fresh/active.
        response_b = client_b.get('/Dashboard-Profile/')
        self.assertEqual(response_b.status_code, 200)

        # Session A must time out despite B being active — this is what
        # the old "most recent row for this user" lookup got wrong.
        response_a = client_a.get('/Dashboard-Profile/', follow=True)
        self.assertRedirects(response_a, '/')
