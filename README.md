# JournalPilot Backend

JournalPilot backend API built with FastAPI.

## Features

- FastAPI application scaffold
- JWT-based authentication
- SQLAlchemy database setup
- Pydantic schemas and validation

## Local setup

1. Create a virtual environment
2. Install dependencies:
   pip install -r requirements.txt
3. Copy the environment example:
   copy .env.example .env
4. Start the API:
   uvicorn app.main:app --reload

## API docs

Once the app is running, open:

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc
