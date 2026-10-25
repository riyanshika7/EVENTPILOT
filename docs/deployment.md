# Render Deployment Guide — EventPilot AI

This guide explains how to deploy EventPilot AI as a free-tier web service on [Render](https://render.com).

---

## 1. Architecture On Render

- **Web Runtime:** Native Python web service running FastAPI and Uvicorn.
- **Port Binding:** Binds to `0.0.0.0` and listens on dynamic `$PORT` supplied by Render.
- **Health Check Path:** `/api/health` monitors service uptime.
- **AI Inference:** Deployed Render web instances do not have local GPUs or local Ollama daemons. Deployed instances call an external hosted Gemma endpoint (e.g. Groq free tier with `gemma2-9b-it`) or run in explicit `demo` mode.

---

## 2. Deploying via Blueprint (`render.yaml`)

1. Push your repository to GitHub:
   ```powershell
   git remote add origin https://github.com/riyanshika7/EVENTPILOT.git
   git push -u origin main
   ```
2. Log into [dashboard.render.com](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Select your connected GitHub repository (`EVENTPILOT`).
5. Render parses [`render.yaml`](render.yaml) automatically and configures:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Health Check: `/api/health`
6. Under Environment Variables, supply your secrets:
   - `INFERENCE_API_KEY`: *(Your free Groq or OpenRouter API key)*
   - `AI_PROVIDER`: `openai_compatible`
   - `GEMMA_MODEL`: `gemma2-9b-it`
   - `INFERENCE_BASE_URL`: `https://api.groq.com/openai/v1`
   - `SENTRY_DSN`: *(Your Sentry DSN)*
7. Click **Apply**. Render will build and deploy your application.

---

## 3. Disclosures & Free-Tier Constraints

- **Ephemeral Storage:** SQLite (`eventpilot.db`) on Render's free tier stores data on an ephemeral filesystem that resets when the container sleeps after 15 minutes of inactivity. For permanent cloud storage, configure a free managed PostgreSQL database via `DATABASE_URL`.
- **Cold Starts:** Free instances spin down after inactivity and may take 30–50 seconds to resume on the initial request.
