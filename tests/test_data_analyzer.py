import pytest
import pandas as pd
from datawizard_core.data_analyzer import compute_basic_statistics, compute_correlation_matrix, detect_missing_data


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'age': [25, 30, 28, 35],
        'salary': [5000, 7000, 6000, 8000],
        'city': ['Istanbul', 'Ankara', 'Izmir', 'Istanbul'],
    })


def test_basic_statistics_numeric(sample_df):
    stats = compute_basic_statistics(sample_df)
    assert 'numeric' in stats
    assert 'age' in stats['numeric']
    assert stats['numeric']['age']['mean'] == pytest.approx(29.5)


def test_basic_statistics_categorical(sample_df):
    stats = compute_basic_statistics(sample_df)
    assert 'categorical' in stats
    assert 'city' in stats['categorical']
    assert stats['categorical']['city']['unique_count'] == 3


def test_correlation_matrix(sample_df):
    corr = compute_correlation_matrix(sample_df)
    assert isinstance(corr, dict)
    assert 'columns' in corr
    assert 'age' in corr['columns']


def test_detect_missing_data_no_missing(sample_df):
    result = detect_missing_data(sample_df)
    assert result['total_missing'] == 0


def test_detect_missing_data_with_missing():
    df = pd.DataFrame({'a': [1, None, 3], 'b': [4, 5, None]})
    result = detect_missing_data(df)
    assert result['total_missing'] == 2