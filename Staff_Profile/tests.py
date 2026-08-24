from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import User_Profile

FAKE_JPEG = b'\xff\xd8\xff\xe0fakejpegbytes'


class StaffRegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username='staff', password='Correct@1234')
        self.client.post('/', {'username': 'staff', 'password': 'Correct@1234'})

    def test_valid_registration_creates_profile(self):
        response = self.client.post('/Staff--Profile-Registration/', {
            'full_name': 'Jane Doe', 'salary': '25000',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User_Profile.objects.filter(User_Full_Name='Jane Doe').exists())

    def test_missing_name_rejected(self):
        response = self.client.post('/Staff--Profile-Registration/', {'salary': '25000'}, follow=True)
        self.assertContains(response, 'required')
        self.assertEqual(User_Profile.objects.count(), 0)

    def test_non_numeric_salary_rejected_not_a_crash(self):
        """Previously: User_Salary=IntegerField, and the view passed the
        raw POST string straight through — a non-numeric value raised
        ValueError at .save() time, an unhandled 500."""
        response = self.client.post('/Staff--Profile-Registration/', {
            'full_name': 'Bad Salary Person', 'salary': 'not-a-number',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'valid salary')
        self.assertFalse(User_Profile.objects.filter(User_Full_Name='Bad Salary Person').exists())

    def test_negative_salary_rejected(self):
        response = self.client.post('/Staff--Profile-Registration/', {
            'full_name': 'Negative Salary Person', 'salary': '-500',
        }, follow=True)
        self.assertContains(response, 'cannot be negative')
        self.assertFalse(User_Profile.objects.filter(User_Full_Name='Negative Salary Person').exists())

    def test_blank_salary_defaults_to_zero(self):
        response = self.client.post('/Staff--Profile-Registration/', {
            'full_name': 'No Salary Person', 'salary': '',
        })
        self.assertEqual(response.status_code, 302)
        profile = User_Profile.objects.get(User_Full_Name='No Salary Person')
        self.assertEqual(profile.User_Salary, 0)

    def test_invalid_email_rejected(self):
        response = self.client.post('/Staff--Profile-Registration/', {
            'full_name': 'Bad Email Person', 'email_id': 'not-an-email',
        }, follow=True)
        self.assertContains(response, 'valid email')
        self.assertFalse(User_Profile.objects.filter(User_Full_Name='Bad Email Person').exists())

    def test_oversized_image_rejected(self):
        big_file = SimpleUploadedFile('big.jpg', b'x' * (6 * 1024 * 1024), content_type='image/jpeg')
        response = self.client.post('/Staff--Profile-Registration/', {
            'full_name': 'Big Photo Person', 'image': big_file,
        }, follow=True)
        self.assertContains(response, 'must be under')
        self.assertFalse(User_Profile.objects.filter(User_Full_Name='Big Photo Person').exists())

    def test_photo_upload_succeeds(self):
        photo = SimpleUploadedFile('test.jpg', FAKE_JPEG, content_type='image/jpeg')
        response = self.client.post('/Staff--Profile-Registration/', {
            'full_name': 'Photo Person', 'image': photo,
        })
        self.assertEqual(response.status_code, 302)
        profile = User_Profile.objects.get(User_Full_Name='Photo Person')
        self.assertTrue(bool(profile.User_Image))
        profile.delete()  # cleans up the uploaded test file too


class StaffUpdateTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username='staff', password='Correct@1234')
        self.client.post('/', {'username': 'staff', 'password': 'Correct@1234'})
        photo = SimpleUploadedFile('original.jpg', FAKE_JPEG, content_type='image/jpeg')
        self.profile = User_Profile.objects.create(
            User_Full_Name='Original Name', User_Salary=20000, User_Image=photo,
        )

    def tearDown(self):
        self.profile.delete()

    def test_update_nonexistent_profile_returns_404(self):
        response = self.client.get('/Staff--Profile-User-Update/999999/')
        self.assertEqual(response.status_code, 404)

    def test_valid_update_succeeds(self):
        response = self.client.post(f'/Staff--Profile-User-Update/{self.profile.id}/', {
            'full_name': 'Updated Name', 'salary': '22000',
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.User_Full_Name, 'Updated Name')
        self.assertEqual(self.profile.User_Salary, 22000)

    def test_update_without_reuploading_photo_preserves_it(self):
        """Previously: the view unconditionally assigned
        request.FILES.get('image', None) to User_Image, so updating any
        other field without re-selecting a photo silently deleted the
        existing one on every save."""
        self.assertTrue(bool(self.profile.User_Image))
        response = self.client.post(f'/Staff--Profile-User-Update/{self.profile.id}/', {
            'full_name': 'Original Name', 'job_title': 'Manager',
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertTrue(bool(self.profile.User_Image))
        self.assertEqual(self.profile.User_Job_Title, 'Manager')

    def test_update_can_replace_photo_with_a_new_one(self):
        new_photo = SimpleUploadedFile('replacement.jpg', FAKE_JPEG, content_type='image/jpeg')
        old_name = self.profile.User_Image.name
        response = self.client.post(f'/Staff--Profile-User-Update/{self.profile.id}/', {
            'full_name': 'Original Name', 'image': new_photo,
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.User_Image.name, old_name)

    def test_update_non_numeric_salary_rejected(self):
        response = self.client.post(f'/Staff--Profile-User-Update/{self.profile.id}/', {
            'full_name': 'Original Name', 'salary': 'garbage',
        }, follow=True)
        self.assertContains(response, 'valid salary')
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.User_Salary, 20000)  # unchanged


class StaffDeleteAndPauseTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username='staff', password='Correct@1234')
        self.client.post('/', {'username': 'staff', 'password': 'Correct@1234'})
        self.profile = User_Profile.objects.create(User_Full_Name='Delete Me', is_active=True)

    def test_delete_via_get_does_not_crash_and_does_not_delete(self):
        """Previously: no else-branch for a non-POST request meant the
        view fell through with no return at all — a hard 500."""
        response = self.client.get(f'/Staff--Profile-User-Delete/{self.profile.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User_Profile.objects.filter(id=self.profile.id).exists())

    def test_delete_via_post_removes_profile(self):
        response = self.client.post(f'/Staff--Profile-User-Delete/{self.profile.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User_Profile.objects.filter(id=self.profile.id).exists())

    def test_pause_via_get_does_not_crash(self):
        response = self.client.get(f'/User-Profile-Pause-Unpause/{self.profile.id}/')
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_active)  # unchanged by the GET

    def test_pause_via_post_toggles_active_status(self):
        response = self.client.post(f'/User-Profile-Pause-Unpause/{self.profile.id}/')
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.is_active)

        response = self.client.post(f'/User-Profile-Pause-Unpause/{self.profile.id}/')
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_active)
