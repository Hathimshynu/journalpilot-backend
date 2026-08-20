# JournalPilot Backend

FastAPI backend for JournalPilot, an academic manuscript analysis service. The API supports user authentication, Google sign-in, manuscript uploads, document text extraction, and Gemini-powered readiness analysis.

## Features

- FastAPI REST API with interactive OpenAPI documentation
- JWT authentication with email/password registration and login
- Google OAuth token verification
- PostgreSQL persistence through SQLAlchemy
- PDF and DOCX text extraction
- Gemini manuscript analysis with validated structured responses
- Static file and manuscript upload directories

## Requirements

- Python 3.11 or newer
- PostgreSQL 14 or newer
- A Gemini API key for manuscript analysis
- A Google OAuth web client ID if Google sign-in is enabled by the frontend

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/<your-account>/journalpilot-backend.git
cd journalpilot-backend
```

### 2. Create a PostgreSQL database

Create a database and user, or use an existing local PostgreSQL installation:

```sql
CREATE USER journalpilot WITH PASSWORD 'replace-with-a-password';
CREATE DATABASE journalpilot OWNER journalpilot;
```

The default connection format is:

```text
postgresql+psycopg://journalpilot:replace-with-a-password@localhost:5432/journalpilot
```

### 3. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Configure environment variables

Copy the example file:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Update `.env` with real values:

```dotenv
DATABASE_URL=postgresql+psycopg://journalpilot:replace-with-a-password@localhost:5432/journalpilot
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.6-flash
GOOGLE_CLIENT_ID=your-google-oauth-web-client-id
FRONTEND_URL=http://localhost:3000
```

Keep `.env` private. It is ignored by Git; only `.env.example` should be committed.

### 6. Start the development server

```bash
python -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

## API documentation

With the server running, open:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

## Main endpoints

### Authentication

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create an account and receive a JWT |
| `POST` | `/api/auth/login` | Log in with email and password |
| `POST` | `/api/auth/google` | Log in with a Google credential |
| `GET` | `/api/auth/me` | Return the authenticated user |

### Manuscripts

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/manuscripts/upload` | Upload a PDF or DOCX manuscript |
| `GET` | `/api/manuscripts` | List the current user's manuscripts |
| `GET` | `/api/manuscripts/{manuscript_id}` | Get one manuscript |

Protected endpoints require:

```http
Authorization: Bearer <access-token>
```

Uploads must include a `title` form field and a `file` form field. Supported file types are PDF and DOCX, with a maximum size of 20 MB.

## Project structure

```text
app/
  api/            HTTP route handlers
  core/           configuration, database, and security
  dependencies/   FastAPI dependencies such as authentication
  models/         SQLAlchemy database models
  schemas/        Pydantic request and response schemas
  services/       document extraction and Gemini integration
  workers/        background-work entry point
  main.py         FastAPI application entry point
static/           static assets
uploads/          uploaded manuscript files (ignored by Git)
tests/            test package
```

## Development notes

- Tables are created automatically when the application starts.
- Manuscript files are stored under `uploads/manuscripts/`.
- The analysis service currently sends at most 60,000 manuscript characters to Gemini and retries failed requests up to three times.
- Do not commit API keys, database passwords, generated uploads, or other secrets.

## Running checks

There are currently no test cases in the repository. After activating the virtual environment, you can verify that the application imports successfully with:

```bash
python -c "from app.main import app; print(app.title)"
```

## License

No license has been added yet. Add a license before distributing this project publicly.
