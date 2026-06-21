import pytest
import pandas as pd
from unittest.mock import patch


REG_CSV = (
    "area,rooms,price\n"
    + "\n".join(f"{40 + i * 5},{1 + (i % 4)},{80000 + i * 3000}" for i in range(40))
)


@pytest.fixture
def trained_regression_model(db, user, tmp_media):
    from datasets.models import Dataset, DataColumn
    from datawizard_core.ml_engine import (
        split_data, train_model, evaluate_regression_model, save_model,
    )
    from ml.models import MLModel, ModelMetric

    (tmp_media / "datasets" / "reg.csv").write_text(REG_CSV)
    ds = Dataset.objects.create(
        user=user, name="reg.csv", file="datasets/reg.csv",
        row_count=40, column_count=3, status="ready",
    )
    DataColumn.objects.create(dataset=ds, name="area", data_type="int64", missing_count=0, unique_count=40)
    DataColumn.objects.create(dataset=ds, name="rooms", data_type="int64", missing_count=0, unique_count=4)
    DataColumn.objects.create(dataset=ds, name="price", data_type="int64", missing_count=0, unique_count=40)

    df = pd.read_csv(str(tmp_media / "datasets" / "reg.csv"))
    split = split_data(df, target_column="price", feature_columns=["area", "rooms"])
    result = train_model(split["X_train"], split["y_train"], "linear_regression", "regression")
    evaluation = evaluate_regression_model(result["model"], split["X_test"], split["y_test"])
    rel_path = save_model(result["model"], str(tmp_media))

    ml_model = MLModel.objects.create(
        user=user, dataset=ds, name="reg_model",
        algorithm="linear_regression", model_type="regression",
        target_column="price", feature_columns=["area", "rooms"],
        hyperparameters={}, train_test_split=0.2,
        training_status="completed", training_duration=0.1,
        model_file=rel_path,
    )
    for k, v in evaluation.items():
        if isinstance(v, (int, float)):
            ModelMetric.objects.create(model=ml_model, metric_name=k, metric_value=v)
        else:
            ModelMetric.objects.create(model=ml_model, metric_name=k, metric_value=None, additional_data=v)
    return ml_model


@pytest.mark.django_db
class TestMLChartFeatureImportance:
    def test_returns_base64_image(self, auth_client, trained_ml_model):
        res = auth_client.get(f"/api/ml/{trained_ml_model.pk}/chart/?type=feature_importance")
        assert res.status_code == 200
        assert "chart" in res.data
        assert res.data["chart"].startswith("data:image/png;base64,")

    def test_without_model_file_returns_400(self, auth_client, db, user, ml_dataset):
        from ml.models import MLModel
        m = MLModel.objects.create(
            user=user, dataset=ml_dataset, name="no_file",
            algorithm="random_forest_classifier", model_type="classification",
            target_column="label", feature_columns=["age", "salary"],
            hyperparameters={},
        )
        res = auth_client.get(f"/api/ml/{m.pk}/chart/?type=feature_importance")
        assert res.status_code == 400

    def test_knn_model_returns_400(self, auth_client, db, user, ml_dataset, tmp_media):
        import pandas as pd
        from datawizard_core.ml_engine import split_data, train_model, save_model
        from ml.models import MLModel

        df = pd.read_csv(str(tmp_media / "datasets" / "ml_test.csv"))
        split = split_data(df, target_column="label", feature_columns=["age", "salary"])
        result = train_model(split["X_train"], split["y_train"], "knn", "classification")
        rel_path = save_model(result["model"], str(tmp_media))

        m = MLModel.objects.create(
            user=user, dataset=ml_dataset, name="knn_chart_model",
            algorithm="knn", model_type="classification",
            target_column="label", feature_columns=["age", "salary"],
            hyperparameters={}, model_file=rel_path,
        )
        res = auth_client.get(f"/api/ml/{m.pk}/chart/?type=feature_importance")
        assert res.status_code == 400


@pytest.mark.django_db
class TestMLChartConfusionMatrix:
    def test_classification_model_returns_image(self, auth_client, trained_ml_model):
        res = auth_client.get(f"/api/ml/{trained_ml_model.pk}/chart/?type=confusion_matrix")
        assert res.status_code == 200
        assert res.data["chart"].startswith("data:image/png;base64,")

    def test_regression_model_returns_400(self, auth_client, trained_regression_model):
        res = auth_client.get(f"/api/ml/{trained_regression_model.pk}/chart/?type=confusion_matrix")
        assert res.status_code == 400


@pytest.mark.django_db
class TestMLChartPredictionVsActual:
    def test_regression_model_returns_image(self, auth_client, trained_regression_model):
        res = auth_client.get(f"/api/ml/{trained_regression_model.pk}/chart/?type=prediction_vs_actual")
        assert res.status_code == 200
        assert res.data["chart"].startswith("data:image/png;base64,")

    def test_classification_model_returns_400(self, auth_client, trained_ml_model):
        res = auth_client.get(f"/api/ml/{trained_ml_model.pk}/chart/?type=prediction_vs_actual")
        assert res.status_code == 400


@pytest.mark.django_db
class TestMLChartEdgeCases:
    def test_unknown_chart_type_returns_400(self, auth_client, trained_ml_model):
        res = auth_client.get(f"/api/ml/{trained_ml_model.pk}/chart/?type=roc_curve")
        assert res.status_code == 400

    def test_no_type_param_returns_400(self, auth_client, trained_ml_model):
        res = auth_client.get(f"/api/ml/{trained_ml_model.pk}/chart/")
        assert res.status_code == 400

    def test_not_found_returns_404(self, auth_client):
        res = auth_client.get("/api/ml/99999/chart/?type=feature_importance")
        assert res.status_code == 404

    def test_unauthorized_returns_401(self, anon_client, trained_ml_model):
        res = anon_client.get(f"/api/ml/{trained_ml_model.pk}/chart/?type=feature_importance")
        assert res.status_code == 401
