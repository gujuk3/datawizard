import time
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    mean_squared_error,
    r2_score,
)

from datawizard_core.exceptions import ValidationError, TrainingError

CLASSIFICATION_ALGORITHMS = {
    "logistic_regression": LogisticRegression,
    "random_forest_classifier": RandomForestClassifier,
    "decision_tree": DecisionTreeClassifier,
    "knn": KNeighborsClassifier,
}

REGRESSION_ALGORITHMS = {
    "linear_regression": LinearRegression,
    "random_forest_regressor": RandomForestRegressor,
}

ALL_ALGORITHMS = {**CLASSIFICATION_ALGORITHMS, **REGRESSION_ALGORITHMS}

ALGORITHM_DEFAULT_PARAMS = {
    "logistic_regression": {"max_iter": 1000, "random_state": 42},
    "random_forest_classifier": {"n_estimators": 100, "random_state": 42},
    "decision_tree": {"random_state": 42},
    "knn": {"n_neighbors": 5},
    "linear_regression": {},
    "random_forest_regressor": {"n_estimators": 100, "random_state": 42},
}

VALID_MODEL_TYPES = ["classification", "regression"]
MIN_TEST_SIZE = 0.1
MAX_TEST_SIZE = 0.5

def split_data(
    df: pd.DataFrame,
    target_column: str,
    feature_columns: list = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:

    # Validate target column
    if target_column not in df.columns:
        raise ValidationError(
            message=f"Target column '{target_column}' not found in DataFrame.",
            details={
                "target_column": target_column,
                "available_columns": list(df.columns),
            },
        )

    # Validate test_size range
    if not (MIN_TEST_SIZE <= test_size <= MAX_TEST_SIZE):
        raise ValidationError(
            message=f"test_size must be between {MIN_TEST_SIZE} and {MAX_TEST_SIZE}. Got {test_size}.",
            details={"test_size": test_size, "min": MIN_TEST_SIZE, "max": MAX_TEST_SIZE},
        )

    # Determine feature columns
    if feature_columns is None:
        feature_columns = [c for c in df.columns if c != target_column]
    else:
        missing = [c for c in feature_columns if c not in df.columns]
        if missing:
            raise ValidationError(
                message=f"Feature columns not found in DataFrame: {missing}",
                details={"missing_columns": missing, "available": list(df.columns)},
            )

    if len(feature_columns) == 0:
        raise ValidationError(
            message="No feature columns available for training.",
            details={"target_column": target_column},
        )

    X = df[feature_columns]
    y = df[target_column]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state,
    )

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "feature_names": feature_columns,
        "train_size": len(X_train),
        "test_size": len(X_test),
    }

def train_model(
    X_train,
    y_train,
    algorithm: str,
    model_type: str,
    hyperparameters: dict = None,
) -> dict:

    # Validate model_type
    if model_type not in VALID_MODEL_TYPES:
        raise TrainingError(
            message=f"Invalid model_type '{model_type}'. Valid: {VALID_MODEL_TYPES}",
            details={"model_type": model_type, "valid": VALID_MODEL_TYPES},
        )

    # Validate algorithm
    if algorithm not in ALL_ALGORITHMS:
        raise TrainingError(
            message=f"Unrecognized algorithm '{algorithm}'. Valid: {list(ALL_ALGORITHMS.keys())}",
            details={"algorithm": algorithm, "valid": list(ALL_ALGORITHMS.keys())},
        )

    # Validate algorithm-model_type match
    if model_type == "classification" and algorithm not in CLASSIFICATION_ALGORITHMS:
        raise TrainingError(
            message=f"Algorithm '{algorithm}' is not a classification algorithm.",
            details={
                "algorithm": algorithm,
                "model_type": model_type,
                "classification_algorithms": list(CLASSIFICATION_ALGORITHMS.keys()),
            },
        )
    if model_type == "regression" and algorithm not in REGRESSION_ALGORITHMS:
        raise TrainingError(
            message=f"Algorithm '{algorithm}' is not a regression algorithm.",
            details={
                "algorithm": algorithm,
                "model_type": model_type,
                "regression_algorithms": list(REGRESSION_ALGORITHMS.keys()),
            },
        )

    # Build parameters: start with defaults, override with user params
    params = ALGORITHM_DEFAULT_PARAMS.get(algorithm, {}).copy()
    if hyperparameters:
        params.update(hyperparameters)

    # Instantiate model
    model_class = ALL_ALGORITHMS[algorithm]

    try:
        model = model_class(**params)
    except TypeError as e:
        raise TrainingError(
            message=f"Invalid hyperparameters for {algorithm}: {str(e)}",
            details={"algorithm": algorithm, "hyperparameters": params, "error": str(e)},
        )

    # Train
    start_time = time.perf_counter()
    try:
        model.fit(X_train, y_train)
    except Exception as e:
        raise TrainingError(
            message=f"Model training failed: {str(e)}",
            details={"algorithm": algorithm, "error": str(e)},
        )
    training_duration = round(time.perf_counter() - start_time, 4)

    return {
        "model": model,
        "algorithm": algorithm,
        "model_type": model_type,
        "hyperparameters": params,
        "training_duration_seconds": training_duration,
    }

def evaluate_classification_model(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)

    # Sorted class labels for consistent matrix axes
    class_labels = sorted([str(c) for c in np.unique(y_test)])

    cm = confusion_matrix(y_test, y_pred)
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
        "confusion_matrix": cm.tolist(),
        "class_labels": class_labels,
        "classification_report": report_dict,
    }


def evaluate_regression_model(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)

    mse = float(mean_squared_error(y_test, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_test, y_pred))

    return {
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "r2_score": round(r2, 4),
        "predictions": [round(float(v), 4) for v in y_pred],
        "actuals": [round(float(v), 4) for v in y_test],
    }

def get_feature_importance(model, feature_names: list) -> list:
    importances = None

    # Tree-based models
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_

    # Linear models (Logistic Regression, Linear Regression)
    elif hasattr(model, "coef_"):
        coef = model.coef_
        # Logistic Regression multiclass: coef_ is 2D → average across classes
        if coef.ndim > 1:
            coef = np.mean(np.abs(coef), axis=0)
        else:
            coef = np.abs(coef)
        importances = coef

    # KNN or models without importance
    else:
        return []

    # Normalize to sum to 1
    total = importances.sum()
    if total > 0:
        importances = importances / total
    else:
        importances = np.zeros(len(feature_names))

    # Build sorted result
    result = []
    for name, imp in zip(feature_names, importances):
        result.append({
            "feature": name,
            "importance": round(float(imp), 4),
            "importance_pct": str(round(float(imp) * 100, 1)),
        })

    result.sort(key=lambda x: x["importance"], reverse=True)

    return result

def run_training_pipeline(df: pd.DataFrame, config: dict) -> dict:
    # Extract config
    target_column = config.get("target_column")
    if not target_column:
        raise ValidationError(
            message="'target_column' is required in training config.",
            details={"config_keys": list(config.keys())},
        )

    algorithm = config.get("algorithm")
    if not algorithm:
        raise ValidationError(
            message="'algorithm' is required in training config.",
            details={"config_keys": list(config.keys())},
        )

    model_type = config.get("model_type")
    if not model_type:
        raise ValidationError(
            message="'model_type' is required in training config.",
            details={"config_keys": list(config.keys())},
        )

    feature_columns = config.get("feature_columns", None)
    test_size = config.get("test_size", 0.2)
    random_state = config.get("random_state", 42)
    hyperparameters = config.get("hyperparameters", None)

    # Step 1: Split data
    split_info = split_data(
        df,
        target_column=target_column,
        feature_columns=feature_columns,
        test_size=test_size,
        random_state=random_state,
    )

    # Step 2: Train model
    train_result = train_model(
        X_train=split_info["X_train"],
        y_train=split_info["y_train"],
        algorithm=algorithm,
        model_type=model_type,
        hyperparameters=hyperparameters,
    )

    model = train_result["model"]

    # Step 3: Evaluate
    if model_type == "classification":
        metrics = evaluate_classification_model(
            model, split_info["X_test"], split_info["y_test"],
        )
    else:
        metrics = evaluate_regression_model(
            model, split_info["X_test"], split_info["y_test"],
        )

    # Step 4: Feature importance
    feature_importance = get_feature_importance(
        model, split_info["feature_names"],
    )

    # Build serializable split_info (without DataFrames/Series)
    split_summary = {
        "feature_names": split_info["feature_names"],
        "train_size": split_info["train_size"],
        "test_size": split_info["test_size"],
    }

    return {
        "model": model,
        "split_info": split_summary,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "training_duration_seconds": train_result["training_duration_seconds"],
        "algorithm": algorithm,
        "model_type": model_type,
    }