import pandas as pd
import numpy as np
from datawizard_core.exceptions import ValidationError

DEFAULT_HISTOGRAM_BINS = 20
TOP_VALUES_COUNT = 5
VALID_CORRELATION_METHODS = ["pearson", "spearman", "kendall"]

def _get_numeric_columns(df: pd.DataFrame) -> list:
    """Returns list of numeric column names."""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def _get_categorical_columns(df: pd.DataFrame) -> list:
    """Returns list of non-numeric column names."""
    return df.select_dtypes(exclude=[np.number]).columns.tolist()

def compute_basic_statistics(df: pd.DataFrame) -> dict:
    numeric_cols = _get_numeric_columns(df)
    categorical_cols = _get_categorical_columns(df)

    numeric_stats = {}
    for col in numeric_cols:
        series = df[col]
        non_null = series.dropna()
        std_val = float(non_null.std()) if len(non_null) > 1 else 0.0

        numeric_stats[col] = {
            "mean": round(float(non_null.mean()), 4) if len(non_null) > 0 else 0.0,
            "median": round(float(non_null.median()), 4) if len(non_null) > 0 else 0.0,
            "std": round(std_val, 4) if not np.isnan(std_val) else 0.0,
            "min": round(float(non_null.min()), 4) if len(non_null) > 0 else 0.0,
            "max": round(float(non_null.max()), 4) if len(non_null) > 0 else 0.0,
            "q1": round(float(non_null.quantile(0.25)), 4) if len(non_null) > 0 else 0.0,
            "q3": round(float(non_null.quantile(0.75)), 4) if len(non_null) > 0 else 0.0,
            "skewness": round(float(non_null.skew()), 4) if len(non_null) > 2 else 0.0,
            "non_null_count": int(non_null.count()),
        }

    categorical_stats = {}
    for col in categorical_cols:
        series = df[col]
        non_null = series.dropna()
        value_counts = non_null.value_counts()

        # Mode: most frequent value
        mode_val = str(value_counts.index[0]) if len(value_counts) > 0 else ""

        # Top N values
        top_values = [
            {"value": str(val), "count": int(cnt)}
            for val, cnt in value_counts.head(TOP_VALUES_COUNT).items()
        ]

        categorical_stats[col] = {
            "mode": mode_val,
            "unique_count": int(non_null.nunique()),
            "top_values": top_values,
            "non_null_count": int(non_null.count()),
        }

    return {
        "numeric": numeric_stats,
        "categorical": categorical_stats,
    }

def compute_column_statistics(df: pd.DataFrame, column_name: str) -> dict:
    if column_name not in df.columns:
        raise ValidationError(
            message=f"Column '{column_name}' not found in DataFrame.",
            details={
                "column_name": column_name,
                "available_columns": list(df.columns),
            },
        )

    series = df[column_name]
    is_numeric = pd.api.types.is_numeric_dtype(series)

    # Get base stats from compute_basic_statistics
    all_stats = compute_basic_statistics(df)

    if is_numeric and column_name in all_stats["numeric"]:
        stats = all_stats["numeric"][column_name].copy()

        # Add distribution: histogram
        non_null = series.dropna()
        if len(non_null) > 0:
            counts, bin_edges = np.histogram(non_null, bins=DEFAULT_HISTOGRAM_BINS)
            stats["distribution"] = {
                "bin_edges": [round(float(e), 4) for e in bin_edges],
                "counts": [int(c) for c in counts],
            }
        else:
            stats["distribution"] = {"bin_edges": [], "counts": []}

    elif column_name in all_stats["categorical"]:
        stats = all_stats["categorical"][column_name].copy()

        # Add distribution: full value counts sorted descending
        non_null = series.dropna()
        value_counts = non_null.value_counts()
        stats["distribution"] = [
            {"value": str(val), "count": int(cnt)}
            for val, cnt in value_counts.items()
        ]

    else:
        # Fallback for edge cases (e.g., datetime columns)
        non_null = series.dropna()
        stats = {
            "non_null_count": int(non_null.count()),
            "unique_count": int(non_null.nunique()),
            "distribution": [],
        }

    stats["column_name"] = column_name
    stats["dtype"] = str(series.dtype)

    return stats

def compute_correlation_matrix(
    df: pd.DataFrame,
    method: str = "pearson",
) -> dict:

    if method not in VALID_CORRELATION_METHODS:
        raise ValidationError(
            message=f"Invalid correlation method '{method}'. Valid: {VALID_CORRELATION_METHODS}",
            details={"method": method, "valid": VALID_CORRELATION_METHODS},
        )

    numeric_df = df.select_dtypes(include=[np.number])

    if numeric_df.shape[1] < 2:
        raise ValidationError(
            message=f"Need at least 2 numeric columns for correlation. Found {numeric_df.shape[1]}.",
            details={"numeric_column_count": numeric_df.shape[1]},
        )

    corr_matrix = numeric_df.corr(method=method)

    # Replace NaN (e.g., zero-variance column) with 0.0
    corr_matrix = corr_matrix.fillna(0.0)

    # Convert to nested list with rounding
    matrix_list = [
        [round(float(val), 4) for val in row]
        for row in corr_matrix.values
    ]

    return {
        "columns": corr_matrix.columns.tolist(),
        "matrix": matrix_list,
        "method": method,
    }

def detect_missing_data(df: pd.DataFrame) -> dict:
    # Replace empty strings and whitespace with NaN for uniform counting
    df_clean = df.replace(r"^\s*$", np.nan, regex=True)

    total_cells = int(df_clean.shape[0] * df_clean.shape[1])
    total_missing = int(df_clean.isna().sum().sum())
    total_missing_pct = round(
        (total_missing / total_cells * 100) if total_cells > 0 else 0.0, 2
    )

    column_reports = []
    for col in df_clean.columns:
        col_total = len(df_clean[col])
        col_missing = int(df_clean[col].isna().sum())
        col_missing_pct = round(
            (col_missing / col_total * 100) if col_total > 0 else 0.0, 2
        )

        column_reports.append({
            "name": col,
            "missing_count": col_missing,
            "missing_pct": col_missing_pct,
            "total_count": col_total,
        })

    return {
        "total_cells": total_cells,
        "total_missing": total_missing,
        "total_missing_pct": total_missing_pct,
        "columns": column_reports,
    }

def detect_outliers(
    df: pd.DataFrame,
    method: str = "iqr",
    threshold: float = 1.5,
) -> dict:

    if method != "iqr":
        raise ValidationError(
            message=f"Unsupported outlier detection method '{method}'. Currently supported: 'iqr'.",
            details={"method": method},
        )

    numeric_cols = _get_numeric_columns(df)
    result = {}

    for col in numeric_cols:
        series = df[col].dropna()

        if len(series) == 0:
            result[col] = {
                "outlier_count": 0,
                "outlier_pct": 0.0,
                "lower_bound": 0.0,
                "upper_bound": 0.0,
                "outlier_indices": [],
            }
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1

        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr

        # Find outlier indices (using original df index, including NaN rows)
        col_series = df[col]
        outlier_mask = (col_series < lower_bound) | (col_series > upper_bound)
        # Exclude NaN from being flagged as outliers
        outlier_mask = outlier_mask & col_series.notna()
        outlier_indices = df.index[outlier_mask].tolist()

        outlier_count = len(outlier_indices)
        total_non_null = int(col_series.notna().sum())
        outlier_pct = round(
            (outlier_count / total_non_null * 100) if total_non_null > 0 else 0.0, 2
        )

        result[col] = {
            "outlier_count": outlier_count,
            "outlier_pct": outlier_pct,
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
            "outlier_indices": outlier_indices,
        }

    return result

def generate_dataset_summary(
    df: pd.DataFrame,
    file_name: str = None,
    file_size_bytes: int = None,
) -> dict:

    numeric_cols = _get_numeric_columns(df)
    categorical_cols = _get_categorical_columns(df)

    total_cells = df.shape[0] * df.shape[1]
    total_missing = int(df.isna().sum().sum())
    missing_pct = round(
        (total_missing / total_cells * 100) if total_cells > 0 else 0.0, 2
    )

    # Memory usage in MB
    memory_bytes = df.memory_usage(deep=True).sum()
    memory_mb = round(memory_bytes / (1024 * 1024), 2)

    # File size conversion
    file_size_mb = None
    if file_size_bytes is not None:
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "numeric_column_count": len(numeric_cols),
        "categorical_column_count": len(categorical_cols),
        "missing_pct": missing_pct,
        "duplicate_row_count": int(df.duplicated().sum()),
        "memory_usage_mb": memory_mb,
        "file_name": file_name,
        "file_size_mb": file_size_mb,
    }