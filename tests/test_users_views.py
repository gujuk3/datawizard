import pytest
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from users.models import EmailVerificationToken, PasswordResetToken

User = get_user_model()


@pytest.mark.django_db
class TestRegister:
    def test_success(self, anon_client):
        with patch("users.views.send_mail"):
            res = anon_client.post("/api/auth/register/", {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepass123",
            })
        assert res.status_code == 201
        assert "email" in res.data

    def test_duplicate_email_returns_400(self, anon_client, user):
        with patch("users.views.send_mail"):
            res = anon_client.post("/api/auth/register/", {
                "username": "anotheruser",
                "email": user.email,
                "password": "securepass123",
            })
        assert res.status_code == 400

    def test_missing_fields_returns_400(self, anon_client):
        res = anon_client.post("/api/auth/register/", {"email": "x@x.com"})
        assert res.status_code == 400

    def test_email_send_failure_returns_500(self, anon_client):
        with patch("users.views.send_mail", side_effect=Exception("SMTP error")):
            res = anon_client.post("/api/auth/register/", {
                "username": "failuser",
                "email": "failuser@example.com",
                "password": "securepass123",
            })
        assert res.status_code == 500


@pytest.mark.django_db
class TestVerifyEmail:
    def test_success(self, anon_client, db):
        new_user = User.objects.create_user(
            username="unverified", email="unverified@example.com",
            password="pass123", is_verified=False,
        )
        token_obj = EmailVerificationToken.objects.create(user=new_user)
        res = anon_client.get(f"/api/auth/verify-email/{token_obj.token}/")
        assert res.status_code == 200
        assert "access" in res.data
        new_user.refresh_from_db()
        assert new_user.is_verified is True

    def test_invalid_token_returns_404(self, anon_client):
        import uuid
        res = anon_client.get(f"/api/auth/verify-email/{uuid.uuid4()}/")
        assert res.status_code == 404

    def test_already_used_token_returns_404(self, anon_client, db):
        u = User.objects.create_user(
            username="u2", email="u2@example.com",
            password="pass123", is_verified=False,
        )
        token_obj = EmailVerificationToken.objects.create(user=u, is_used=True)
        res = anon_client.get(f"/api/auth/verify-email/{token_obj.token}/")
        assert res.status_code == 404


@pytest.mark.django_db
class TestLogin:
    def test_success(self, anon_client, user):
        res = anon_client.post("/api/auth/login/", {
            "email": "test@example.com",
            "password": "testpass123",
        })
        assert res.status_code == 200
        assert "access" in res.data

    def test_wrong_password_returns_401(self, anon_client, user):
        res = anon_client.post("/api/auth/login/", {
            "email": "test@example.com",
            "password": "wrongpass",
        })
        assert res.status_code == 401

    def test_unverified_user_cannot_login(self, anon_client, db):
        u = User.objects.create_user(
            username="unverified2", email="unv@example.com",
            password="pass123", is_verified=False,
        )
        res = anon_client.post("/api/auth/login/", {"email": u.email, "password": "pass123"})
        assert res.status_code == 401


@pytest.mark.django_db
class TestMe:
    def test_authenticated_returns_user_data(self, auth_client, user):
        res = auth_client.get("/api/auth/me/")
        assert res.status_code == 200
        assert res.data["email"] == user.email

    def test_unauthenticated_returns_401(self, anon_client):
        res = anon_client.get("/api/auth/me/")
        assert res.status_code == 401


@pytest.mark.django_db
class TestForgotPassword:
    def test_existing_email_returns_200(self, anon_client, user):
        with patch("users.views.send_mail"):
            res = anon_client.post("/api/auth/forgot-password/", {"email": user.email})
        assert res.status_code == 200

    def test_nonexistent_email_still_returns_200(self, anon_client):
        res = anon_client.post("/api/auth/forgot-password/", {"email": "nobody@example.com"})
        assert res.status_code == 200


@pytest.mark.django_db
class TestResetPassword:
    def _make_reset_token(self, user):
        return PasswordResetToken.objects.create(user=user)

    def test_success(self, anon_client, user):
        token_obj = self._make_reset_token(user)
        res = anon_client.post("/api/auth/reset-password/", {
            "token": str(token_obj.token),
            "new_password": "newpassword123",
        })
        assert res.status_code == 200
        user.refresh_from_db()
        assert user.check_password("newpassword123")

    def test_marks_token_used(self, anon_client, user):
        token_obj = self._make_reset_token(user)
        anon_client.post("/api/auth/reset-password/", {
            "token": str(token_obj.token),
            "new_password": "newpassword123",
        })
        token_obj.refresh_from_db()
        assert token_obj.is_used is True

    def test_missing_fields_returns_400(self, anon_client):
        res = anon_client.post("/api/auth/reset-password/", {"token": "something"})
        assert res.status_code == 400

    def test_short_password_returns_400(self, anon_client, user):
        token_obj = self._make_reset_token(user)
        res = anon_client.post("/api/auth/reset-password/", {
            "token": str(token_obj.token),
            "new_password": "short",
        })
        assert res.status_code == 400

    def test_invalid_token_returns_400(self, anon_client):
        import uuid
        res = anon_client.post("/api/auth/reset-password/", {
            "token": str(uuid.uuid4()),
            "new_password": "newpassword123",
        })
        assert res.status_code == 400

    def test_expired_token_returns_400(self, anon_client, user):
        token_obj = PasswordResetToken.objects.create(user=user)
        token_obj.expires_at = timezone.now() - timedelta(hours=2)
        token_obj.save()
        res = anon_client.post("/api/auth/reset-password/", {
            "token": str(token_obj.token),
            "new_password": "newpassword123",
        })
        assert res.status_code == 400

    def test_used_token_returns_400(self, anon_client, user):
        token_obj = PasswordResetToken.objects.create(user=user)
        token_obj.is_used = True
        token_obj.save()
        res = anon_client.post("/api/auth/reset-password/", {
            "token": str(token_obj.token),
            "new_password": "newpassword123",
        })
        assert res.status_code == 400
