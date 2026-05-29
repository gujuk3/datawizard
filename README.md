# DataWizard

No-code data analysis and machine learning platform. Upload a CSV, explore statistics, train ML models, and get AI-generated explanations — no coding required.

## Features

- CSV upload and preview
- Descriptive statistics, correlation matrix, missing-value analysis
- Data preprocessing (imputation, encoding, scaling)
- Model training: Logistic Regression, Linear Regression, Random Forest, Decision Tree, KNN
- Model evaluation: accuracy, precision, recall, F1, confusion matrix, SHAP values
- Prediction on trained models (no retraining — models are serialized to disk)
- LLM-generated explanations via Groq or a local MLX-LM server
- JWT authentication with email verification and password reset

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

Create a `.env` file in the project root with the following:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for local dev, `False` for production |
| `DATABASE_URL` | Postgres URL — leave unset to use SQLite locally |
| `POSTGRES_PASSWORD` | Postgres password used by docker-compose |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` or `console.EmailBackend` for dev |
| `EMAIL_HOST_USER` | Gmail address |
| `EMAIL_HOST_PASSWORD` | Gmail App Password (16 chars) |
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
| `ollama` | 11434 | Ollama — optional, start with `--profile local-llm` |

## Running Tests

```bash
pytest
```
