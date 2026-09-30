from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class RegistrationLoginFlowTests(TestCase):
    def setUp(self):
        # DRF's ScopedRateThrottle is backed by the real Redis cache (by design --
        # see CACHES in settings), which Django's per-test transaction rollback does
        # NOT reset. Without this, tests in this class throttle each other.
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)

    def test_register_logs_in_and_sends_verification_email(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "user@example.com", "password": "StrongPass123!", "full_name": "Test User"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("تایید ایمیل", mail.outbox[0].subject)

        me = self.client.get("/api/auth/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["email"], "user@example.com")
        self.assertFalse(me.data["is_email_verified"])

    def test_login_with_wrong_password_returns_neutral_message(self):
        User.objects.create_user(email="user@example.com", password="StrongPass123!")
        response = self.client.post(
            "/api/auth/login/", {"email": "user@example.com", "password": "wrong"}, format="json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "ایمیل یا رمز عبور نادرست است.")

    def test_login_with_unknown_email_returns_same_neutral_message(self):
        response = self.client.post(
            "/api/auth/login/", {"email": "nobody@example.com", "password": "whatever123"}, format="json"
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "ایمیل یا رمز عبور نادرست است.")

    def test_authenticated_mutation_requires_csrf_token(self):
        User.objects.create_user(email="user@example.com", password="StrongPass123!")
        self.client.post("/api/auth/login/", {"email": "user@example.com", "password": "StrongPass123!"}, format="json")

        # No X-CSRFToken header -> Django's CsrfViewMiddleware must reject this,
        # since DRF's SessionAuthentication.enforce_csrf() runs for authenticated requests.
        response = self.client.patch("/api/auth/me/", {"full_name": "New Name"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_forgot_password_neutral_for_existing_and_unknown_email(self):
        User.objects.create_user(email="user@example.com", password="StrongPass123!")
        existing = self.client.post("/api/auth/forgot-password/", {"email": "user@example.com"}, format="json")
        unknown = self.client.post("/api/auth/forgot-password/", {"email": "nobody@example.com"}, format="json")
        self.assertEqual(existing.status_code, 200)
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(existing.data["detail"], unknown.data["detail"])

    def test_full_password_reset_flow(self):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        from .tokens import password_reset_token_generator

        user = User.objects.create_user(email="user@example.com", password="OldPass123!")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token_generator.make_token(user)

        response = self.client.post(
            "/api/auth/reset-password/",
            {"uid": uid, "token": token, "new_password": "NewPass456!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        login = self.client.post(
            "/api/auth/login/", {"email": "user@example.com", "password": "NewPass456!"}, format="json"
        )
        self.assertEqual(login.status_code, 200)

    def test_email_verification_flow(self):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        from .tokens import email_verification_token_generator

        user = User.objects.create_user(email="user@example.com", password="StrongPass123!")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token_generator.make_token(user)

        response = self.client.post("/api/auth/verify-email/", {"uid": uid, "token": token}, format="json")
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
