import os
import uuid
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import seaborn as sns

DEFAULT_OUTPUT_DIR = "plots"
DEFAULT_DPI = 150
DEFAULT_FIGSIZE = (10, 6)

# DataWizard color palette
COLORS = {
    "primary": "#6c5ce7",
    "secondary": "#00b894",
    "accent": "#fdcb6e",
    "danger": "#d63031",
    "neutral": "#636e72",
    "light": "#dfe6e9",
    "dark": "#2d3436",
}

PALETTE_MULTI = [
    "#6c5ce7", "#00b894", "#fdcb6e", "#d63031",
    "#0984e3", "#e17055", "#00cec9", "#fd79a8",
    "#636e72", "#a29bfe",
]

# Apply consistent style
sns.set_theme(style="whitegrid", palette=PALETTE_MULTI)
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "font.family": "sans-serif",
    "font.size": 10,
})

def _ensure_output_dir(output_path: str = None) -> str:
    if output_path is None:
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        filename = f"plot_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(DEFAULT_OUTPUT_DIR, filename)
    else:
        directory = os.path.dirname(output_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    return output_path


def _save_and_close(fig, output_path: str) -> str:
    fig.savefig(
        output_path,
        dpi=DEFAULT_DPI,
        bbox_inches="tight",
        facecolor="white",
        transparent=False,
    )
    plt.close(fig)
    return os.path.abspath(output_path)

def plot_histogram(
    df: pd.DataFrame,
    column: str,
    bins: int = 30,
    output_path: str = None,
) -> str:
    output_path = _ensure_output_dir(output_path)

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)

    sns.histplot(
        data=df,
        x=column,
        bins=bins,
        color=COLORS["primary"],
        kde=True,
        edgecolor="white",
        linewidth=0.5,
        alpha=0.7,
        ax=ax,
    )

    ax.set_title(f"Distribution of {column}", fontsize=14, fontweight="bold",
                 color=COLORS["dark"], pad=12)
    ax.set_xlabel(column, fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)

    return _save_and_close(fig, output_path)

def plot_scatter(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    hue_column: str = None,
    output_path: str = None,
) -> str:
    output_path = _ensure_output_dir(output_path)

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)

    scatter_kwargs = {
        "data": df,
        "x": x_column,
        "y": y_column,
        "alpha": 0.6,
        "edgecolor": "white",
        "linewidth": 0.3,
        "ax": ax,
    }

    if hue_column:
        scatter_kwargs["hue"] = hue_column
        n_unique = df[hue_column].nunique()
        scatter_kwargs["palette"] = PALETTE_MULTI[:n_unique]
    else:
        scatter_kwargs["color"] = COLORS["primary"]

    sns.scatterplot(**scatter_kwargs)

    ax.set_title(f"{y_column} vs {x_column}", fontsize=14, fontweight="bold",
                 color=COLORS["dark"], pad=12)
    ax.set_xlabel(x_column, fontsize=11)
    ax.set_ylabel(y_column, fontsize=11)

    if hue_column:
        ax.legend(title=hue_column, fontsize=9, title_fontsize=10)

    return _save_and_close(fig, output_path)

def plot_box(
    df: pd.DataFrame,
    columns: list,
    output_path: str = None,
) -> str:
    output_path = _ensure_output_dir(output_path)

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)

    # Melt for seaborn if multiple columns
    plot_data = df[columns].melt(var_name="Column", value_name="Value")

    sns.boxplot(
        data=plot_data,
        x="Column",
        y="Value",
        hue="Column",
        palette=PALETTE_MULTI[:len(columns)],
        width=0.5,
        legend=False,
        flierprops={"marker": "o", "markerfacecolor": COLORS["danger"],
                     "markersize": 4, "alpha": 0.5},
        ax=ax,
    )

    ax.set_title("Box Plot Comparison", fontsize=14, fontweight="bold",
                 color=COLORS["dark"], pad=12)
    ax.set_xlabel("", fontsize=11)
    ax.set_ylabel("Value", fontsize=11)

    # Rotate x labels if many columns
    if len(columns) > 4:
        ax.tick_params(axis="x", rotation=45)

    return _save_and_close(fig, output_path)

def plot_bar_chart(
    df: pd.DataFrame,
    column: str,
    top_n: int = 10,
    output_path: str = None,
) -> str:
    output_path = _ensure_output_dir(output_path)

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)

    value_counts = df[column].value_counts().head(top_n)

    bars = ax.barh(
        y=value_counts.index.astype(str),
        width=value_counts.values,
        color=COLORS["primary"],
        edgecolor="white",
        linewidth=0.5,
        alpha=0.85,
    )

    # Add count labels on bars
    for bar, count in zip(bars, value_counts.values):
        ax.text(
            bar.get_width() + max(value_counts.values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            str(count),
            va="center",
            fontsize=9,
            color=COLORS["dark"],
        )

    ax.set_title(f"Top {top_n} Values in {column}", fontsize=14, fontweight="bold",
                 color=COLORS["dark"], pad=12)
    ax.set_xlabel("Count", fontsize=11)
    ax.set_ylabel(column, fontsize=11)
    ax.invert_yaxis()  # Highest count on top

    return _save_and_close(fig, output_path)

def plot_correlation_heatmap(
    corr_data: dict,
    output_path: str = None,
) -> str:
    output_path = _ensure_output_dir(output_path)

    columns = corr_data["columns"]
    matrix = np.array(corr_data["matrix"])

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)

    # Custom diverging colormap centered on 0
    cmap = sns.diverging_palette(250, 150, s=80, l=55, as_cmap=True)

    sns.heatmap(
        matrix,
        annot=True,
        fmt=".2f",
        cmap=cmap,
        center=0,
        vmin=-1,
        vmax=1,
        xticklabels=columns,
        yticklabels=columns,
        square=True,
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"shrink": 0.8, "label": "Correlation"},
        annot_kws={"size": 9},
        ax=ax,
    )

    ax.set_title(f"Correlation Matrix ({corr_data.get('method', 'pearson').title()})",
                 fontsize=14, fontweight="bold", color=COLORS["dark"], pad=12)

    # Rotate labels for readability
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)

    return _save_and_close(fig, output_path)

def plot_confusion_matrix(
    cm_data: list,
    class_labels: list,
    output_path: str = None,
) -> str:
    output_path = _ensure_output_dir(output_path)

    cm = np.array(cm_data)
    fig, ax = plt.subplots(figsize=(8, 6))

    # Use a green-based colormap (matches mockup Figure 9)
    cmap = sns.light_palette(COLORS["secondary"], as_cmap=True)

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap=cmap,
        xticklabels=class_labels,
        yticklabels=class_labels,
        square=True,
        linewidths=1,
        linecolor="white",
        cbar=False,
        annot_kws={"size": 14, "fontweight": "bold"},
        ax=ax,
    )

    ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold",
                 color=COLORS["dark"], pad=12)
    ax.set_xlabel("Predicted Label", fontsize=11)
    ax.set_ylabel("True Label", fontsize=11)

    return _save_and_close(fig, output_path)

def plot_prediction_vs_actual(
    predictions: list,
    actuals: list,
    output_path: str = None,
) -> str:
    output_path = _ensure_output_dir(output_path)

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)

    predictions = np.array(predictions)
    actuals = np.array(actuals)

    # Scatter points
    ax.scatter(
        actuals, predictions,
        color=COLORS["primary"],
        alpha=0.5,
        edgecolor="white",
        linewidth=0.3,
        s=40,
    )

    # Perfect prediction line
    all_vals = np.concatenate([actuals, predictions])
    line_min, line_max = all_vals.min(), all_vals.max()
    margin = (line_max - line_min) * 0.05
    line_range = [line_min - margin, line_max + margin]

    ax.plot(
        line_range, line_range,
        color=COLORS["danger"],
        linestyle="--",
        linewidth=1.5,
        alpha=0.7,
        label="Perfect Prediction",
    )

    ax.set_title("Predicted vs Actual Values", fontsize=14, fontweight="bold",
                 color=COLORS["dark"], pad=12)
    ax.set_xlabel("Actual Values", fontsize=11)
    ax.set_ylabel("Predicted Values", fontsize=11)
    ax.legend(fontsize=9)

    # Equal aspect ratio for proper 45° line
    ax.set_xlim(line_range)
    ax.set_ylim(line_range)

    return _save_and_close(fig, output_path)

def plot_feature_importance(
    importance_data: list,
    top_n: int = 10,
    output_path: str = None,
) -> str:
    output_path = _ensure_output_dir(output_path)

    if not importance_data:
        # Empty plot with message for models without importance
        fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
        ax.text(0.5, 0.5, "Feature importance not available\nfor this model type.",
                ha="center", va="center", fontsize=14, color=COLORS["neutral"],
                transform=ax.transAxes)
        ax.set_axis_off()
        return _save_and_close(fig, output_path)

    # Take top N
    data = importance_data[:top_n]

    # Reverse for horizontal bar (highest on top)
    features = [d["feature"] for d in reversed(data)]
    importances = [d["importance"] for d in reversed(data)]
    pcts = [d["importance_pct"] for d in reversed(data)]

    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)

    # Gradient colors based on importance
    max_imp = max(importances) if importances else 1
    bar_colors = [
        COLORS["primary"] if imp >= max_imp * 0.5
        else COLORS["secondary"] if imp >= max_imp * 0.25
        else COLORS["neutral"]
        for imp in importances
    ]

    bars = ax.barh(
        y=features,
        width=importances,
        color=bar_colors,
        edgecolor="white",
        linewidth=0.5,
        alpha=0.85,
        height=0.6,
    )

    # Add percentage labels
    for bar, pct in zip(bars, pcts):
        ax.text(
            bar.get_width() + max_imp * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{pct}%",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=COLORS["dark"],
        )

    ax.set_title("Feature Importance", fontsize=14, fontweight="bold",
                 color=COLORS["dark"], pad=12)
    ax.set_xlabel("Importance", fontsize=11)
    ax.set_xlim(0, max_imp * 1.15)  # Room for labels

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return _save_and_close(fig, output_path)