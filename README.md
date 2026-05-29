# DataWizard

No-code data analysis and machine learning platform for non-technical users.

## Local Development (SQLite)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in your keys
python manage.py migrate
python manage.py runserver
```

```bash
cd frontend && npm install && npm start
```

## Docker (PostgreSQL)

```bash
cp .env.example .env        # fill in your keys
docker compose up --build
```

The app will be available at http://localhost:8000.

On first run, create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

### Environment variables

See `.env.example` for all required variables. Key ones:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | Postgres URL — leave unset for local SQLite |
| `EMAIL_BACKEND` | Use `smtp.EmailBackend` for real email, `console.EmailBackend` for dev |
| `EMAIL_HOST_USER` | Gmail address |
| `EMAIL_HOST_PASSWORD` | Gmail App Password (16 chars) |
| `LLM_PROVIDER` | `groq` (cloud) or `local` (MLX-LM server) |
| `GROQ_API_KEY` | Groq API key |

### Services

| Service | Port | Description |
|---|---|---|
| `web` | 8000 | Django + React (WhiteNoise) |
| `db` | 5432 | PostgreSQL 16 |
| `ollama` | 11434 | Ollama (optional, for local LLM generation) |
