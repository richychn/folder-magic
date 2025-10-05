# Drive Explorer

Full-stack reference app that authenticates with Google, lets a user pick a Drive folder, and lists its immediate
children. The backend is a FastAPI service handling OAuth and Google Drive API calls; the frontend is a Vite React
app using Google Picker for folder selection.

## Prerequisites
- Python 3.11+
- Node.js 18+
- Google Cloud project with OAuth consent screen and Drive API enabled

## Google Credentials
Create OAuth 2.0 credentials (Web application) and set the authorized redirect URI to `http://localhost:8000/api/auth/callback`.
Collect:
- Client ID
- Client secret

Create an API key for Google Picker.

## Backend Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Environment variables (use `.env` or export before running):
```bash
export GOOGLE_CLIENT_ID="<client-id>"
export GOOGLE_CLIENT_SECRET="<client-secret>"
export SESSION_SECRET_KEY="<random-32-char-string>"
export FRONTEND_ORIGIN="http://localhost:5173"
export BACKEND_ALLOWED_ORIGINS="http://localhost:5173"
# Optional: override session cookie settings in production
# export SESSION_COOKIE_SECURE="true"
```

Run the server:
```bash
uvicorn backend.app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

## Frontend Setup
```bash
cd frontend
npm install
```

Create `frontend/.env.local` (Vite loads this automatically):
```
VITE_BACKEND_ORIGIN=http://localhost:8000
VITE_GOOGLE_API_KEY=<google-picker-api-key>
```

Start the dev server:
```bash
npm run dev
```

## Usage
1. Start both servers.
2. Open `http://localhost:5173`.
3. Sign in with Google (OAuth handled on the backend via httpOnly cookie).
4. Launch the folder picker to choose a Drive folder; the page lists first-level subfolders and files with metadata.

## Testing & Formatting
- Backend: add new tests with `pytest`. (No tests included yet.)
- Linting: install `ruff` (see `pyproject.toml`) and run `ruff check .`.
- Frontend: use `npm run build` to ensure the production bundle compiles.
