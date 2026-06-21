import pytest


@pytest.mark.django_db
class TestAnalyticsChartHistogram:
    def test_numeric_column_returns_base64_image(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=histogram&column=age")
        assert res.status_code == 200
        assert "chart" in res.data
        assert res.data["chart"].startswith("data:image/png;base64,")

    def test_missing_column_returns_400(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=histogram&column=nonexistent")
        assert res.status_code == 400

    def test_non_numeric_column_returns_400(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=histogram&column=city")
        assert res.status_code == 400

    def test_empty_column_param_returns_400(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=histogram")
        assert res.status_code == 400


@pytest.mark.django_db
class TestAnalyticsChartBar:
    def test_categorical_column_returns_image(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=bar&column=city")
        assert res.status_code == 200
        assert res.data["chart"].startswith("data:image/png;base64,")

    def test_numeric_column_also_works(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=bar&column=age")
        assert res.status_code == 200

    def test_missing_column_returns_400(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=bar&column=missing")
        assert res.status_code == 400


@pytest.mark.django_db
class TestAnalyticsChartBox:
    def test_returns_image(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=box")
        assert res.status_code == 200
        assert res.data["chart"].startswith("data:image/png;base64,")


@pytest.mark.django_db
class TestAnalyticsChartScatter:
    def test_valid_x_and_y_returns_image(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=scatter&x=age&y=salary")
        assert res.status_code == 200
        assert res.data["chart"].startswith("data:image/png;base64,")

    def test_with_hue_column(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=scatter&x=age&y=salary&hue=city")
        assert res.status_code == 200

    def test_missing_x_returns_400(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=scatter&y=salary")
        assert res.status_code == 400

    def test_missing_y_returns_400(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=scatter&x=age")
        assert res.status_code == 400

    def test_invalid_x_column_returns_400(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=scatter&x=nope&y=salary")
        assert res.status_code == 400


@pytest.mark.django_db
class TestAnalyticsChartCorrelation:
    def test_returns_image(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=correlation")
        assert res.status_code == 200
        assert res.data["chart"].startswith("data:image/png;base64,")

    def test_spearman_method(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=correlation&method=spearman")
        assert res.status_code == 200


@pytest.mark.django_db
class TestAnalyticsChartEdgeCases:
    def test_unknown_chart_type_returns_400(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/?type=pie")
        assert res.status_code == 400

    def test_no_type_param_returns_400(self, auth_client, dataset):
        res = auth_client.get(f"/api/analytics/{dataset.pk}/chart/")
        assert res.status_code == 400

    def test_not_found_dataset_returns_404(self, auth_client):
        res = auth_client.get("/api/analytics/99999/chart/?type=histogram&column=x")
        assert res.status_code == 404

    def test_unauthorized_returns_401(self, anon_client, dataset):
        res = anon_client.get(f"/api/analytics/{dataset.pk}/chart/?type=box")
        assert res.status_code == 401

    def test_wrong_user_dataset_returns_404(self, auth_client, db):
        from django.contrib.auth import get_user_model
        from datasets.models import Dataset
        other = get_user_model().objects.create_user(
            username="chart_other", email="chart_other@example.com",
            password="pass", is_verified=True,
        )
        ds = Dataset.objects.create(user=other, name="x.csv", file="datasets/x.csv", row_count=1, column_count=1)
        res = auth_client.get(f"/api/analytics/{ds.pk}/chart/?type=box")
        assert res.status_code == 404
