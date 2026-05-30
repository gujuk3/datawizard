# DataWizard

No-code data analysis and machine learning platform. Upload a CSV, explore statistics, train ML models, and get AI-generated explanations — no coding required.

## Features

- CSV upload and preview
- Descriptive statistics, correlation matrix, missing-value analysis
- Data preprocessing: imputation (mean/median/mode), encoding (one-hot/label), normalization (min-max/z-score), outlier removal
- Model training: Logistic Regression, Linear Regression, Random Forest, Decision Tree, KNN
- Model evaluation: accuracy, precision, recall, F1, confusion matrix, SHAP values
- Prediction on trained models (no retraining — models serialized to disk with `joblib`)
- LLM-generated explanations via Groq or a local MLX-LM server
- JWT authentication with email verification and password reset
- Mobile-responsive UI (collapsible sidebar)

## Local Development (SQLite)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

```bash
cd frontend && npm install && npm start
```

Frontend dev server runs on `:3000` and proxies `/api` requests to Django on `:8000`.

## Docker (PostgreSQL)

```bash
docker compose up --build
```

The app will be available at `http://localhost:8000`. On first run, create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

## Environment Variables

Create a `.env` file in the project root:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for local dev, `False` for production |
| `DATABASE_URL` | Postgres URL — leave unset to use SQLite locally |
| `POSTGRES_PASSWORD` | Postgres password used by docker-compose |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` or `console.EmailBackend` for dev |
| `RESEND_API_KEY` | Resend API key for transactional emails |
| `DEFAULT_FROM_EMAIL` | Sender address for outgoing emails |
| `FRONTEND_URL` | Base URL for email links (e.g. `http://localhost:8000`) |
| `LLM_PROVIDER` | `groq` (cloud) or `local` (MLX-LM server) |
| `GROQ_API_KEY` | Groq API key (required when `LLM_PROVIDER=groq`) |
| `LOCAL_LLM_BASE_URL` | Base URL of local OpenAI-compatible server |
| `LOCAL_LLM_MODEL` | Model name for local LLM |

## Services (Docker)

| Service | Port | Description |
|---|---|---|
| `web` | 8000 | Django + React (WhiteNoise) |
| `db` | 5432 | PostgreSQL 16 |

## Architecture

### Django Apps

| App | Responsibility |
|---|---|
| `users` | Custom `User` model, JWT auth, email verification, password reset |
| `datasets` | CSV upload/preview/delete — files stored under `media/` |
| `analytics` | Statistics, correlation, missing-value analysis, preprocessing, LLM explain |
| `ml` | Model training, evaluation, serialization, prediction |

All API routes are under `/api/`. Every other URL hits a catch-all that serves `index.html` for client-side React routing.

### `datawizard_core/` — Pure Python Engine

Intentionally decoupled from Django so it can be tested without the ORM:

| Module | Responsibility |
|---|---|
| `data_loader.py` | CSV loading and validation |
| `data_analyzer.py` | Statistics, correlation, missing-value analysis, outlier detection |
| `data_preprocessor.py` | Imputation, encoding, scaling, outlier removal, pipeline |
| `ml_engine.py` | Split, train, evaluate, feature importance, SHAP, save/load via joblib |
| `llm_prompter.py` | Prompt builder + Groq/local LLM caller |
| `visualizer.py` | Chart generation |
| `exceptions.py` | `ValidationError`, `TrainingError`, `LLMError`, etc. |

### ML Model Persistence

Trained sklearn models are serialized with `joblib` into `media/ml_models/<uuid>.pkl`. The path is stored in `MLModel.model_file` (FileField). Predictions load the `.pkl` directly — no retraining on predict.

### Auth Flow

JWT via `djangorestframework_simplejwt`. Email verification is required after registration — token stored in `EmailVerificationToken`. Password reset uses `PasswordResetToken` (1-hour expiry). Custom user model: `users.User`.

## Running Tests

Tests use SQLite in-memory via `core.test_settings` — no PostgreSQL needed locally.

```bash
source venv/bin/activate
pytest
```

Run with coverage:

```bash
pytest --cov=datawizard_core --cov=analytics --cov=datasets --cov=users --cov=ml --cov-report=term-missing
```

### Test Structure

| File | Covers |
|---|---|
| `tests/test_data_loader.py` | CSV loading, validation, type detection, preview |
| `tests/test_data_analyzer.py` | Statistics, correlation, missing-value detection, outliers, summaries |
| `tests/test_data_preprocessor.py` | Imputation, encoding, normalization, outlier removal, pipeline |
| `tests/test_ml_engine.py` | Split, train, evaluate, feature importance, save/load, pipeline |
| `tests/test_analytics_views.py` | Analytics API endpoints |
| `tests/test_datasets_views.py` | Dataset CRUD API endpoints |
| `tests/test_users_views.py` | Auth API endpoints (register, verify, login, reset) |
