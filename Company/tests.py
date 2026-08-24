from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from .models import Company_Profile


def _minimal_post(**overrides):
    """Every field the registration/update form submits, defaulted to
    blank so a test only needs to override what it cares about."""
    fields = {
        'company_name': '', 'company_address': '', 'company_email': '',
        'company_country': '', 'company_pincode': '', 'company_nationality': '',
        'company_mobile_number': '', 'company_phone_number': '',
        'company_discount_percentage': '', 'company_instruction': '',
        'company_gst_number': '', 'company_gst_percentage': '',
        'company_tcs_percentage': '', 'company_tds_percentage': '',
        'company_md_one_name': '', 'company_md_one_email': '', 'company_md_one_mobile_number': '',
        'company_md_second_name': '', 'company_md_second_email': '', 'company_md_second_mobile_number': '',
        'company_hr_head_name': '', 'company_hr_head_email': '', 'company_hr_head_mobile_number': '',
        'company_assitant_hr_name': '', 'company_assitant_hr_email': '', 'company_assistant_hr_mobile_number': '',
        'company_accountant_head_name': '', 'company_accountant_head_email': '', 'company_accountant_head_mobile_number': '',
        'company_accountant_assistant_one_name': '', 'company_accountant_assistant_one_email': '', 'company_accountant_assistant_one_mobile_number': '',
        'company_accountant_assistant_two_name': '', 'company_accountant_assistant_two_email': '', 'company_accountant_assistant_two_mobile_number': '',
    }
    fields.update(overrides)
    return fields


class CompanyRegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username='staff', password='Correct@1234')
        self.client.post('/', {'username': 'staff', 'password': 'Correct@1234'})

    def test_valid_registration_creates_company(self):
        response = self.client.post('/Company--Profile-Registration/', _minimal_post(
            company_name='Acme Textiles', company_gst_number='24ACME0001Z9',
        ))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Company_Profile.objects.filter(Company_Name='Acme Textiles').exists())

    def test_assistant_hr_mobile_number_is_actually_saved(self):
        """The Add view previously read 'company_assitant_hr_mobile_number'
        (missing an 's') while the form has only ever submitted
        'company_assistant_hr_mobile_number' — every company ever added
        silently lost this field. See docs/backend-hardening-log.md."""
        self.client.post('/Company--Profile-Registration/', _minimal_post(
            company_name='Typo Check Co', company_assistant_hr_mobile_number='9123456789',
        ))
        company = Company_Profile.objects.get(Company_Name='Typo Check Co')
        self.assertEqual(company.Company_Assitant_HR_Mobile_Number, '9123456789')

    def test_missing_name_rejected(self):
        response = self.client.post('/Company--Profile-Registration/', _minimal_post(), follow=True)
        self.assertContains(response, 'required')
        self.assertEqual(Company_Profile.objects.count(), 0)

    def test_duplicate_name_rejected_with_friendly_message_not_raw_sql_error(self):
        Company_Profile.objects.create(Company_Name='Dup Co')
        response = self.client.post('/Company--Profile-Registration/', _minimal_post(
            company_name='Dup Co',
        ), follow=True)
        self.assertContains(response, 'already exists')
        self.assertNotContains(response, 'UNIQUE constraint')
        self.assertEqual(Company_Profile.objects.filter(Company_Name='Dup Co').count(), 1)

    def test_duplicate_gst_number_rejected(self):
        Company_Profile.objects.create(Company_Name='First Co', Company_GST_Number='24DUPGST0001Z9')
        response = self.client.post('/Company--Profile-Registration/', _minimal_post(
            company_name='Second Co', company_gst_number='24DUPGST0001Z9',
        ), follow=True)
        self.assertContains(response, 'already exists')
        self.assertFalse(Company_Profile.objects.filter(Company_Name='Second Co').exists())

    def test_two_companies_can_both_have_blank_gst_number(self):
        """The uniqueness constraint must not accidentally apply to blank
        GST numbers — most companies won't have one filled in."""
        Company_Profile.objects.create(Company_Name='No GST One')
        response = self.client.post('/Company--Profile-Registration/', _minimal_post(
            company_name='No GST Two',
        ))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Company_Profile.objects.filter(Company_Name='No GST Two').exists())

    def test_invalid_email_rejected(self):
        response = self.client.post('/Company--Profile-Registration/', _minimal_post(
            company_name='Bad Email Co', company_email='not-an-email',
        ), follow=True)
        self.assertContains(response, 'valid email')
        self.assertFalse(Company_Profile.objects.filter(Company_Name='Bad Email Co').exists())

    def test_percentage_out_of_range_rejected(self):
        response = self.client.post('/Company--Profile-Registration/', _minimal_post(
            company_name='Bad Percent Co', company_gst_percentage='150',
        ), follow=True)
        self.assertContains(response, 'between 0 and 100')
        self.assertFalse(Company_Profile.objects.filter(Company_Name='Bad Percent Co').exists())


class CompanyUpdateTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username='staff', password='Correct@1234')
        self.client.post('/', {'username': 'staff', 'password': 'Correct@1234'})
        self.company = Company_Profile.objects.create(Company_Name='Original Name', Company_Discount_Percentage='10')

    def test_update_nonexistent_company_returns_404_not_crash(self):
        """Previously: UnboundLocalError (a hard 500) — .get(id=id) raised
        DoesNotExist, was caught by the generic except, but the final
        render() outside the try/except still referenced the never-assigned
        `queryset` variable."""
        response = self.client.get('/Company--Profile-Update/999999/')
        self.assertEqual(response.status_code, 404)

    def test_valid_update_succeeds(self):
        response = self.client.post(f'/Company--Profile-Update/{self.company.id}/', _minimal_post(
            company_name='Updated Name',
        ))
        self.assertEqual(response.status_code, 302)
        self.company.refresh_from_db()
        self.assertEqual(self.company.Company_Name, 'Updated Name')

    def test_clearing_a_decimal_field_does_not_crash(self):
        """Previously: assigning '' to a DecimalField attribute and
        calling .save() raised ValidationError — any Update submission
        clearing Discount/GST/TCS/TDS percentage crashed the request."""
        response = self.client.post(f'/Company--Profile-Update/{self.company.id}/', _minimal_post(
            company_name='Original Name', company_discount_percentage='',
        ))
        self.assertEqual(response.status_code, 302)
        self.company.refresh_from_db()
        self.assertEqual(str(self.company.Company_Discount_Percentage), '0.00')

    def test_update_to_duplicate_gst_number_rejected(self):
        Company_Profile.objects.create(Company_Name='Other Co', Company_GST_Number='24OTHERGST01Z9')
        response = self.client.post(f'/Company--Profile-Update/{self.company.id}/', _minimal_post(
            company_name='Original Name', company_gst_number='24OTHERGST01Z9',
        ), follow=True)
        self.assertContains(response, 'already exists')
        self.company.refresh_from_db()
        self.assertNotEqual(self.company.Company_GST_Number, '24OTHERGST01Z9')

    def test_update_can_keep_its_own_gst_number(self):
        """Excluding the current row from the duplicate check — updating
        a company without changing its GST number must not reject itself
        as a 'duplicate'."""
        self.company.Company_GST_Number = '24SELFGST0001Z9'
        self.company.save()
        response = self.client.post(f'/Company--Profile-Update/{self.company.id}/', _minimal_post(
            company_name='Original Name', company_gst_number='24SELFGST0001Z9',
        ))
        self.assertEqual(response.status_code, 302)


class CompanyDeleteTests(TestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username='staff', password='Correct@1234')
        self.client.post('/', {'username': 'staff', 'password': 'Correct@1234'})
        self.company = Company_Profile.objects.create(Company_Name='Delete Me')

    def test_delete_via_get_does_not_crash_and_does_not_delete(self):
        """Previously: no `request.method == 'POST'` else-branch meant a
        GET request fell through the whole function with no return value
        at all — Django raised "didn't return an HttpResponse" (a hard
        500) for any GET to this URL."""
        response = self.client.get(f'/Company--Profile-User-Delete/{self.company.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Company_Profile.objects.filter(id=self.company.id).exists())

    def test_delete_via_post_removes_company(self):
        response = self.client.post(f'/Company--Profile-User-Delete/{self.company.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Company_Profile.objects.filter(id=self.company.id).exists())

    def test_delete_nonexistent_company_handled_gracefully(self):
        response = self.client.post('/Company--Profile-User-Delete/999999/')
        self.assertEqual(response.status_code, 200)  # friendly error_page.html, not a crash
