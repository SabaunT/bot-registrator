from django.test import TestCase
from apps.utils.telegramcalendar import create_calendar

# Create your tests here.
class ATestCase(TestCase):
    def test_aa(self):
        print(create_calendar('mock', 2019, 9))
