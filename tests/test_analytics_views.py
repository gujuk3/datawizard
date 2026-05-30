import pytest
from unittest.mock import patch


@pytest.mark.django_db
class TestStatisticsView:
    def test_success(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/statistics/")
        assert res.status_code == 200
        assert "statistics" in res.data
        assert "numeric" in res.data["statistics"]

    def test_unauthorized(self, anon_client, dataset):
        res = anon_client.get(f"/api/analytics/{dataset.pk}/statistics/")
        assert res.status_code == 401

    def test_not_found(self, auth_client):
        res = auth_client.get("/api/analytics/99999/statistics/")
        assert res.status_code == 404

    def test_wrong_user_returns_404(self, auth_client, db):
        from django.contrib.auth import get_user_model
        from datasets.models import Dataset
        other = get_user_model().objects.create_user(
            username="other", email="other@example.com",
            password="pass123", is_verified=True,
        )
        ds = Dataset.objects.create(user=other, name="x.csv", file="datasets/x.csv", row_count=1, column_count=1)
        res = auth_client.get(f"/api/analytics/{ds.pk}/statistics/")
        assert res.status_code == 404


@pytest.mark.django_db
class TestMissingValuesView:
    def test_success(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/missing/")
        assert res.status_code == 200
        assert "missing_values" in res.data
        assert res.data["missing_values"]["total_missing"] == 0

    def test_reports_missing(self, auth_client, dataset_with_missing):
        res = auth_client.get(f"/api/analytics/{dataset_with_missing.pk}/missing/")
        assert res.status_code == 200
        assert res.data["missing_values"]["total_missing"] > 0


@pytest.mark.django_db
class TestCorrelationView:
    def test_success(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/correlation/")
        assert res.status_code == 200
        assert "correlation" in res.data
        assert "matrix" in res.data["correlation"]

    def test_pearson_method(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/correlation/?method=pearson")
        assert res.status_code == 200

    def test_invalid_method_returns_error(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/correlation/?method=invalid")
        assert res.status_code == 500


@pytest.mark.django_db
class TestPreprocessView:
    def test_no_missing_data_returns_400(self, auth_client, dataset):
        res = auth_client.post(
            f"/api/analytics/{dataset.pk}/preprocess/",
            {"strategy": "mean"},
        )
        assert res.status_code == 400
        assert "eksik değer" in res.data["error"]

    def test_fills_missing_and_persists(self, auth_client, dataset_with_missing):
        from datasets.models import DataColumn
        res = auth_client.post(
            f"/api/analytics/{dataset_with_missing.pk}/preprocess/",
            {"strategy": "mean"},
        )
        assert res.status_code == 200
        report = res.data["report"]
        assert report["values_filled"] > 0
        # DataColumn records should be updated
        assert DataColumn.objects.filter(dataset=dataset_with_missing, missing_count=0).count() == 3

    def test_drop_strategy_reduces_rows(self, auth_client, dataset_with_missing):
        from datasets.models import Dataset
        res = auth_client.post(
            f"/api/analytics/{dataset_with_missing.pk}/preprocess/",
            {"strategy": "drop"},
        )
        assert res.status_code == 200
        report = res.data["report"]
        assert report["rows_after"] < report["rows_before"]
        dataset_with_missing.refresh_from_db()
        assert dataset_with_missing.row_count == report["rows_after"]

    def test_invalid_strategy_returns_400(self, auth_client, dataset_with_missing):
        res = auth_client.post(
            f"/api/analytics/{dataset_with_missing.pk}/preprocess/",
            {"strategy": "unknown"},
        )
        assert res.status_code == 400

    def test_unauthorized(self, anon_client, dataset_with_missing):
        res = anon_client.post(
            f"/api/analytics/{dataset_with_missing.pk}/preprocess/",
            {"strategy": "mean"},
        )
        assert res.status_code == 401


@pytest.mark.django_db
class TestLlmExplainView:
    def test_success(self, auth_client, dataset):
        with patch("analytics.views.call_llm", return_value="This dataset has nice statistics."):
            res = auth_client.post(
                f"/api/analytics/{dataset.pk}/explain/",
                {"type": "statistics"},
            )
        assert res.status_code == 200
        assert "explanation" in res.data
        assert res.data["explanation"] == "This dataset has nice statistics."

    def test_llm_error_returns_500(self, auth_client, dataset):
        from datawizard_core.exceptions import LLMError
        with patch("analytics.views.call_llm", side_effect=LLMError("LLM unavailable")):
            res = auth_client.post(f"/api/analytics/{dataset.pk}/explain/", {"type": "statistics"})
        assert res.status_code == 500

    def test_correlation_silently_skipped_on_single_numeric(self, auth_client, tmp_media, db, user):
        """Single numeric column — correlation raises, view should still succeed."""
        from datasets.models import Dataset
        single_col_csv = "label\n0\n1\n0\n1\n"
        (tmp_media / "datasets" / "single.csv").write_text(single_col_csv)
        ds = Dataset.objects.create(
            user=user, name="single.csv", file="datasets/single.csv",
            row_count=4, column_count=1, status="ready",
        )
        with patch("analytics.views.call_llm", return_value="ok"):
            res = auth_client.post(f"/api/analytics/{ds.pk}/explain/", {"type": "statistics"})
        assert res.status_code == 200


@pytest.mark.django_db
class TestViewErrorPaths:
    """Cover exception handler branches (500 paths) in statistics, correlation, missing views."""

    def test_statistics_load_failure_returns_500(self, auth_client, dataset):
        with patch("analytics.views._load_df", side_effect=Exception("disk error")):
            res = auth_client.get(f"/api/analytics/{dataset.pk}/statistics/")
        assert res.status_code == 500

    def test_correlation_load_failure_returns_500(self, auth_client, dataset):
        with patch("analytics.views._load_df", side_effect=Exception("disk error")):
            res = auth_client.get(f"/api/analytics/{dataset.pk}/correlation/")
        assert res.status_code == 500

    def test_missing_values_load_failure_returns_500(self, auth_client, dataset):
        with patch("analytics.views._load_df", side_effect=Exception("disk error")):
            res = auth_client.get(f"/api/analytics/{dataset.pk}/missing/")
        assert res.status_code == 500

    def test_preprocess_general_exception_returns_500(self, auth_client, dataset_with_missing):
        with patch("analytics.views._load_df", side_effect=Exception("unexpected")):
            res = auth_client.post(
                f"/api/analytics/{dataset_with_missing.pk}/preprocess/",
                {"strategy": "mean"},
            )
        assert res.status_code == 500
