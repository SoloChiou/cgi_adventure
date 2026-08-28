from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings


class EnsureDevelopmentAdminTests(TestCase):
    @override_settings(DEBUG=True, DEV_ADMIN_USERNAME="test-admin", DEV_ADMIN_PASSWORD="Test-only@not-a-credential")
    def test_creates_superuser_with_configured_password(self):
        call_command("ensure_dev_admin", verbosity=0)
        user = get_user_model().objects.get(username="test-admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("Test-only@not-a-credential"))
