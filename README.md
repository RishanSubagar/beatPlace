# BeatPlace

BeatPlace is a research-and-contact-discovery app that helps you upload a ZIP of beats, research target artists, find likely contact emails, and store the results as a job workflow.

## What it does

- Upload a ZIP archive containing tracks or release assets
- Enter one or more artist names to research
- Query search results for each artist using Serper
- Cache recent research results to avoid duplicate searches
- Fetch public pages and extract candidate contact emails
- Persist job state in SQLite and expose status via API/SSE
- Review candidate contacts without sending anything automatically

## Current stack

- Backend: Python + FastAPI + SQLite
- Frontend: React + Vite + Material UI
- Research: Serper API
- Contact extraction: OpenAI-based extraction pipeline
- Email delivery: SMTP integration prepared for production use

## CURRENT ISSUE
Pitfall when webistes hide email with javascript (requiring a paid account). Applications works as is, just low quality results.
May change to be more general purpose with user editable context to find anybody's email.

## Project structure

```text
backend/
  app/
    main.py
    job_service.py
    job_repository.py
    job_events.py
    models.py
    services/
  data/
    jobs.sqlite3
  tests/
frontend/
  src/
  public/
```

## Local setup

### 1) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with your SMTP and API credentials:

```env
SMTP_HOST=...
SMTP_PORT=...
SMTP_USER=...
SMTP_PASSWORD=...
SERPER_API_KEY=...
OPENAI_API_KEY=...
```

Then start the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- http://localhost:8000
- Health check: http://localhost:8000/health

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open the Vite app in the browser, typically at:

- http://localhost:5173

## API overview

Key endpoints:

- `POST /upload` - upload ZIP + artist names
- `GET /jobs/{job_id}` - fetch job status
- `GET /jobs/{job_id}/events` - SSE job updates
- `GET /jobs/{job_id}/people` - per-person status
- `GET /jobs/{job_id}/candidates` - contact candidates

## Status flow

A job progresses through statuses such as:

- `queued`
- `researching`
- `interpreting`
- `awaiting_approval`
- `completed`
- `failed`

People can also be tracked in states like:

- `researching`
- `finding_contacts`
- `pending_review`
- `no_candidates`
- `failed`

## Testing

Run the backend test suite:

```bash
cd backend
source .venv/bin/activate
python -m unittest discover tests
```

## Notes

- Research results are cached for 15 days to reduce duplicate Serper calls.
- Candidate emails are stored in SQLite pending review rather than sent immediately.
- The current app is a working research workflow scaffold; sending is intentionally guarded and not automatic.
