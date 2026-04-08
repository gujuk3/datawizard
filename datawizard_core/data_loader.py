import os
import pandas as pd
import numpy as np
from datawizard_core.exceptions import InvalidFileError, ValidationError

SUPPORTED_ENCODINGS = ["utf-8", "latin-1", "iso-8859-9"]
SUPPORTED_DELIMITERS = [",", ";", "\t"]
MAX_FILE_SIZE_MB = 50
HIGH_CARDINALITY_THRESHOLD = 50
BOOLEAN_VALUES = {0, 1}
SAMPLE_VALUES_COUNT = 5


def validate_file_size(file_path: str, max_size_mb: float = MAX_FILE_SIZE_MB) -> dict:
    if not os.path.exists(file_path):
        return {
            "valid": False,
            "file_size_mb": 0.0,
            "max_size_mb": max_size_mb,
        }

    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

    return {
        "valid": file_size_mb <= max_size_mb,
        "file_size_mb": file_size_mb,
        "max_size_mb": max_size_mb,
    }


def load_csv(
    file_path: str,
    encoding: str = "utf-8",
    delimiter: str = ",",
) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise InvalidFileError(
            message=f"File not found: {file_path}",
            details={"file_path": file_path},
        )

    _, ext = os.path.splitext(file_path)
    if ext.lower() != ".csv":
        raise InvalidFileError(
            message=f"Invalid file extension '{ext}'. Only .csv files are accepted.",
            details={"file_path": file_path, "extension": ext},
        )

    if encoding not in SUPPORTED_ENCODINGS:
        raise InvalidFileError(
            message=f"Unsupported encoding '{encoding}'. Supported: {SUPPORTED_ENCODINGS}",
            details={"encoding": encoding, "supported": SUPPORTED_ENCODINGS},
        )

    if delimiter not in SUPPORTED_DELIMITERS:
        raise InvalidFileError(
            message=f"Unsupported delimiter '{delimiter}'. Supported: {SUPPORTED_DELIMITERS}",
            details={"delimiter": delimiter, "supported": SUPPORTED_DELIMITERS},
        )

    try:
        df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
    except UnicodeDecodeError:
        raise InvalidFileError(
            message=f"Cannot decode file with encoding '{encoding}'. Try a different encoding.",
            details={"file_path": file_path, "encoding": encoding},
        )
    except pd.errors.ParserError as e:
        raise InvalidFileError(
            message=f"CSV parsing failed: {str(e)}",
            details={"file_path": file_path, "parser_error": str(e)},
        )
    except Exception as e:
        raise InvalidFileError(
            message=f"Unexpected error reading file: {str(e)}",
            details={"file_path": file_path, "error": str(e)},
        )

    if df.shape[0] == 0 or df.shape[1] == 0:
        raise ValidationError(
            message="The CSV file is empty (0 rows or 0 columns).",
            details={"rows": df.shape[0], "columns": df.shape[1]},
        )

    return df


def validate_csv_structure(df: pd.DataFrame) -> dict:
    errors = []
    row_count = len(df)
    column_count = len(df.columns)

    if row_count == 0:
        errors.append("Dataset contains no rows.")

    column_names = list(df.columns)
    unnamed_cols = [
        str(c) for c in column_names
        if str(c).strip() == "" or str(c).startswith("Unnamed")
    ]
    if unnamed_cols:
        errors.append(
            f"Found {len(unnamed_cols)} unnamed or empty column header(s): {unnamed_cols}"
        )

    seen = {}
    duplicate_columns = []
    for col in column_names:
        col_str = str(col)
        if col_str in seen:
            if col_str not in duplicate_columns:
                duplicate_columns.append(col_str)
        seen[col_str] = True

    if duplicate_columns:
        errors.append(
            f"Duplicate column names detected: {duplicate_columns}"
        )

    empty_columns = [
        col for col in df.columns
        if df[col].isna().all()
    ]
    if empty_columns:
        errors.append(
            f"{len(empty_columns)} column(s) are completely empty: {empty_columns}"
        )

    if df.isna().all().all() and row_count > 0:
        errors.append("All cells in the dataset are null.")

    return {
        "valid": len(errors) == 0,
        "row_count": row_count,
        "column_count": column_count,
        "duplicate_columns": duplicate_columns,
        "empty_columns": empty_columns,
        "errors": errors,
    }


def detect_column_types(df: pd.DataFrame) -> dict:
    result = {}

    for col in df.columns:
        series = df[col]
        original_dtype = str(series.dtype)
        unique_vals = series.dropna().unique()
        unique_count = len(unique_vals)

        sample_values = [
            str(v) for v in unique_vals[:SAMPLE_VALUES_COUNT]
        ]

        high_cardinality = False

        if pd.api.types.is_bool_dtype(series):
            dtype = "boolean"

        elif pd.api.types.is_numeric_dtype(series):
            non_null_unique = set(series.dropna().unique())
            if non_null_unique.issubset(BOOLEAN_VALUES) and len(non_null_unique) <= 2:
                dtype = "boolean"
            else:
                dtype = "numeric"

        elif pd.api.types.is_datetime64_any_dtype(series):
            dtype = "datetime"

        else:
            dtype = "categorical"
            if unique_count > HIGH_CARDINALITY_THRESHOLD:
                high_cardinality = True

        result[col] = {
            "dtype": dtype,
            "original_dtype": original_dtype,
            "unique_count": unique_count,
            "sample_values": sample_values,
            "high_cardinality": high_cardinality,
        }

    return result


def get_data_preview(df: pd.DataFrame, n_rows: int = 5) -> dict:
    n_rows = min(n_rows, len(df))

    preview_df = df.head(n_rows)

    rows = []
    for _, row in preview_df.iterrows():
        row_dict = {}
        for col in df.columns:
            val = row[col]

            if pd.isna(val):
                row_dict[col] = None
            elif isinstance(val, (np.integer,)):
                row_dict[col] = int(val)
            elif isinstance(val, (np.floating,)):
                row_dict[col] = float(val)
            elif isinstance(val, pd.Timestamp):
                row_dict[col] = val.isoformat()
            else:
                row_dict[col] = val

        rows.append(row_dict)

    return {
        "columns": list(df.columns),
        "rows": rows,
        "total_rows": len(df),
        "total_columns": len(df.columns),
    }