from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class GuestTripOwnershipTests(TestCase):
    def setUp(self):
        cache.clear()  # see apps.accounts.tests for why: Redis-backed throttle cache persists across tests
        self.client = APIClient()

    def test_guest_can_create_and_read_own_trip(self):
        create = self.client.post(
            "/api/trips/", {"title": "Guest trip", "origin": "تهران", "destination": "شیراز"}, format="json"
        )
        self.assertEqual(create.status_code, 201)
        trip_id = create.data["id"]

        get_response = self.client.get(f"/api/trips/{trip_id}/")
        self.assertEqual(get_response.status_code, 200)

    def test_another_anonymous_session_cannot_access_the_trip(self):
        create = self.client.post(
            "/api/trips/", {"title": "Guest trip", "origin": "تهران", "destination": "شیراز"}, format="json"
        )
        trip_id = create.data["id"]

        stranger_client = APIClient()  # fresh client -> fresh/no session cookie
        response = stranger_client.get(f"/api/trips/{trip_id}/")
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_trip_also_returns_404_not_403(self):
        response = self.client.get("/api/trips/00000000-0000-0000-0000-000000000000/")
        self.assertEqual(response.status_code, 404)

    def test_guest_trip_transfers_to_account_on_register(self):
        create = self.client.post(
            "/api/trips/", {"title": "Guest trip", "origin": "تهران", "destination": "شیراز"}, format="json"
        )
        trip_id = create.data["id"]

        register = self.client.post(
            "/api/auth/register/",
            {"email": "traveler@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(register.status_code, 201)

        trips = self.client.get("/api/trips/")
        self.assertEqual(trips.status_code, 200)
        self.assertEqual(len(trips.data), 1)
        self.assertEqual(trips.data[0]["id"], trip_id)

        user = User.objects.get(email="traveler@example.com")
        from .models import Trip

        trip = Trip.objects.get(pk=trip_id)
        self.assertEqual(trip.owner_id, user.id)
        self.assertEqual(trip.guest_session_key, "")

    def test_guest_trip_transfers_to_account_on_login(self):
        User.objects.create_user(email="existing@example.com", password="StrongPass123!")

        create = self.client.post(
            "/api/trips/", {"title": "Guest trip", "origin": "تهران", "destination": "شیراز"}, format="json"
        )
        trip_id = create.data["id"]

        login = self.client.post(
            "/api/auth/login/", {"email": "existing@example.com", "password": "StrongPass123!"}, format="json"
        )
        self.assertEqual(login.status_code, 200)

        from .models import Trip

        trip = Trip.objects.get(pk=trip_id)
        self.assertEqual(trip.owner.email, "existing@example.com")

    def test_preferences_patch_is_synced_on_single_object(self):
        create = self.client.post("/api/trips/", {"origin": "تهران", "destination": "شیراز"}, format="json")
        trip_id = create.data["id"]

        patch = self.client.patch(
            f"/api/trips/{trip_id}/preferences/",
            {"adults_count": 2, "pace": "balanced"},
            format="json",
        )
        self.assertEqual(patch.status_code, 200)

        get_response = self.client.get(f"/api/trips/{trip_id}/")
        self.assertEqual(get_response.data["preferences"]["adults_count"], 2)
        self.assertEqual(get_response.data["preferences"]["pace"], "balanced")
