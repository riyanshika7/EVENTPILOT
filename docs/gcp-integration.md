# Google Cloud Platform (GCP) Integration — Cloud Run & Production Strategy

**Project:** EventPilot AI — Plan Less, Celebrate More 🦥  
**Selected GCP Service:** **Google Cloud Run (Containerized Microservice)**  
**Target Persona:** College event organizers requiring multi-user reliability, zero local daemon requirements, and high availability.

---

## 1. Why Google Cloud Run?

While EventPilot AI is tested and configured locally with SQLite and Ollama, running a production web service for college organizers across campus networks requires a containerized runtime that:
1. **Does not require local laptops to be online.**
2. **Autoscales to zero** during inactive hours (zero continuous cost).
3. **Instantly bursts capacity** during busy campus registration weeks without manual server provisioning.
4. **Isolates environment secrets** (e.g. Sentry DSN, Gemma API credentials) inside Google Cloud Secret Manager.

Google AI Studio and Antigravity provide model prototyping and development tooling, but **Google Cloud Run** provides the native serverless cloud infrastructure on GCP.

---

## 2. Cloud Run Container Specification (`Dockerfile`)

```dockerfile
# Multi-stage lightweight Python container
FROM python:3.11-slim

# Prevent Python from writing .pyc files & buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend source
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose port and start via uvicorn
EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 3. Production Database Architecture on GCP

When migrating from local SQLite to Google Cloud Run:
- **Limitation Disclosed:** Cloud Run instances have ephemeral filesystems. Data in a local `eventpilot.db` resets when instances scale to zero.
- **Production Solution:** Connect Cloud Run to **Google Cloud SQL for PostgreSQL** (or an external hosted PostgreSQL URL) via `DATABASE_URL`. EventPilot AI's repository design abstracts persistence, allowing seamless migration by setting `DATABASE_URL=postgresql://user:pass@host:5432/eventpilot`.

---

## 4. Step-by-Step GCP Deployment Commands

To deploy EventPilot AI to Cloud Run using the `gcloud` CLI:

```bash
# 1. Authenticate with Google Cloud
gcloud auth login
gcloud config set project [YOUR_GCP_PROJECT_ID]

# 2. Build and deploy to Cloud Run
gcloud run deploy eventpilot-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AI_PROVIDER=openai_compatible,GEMMA_MODEL=gemma2-9b-it,INFERENCE_BASE_URL=https://api.groq.com/openai/v1 \
  --set-secrets INFERENCE_API_KEY=gemma-api-key:latest,SENTRY_DSN=sentry-dsn:latest
```

---

## 5. Cost & Free-Tier Suitability

- **Cloud Run Free Tier:** GCP provides **2 million free requests per month**, 360,000 GB-seconds of memory, and 180,000 vCPU-seconds free per month.
- EventPilot AI runs comfortably within the free allowance for student events and hackathon demonstrations.
