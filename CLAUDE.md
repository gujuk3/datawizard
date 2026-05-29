# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

DataWizard is a no-code data analysis and ML platform. Users upload CSV files, run analytics and preprocessing, train sklearn models, and get LLM-generated explanations. The backend is Django REST Framework; the frontend is a React SPA served by WhiteNoise from the same Django process.

## Commands

### Backend
```bash
source venv/bin/activate
python manage.py runserver        # dev server on :8000 (SQLite by default)
python manage.py migrate
pytest                            # run all tests
pytest tests/test_ml_engine.py   # run a single test file
```

### Frontend
```bash
cd frontend
npm install
npm start        # dev server on :3000, proxies /api to :8000
npm run build    # production build → frontend/build/ (committed to repo)
```

### Docker (PostgreSQL, production-like)
```bash
docker compose up --build
docker compose exec web python manage.py createsuperuser
```
`entrypoint.sh` runs `migrate` and `collectstatic` automatically on container start.

## Architecture

### Django apps
| App | Responsibility |
|---|---|
| `users` | Custom `User` model, JWT auth, email verification, password reset |
| `datasets` | CSV upload/preview/delete — files stored under `media/` |
| `analytics` | Statistics, correlation, missing-value analysis, preprocessing, LLM explain |
| `ml` | Model training, evaluation, serialization, prediction |

All API routes are under `/api/`. Every other URL hits a catch-all that serves `index.html` for client-side React routing.

### `datawizard_core/` — pure Python, no Django
The engine layer, intentionally decoupled from Django so it can be tested without the ORM:
- `data_loader.py` — CSV loading and validation
- `data_analyzer.py` — statistics, correlation, missing-value analysis
- `data_preprocessor.py` — imputation, encoding, scaling
- `ml_engine.py` — split, train, evaluate, feature importance, SHAP, `save_model`/`load_model` via joblib
- `llm_prompter.py` — prompt builder + Groq/local LLM caller
- `visualizer.py` — chart generation
- `exceptions.py` — `ValidationError`, `TrainingError`

Django views are thin: load data → call `datawizard_core` → persist to DB.

### ML model persistence
Trained sklearn models are serialized with `joblib` into `media/ml_models/<uuid>.pkl`. The path is stored in `MLModel.model_file` (FileField). Predictions load the `.pkl` directly — no retraining on predict. `MLModel` records without a `model_file` (trained before this feature) return HTTP 400 asking the user to retrain.

### Auth flow
JWT via `djangorestframework_simplejwt`. Email verification is required after registration — token stored in `EmailVerificationToken`. Password reset uses `PasswordResetToken`. Custom user model: `users.User`.

### LLM
Controlled by `LLM_PROVIDER` env var (`groq` or `local`). Groq uses the `groq` Python SDK. Local uses an OpenAI-compatible endpoint at `LOCAL_LLM_BASE_URL`. All prompting goes through `datawizard_core/llm_prompter.py`.

### Key model notes
- `MLModel.feature_columns` and `MLModel.hyperparameters` are `JSONField`.
- `ModelMetric` stores scalar metrics as `FloatField`; complex metrics (confusion matrix, classification report) go into `additional_data` (`JSONField`).
- Tests live in `tests/` (not inside apps). `pytest.ini` sets `DJANGO_SETTINGS_MODULE = core.settings`.
