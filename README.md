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
# Send beats fast
