import pandas as pd
import numpy as np
from datawizard_core.exceptions import PreprocessingError, ValidationError
from datawizard_core.data_analyzer import detect_outliers as _detect_outliers

VALID_MISSING_STRATEGIES = ["drop", "mean", "median"]
VALID_ENCODING_METHODS = ["onehot", "label"]
VALID_NORMALIZATION_METHODS = ["minmax", "zscore"]
HIGH_CARDINALITY_WARNING_THRESHOLD = 20

PIPELINE_STEP_ORDER = [
    "missing_values",
    "outlier_removal",
    "normalization",
    "encoding",
]

def _get_numeric_columns(df: pd.DataFrame) -> list:
    """Returns list of numeric column names."""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def _get_categorical_columns(df: pd.DataFrame) -> list:
    """Returns list of non-numeric (object/category) column names."""
    return df.select_dtypes(include=["object", "category"]).columns.tolist()


def _validate_columns_exist(df: pd.DataFrame, columns: list, context: str):
    """Raises ValidationError if any column is missing from df."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValidationError(
            message=f"{context}: columns not found in DataFrame: {missing}",
            details={"missing_columns": missing, "available": list(df.columns)},
        )

def handle_missing_values(
    df: pd.DataFrame,
    strategy: str,
    columns: list = None,
) -> tuple:

    if strategy not in VALID_MISSING_STRATEGIES:
        raise PreprocessingError(
            message=f"Invalid missing value strategy '{strategy}'. Valid: {VALID_MISSING_STRATEGIES}",
            details={"strategy": strategy, "valid": VALID_MISSING_STRATEGIES},
        )

    result = df.copy()
    rows_before = len(result)
    target_cols = columns if columns is not None else list(result.columns)

    _validate_columns_exist(result, target_cols, "handle_missing_values")

    values_filled = 0

    if strategy == "drop":
        result = result.dropna(subset=target_cols)

    elif strategy in ("mean", "median"):
        for col in target_cols:
            missing_count = int(result[col].isna().sum())
            if missing_count == 0:
                continue

            if pd.api.types.is_numeric_dtype(result[col]):
                if strategy == "mean":
                    fill_value = result[col].mean()
                else:
                    fill_value = result[col].median()
            else:
                # Non-numeric: fill with mode
                mode_values = result[col].mode()
                fill_value = mode_values.iloc[0] if len(mode_values) > 0 else ""

            result[col] = result[col].fillna(fill_value)
            values_filled += missing_count

    rows_after = len(result)

    # Determine which columns were actually affected
    columns_affected = []
    for col in target_cols:
        original_missing = int(df[col].isna().sum())
        if original_missing > 0:
            columns_affected.append(col)

    report = {
        "strategy": strategy,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "values_filled": values_filled,
        "columns_affected": columns_affected,
    }

    return result, report

def encode_categorical_columns(
    df: pd.DataFrame,
    columns: list = None,
    method: str = "onehot",
) -> tuple:

    if method not in VALID_ENCODING_METHODS:
        raise PreprocessingError(
            message=f"Invalid encoding method '{method}'. Valid: {VALID_ENCODING_METHODS}",
            details={"method": method, "valid": VALID_ENCODING_METHODS},
        )

    result = df.copy()
    target_cols = columns if columns is not None else _get_categorical_columns(result)

    if not target_cols:
        return result, {
            "method": method,
            "columns_encoded": [],
            "new_columns_created": [],
            "mapping": {},
        }

    _validate_columns_exist(result, target_cols, "encode_categorical_columns")

    # Filter to only actual categorical columns in target list
    actual_categorical = [
        c for c in target_cols
        if not pd.api.types.is_numeric_dtype(result[c])
    ]

    new_columns_created = []
    mapping = {}
    columns_encoded = []

    # Log warning for high cardinality columns
    warnings = []
    for col in actual_categorical:
        unique_count = result[col].nunique()
        if unique_count > HIGH_CARDINALITY_WARNING_THRESHOLD:
            warnings.append(
                f"Column '{col}' has {unique_count} unique values (>{HIGH_CARDINALITY_WARNING_THRESHOLD})."
            )

    if method == "onehot":
        # Track original columns before encoding
        original_cols = set(result.columns)

        result = pd.get_dummies(result, columns=actual_categorical, dtype=int)

        # Identify new columns
        new_columns_created = [
            c for c in result.columns if c not in original_cols
        ]
        columns_encoded = actual_categorical

    elif method == "label":
        for col in actual_categorical:
            # Sort categories for deterministic label assignment
            categories = sorted(result[col].dropna().unique())
            cat_to_int = {cat: idx for idx, cat in enumerate(categories)}
            mapping[col] = cat_to_int

            result[col] = result[col].map(cat_to_int)
            columns_encoded.append(col)

    report = {
        "method": method,
        "columns_encoded": columns_encoded,
        "new_columns_created": new_columns_created,
        "mapping": mapping,
    }

    if warnings:
        report["warnings"] = warnings

    return result, report

def normalize_columns(
    df: pd.DataFrame,
    columns: list = None,
    method: str = "minmax",
) -> tuple:

    if method not in VALID_NORMALIZATION_METHODS:
        raise PreprocessingError(
            message=f"Invalid normalization method '{method}'. Valid: {VALID_NORMALIZATION_METHODS}",
            details={"method": method, "valid": VALID_NORMALIZATION_METHODS},
        )

    result = df.copy()
    target_cols = columns if columns is not None else _get_numeric_columns(result)

    if not target_cols:
        return result, {
            "method": method,
            "columns_normalized": [],
            "parameters": {},
            "skipped_columns": [],
        }

    _validate_columns_exist(result, target_cols, "normalize_columns")

    # Filter to only numeric columns in target list
    actual_numeric = [
        c for c in target_cols
        if pd.api.types.is_numeric_dtype(result[c])
    ]

    parameters = {}
    columns_normalized = []
    skipped_columns = []

    for col in actual_numeric:
        series = result[col]

        if method == "minmax":
            col_min = float(series.min())
            col_max = float(series.max())

            # Skip zero-variance (min == max)
            if col_min == col_max:
                skipped_columns.append(col)
                continue

            result[col] = (series - col_min) / (col_max - col_min)
            parameters[col] = {
                "min": round(col_min, 6),
                "max": round(col_max, 6),
            }
            columns_normalized.append(col)

        elif method == "zscore":
            col_mean = float(series.mean())
            col_std = float(series.std())

            # Skip zero-variance (std == 0)
            if col_std == 0 or np.isnan(col_std):
                skipped_columns.append(col)
                continue

            result[col] = (series - col_mean) / col_std
            parameters[col] = {
                "mean": round(col_mean, 6),
                "std": round(col_std, 6),
            }
            columns_normalized.append(col)

    report = {
        "method": method,
        "columns_normalized": columns_normalized,
        "parameters": parameters,
        "skipped_columns": skipped_columns,
    }

    return result, report

def remove_outliers(
    df: pd.DataFrame,
    columns: list = None,
    method: str = "iqr",
    threshold: float = 1.5,
) -> tuple:

    result = df.copy()
    rows_before = len(result)

    target_cols = columns if columns is not None else _get_numeric_columns(result)

    if not target_cols:
        return result, {
            "rows_before": rows_before,
            "rows_after": rows_before,
            "rows_removed": 0,
            "columns_checked": [],
        }

    _validate_columns_exist(result, target_cols, "remove_outliers")

    # Use detect_outliers to find all outlier indices
    # Build a temporary df with only target columns for detection
    outlier_report = _detect_outliers(result, method=method, threshold=threshold)

    # Collect all unique outlier row indices across target columns
    all_outlier_indices = set()
    columns_checked = []

    for col in target_cols:
        if col in outlier_report:
            indices = outlier_report[col]["outlier_indices"]
            all_outlier_indices.update(indices)
            columns_checked.append(col)

    # Drop outlier rows
    result = result.drop(index=list(all_outlier_indices))
    result = result.reset_index(drop=True)

    rows_after = len(result)

    report = {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_before - rows_after,
        "columns_checked": columns_checked,
    }

    return result, report

def preprocess_pipeline(df: pd.DataFrame, config: dict) -> tuple:

    # Validate config keys
    valid_keys = set(PIPELINE_STEP_ORDER)
    unknown_keys = set(config.keys()) - valid_keys
    if unknown_keys:
        raise PreprocessingError(
            message=f"Unknown pipeline config keys: {unknown_keys}. Valid: {valid_keys}",
            details={"unknown_keys": list(unknown_keys), "valid_keys": list(valid_keys)},
        )

    result = df.copy()
    rows_before = len(result)
    combined_report = {
        "steps_executed": [],
        "rows_before": rows_before,
    }

    # Execute steps in fixed order
    for step in PIPELINE_STEP_ORDER:
        if step not in config:
            continue

        step_config = config[step]

        if step == "missing_values":
            result, report = handle_missing_values(
                result,
                strategy=step_config.get("strategy", "drop"),
                columns=step_config.get("columns", None),
            )

        elif step == "outlier_removal":
            result, report = remove_outliers(
                result,
                columns=step_config.get("columns", None),
                method=step_config.get("method", "iqr"),
                threshold=step_config.get("threshold", 1.5),
            )

        elif step == "normalization":
            result, report = normalize_columns(
                result,
                columns=step_config.get("columns", None),
                method=step_config.get("method", "minmax"),
            )

        elif step == "encoding":
            result, report = encode_categorical_columns(
                result,
                columns=step_config.get("columns", None),
                method=step_config.get("method", "onehot"),
            )

        combined_report[step] = report
        combined_report["steps_executed"].append(step)

    combined_report["rows_after"] = len(result)

    return result, combined_report