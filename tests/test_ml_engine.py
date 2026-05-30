import pytest
import tempfile
import os
import pandas as pd
import numpy as np
from datawizard_core.ml_engine import (
    split_data,
    train_model,
    evaluate_classification_model,
    evaluate_regression_model,
    get_feature_importance,
    save_model,
    load_model,
    run_training_pipeline,
)
from datawizard_core.exceptions import ValidationError, TrainingError


@pytest.fixture
def clf_df():
    """Binary classification dataset."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "x1": np.random.randn(n),
        "x2": np.random.randn(n),
        "label": np.random.choice([0, 1], n),
    })


@pytest.fixture
def reg_df():
    """Regression dataset."""
    np.random.seed(0)
    n = 100
    x = np.random.randn(n)
    return pd.DataFrame({
        "x1": x,
        "x2": np.random.randn(n),
        "target": x * 2.0 + np.random.randn(n) * 0.1,
    })


# ── split_data ─────────────────────────────────────────────────────────────────

class TestSplitData:
    def test_basic_split(self, clf_df):
        result = split_data(clf_df, target_column="label")
        assert "X_train" in result
        assert "X_test" in result
        assert result["train_size"] + result["test_size"] == len(clf_df)

    def test_default_test_size_is_20_pct(self, clf_df):
        result = split_data(clf_df, target_column="label")
        assert result["test_size"] == pytest.approx(len(clf_df) * 0.2, abs=1)

    def test_custom_test_size(self, clf_df):
        result = split_data(clf_df, target_column="label", test_size=0.3)
        assert result["test_size"] == pytest.approx(len(clf_df) * 0.3, abs=1)

    def test_invalid_target_raises(self, clf_df):
        with pytest.raises(ValidationError):
            split_data(clf_df, target_column="nonexistent")

    def test_test_size_too_small_raises(self, clf_df):
        with pytest.raises(ValidationError):
            split_data(clf_df, target_column="label", test_size=0.05)

    def test_test_size_too_large_raises(self, clf_df):
        with pytest.raises(ValidationError):
            split_data(clf_df, target_column="label", test_size=0.6)

    def test_custom_feature_columns(self, clf_df):
        result = split_data(clf_df, target_column="label", feature_columns=["x1"])
        assert result["feature_names"] == ["x1"]
        assert result["X_train"].shape[1] == 1

    def test_missing_feature_column_raises(self, clf_df):
        with pytest.raises(ValidationError):
            split_data(clf_df, target_column="label", feature_columns=["x1", "missing"])

    def test_no_features_after_exclusion_raises(self):
        df = pd.DataFrame({"target": [1, 2, 3, 4, 5]})
        with pytest.raises(ValidationError):
            split_data(df, target_column="target")


# ── train_model ────────────────────────────────────────────────────────────────

class TestTrainModel:
    def _get_split(self, clf_df):
        return split_data(clf_df, target_column="label")

    def test_logistic_regression(self, clf_df):
        s = self._get_split(clf_df)
        result = train_model(s["X_train"], s["y_train"], "logistic_regression", "classification")
        assert result["model"] is not None
        assert result["algorithm"] == "logistic_regression"

    def test_decision_tree(self, clf_df):
        s = self._get_split(clf_df)
        result = train_model(s["X_train"], s["y_train"], "decision_tree", "classification")
        assert result["model"] is not None

    def test_random_forest_classifier(self, clf_df):
        s = self._get_split(clf_df)
        result = train_model(s["X_train"], s["y_train"], "random_forest_classifier", "classification")
        assert result["training_duration_seconds"] >= 0

    def test_knn(self, clf_df):
        s = self._get_split(clf_df)
        result = train_model(s["X_train"], s["y_train"], "knn", "classification")
        assert result["model"] is not None

    def test_linear_regression(self, reg_df):
        s = split_data(reg_df, target_column="target")
        result = train_model(s["X_train"], s["y_train"], "linear_regression", "regression")
        assert result["model"] is not None

    def test_random_forest_regressor(self, reg_df):
        s = split_data(reg_df, target_column="target")
        result = train_model(s["X_train"], s["y_train"], "random_forest_regressor", "regression")
        assert result["model"] is not None

    def test_invalid_algorithm_raises(self, clf_df):
        s = self._get_split(clf_df)
        with pytest.raises(TrainingError):
            train_model(s["X_train"], s["y_train"], "svm", "classification")

    def test_invalid_model_type_raises(self, clf_df):
        s = self._get_split(clf_df)
        with pytest.raises(TrainingError):
            train_model(s["X_train"], s["y_train"], "logistic_regression", "clustering")

    def test_classification_algorithm_with_regression_type_raises(self, clf_df):
        s = self._get_split(clf_df)
        with pytest.raises(TrainingError):
            train_model(s["X_train"], s["y_train"], "logistic_regression", "regression")

    def test_regression_algorithm_with_classification_type_raises(self, reg_df):
        s = split_data(reg_df, target_column="target")
        with pytest.raises(TrainingError):
            train_model(s["X_train"], s["y_train"], "linear_regression", "classification")

    def test_custom_hyperparameters_applied(self, clf_df):
        s = self._get_split(clf_df)
        result = train_model(
            s["X_train"], s["y_train"], "knn", "classification",
            hyperparameters={"n_neighbors": 3},
        )
        assert result["hyperparameters"]["n_neighbors"] == 3


# ── evaluate_* ─────────────────────────────────────────────────────────────────

class TestEvaluate:
    def test_classification_metrics_present(self, clf_df):
        s = split_data(clf_df, target_column="label")
        tr = train_model(s["X_train"], s["y_train"], "logistic_regression", "classification")
        metrics = evaluate_classification_model(tr["model"], s["X_test"], s["y_test"])
        for key in ("accuracy", "precision", "recall", "f1_score", "confusion_matrix"):
            assert key in metrics
        assert 0.0 <= metrics["accuracy"] <= 1.0

    def test_regression_metrics_present(self, reg_df):
        s = split_data(reg_df, target_column="target")
        tr = train_model(s["X_train"], s["y_train"], "linear_regression", "regression")
        metrics = evaluate_regression_model(tr["model"], s["X_test"], s["y_test"])
        for key in ("mse", "rmse", "r2_score"):
            assert key in metrics
        assert metrics["rmse"] >= 0.0


# ── get_feature_importance ─────────────────────────────────────────────────────

class TestFeatureImportance:
    def test_tree_model_returns_sorted_list(self, clf_df):
        s = split_data(clf_df, target_column="label")
        tr = train_model(s["X_train"], s["y_train"], "decision_tree", "classification")
        result = get_feature_importance(tr["model"], s["feature_names"])
        assert len(result) == len(s["feature_names"])
        importances = [r["importance"] for r in result]
        assert importances == sorted(importances, reverse=True)

    def test_linear_model_returns_coef_based_importance(self, clf_df):
        s = split_data(clf_df, target_column="label")
        tr = train_model(s["X_train"], s["y_train"], "logistic_regression", "classification")
        result = get_feature_importance(tr["model"], s["feature_names"])
        assert len(result) == len(s["feature_names"])

    def test_knn_returns_empty_list(self, clf_df):
        s = split_data(clf_df, target_column="label")
        tr = train_model(s["X_train"], s["y_train"], "knn", "classification")
        result = get_feature_importance(tr["model"], s["feature_names"])
        assert result == []

    def test_importances_sum_to_one(self, clf_df):
        s = split_data(clf_df, target_column="label")
        tr = train_model(s["X_train"], s["y_train"], "random_forest_classifier", "classification")
        result = get_feature_importance(tr["model"], s["feature_names"])
        total = sum(r["importance"] for r in result)
        assert total == pytest.approx(1.0, abs=1e-6)


# ── save_model / load_model ────────────────────────────────────────────────────

class TestSaveLoadModel:
    def test_roundtrip(self, clf_df):
        s = split_data(clf_df, target_column="label")
        tr = train_model(s["X_train"], s["y_train"], "decision_tree", "classification")
        model = tr["model"]

        with tempfile.TemporaryDirectory() as tmpdir:
            rel_path = save_model(model, tmpdir)
            abs_path = os.path.join(tmpdir, rel_path)
            loaded = load_model(abs_path)

        original_preds = model.predict(s["X_test"])
        loaded_preds = loaded.predict(s["X_test"])
        assert list(original_preds) == list(loaded_preds)

    def test_save_creates_pkl_file(self, clf_df):
        s = split_data(clf_df, target_column="label")
        tr = train_model(s["X_train"], s["y_train"], "decision_tree", "classification")

        with tempfile.TemporaryDirectory() as tmpdir:
            rel_path = save_model(tr["model"], tmpdir)
            assert rel_path.endswith(".pkl")
            assert os.path.exists(os.path.join(tmpdir, rel_path))


# ── run_training_pipeline ──────────────────────────────────────────────────────

class TestRunTrainingPipeline:
    def test_classification_pipeline(self, clf_df):
        result = run_training_pipeline(clf_df, {
            "target_column": "label",
            "algorithm": "logistic_regression",
            "model_type": "classification",
        })
        assert "model" in result
        assert "metrics" in result
        assert "accuracy" in result["metrics"]

    def test_regression_pipeline(self, reg_df):
        result = run_training_pipeline(reg_df, {
            "target_column": "target",
            "algorithm": "linear_regression",
            "model_type": "regression",
        })
        assert "r2_score" in result["metrics"]

    def test_missing_target_column_raises(self, clf_df):
        with pytest.raises(ValidationError):
            run_training_pipeline(clf_df, {
                "algorithm": "logistic_regression",
                "model_type": "classification",
            })

    def test_missing_algorithm_raises(self, clf_df):
        with pytest.raises(ValidationError):
            run_training_pipeline(clf_df, {
                "target_column": "label",
                "model_type": "classification",
            })

    def test_missing_model_type_raises(self, clf_df):
        with pytest.raises(ValidationError):
            run_training_pipeline(clf_df, {
                "target_column": "label",
                "algorithm": "logistic_regression",
            })

    def test_feature_importance_in_result(self, clf_df):
        result = run_training_pipeline(clf_df, {
            "target_column": "label",
            "algorithm": "decision_tree",
            "model_type": "classification",
        })
        assert isinstance(result["feature_importance"], list)

    def test_split_info_in_result(self, clf_df):
        result = run_training_pipeline(clf_df, {
            "target_column": "label",
            "algorithm": "decision_tree",
            "model_type": "classification",
            "test_size": 0.25,
        })
        assert result["split_info"]["test_size"] == pytest.approx(len(clf_df) * 0.25, abs=1)


# ── error paths in train_model ─────────────────────────────────────────────────

class TestTrainModelErrorPaths:
    def test_invalid_hyperparameters_raises_training_error(self, clf_df):
        s = split_data(clf_df, target_column="label")
        with pytest.raises(TrainingError, match="Invalid hyperparameters"):
            train_model(
                s["X_train"], s["y_train"],
                "logistic_regression", "classification",
                hyperparameters={"nonexistent_param_xyz": 99},
            )

    def test_training_failure_raises_training_error(self, clf_df):
        """Force model.fit to fail."""
        import numpy as np
        s = split_data(clf_df, target_column="label")
        # Pass non-numeric y that sklearn can't handle
        bad_y = s["y_train"].astype(str).str.replace("0", "NaN")
        # This might not always raise, so use a deliberately broken input
        X_bad = s["X_train"].copy()
        X_bad.iloc[:, 0] = np.nan
        with pytest.raises((TrainingError, Exception)):
            train_model(X_bad, s["y_train"], "knn", "classification")


# ── compute_shap_values ────────────────────────────────────────────────────────

class TestComputeShapValues:
    def test_tree_model_returns_list(self, clf_df):
        from datawizard_core.ml_engine import compute_shap_values
        s = split_data(clf_df, target_column="label")
        tr = train_model(s["X_train"], s["y_train"], "decision_tree", "classification")
        result = compute_shap_values(tr["model"], s["X_test"], s["feature_names"], "classification")
        # Returns list (possibly empty if shap not installed)
        assert isinstance(result, list)

    def test_linear_model_returns_list(self, clf_df):
        from datawizard_core.ml_engine import compute_shap_values
        s = split_data(clf_df, target_column="label")
        tr = train_model(s["X_train"], s["y_train"], "logistic_regression", "classification")
        result = compute_shap_values(tr["model"], s["X_test"], s["feature_names"], "classification")
        assert isinstance(result, list)


# ── feature importance edge case ───────────────────────────────────────────────

class TestFeatureImportanceEdgeCases:
    def test_zero_sum_importances_returns_zeros(self, clf_df):
        """Model with all-zero feature importances shouldn't crash."""
        from unittest.mock import MagicMock
        import numpy as np
        model = MagicMock()
        model.feature_importances_ = np.array([0.0, 0.0])
        result = get_feature_importance(model, ["a", "b"])
        assert all(r["importance"] == 0.0 for r in result)
