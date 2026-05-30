import pytest
import pandas as pd
import numpy as np
from datawizard_core.data_preprocessor import (
    handle_missing_values,
    encode_categorical_columns,
    normalize_columns,
    remove_outliers,
    preprocess_pipeline,
)
from datawizard_core.exceptions import PreprocessingError, ValidationError


@pytest.fixture
def df():
    return pd.DataFrame({
        "age": [25.0, np.nan, 28.0, 35.0],
        "salary": [5000.0, 7000.0, np.nan, 8000.0],
        "city": ["Istanbul", "Ankara", np.nan, "Istanbul"],
    })


@pytest.fixture
def clean_df():
    return pd.DataFrame({
        "age": [25, 30, 28, 35],
        "salary": [5000, 7000, 6000, 8000],
        "city": ["Istanbul", "Ankara", "Izmir", "Istanbul"],
    })


# ── handle_missing_values ──────────────────────────────────────────────────────

class TestHandleMissingValues:
    def test_mean_fills_numeric(self, df):
        result, report = handle_missing_values(df, strategy="mean")
        assert result["age"].isna().sum() == 0
        assert result["salary"].isna().sum() == 0
        assert report["values_filled"] == 3
        assert "age" in report["columns_affected"]
        assert "salary" in report["columns_affected"]

    def test_median_fills_numeric(self, df):
        result, report = handle_missing_values(df, strategy="median")
        assert result["age"].isna().sum() == 0
        assert report["values_filled"] >= 2

    def test_mean_fills_categorical_with_mode(self, df):
        result, report = handle_missing_values(df, strategy="mean")
        assert result["city"].isna().sum() == 0
        assert result["city"].iloc[2] == "Istanbul"

    def test_drop_removes_rows_with_missing(self, df):
        result, report = handle_missing_values(df, strategy="drop")
        assert len(result) < len(df)
        assert result.isna().sum().sum() == 0
        assert report["rows_after"] < report["rows_before"]

    def test_no_missing_returns_unchanged(self, clean_df):
        result, report = handle_missing_values(clean_df, strategy="mean")
        assert report["values_filled"] == 0
        assert report["columns_affected"] == []
        assert len(result) == len(clean_df)

    def test_invalid_strategy_raises(self, df):
        with pytest.raises(PreprocessingError):
            handle_missing_values(df, strategy="unknown")

    def test_invalid_column_raises(self, df):
        with pytest.raises(ValidationError):
            handle_missing_values(df, strategy="mean", columns=["nonexistent"])

    def test_specific_columns_only_fills_those(self, df):
        result, report = handle_missing_values(df, strategy="mean", columns=["age"])
        assert result["age"].isna().sum() == 0
        assert result["salary"].isna().sum() > 0

    def test_rows_before_after_reported(self, df):
        _, report = handle_missing_values(df, strategy="mean")
        assert report["rows_before"] == len(df)
        assert report["rows_after"] == len(df)


# ── encode_categorical_columns ─────────────────────────────────────────────────

class TestEncodeCategorical:
    def test_onehot_creates_dummy_columns(self, clean_df):
        result, report = encode_categorical_columns(clean_df, method="onehot")
        assert "city" not in result.columns
        assert any(c.startswith("city_") for c in result.columns)
        assert report["columns_encoded"] == ["city"]

    def test_label_encodes_to_integers(self, clean_df):
        result, report = encode_categorical_columns(clean_df, method="label")
        assert pd.api.types.is_numeric_dtype(result["city"])
        assert report["method"] == "label"

    def test_label_encoding_is_deterministic(self, clean_df):
        r1, _ = encode_categorical_columns(clean_df.copy(), method="label")
        r2, _ = encode_categorical_columns(clean_df.copy(), method="label")
        assert list(r1["city"]) == list(r2["city"])

    def test_invalid_method_raises(self, clean_df):
        with pytest.raises(PreprocessingError):
            encode_categorical_columns(clean_df, method="hash")

    def test_no_categorical_columns_returns_unchanged(self):
        numeric_df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result, report = encode_categorical_columns(numeric_df, method="onehot")
        assert list(result.columns) == ["a", "b"]
        assert report["columns_encoded"] == []

    def test_high_cardinality_warning(self):
        many_cats = pd.DataFrame({"col": [str(i) for i in range(25)]})
        _, report = encode_categorical_columns(many_cats, method="onehot")
        assert "warnings" in report

    def test_specific_columns_only_encodes_those(self, clean_df):
        _, report = encode_categorical_columns(clean_df, columns=["city"], method="label")
        assert report["columns_encoded"] == ["city"]


# ── normalize_columns ──────────────────────────────────────────────────────────

class TestNormalizeColumns:
    def test_minmax_range_zero_to_one(self, clean_df):
        result, report = normalize_columns(clean_df, method="minmax")
        for col in report["columns_normalized"]:
            assert result[col].min() >= 0.0
            assert result[col].max() <= 1.0

    def test_zscore_mean_near_zero(self, clean_df):
        result, report = normalize_columns(clean_df, method="zscore")
        for col in report["columns_normalized"]:
            assert abs(result[col].mean()) < 1e-9

    def test_zero_variance_column_skipped(self):
        df = pd.DataFrame({"a": [5, 5, 5], "b": [1, 2, 3]})
        result, report = normalize_columns(df, method="minmax")
        assert "a" in report["skipped_columns"]
        assert "b" in report["columns_normalized"]

    def test_no_numeric_columns_returns_unchanged(self):
        df = pd.DataFrame({"city": ["A", "B", "C"]})
        result, report = normalize_columns(df, method="minmax")
        assert report["columns_normalized"] == []

    def test_invalid_method_raises(self, clean_df):
        with pytest.raises(PreprocessingError):
            normalize_columns(clean_df, method="log")

    def test_specific_columns_only_normalizes_those(self, clean_df):
        _, report = normalize_columns(clean_df, columns=["age"], method="minmax")
        assert report["columns_normalized"] == ["age"]


# ── remove_outliers ─────────────────────────────────────────────────────────────

class TestRemoveOutliers:
    def test_removes_extreme_values(self):
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 1000]})
        result, report = remove_outliers(df)
        assert report["rows_removed"] >= 1
        assert 1000 not in result["x"].values

    def test_no_outliers_returns_unchanged(self, clean_df):
        result, report = remove_outliers(clean_df)
        assert report["rows_removed"] == 0
        assert len(result) == len(clean_df)

    def test_no_numeric_columns_returns_unchanged(self):
        df = pd.DataFrame({"city": ["A", "B", "C"]})
        result, report = remove_outliers(df)
        assert len(result) == 3
        assert report["rows_removed"] == 0


# ── preprocess_pipeline ────────────────────────────────────────────────────────

class TestPreprocessPipeline:
    def test_pipeline_missing_values_step(self, df):
        config = {"missing_values": {"strategy": "mean"}}
        result, report = preprocess_pipeline(df, config)
        assert result.isna().sum().sum() == 0
        assert "missing_values" in report["steps_executed"]

    def test_pipeline_full(self, clean_df):
        config = {
            "normalization": {"method": "minmax"},
            "encoding": {"method": "label"},
        }
        result, report = preprocess_pipeline(clean_df, config)
        assert set(report["steps_executed"]) == {"normalization", "encoding"}

    def test_pipeline_respects_step_order(self, df):
        config = {
            "encoding": {"method": "label"},
            "missing_values": {"strategy": "drop"},
        }
        result, report = preprocess_pipeline(df, config)
        # missing_values must run before encoding regardless of dict order
        assert report["steps_executed"].index("missing_values") < report["steps_executed"].index("encoding")

    def test_pipeline_unknown_key_raises(self, clean_df):
        with pytest.raises(PreprocessingError):
            preprocess_pipeline(clean_df, {"unknown_step": {}})

    def test_pipeline_rows_before_after_tracked(self, df):
        config = {"missing_values": {"strategy": "drop"}}
        _, report = preprocess_pipeline(df, config)
        assert "rows_before" in report
        assert "rows_after" in report

    def test_pipeline_outlier_removal_step(self):
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 1000], "y": [1, 2, 3, 4, 5, 6]})
        config = {"outlier_removal": {"method": "iqr", "threshold": 1.5}}
        result, report = preprocess_pipeline(df, config)
        assert "outlier_removal" in report["steps_executed"]
        assert len(result) < len(df)


# ── normalize_columns zscore NaN edge case ────────────────────────────────────

class TestNormalizeZscoreNan:
    def test_zscore_skips_nan_std_column(self):
        """Column with all-same values and NaN — std is NaN, should be skipped."""
        df = pd.DataFrame({"x": [5.0, np.nan, 5.0, 5.0], "y": [1.0, 2.0, 3.0, 4.0]})
        result, report = normalize_columns(df, method="zscore")
        assert "x" in report["skipped_columns"]
        assert "y" in report["columns_normalized"]
