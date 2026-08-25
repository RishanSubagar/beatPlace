# Send beats fast

Demo scaffold: minimal backend + frontend to accept a ZIP, parse artist names, and demo sending via Nodemailer.

Quick start (demo):

1. Install dependencies for the backend

```bash
cd backend
npm install
```

2. (Optional) create `.env` from `.env.example` to configure SMTP. If you skip this, the server will use a test account and return preview URLs.

3. Start the server

```bash
npm start
```

4. Open http://localhost:3000 in your browser and try the demo form.

Next recommended steps:
- Replace `backend/emailFinder.js` with a real search/people-API integration (SerpAPI, Hunter, Clearbit, etc.).
- Add a background queue (Redis + BullMQ) for discovery and mass-sending.
- Replace demo frontend with a React app (I can scaffold this next).

Python FastAPI rewrite (new):
- A FastAPI backend has been added under `backend-python/`.
- It keeps the same upload/send demo behavior without introducing a database yet.
- Start it with:

```bash
cd backend-python
python3 -m venv --without-pip .venv
python3 -m pip --python .venv install -r requirements.txt
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 and submit the same form.
# Send beats fast
