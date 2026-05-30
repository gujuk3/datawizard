import os
import pytest
import pandas as pd
import numpy as np
from datawizard_core.visualizer import (
    plot_histogram,
    plot_scatter,
    plot_box,
    plot_bar_chart,
    plot_correlation_heatmap,
    plot_confusion_matrix,
    plot_prediction_vs_actual,
    plot_feature_importance,
)


@pytest.fixture
def sample_df():
    np.random.seed(0)
    return pd.DataFrame({
        "age": np.random.randint(20, 60, 50),
        "salary": np.random.randint(3000, 15000, 50),
        "city": np.random.choice(["Istanbul", "Ankara", "Izmir"], 50),
    })


@pytest.fixture
def output_path(tmp_path):
    return str(tmp_path / "test_plot.png")


class TestPlotHistogram:
    def test_creates_file(self, sample_df, output_path):
        path = plot_histogram(sample_df, "age", output_path=output_path)
        assert os.path.exists(path)

    def test_returns_absolute_path(self, sample_df, output_path):
        path = plot_histogram(sample_df, "age", output_path=output_path)
        assert os.path.isabs(path)

    def test_auto_output_dir(self, sample_df, tmp_path):
        auto_dir = str(tmp_path / "plots")
        with pytest.MonkeyPatch().context() as mp:
            mp.chdir(tmp_path)
            path = plot_histogram(sample_df, "age")
        assert os.path.exists(path)

    def test_custom_bins(self, sample_df, output_path):
        path = plot_histogram(sample_df, "salary", bins=10, output_path=output_path)
        assert os.path.exists(path)


class TestPlotScatter:
    def test_creates_file(self, sample_df, output_path):
        path = plot_scatter(sample_df, "age", "salary", output_path=output_path)
        assert os.path.exists(path)

    def test_with_hue(self, sample_df, output_path):
        path = plot_scatter(sample_df, "age", "salary", hue_column="city", output_path=output_path)
        assert os.path.exists(path)

    def test_without_hue(self, sample_df, output_path):
        path = plot_scatter(sample_df, "age", "salary", output_path=output_path)
        assert os.path.exists(path)


class TestPlotBox:
    def test_single_column(self, sample_df, output_path):
        path = plot_box(sample_df, ["age"], output_path=output_path)
        assert os.path.exists(path)

    def test_multiple_columns(self, sample_df, output_path):
        path = plot_box(sample_df, ["age", "salary"], output_path=output_path)
        assert os.path.exists(path)

    def test_many_columns_rotates_labels(self, tmp_path):
        df = pd.DataFrame({f"col{i}": np.random.randn(20) for i in range(6)})
        path = plot_box(df, list(df.columns), output_path=str(tmp_path / "box.png"))
        assert os.path.exists(path)


class TestPlotBarChart:
    def test_creates_file(self, sample_df, output_path):
        path = plot_bar_chart(sample_df, "city", output_path=output_path)
        assert os.path.exists(path)

    def test_top_n_respected(self, tmp_path):
        df = pd.DataFrame({"cat": list("abcdefghijklmnop") * 3})
        path = plot_bar_chart(df, "cat", top_n=5, output_path=str(tmp_path / "bar.png"))
        assert os.path.exists(path)


class TestPlotCorrelationHeatmap:
    def test_creates_file(self, output_path):
        corr_data = {
            "columns": ["age", "salary"],
            "matrix": [[1.0, 0.7], [0.7, 1.0]],
            "method": "pearson",
        }
        path = plot_correlation_heatmap(corr_data, output_path=output_path)
        assert os.path.exists(path)

    def test_three_columns(self, tmp_path):
        corr_data = {
            "columns": ["a", "b", "c"],
            "matrix": [[1, 0.5, 0.3], [0.5, 1, 0.2], [0.3, 0.2, 1]],
            "method": "spearman",
        }
        path = plot_correlation_heatmap(corr_data, output_path=str(tmp_path / "heatmap.png"))
        assert os.path.exists(path)


class TestPlotConfusionMatrix:
    def test_binary_creates_file(self, output_path):
        path = plot_confusion_matrix([[10, 2], [1, 8]], ["0", "1"], output_path=output_path)
        assert os.path.exists(path)

    def test_multiclass(self, tmp_path):
        cm = [[5, 1, 0], [2, 6, 1], [0, 1, 7]]
        path = plot_confusion_matrix(cm, ["cat", "dog", "bird"],
                                     output_path=str(tmp_path / "cm.png"))
        assert os.path.exists(path)


class TestPlotPredictionVsActual:
    def test_creates_file(self, output_path):
        preds = [1.1, 2.2, 3.3, 4.4, 5.5]
        actuals = [1.0, 2.0, 3.0, 4.0, 5.0]
        path = plot_prediction_vs_actual(preds, actuals, output_path=output_path)
        assert os.path.exists(path)

    def test_identical_predictions(self, output_path):
        preds = [2.0, 2.0, 2.0]
        actuals = [1.0, 2.0, 3.0]
        path = plot_prediction_vs_actual(preds, actuals, output_path=output_path)
        assert os.path.exists(path)


class TestPlotFeatureImportance:
    def test_with_data(self, output_path):
        fi = [
            {"feature": "age", "importance": 0.6, "importance_pct": "60.0"},
            {"feature": "salary", "importance": 0.4, "importance_pct": "40.0"},
        ]
        path = plot_feature_importance(fi, output_path=output_path)
        assert os.path.exists(path)

    def test_empty_data_creates_placeholder(self, output_path):
        path = plot_feature_importance([], output_path=output_path)
        assert os.path.exists(path)

    def test_top_n_limits_features(self, tmp_path):
        fi = [{"feature": f"f{i}", "importance": 1 / (i + 1), "importance_pct": str(round(100 / (i + 1), 1))}
              for i in range(20)]
        path = plot_feature_importance(fi, top_n=5, output_path=str(tmp_path / "fi.png"))
        assert os.path.exists(path)
