from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase


class ReportsProfileTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='reports_staff', password='Correct@1234')
        self.client.post('/', {'username': 'reports_staff', 'password': 'Correct@1234'})

    def test_reports_page_loads(self):
        response = self.client.get('/Reports-Profile/')
        self.assertEqual(response.status_code, 200)
