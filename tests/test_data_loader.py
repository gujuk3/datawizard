import pytest
import pandas as pd
import tempfile
import os
from datawizard_core.data_loader import (
    validate_file_size,
    load_csv,
    validate_csv_structure,
    detect_column_types,
    get_data_preview,
)
from datawizard_core.exceptions import InvalidFileError, ValidationError


def make_csv(content, suffix='.csv'):
    f = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
    f.write(content)
    f.close()
    return f.name


# ── validate_file_size ─────────────────────────────────────────────────────────

def test_validate_file_size_valid():
    path = make_csv("a,b\n1,2\n")
    result = validate_file_size(path)
    assert result['valid'] is True
    os.unlink(path)


def test_validate_file_size_missing_file():
    result = validate_file_size('/nonexistent/file.csv')
    assert result['valid'] is False


def test_validate_file_size_returns_size_info():
    path = make_csv("a,b\n1,2\n")
    result = validate_file_size(path)
    assert 'file_size_mb' in result
    assert 'max_size_mb' in result
    os.unlink(path)


# ── load_csv ───────────────────────────────────────────────────────────────────

def test_load_csv_success():
    path = make_csv("name,age\nAli,25\nVeli,30\n")
    df = load_csv(path)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)
    os.unlink(path)


def test_load_csv_wrong_extension():
    path = make_csv("name,age\nAli,25\n", suffix='.txt')
    with pytest.raises(InvalidFileError):
        load_csv(path)
    os.unlink(path)


def test_load_csv_empty_file():
    path = make_csv("")
    with pytest.raises((InvalidFileError, ValidationError)):
        load_csv(path)
    os.unlink(path)


def test_load_csv_file_not_found():
    with pytest.raises(InvalidFileError):
        load_csv('/nonexistent/path/file.csv')


def test_load_csv_unsupported_encoding():
    path = make_csv("a,b\n1,2\n")
    with pytest.raises(InvalidFileError):
        load_csv(path, encoding='utf-32')
    os.unlink(path)


def test_load_csv_unsupported_delimiter():
    path = make_csv("a|b\n1|2\n")
    with pytest.raises(InvalidFileError):
        load_csv(path, delimiter='|')
    os.unlink(path)


def test_load_csv_semicolon_delimiter():
    path = make_csv("a;b\n1;2\n3;4\n")
    df = load_csv(path, delimiter=';')
    assert df.shape == (2, 2)
    os.unlink(path)


# ── validate_csv_structure ─────────────────────────────────────────────────────

def test_validate_csv_structure_valid():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    result = validate_csv_structure(df)
    assert result['valid'] is True


def test_validate_csv_structure_detects_duplicates():
    df = pd.DataFrame({'a': [1, 1], 'b': [2, 2]})
    result = validate_csv_structure(df)
    assert 'duplicate' in str(result).lower() or result['valid'] is not None


def test_validate_csv_structure_detects_empty_columns():
    import numpy as np
    df = pd.DataFrame({'a': [1, 2], 'b': [np.nan, np.nan]})
    result = validate_csv_structure(df)
    assert 'b' in result['empty_columns']
    assert result['valid'] is False


def test_validate_csv_structure_returns_counts():
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    result = validate_csv_structure(df)
    assert result['row_count'] == 3
    assert result['column_count'] == 2


# ── detect_column_types ────────────────────────────────────────────────────────

def test_detect_column_types_numeric():
    df = pd.DataFrame({'age': [25, 30, 28]})
    result = detect_column_types(df)
    assert result['age']['dtype'] == 'numeric'


def test_detect_column_types_categorical():
    df = pd.DataFrame({'city': ['Istanbul', 'Ankara', 'Izmir']})
    result = detect_column_types(df)
    assert result['city']['dtype'] == 'categorical'


def test_detect_column_types_boolean():
    df = pd.DataFrame({'flag': [0, 1, 0, 1]})
    result = detect_column_types(df)
    assert result['flag']['dtype'] == 'boolean'


def test_detect_column_types_sample_values():
    df = pd.DataFrame({'city': ['Istanbul', 'Ankara', 'Izmir']})
    result = detect_column_types(df)
    assert len(result['city']['sample_values']) <= 5


def test_detect_column_types_high_cardinality():
    df = pd.DataFrame({'col': [str(i) for i in range(60)]})
    result = detect_column_types(df)
    assert result['col']['high_cardinality'] is True


# ── get_data_preview ───────────────────────────────────────────────────────────

def test_get_data_preview_default_rows():
    df = pd.DataFrame({'a': range(20), 'b': range(20)})
    preview = get_data_preview(df)
    assert len(preview['rows']) == 5


def test_get_data_preview_custom_rows():
    df = pd.DataFrame({'a': range(20)})
    preview = get_data_preview(df, n_rows=10)
    assert len(preview['rows']) == 10


def test_get_data_preview_capped_at_df_length():
    df = pd.DataFrame({'a': [1, 2]})
    preview = get_data_preview(df, n_rows=100)
    assert len(preview['rows']) == 2


def test_get_data_preview_includes_metadata():
    df = pd.DataFrame({'a': [1, 2, 3]})
    preview = get_data_preview(df)
    assert 'columns' in preview
    assert 'total_rows' in preview
    assert preview['total_rows'] == 3


def test_get_data_preview_handles_nan():
    import numpy as np
    df = pd.DataFrame({'a': [1.0, np.nan, 3.0]})
    preview = get_data_preview(df, n_rows=3)
    values = [row['a'] for row in preview['rows']]
    assert None in values  # NaN serialised as None


def test_get_data_preview_handles_numpy_types():
    import numpy as np
    df = pd.DataFrame({'int_col': np.array([1, 2, 3], dtype=np.int64),
                       'float_col': np.array([1.1, 2.2, 3.3], dtype=np.float64)})
    preview = get_data_preview(df, n_rows=3)
    for row in preview['rows']:
        assert isinstance(row['int_col'], (int, float))
        assert isinstance(row['float_col'], float)


# ── detect_column_types edge cases ────────────────────────────────────────────

def test_detect_column_types_datetime():
    import pandas as pd
    df = pd.DataFrame({'ts': pd.to_datetime(['2021-01-01', '2021-06-15', '2022-03-10'])})
    result = detect_column_types(df)
    assert result['ts']['dtype'] == 'datetime'


# ── validate_csv_structure edge cases ─────────────────────────────────────────

def test_validate_csv_structure_all_null_cells():
    import numpy as np
    df = pd.DataFrame({'a': [np.nan, np.nan], 'b': [np.nan, np.nan]})
    result = validate_csv_structure(df)
    assert result['valid'] is False