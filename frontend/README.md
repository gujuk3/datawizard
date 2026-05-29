# DataWizard Frontend

React SPA for the DataWizard platform. Communicates with the Django backend via `/api`.

## Development

```bash
npm install
npm start
```

Runs on `http://localhost:3000`. API requests are proxied to Django at `http://localhost:8000` (configured in `package.json` → `"proxy"`).

## Production Build

```bash
npm run build
```

Outputs to `frontend/build/`. Django serves this via WhiteNoise — no separate static server needed. The build is committed to the repo so Docker doesn't require a separate Node build step outside the container.

## Pages

| Route | Page |
|---|---|
| `/login` | Login |
| `/register` | Register |
| `/verify-email` | Email verification |
| `/forgot-password` | Request password reset |
| `/reset-password` | Set new password |
| `/upload` | Upload CSV dataset |
| `/analytics` | Dataset analysis and preprocessing |
| `/model-training` | Train and evaluate ML models |
