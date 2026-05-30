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

| Route | Page | Description |
|---|---|---|
| `/login` | Login | JWT login with email verification guard |
| `/register` | Register | Creates account, sends verification email |
| `/verify-email/:token` | Email Verification | Verifies token and auto-logs in |
| `/forgot-password` | Forgot Password | Sends password reset link |
| `/reset-password/:token` | Reset Password | Sets new password |
| `/dashboard` | Dashboard | Overview and quick links |
| `/upload` | Upload Dataset | CSV file upload with LLM initial insights |
| `/analytics` | Analytics | Statistics, correlation, missing-value analysis, preprocessing, AI explanation |
| `/training` | Model Training | Train and evaluate sklearn models |
| `/datasets` | My Datasets | Browse, preview, and delete uploaded datasets |

## Component Structure

```
src/
  api.js              — Axios instance with JWT interceptors
  App.js              — Router setup
  components/
    Layout.js         — App shell: responsive sidebar (mobile-friendly), nav links
    MarkdownText.js   — Renders LLM markdown output
  pages/
    Login.js
    Register.js
    VerifyEmail.js
    ForgotPassword.js
    ResetPassword.js
    Dashboard.js
    Upload.js
    Analytics.js
    ModelTraining.js
    MyDatasets.js
    DatasetDetail.js
```

## Mobile Support

The sidebar collapses on screens ≤ 768 px. A hamburger button (☰) appears in the top-left of the main content area to open it; tapping the overlay or a nav link closes it.
