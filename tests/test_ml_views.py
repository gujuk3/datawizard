import pytest
from unittest.mock import patch


@pytest.mark.django_db
class TestTrainView:
    def test_success(self, auth_client, ml_dataset, tmp_media):
        with patch("ml.views.call_llm", return_value="Great model!"):
            res = auth_client.post("/api/ml/train/", {
                "dataset_id": ml_dataset.pk,
                "name": "my_model",
                "algorithm": "logistic_regression",
                "model_type": "classification",
                "target_column": "label",
                "feature_columns": ["age", "salary"],
                "test_size": 0.2,
            }, format="json")
        assert res.status_code == 201
        assert "model" in res.data
        assert res.data["model"]["name"] == "my_model"
        assert "evaluation" in res.data
        assert "feature_importance" in res.data

    def test_missing_name_returns_400(self, auth_client, ml_dataset):
        res = auth_client.post("/api/ml/train/", {
            "dataset_id": ml_dataset.pk,
            "algorithm": "logistic_regression",
            "model_type": "classification",
            "target_column": "label",
        }, format="json")
        assert res.status_code == 400

    def test_duplicate_name_returns_400(self, auth_client, trained_ml_model, ml_dataset):
        with patch("ml.views.call_llm", return_value=""):
            res = auth_client.post("/api/ml/train/", {
                "dataset_id": ml_dataset.pk,
                "name": trained_ml_model.name,
                "algorithm": "logistic_regression",
                "model_type": "classification",
                "target_column": "label",
                "feature_columns": ["age", "salary"],
            }, format="json")
        assert res.status_code == 400
        assert "zaten mevcut" in res.data["error"]

    def test_missing_dataset_id_returns_400(self, auth_client):
        res = auth_client.post("/api/ml/train/", {
            "name": "m",
            "algorithm": "logistic_regression",
            "model_type": "classification",
        }, format="json")
        assert res.status_code == 400

    def test_dataset_not_found_returns_404(self, auth_client):
        res = auth_client.post("/api/ml/train/", {
            "name": "m",
            "dataset_id": 99999,
            "algorithm": "logistic_regression",
            "model_type": "classification",
            "target_column": "label",
        }, format="json")
        assert res.status_code == 404

    def test_invalid_algorithm_returns_400(self, auth_client, ml_dataset):
        res = auth_client.post("/api/ml/train/", {
            "dataset_id": ml_dataset.pk,
            "name": "m",
            "algorithm": "svm",
            "model_type": "classification",
            "target_column": "label",
            "feature_columns": ["age", "salary"],
        }, format="json")
        assert res.status_code == 400

    def test_llm_failure_does_not_break_training(self, auth_client, ml_dataset, tmp_media):
        with patch("ml.views.call_llm", side_effect=Exception("LLM down")):
            res = auth_client.post("/api/ml/train/", {
                "dataset_id": ml_dataset.pk,
                "name": "robust_model",
                "algorithm": "decision_tree",
                "model_type": "classification",
                "target_column": "label",
                "feature_columns": ["age", "salary"],
            }, format="json")
        assert res.status_code == 201
        assert res.data["llm_explanation"] is None

    def test_unauthorized(self, anon_client, ml_dataset):
        res = anon_client.post("/api/ml/train/", {
            "dataset_id": ml_dataset.pk,
            "name": "m",
            "algorithm": "logistic_regression",
            "model_type": "classification",
            "target_column": "label",
        }, format="json")
        assert res.status_code == 401


@pytest.mark.django_db
class TestListModelsView:
    def test_empty(self, auth_client):
        res = auth_client.get("/api/ml/")
        assert res.status_code == 200
        assert res.data == []

    def test_returns_user_models(self, auth_client, trained_ml_model):
        res = auth_client.get("/api/ml/")
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["name"] == trained_ml_model.name

    def test_does_not_return_other_user_models(self, auth_client, db, tmp_media):
        from django.contrib.auth import get_user_model
        from datasets.models import Dataset
        from ml.models import MLModel
        other = get_user_model().objects.create_user(
            username="other3", email="other3@example.com",
            password="pass", is_verified=True,
        )
        ds = Dataset.objects.create(user=other, name="x.csv", file="x.csv", row_count=1, column_count=1)
        MLModel.objects.create(
            user=other, dataset=ds, name="other_model",
            algorithm="knn", model_type="classification",
            target_column="y", feature_columns=[], hyperparameters={},
        )
        res = auth_client.get("/api/ml/")
        assert res.status_code == 200
        assert all(m["name"] != "other_model" for m in res.data)

    def test_unauthorized(self, anon_client):
        res = anon_client.get("/api/ml/")
        assert res.status_code == 401


@pytest.mark.django_db
class TestModelDetailView:
    def test_success(self, auth_client, trained_ml_model):
        res = auth_client.get(f"/api/ml/{trained_ml_model.pk}/")
        assert res.status_code == 200
        assert res.data["name"] == trained_ml_model.name

    def test_not_found(self, auth_client):
        res = auth_client.get("/api/ml/99999/")
        assert res.status_code == 404

    def test_wrong_user_returns_404(self, auth_client, db, tmp_media):
        from django.contrib.auth import get_user_model
        from datasets.models import Dataset
        from ml.models import MLModel
        other = get_user_model().objects.create_user(
            username="other4", email="other4@example.com",
            password="pass", is_verified=True,
        )
        ds = Dataset.objects.create(user=other, name="x.csv", file="x.csv", row_count=1, column_count=1)
        m = MLModel.objects.create(
            user=other, dataset=ds, name="secret_model",
            algorithm="knn", model_type="classification",
            target_column="y", feature_columns=[], hyperparameters={},
        )
        res = auth_client.get(f"/api/ml/{m.pk}/")
        assert res.status_code == 404


@pytest.mark.django_db
class TestPredictView:
    def test_success(self, auth_client, trained_ml_model):
        res = auth_client.post(
            f"/api/ml/{trained_ml_model.pk}/predict/",
            {"features": {"age": 28, "salary": 6000}},
            format="json",
        )
        assert res.status_code == 200
        assert "prediction" in res.data
        assert res.data["prediction"] in (0, 1)

    def test_no_features_returns_400(self, auth_client, trained_ml_model):
        res = auth_client.post(
            f"/api/ml/{trained_ml_model.pk}/predict/",
            {"features": {}},
            format="json",
        )
        assert res.status_code == 400

    def test_not_found_returns_404(self, auth_client):
        res = auth_client.post("/api/ml/99999/predict/", {"features": {"x": 1}}, format="json")
        assert res.status_code == 404

    def test_no_model_file_returns_400(self, auth_client, db, user, ml_dataset):
        from ml.models import MLModel
        m = MLModel.objects.create(
            user=user, dataset=ml_dataset, name="no_file_model",
            algorithm="knn", model_type="classification",
            target_column="label", feature_columns=["age", "salary"],
            hyperparameters={},
        )
        res = auth_client.post(
            f"/api/ml/{m.pk}/predict/",
            {"features": {"age": 28, "salary": 6000}},
            format="json",
        )
        assert res.status_code == 400

    def test_unauthorized(self, anon_client, trained_ml_model):
        res = anon_client.post(
            f"/api/ml/{trained_ml_model.pk}/predict/",
            {"features": {"age": 28}},
            format="json",
        )
        assert res.status_code == 401


@pytest.mark.django_db
class TestDeleteModelView:
    def test_success(self, auth_client, trained_ml_model):
        pk = trained_ml_model.pk
        res = auth_client.delete(f"/api/ml/{pk}/delete/")
        assert res.status_code == 204
        from ml.models import MLModel
        assert not MLModel.objects.filter(pk=pk).exists()

    def test_not_found(self, auth_client):
        res = auth_client.delete("/api/ml/99999/delete/")
        assert res.status_code == 404

    def test_unauthorized(self, anon_client, trained_ml_model):
        res = anon_client.delete(f"/api/ml/{trained_ml_model.pk}/delete/")
        assert res.status_code == 401
