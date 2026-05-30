import pytest
import pandas as pd
import numpy as np
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from datasets.models import Dataset, DataColumn

User = get_user_model()

CLEAN_CSV = "age,salary,city\n25,5000,Istanbul\n30,7000,Ankara\n28,6000,Izmir\n35,8000,Istanbul\n"
MISSING_CSV = "age,salary,city\n25,,Istanbul\n30,7000,\n28,6000,Izmir\n35,8000,Istanbul\n"

# 40-row binary classification dataset — enough for reliable train/test split
_rows = [f"{20 + i},{4000 + i * 200},{i % 2}" for i in range(40)]
ML_CSV = "age,salary,label\n" + "\n".join(_rows)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        is_verified=True,
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def tmp_media(settings, tmp_path):
    """Override MEDIA_ROOT to an isolated temp dir for each test."""
    settings.MEDIA_ROOT = str(tmp_path)
    (tmp_path / "datasets").mkdir()
    return tmp_path


@pytest.fixture
def dataset(db, user, tmp_media):
    (tmp_media / "datasets" / "test.csv").write_text(CLEAN_CSV)
    ds = Dataset.objects.create(
        user=user,
        name="test.csv",
        file="datasets/test.csv",
        row_count=4,
        column_count=3,
        status="ready",
    )
    DataColumn.objects.create(dataset=ds, name="age", data_type="int64", missing_count=0, unique_count=4)
    DataColumn.objects.create(dataset=ds, name="salary", data_type="int64", missing_count=0, unique_count=4)
    DataColumn.objects.create(dataset=ds, name="city", data_type="object", missing_count=0, unique_count=3)
    return ds


@pytest.fixture
def dataset_with_missing(db, user, tmp_media):
    (tmp_media / "datasets" / "missing.csv").write_text(MISSING_CSV)
    ds = Dataset.objects.create(
        user=user,
        name="missing.csv",
        file="datasets/missing.csv",
        row_count=4,
        column_count=3,
        status="ready",
    )
    DataColumn.objects.create(dataset=ds, name="age", data_type="float64", missing_count=0, unique_count=4)
    DataColumn.objects.create(dataset=ds, name="salary", data_type="float64", missing_count=1, unique_count=3)
    DataColumn.objects.create(dataset=ds, name="city", data_type="object", missing_count=1, unique_count=3)
    return ds


@pytest.fixture
def ml_dataset(db, user, tmp_media):
    (tmp_media / "datasets" / "ml_test.csv").write_text(ML_CSV)
    ds = Dataset.objects.create(
        user=user,
        name="ml_test.csv",
        file="datasets/ml_test.csv",
        row_count=40,
        column_count=3,
        status="ready",
    )
    DataColumn.objects.create(dataset=ds, name="age", data_type="int64", missing_count=0, unique_count=40)
    DataColumn.objects.create(dataset=ds, name="salary", data_type="int64", missing_count=0, unique_count=40)
    DataColumn.objects.create(dataset=ds, name="label", data_type="int64", missing_count=0, unique_count=2)
    return ds


@pytest.fixture
def trained_ml_model(db, user, ml_dataset, tmp_media):
    from datawizard_core.ml_engine import (
        split_data, train_model, evaluate_classification_model, save_model,
    )
    from ml.models import MLModel, ModelMetric

    df = pd.read_csv(str(tmp_media / "datasets" / "ml_test.csv"))
    split = split_data(df, target_column="label", feature_columns=["age", "salary"])
    result = train_model(split["X_train"], split["y_train"], "logistic_regression", "classification")
    evaluation = evaluate_classification_model(result["model"], split["X_test"], split["y_test"])
    rel_path = save_model(result["model"], str(tmp_media))

    ml_model = MLModel.objects.create(
        user=user,
        dataset=ml_dataset,
        name="test_model",
        algorithm="logistic_regression",
        model_type="classification",
        target_column="label",
        feature_columns=["age", "salary"],
        hyperparameters={},
        train_test_split=0.2,
        training_status="completed",
        training_duration=0.1,
        model_file=rel_path,
    )
    for k, v in evaluation.items():
        if isinstance(v, (int, float)):
            ModelMetric.objects.create(model=ml_model, metric_name=k, metric_value=v)
        else:
            ModelMetric.objects.create(model=ml_model, metric_name=k, metric_value=None, additional_data=v)
    return ml_model
