from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationAndAuthTests(APITestCase):
    def test_register_creates_user_with_role(self):
        response = self.client.post("/api/auth/register/", {
            "username": "jane",
            "email": "jane@example.com",
            "password": "correct-horse-battery",
            "role": "student",
        })
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="jane")
        self.assertEqual(user.role, "student")
        self.assertTrue(user.check_password("correct-horse-battery"))

    def test_register_rejects_short_password(self):
        response = self.client.post("/api/auth/register/", {
            "username": "jane", "email": "jane@example.com", "password": "short", "role": "student",
        })
        self.assertEqual(response.status_code, 400)

    def test_login_returns_jwt_pair(self):
        User.objects.create_user(username="jane", email="jane@example.com", password="correct-horse-battery", role="student")
        response = self.client.post("/api/auth/token/", {"username": "jane", "password": "correct-horse-battery"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_rejects_wrong_password(self):
        User.objects.create_user(username="jane", email="jane@example.com", password="correct-horse-battery", role="student")
        response = self.client.post("/api/auth/token/", {"username": "jane", "password": "wrong"})
        self.assertEqual(response.status_code, 401)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_returns_own_profile(self):
        user = User.objects.create_user(username="jane", email="jane@example.com", password="pw", role="ministry_admin")
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "jane")
        self.assertEqual(response.data["role"], "ministry_admin")
