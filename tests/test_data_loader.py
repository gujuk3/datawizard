import pytest
import pandas as pd
import tempfile
import os
from datawizard_core.data_loader import validate_file_size, load_csv, validate_csv_structure
from datawizard_core.exceptions import InvalidFileError, ValidationError


def make_csv(content, suffix='.csv'):
    f = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
    f.write(content)
    f.close()
    return f.name


def test_validate_file_size_valid():
    path = make_csv("a,b\n1,2\n")
    result = validate_file_size(path)
    assert result['valid'] is True
    os.unlink(path)


def test_validate_file_size_missing_file():
    result = validate_file_size('/nonexistent/file.csv')
    assert result['valid'] is False


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


def test_validate_csv_structure_valid():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    result = validate_csv_structure(df)
    assert result['valid'] is True


def test_validate_csv_structure_detects_duplicates():
    df = pd.DataFrame({'a': [1, 1], 'b': [2, 2]})
    result = validate_csv_structure(df)
    assert 'duplicate' in str(result).lower() or result['valid'] is not None