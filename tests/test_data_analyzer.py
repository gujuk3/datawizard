import pytest
import pandas as pd
import numpy as np
from datawizard_core.data_analyzer import (
    compute_basic_statistics,
    compute_correlation_matrix,
    compute_column_statistics,
    detect_missing_data,
    detect_outliers,
    generate_dataset_summary,
)
from datawizard_core.exceptions import ValidationError


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'age': [25, 30, 28, 35],
        'salary': [5000, 7000, 6000, 8000],
        'city': ['Istanbul', 'Ankara', 'Izmir', 'Istanbul'],
    })


# ── compute_basic_statistics ───────────────────────────────────────────────────

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


def test_basic_statistics_numeric_fields(sample_df):
    s = compute_basic_statistics(sample_df)['numeric']['age']
    for field in ('mean', 'median', 'std', 'min', 'max', 'q1', 'q3', 'skewness', 'non_null_count'):
        assert field in s


def test_basic_statistics_categorical_top_values(sample_df):
    s = compute_basic_statistics(sample_df)['categorical']['city']
    assert 'top_values' in s
    assert isinstance(s['top_values'], list)


# ── compute_correlation_matrix ─────────────────────────────────────────────────

def test_correlation_matrix(sample_df):
    corr = compute_correlation_matrix(sample_df)
    assert isinstance(corr, dict)
    assert 'columns' in corr
    assert 'age' in corr['columns']


def test_correlation_matrix_pearson(sample_df):
    corr = compute_correlation_matrix(sample_df, method='pearson')
    assert corr['method'] == 'pearson'


def test_correlation_matrix_spearman(sample_df):
    corr = compute_correlation_matrix(sample_df, method='spearman')
    assert corr['method'] == 'spearman'


def test_correlation_matrix_invalid_method_raises(sample_df):
    with pytest.raises(ValidationError):
        compute_correlation_matrix(sample_df, method='invalid')


def test_correlation_matrix_fewer_than_2_numeric_raises():
    df = pd.DataFrame({'city': ['A', 'B', 'C']})
    with pytest.raises(ValidationError):
        compute_correlation_matrix(df)


# ── detect_missing_data ────────────────────────────────────────────────────────

def test_detect_missing_data_no_missing(sample_df):
    result = detect_missing_data(sample_df)
    assert result['total_missing'] == 0


def test_detect_missing_data_with_missing():
    df = pd.DataFrame({'a': [1, None, 3], 'b': [4, 5, None]})
    result = detect_missing_data(df)
    assert result['total_missing'] == 2


def test_detect_missing_data_whitespace_counted():
    df = pd.DataFrame({'a': ['hello', '   ', 'world']})
    result = detect_missing_data(df)
    assert result['total_missing'] == 1


def test_detect_missing_data_column_report(sample_df):
    result = detect_missing_data(sample_df)
    assert len(result['columns']) == 3
    assert all('missing_count' in c for c in result['columns'])


# ── compute_column_statistics ──────────────────────────────────────────────────

def test_compute_column_statistics_numeric(sample_df):
    stats = compute_column_statistics(sample_df, 'age')
    assert stats['column_name'] == 'age'
    assert 'distribution' in stats
    assert 'bin_edges' in stats['distribution']


def test_compute_column_statistics_categorical(sample_df):
    stats = compute_column_statistics(sample_df, 'city')
    assert stats['column_name'] == 'city'
    assert isinstance(stats['distribution'], list)


def test_compute_column_statistics_invalid_column_raises(sample_df):
    with pytest.raises(ValidationError):
        compute_column_statistics(sample_df, 'nonexistent')


# ── detect_outliers ────────────────────────────────────────────────────────────

def test_detect_outliers_finds_extreme_value():
    df = pd.DataFrame({'x': [1, 2, 3, 4, 5, 1000]})
    result = detect_outliers(df)
    assert 'x' in result
    assert result['x']['outlier_count'] >= 1


def test_detect_outliers_no_outliers(sample_df):
    result = detect_outliers(sample_df)
    for col in ('age', 'salary'):
        assert result[col]['outlier_count'] == 0


def test_detect_outliers_invalid_method_raises(sample_df):
    with pytest.raises(ValidationError):
        detect_outliers(sample_df, method='zscore')


def test_detect_outliers_empty_column():
    df = pd.DataFrame({'x': [np.nan, np.nan, np.nan]})
    result = detect_outliers(df)
    assert result['x']['outlier_count'] == 0


# ── generate_dataset_summary ───────────────────────────────────────────────────

def test_generate_dataset_summary_keys(sample_df):
    summary = generate_dataset_summary(sample_df)
    for key in ('row_count', 'column_count', 'numeric_column_count', 'categorical_column_count',
                'missing_pct', 'duplicate_row_count', 'memory_usage_mb'):
        assert key in summary


def test_generate_dataset_summary_counts(sample_df):
    summary = generate_dataset_summary(sample_df)
    assert summary['row_count'] == 4
    assert summary['column_count'] == 3
    assert summary['numeric_column_count'] == 2
    assert summary['categorical_column_count'] == 1


def test_generate_dataset_summary_with_metadata(sample_df):
    one_mb = 1024 * 1024
    summary = generate_dataset_summary(sample_df, file_name='test.csv', file_size_bytes=one_mb)
    assert summary['file_name'] == 'test.csv'
    assert summary['file_size_mb'] == pytest.approx(1.0, rel=1e-3)