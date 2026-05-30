import io
import pytest
from unittest.mock import patch
import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile


CLEAN_CSV = b"age,salary,city\n25,5000,Istanbul\n30,7000,Ankara\n28,6000,Izmir\n"


def _make_csv(content=CLEAN_CSV, name="test.csv"):
    return SimpleUploadedFile(name, content, content_type="text/csv")


@pytest.mark.django_db
class TestListDatasets:
    def test_empty_list(self, auth_client):
        res = auth_client.get("/api/datasets/")
        assert res.status_code == 200
        assert res.data == []

    def test_returns_user_datasets(self, auth_client, dataset):
        res = auth_client.get("/api/datasets/")
        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["name"] == "test.csv"

    def test_unauthorized(self, anon_client):
        res = anon_client.get("/api/datasets/")
        assert res.status_code == 401


@pytest.mark.django_db
class TestUploadDataset:
    def test_upload_success(self, auth_client, tmp_media):
        sample_df = pd.DataFrame({"age": [25, 30], "salary": [5000, 7000]})
        with patch("datasets.views.load_csv", return_value=sample_df), \
             patch("datasets.views.validate_file_size", return_value={"valid": True, "file_size_mb": 0.01, "max_size_mb": 50}), \
             patch("datasets.views.validate_csv_structure", return_value={"valid": True, "errors": [], "duplicate_columns": [], "empty_columns": [], "row_count": 2, "column_count": 2}), \
             patch("datasets.views.call_llm", return_value=None):
            res = auth_client.post("/api/datasets/upload/", {"file": _make_csv()}, format="multipart")
        assert res.status_code == 201
        assert "dataset" in res.data

    def test_no_file_returns_400(self, auth_client):
        res = auth_client.post("/api/datasets/upload/", {}, format="multipart")
        assert res.status_code == 400

    def test_unauthorized(self, anon_client):
        res = anon_client.post("/api/datasets/upload/", {"file": _make_csv()}, format="multipart")
        assert res.status_code == 401


@pytest.mark.django_db
class TestDatasetDetail:
    def test_success(self, auth_client, dataset):
        res = auth_client.get(f"/api/datasets/{dataset.pk}/")
        assert res.status_code == 200
        assert res.data["name"] == "test.csv"

    def test_not_found(self, auth_client):
        res = auth_client.get("/api/datasets/99999/")
        assert res.status_code == 404

    def test_wrong_user_returns_404(self, auth_client, db):
        from django.contrib.auth import get_user_model
        from datasets.models import Dataset
        other = get_user_model().objects.create_user(
            username="other2", email="other2@example.com",
            password="pass123", is_verified=True,
        )
        ds = Dataset.objects.create(user=other, name="x.csv", file="x.csv", row_count=1, column_count=1)
        res = auth_client.get(f"/api/datasets/{ds.pk}/")
        assert res.status_code == 404


@pytest.mark.django_db
class TestDatasetPreview:
    def test_success(self, auth_client, dataset):
        res = auth_client.get(f"/api/datasets/{dataset.pk}/preview/")
        assert res.status_code == 200
        assert "columns" in res.data
        assert "rows" in res.data
        assert res.data["columns"] == ["age", "salary", "city"]


@pytest.mark.django_db
class TestDeleteDataset:
    def test_success(self, auth_client, dataset):
        pk = dataset.pk
        res = auth_client.delete(f"/api/datasets/{pk}/delete/")
        assert res.status_code == 204
        from datasets.models import Dataset
        assert not Dataset.objects.filter(pk=pk).exists()

    def test_not_found(self, auth_client):
        res = auth_client.delete("/api/datasets/99999/delete/")
        assert res.status_code == 404

    def test_unauthorized(self, anon_client, dataset):
        res = anon_client.delete(f"/api/datasets/{dataset.pk}/delete/")
        assert res.status_code == 401


@pytest.mark.django_db
class TestUploadErrorPaths:
    def test_file_too_large_returns_400(self, auth_client, tmp_media):
        with patch("datasets.views.validate_file_size",
                   return_value={"valid": False, "file_size_mb": 60.0, "max_size_mb": 50}):
            res = auth_client.post("/api/datasets/upload/", {"file": _make_csv()}, format="multipart")
        assert res.status_code == 400
        assert "File too large" in res.data["error"]

    def test_invalid_csv_raises_400(self, auth_client, tmp_media):
        from datawizard_core.exceptions import InvalidFileError
        with patch("datasets.views.validate_file_size",
                   return_value={"valid": True, "file_size_mb": 0.01, "max_size_mb": 50}), \
             patch("datasets.views.load_csv", side_effect=InvalidFileError("Bad CSV")):
            res = auth_client.post("/api/datasets/upload/", {"file": _make_csv()}, format="multipart")
        assert res.status_code == 400

    def test_preview_load_failure_returns_500(self, auth_client, dataset):
        with patch("datasets.views.load_csv", side_effect=Exception("io error")):
            res = auth_client.get(f"/api/datasets/{dataset.pk}/preview/")
        assert res.status_code == 500
