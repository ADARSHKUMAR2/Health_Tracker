# Health Tracker AI

A personal health analytics platform that combines Apple Health data, a PyTorch forecasting model, and multi-agent OpenAI coaching. Users can explore historical biometrics, get AI-driven insights, and receive predictions for tomorrow's resting heart rate.

## Architecture

```
┌─────────────────┐     JWT (Bearer)      ┌──────────────────┐
│  Next.js +      │ ────────────────────► │  FastAPI         │
│  Clerk Auth     │ ◄── streamed markdown │  (health-chat)   │
└─────────────────┘                       └────────┬─────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    ▼                              ▼                              ▼
            OpenAI Agents                   SQLite DB                      AWS S3
         (Lead Health Coach)            (daily_metrics)                  (sync)
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
  Historical Analyst    Predictive Forecaster
  (past metrics)        (PyTorch ML model)
```

| Layer | Stack |
|-------|-------|
| Frontend (primary) | Next.js, Clerk (`@clerk/nextjs@7.3.2`), streamed markdown UI |
| Frontend (legacy) | Streamlit dashboard + chat |
| Backend | FastAPI, `fastapi-clerk-auth`, OpenAI Agents SDK |
| Data | SQLite (`data/health_data.db`), Apple Health XML export |
| ML | PyTorch (`ML/models/`) |
| Storage | AWS S3 (database sync) |

## Clerk Authentication Flow

1. User signs in with Clerk.
2. User submits consultation notes in `pages/product.tsx`.
3. Frontend gets a Clerk JWT with `getToken()` and sends it as `Authorization: Bearer <token>`.
4. FastAPI verifies the JWT (`fastapi-clerk-auth`) and streams model output from OpenAI.
5. UI renders streamed markdown in real time.

### Clerk Compatibility Note

This project currently uses `@clerk/nextjs@7.3.2`.  
In this version, `SignedIn`, `SignedOut`, and `Protect` are not exported from `@clerk/nextjs` for this setup, so auth-aware UI is implemented with:

- `useAuth()` (`isSignedIn`) and
- `ClerkLoaded` / `ClerkLoading`

## Project Structure

```
health_tracker_AI/
├── backend/
│   ├── api.py              # FastAPI routes (health-chat, ingest-health)
│   └── storage_s3.py       # S3 database sync
├── frontend/
│   └── main_ui.py            # Streamlit UI (chat + 30-day dashboard)
├── openai_agents/
│   ├── health_agent.py       # Lead coach + specialist handoffs
│   ├── schemas.py            # Pydantic models & agent instructions
│   └── agent_tools/          # SQLite query + ML prediction tools
├── ML/
│   ├── train_model.py        # PyTorch model training
│   ├── predict.py            # Tomorrow's HR inference
│   └── models/               # Trained weights & scalers
├── services/
│   └── parse_export.py       # Apple Health XML → SQLite
├── shared/
│   └── config.py             # OpenAI / model configuration
└── data/
    ├── export.xml            # Apple Health export (not committed)
    └── health_data.db        # Local metrics database
```

## Features

- **Multi-agent coaching** — A lead health coach delegates to a historical analyst (SQLite queries) and a predictive forecaster (PyTorch model).
- **Apple Health ingestion** — Parses `export.xml` into daily step count, resting HR, and sleep hours.
- **Real-time ingestion** — iOS Shortcut webhook (`POST /api/ingest-health`) for daily metric updates.
- **S3 sync** — Database pulled on server startup and pushed after writes.
- **Streamlit dashboard** — 30-day charts for steps, heart rate, and sleep (legacy UI).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/health-chat` | Send a message to the health coach agent (Clerk JWT required in Next.js frontend) |
| `POST` | `/api/ingest-health` | Upsert daily metrics and sync to S3 |

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Node.js 18+ (for Next.js frontend)
- Clerk application (publishable + secret keys)
- OpenAI API key (or GitHub Models token)
- AWS credentials (optional, for S3 sync)

### Backend

```bash
# Install dependencies
uv sync

# Create .env with:
# OPENAI_API_KEY=...
# GITHUB_TOKEN=...          # optional, for GitHub Models
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# AWS_BUCKET_NAME=...
# CLERK_SECRET_KEY=...      # for JWT verification

# Parse Apple Health export into SQLite
uv run python services/parse_export.py

# Train the ML model (optional)
uv run python ML/train_model.py

# Start the API server
uv run uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

### Next.js Frontend (Clerk)

```bash
cd frontend-next   # or your Next.js app directory
npm install

# .env.local:
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
# CLERK_SECRET_KEY=...
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

### Streamlit UI (legacy)

```bash
uv run streamlit run frontend/main_ui.py
```

## Data Pipeline

1. Export Apple Health data from the Health app → place `export.xml` in `data/`.
2. Run `services/parse_export.py` to aggregate daily metrics into SQLite.
3. Optionally train the PyTorch model with `ML/train_model.py`.
4. On API startup, the latest database is downloaded from S3 (if configured).
5. Daily updates can arrive via the iOS Shortcut webhook or manual ingestion.

## License

Private project — all rights reserved.
