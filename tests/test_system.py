"""
System tests — end-to-end user journeys through the full API stack.
Each test class simulates a complete real-world scenario from first HTTP
request to final assertion, touching Auth → Datasets → Analytics → ML.
"""
import io
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

CLEAN_CSV = "age,salary,city\n25,5000,Istanbul\n30,7000,Ankara\n28,6000,Izmir\n35,8000,Istanbul\n"
_rows = [f"{20 + i},{4000 + i * 200},{i % 2}" for i in range(40)]
ML_CSV = "age,salary,label\n" + "\n".join(_rows)
REG_CSV = (
    "area,rooms,price\n"
    + "\n".join(f"{40 + i * 5},{1 + (i % 4)},{80000 + i * 3000}" for i in range(40))
)


def _make_csv_file(content: str, name: str = "data.csv"):
    f = io.BytesIO(content.encode())
    f.name = name
    return f


def _auth_client_for(user) -> APIClient:
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")
    return client


@pytest.mark.django_db
class TestUserRegistrationAndAuthFlow:
    """
    System test: full registration → email verification → login cycle.
    Verifies that each step produces the correct state before the next.
    """

    def test_register_then_verify_then_login(self, anon_client):
        from users.models import EmailVerificationToken

        with patch("users.views.send_mail"):
            res = anon_client.post("/api/auth/register/", {
                "username": "sys_user",
                "email": "sys@example.com",
                "password": "securepass123",
            })
        assert res.status_code == 201

        # Unverified user cannot log in
        login_res = anon_client.post("/api/auth/login/", {
            "email": "sys@example.com",
            "password": "securepass123",
        })
        assert login_res.status_code == 401

        # Verify email
        user = User.objects.get(email="sys@example.com")
        token_obj = EmailVerificationToken.objects.get(user=user, is_used=False)
        verify_res = anon_client.get(f"/api/auth/verify-email/{token_obj.token}/")
        assert verify_res.status_code == 200
        assert "access" in verify_res.data

        # Now login succeeds
        login_res2 = anon_client.post("/api/auth/login/", {
            "email": "sys@example.com",
            "password": "securepass123",
        })
        assert login_res2.status_code == 200
        assert "access" in login_res2.data

    def test_authenticated_user_can_access_profile(self, db):
        user = User.objects.create_user(
            username="profile_user", email="profile@example.com",
            password="pass", is_verified=True,
        )
        client = _auth_client_for(user)
        res = client.get("/api/auth/me/")
        assert res.status_code == 200
        assert res.data["email"] == "profile@example.com"

    def test_full_password_reset_flow(self, anon_client, db):
        from users.models import PasswordResetToken

        user = User.objects.create_user(
            username="reset_user", email="reset@example.com",
            password="oldpass123", is_verified=True,
        )

        # Request reset
        with patch("users.views.send_mail"):
            forgot_res = anon_client.post("/api/auth/forgot-password/", {"email": "reset@example.com"})
        assert forgot_res.status_code == 200

        # Reset with token
        token_obj = PasswordResetToken.objects.get(user=user, is_used=False)
        reset_res = anon_client.post("/api/auth/reset-password/", {
            "token": str(token_obj.token),
            "new_password": "newpass456",
        })
        assert reset_res.status_code == 200

        # Login with new password
        login_res = anon_client.post("/api/auth/login/", {
            "email": "reset@example.com",
            "password": "newpass456",
        })
        assert login_res.status_code == 200

        # Old password no longer works
        old_login = anon_client.post("/api/auth/login/", {
            "email": "reset@example.com",
            "password": "oldpass123",
        })
        assert old_login.status_code == 401


@pytest.mark.django_db
class TestAnalyticsWorkflow:
    """
    System test: upload CSV → statistics → missing values → preprocess → verify persisted changes.
    """

    def test_upload_then_statistics(self, tmp_media, db):
        user = User.objects.create_user(
            username="ana_user", email="ana@example.com",
            password="pass", is_verified=True,
        )
        client = _auth_client_for(user)

        csv_file = _make_csv_file(CLEAN_CSV, "clean.csv")
        upload_res = client.post("/api/datasets/upload/", {"file": csv_file}, format="multipart")
        assert upload_res.status_code == 201
        dataset_id = upload_res.data["dataset"]["id"]

        stats_res = client.get(f"/api/analytics/{dataset_id}/statistics/")
        assert stats_res.status_code == 200
        assert "numeric" in stats_res.data["statistics"]
        assert "age" in stats_res.data["statistics"]["numeric"]

    def test_upload_then_missing_values_then_preprocess(self, tmp_media, db):
        MISSING_CSV = "age,salary,city\n25,,Istanbul\n30,7000,\n28,6000,Izmir\n35,8000,Istanbul\n"
        user = User.objects.create_user(
            username="preprocess_user", email="preprocess@example.com",
            password="pass", is_verified=True,
        )
        client = _auth_client_for(user)

        csv_file = _make_csv_file(MISSING_CSV, "missing.csv")
        upload_res = client.post("/api/datasets/upload/", {"file": csv_file}, format="multipart")
        assert upload_res.status_code == 201
        dataset_id = upload_res.data["dataset"]["id"]

        # Missing values detected
        missing_res = client.get(f"/api/analytics/{dataset_id}/missing/")
        assert missing_res.status_code == 200
        assert missing_res.data["missing_values"]["total_missing"] > 0

        # Preprocess
        preprocess_res = client.post(f"/api/analytics/{dataset_id}/preprocess/", {"strategy": "mean"})
        assert preprocess_res.status_code == 200
        assert preprocess_res.data["report"]["values_filled"] > 0

        # Missing values now zero
        missing_after = client.get(f"/api/analytics/{dataset_id}/missing/")
        assert missing_after.data["missing_values"]["total_missing"] == 0

    def test_upload_then_correlation(self, tmp_media, db):
        user = User.objects.create_user(
            username="corr_user", email="corr@example.com",
            password="pass", is_verified=True,
        )
        client = _auth_client_for(user)

        csv_file = _make_csv_file(CLEAN_CSV, "corr.csv")
        upload_res = client.post("/api/datasets/upload/", {"file": csv_file}, format="multipart")
        assert upload_res.status_code == 201
        dataset_id = upload_res.data["dataset"]["id"]

        corr_res = client.get(f"/api/analytics/{dataset_id}/correlation/")
        assert corr_res.status_code == 200
        assert "matrix" in corr_res.data["correlation"]
        assert "columns" in corr_res.data["correlation"]


@pytest.mark.django_db
class TestMLWorkflow:
    """
    System test: upload → train classification → list → detail → predict → delete.
    Also covers regression training and prediction.
    """

    def test_classification_train_predict_delete(self, tmp_media, db):
        user = User.objects.create_user(
            username="ml_sys_user", email="mlsys@example.com",
            password="pass", is_verified=True,
        )
        client = _auth_client_for(user)

        # Upload
        csv_file = _make_csv_file(ML_CSV, "ml.csv")
        upload_res = client.post("/api/datasets/upload/", {"file": csv_file}, format="multipart")
        assert upload_res.status_code == 201
        dataset_id = upload_res.data["dataset"]["id"]

        # Train
        with patch("ml.views.call_llm", return_value="Good model!"):
            train_res = client.post("/api/ml/train/", {
                "dataset_id": dataset_id,
                "name": "clf_model",
                "algorithm": "logistic_regression",
                "model_type": "classification",
                "target_column": "label",
                "feature_columns": ["age", "salary"],
                "test_size": 0.2,
            }, format="json")
        assert train_res.status_code == 201
        model_id = train_res.data["model"]["id"]
        assert "evaluation" in train_res.data
        assert "feature_importance" in train_res.data
        assert "shap_values" in train_res.data
        assert train_res.data["llm_explanation"] == "Good model!"

        # List
        list_res = client.get("/api/ml/")
        assert list_res.status_code == 200
        assert any(m["id"] == model_id for m in list_res.data)

        # Detail
        detail_res = client.get(f"/api/ml/{model_id}/")
        assert detail_res.status_code == 200
        assert detail_res.data["name"] == "clf_model"

        # Predict
        predict_res = client.post(f"/api/ml/{model_id}/predict/", {
            "features": {"age": 28, "salary": 6000}
        }, format="json")
        assert predict_res.status_code == 200
        assert predict_res.data["prediction"] in (0, 1)

        # Delete
        delete_res = client.delete(f"/api/ml/{model_id}/delete/")
        assert delete_res.status_code == 204

        # Model no longer accessible
        detail_after = client.get(f"/api/ml/{model_id}/")
        assert detail_after.status_code == 404

    def test_regression_train_and_predict(self, tmp_media, db):
        user = User.objects.create_user(
            username="reg_sys_user", email="regsys@example.com",
            password="pass", is_verified=True,
        )
        client = _auth_client_for(user)

        csv_file = _make_csv_file(REG_CSV, "reg.csv")
        upload_res = client.post("/api/datasets/upload/", {"file": csv_file}, format="multipart")
        assert upload_res.status_code == 201
        dataset_id = upload_res.data["dataset"]["id"]

        with patch("ml.views.call_llm", return_value=""):
            train_res = client.post("/api/ml/train/", {
                "dataset_id": dataset_id,
                "name": "reg_model",
                "algorithm": "linear_regression",
                "model_type": "regression",
                "target_column": "price",
                "feature_columns": ["area", "rooms"],
                "test_size": 0.2,
            }, format="json")
        assert train_res.status_code == 201
        model_id = train_res.data["model"]["id"]
        assert "mse" in train_res.data["evaluation"]
        assert "r2_score" in train_res.data["evaluation"]

        predict_res = client.post(f"/api/ml/{model_id}/predict/", {
            "features": {"area": 80, "rooms": 3}
        }, format="json")
        assert predict_res.status_code == 200
        assert isinstance(predict_res.data["prediction"], float)


@pytest.mark.django_db
class TestCrossUserIsolation:
    """
    System test: verifies that one user cannot read or act on another user's data.
    """

    def test_user_cannot_access_other_users_dataset(self, tmp_media, db):
        user_a = User.objects.create_user(
            username="user_a", email="a@example.com", password="pass", is_verified=True,
        )
        user_b = User.objects.create_user(
            username="user_b", email="b@example.com", password="pass", is_verified=True,
        )
        client_a = _auth_client_for(user_a)
        client_b = _auth_client_for(user_b)

        csv_file = _make_csv_file(CLEAN_CSV, "a.csv")
        upload_res = client_a.post("/api/datasets/upload/", {"file": csv_file}, format="multipart")
        assert upload_res.status_code == 201
        dataset_id = upload_res.data["dataset"]["id"]

        # User B cannot see User A's dataset detail
        res = client_b.get(f"/api/datasets/{dataset_id}/")
        assert res.status_code == 404

        # User B cannot run analytics on User A's dataset
        res = client_b.get(f"/api/analytics/{dataset_id}/statistics/")
        assert res.status_code == 404

    def test_user_cannot_predict_on_other_users_model(self, tmp_media, db):
        user_a = User.objects.create_user(
            username="model_owner", email="owner@example.com", password="pass", is_verified=True,
        )
        user_b = User.objects.create_user(
            username="model_thief", email="thief@example.com", password="pass", is_verified=True,
        )
        client_a = _auth_client_for(user_a)
        client_b = _auth_client_for(user_b)

        csv_file = _make_csv_file(ML_CSV, "ml.csv")
        upload_res = client_a.post("/api/datasets/upload/", {"file": csv_file}, format="multipart")
        dataset_id = upload_res.data["dataset"]["id"]

        with patch("ml.views.call_llm", return_value=""):
            train_res = client_a.post("/api/ml/train/", {
                "dataset_id": dataset_id,
                "name": "private_model",
                "algorithm": "decision_tree",
                "model_type": "classification",
                "target_column": "label",
                "feature_columns": ["age", "salary"],
            }, format="json")
        assert train_res.status_code == 201
        model_id = train_res.data["model"]["id"]

        # User B list: should not see User A's model
        list_res = client_b.get("/api/ml/")
        assert all(m["id"] != model_id for m in list_res.data)

        # User B predict: should 404
        predict_res = client_b.post(f"/api/ml/{model_id}/predict/", {
            "features": {"age": 25, "salary": 5000}
        }, format="json")
        assert predict_res.status_code == 404

    def test_dataset_list_returns_only_own_datasets(self, tmp_media, db):
        user_a = User.objects.create_user(
            username="list_a", email="lista@example.com", password="pass", is_verified=True,
        )
        user_b = User.objects.create_user(
            username="list_b", email="listb@example.com", password="pass", is_verified=True,
        )
        client_a = _auth_client_for(user_a)
        client_b = _auth_client_for(user_b)

        client_a.post("/api/datasets/upload/",
                      {"file": _make_csv_file(CLEAN_CSV, "a1.csv")}, format="multipart")
        client_a.post("/api/datasets/upload/",
                      {"file": _make_csv_file(CLEAN_CSV, "a2.csv")}, format="multipart")
        client_b.post("/api/datasets/upload/",
                      {"file": _make_csv_file(CLEAN_CSV, "b1.csv")}, format="multipart")

        res_a = client_a.get("/api/datasets/")
        res_b = client_b.get("/api/datasets/")

        assert res_a.status_code == 200
        assert res_b.status_code == 200
        assert len(res_a.data) == 2
        assert len(res_b.data) == 1
