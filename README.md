---
title: Wakeel AI Backend
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Wakeel AI - Backend 🚀

This is the FastAPI backend for the Wakeel AI mobile application. It provides a robust, asynchronous API with comprehensive authentication, a modular project structure, and advanced AI agents for legal assistance, document analysis, and voice transcription.

## What's Built So Far

We've established a full-featured backend architecture encompassing authentication, case management, real-time chat, AI-driven legal analysis, document processing, and voice transcription.

### 1. Core Architecture & Database
- **Framework**: Built on **FastAPI** to ensure high performance and automatic interactive API documentation (Swagger UI).
- **Asynchronous ORM**: Integrated **SQLAlchemy 2.0** with async support, currently running on a local SQLite database (`wakeel-ai.db`) for rapid development.
- **Version Control**: Set up **Alembic** to manage database schema migrations asynchronously.

### 2. User & Authentication Models
- **Universal User Model**: Created a flexible `User` model that seamlessly accommodates both standard manual signups and third-party social logins (Google Auth).
- **Security**: Utilizes native `bcrypt` to securely hash user passwords.
- **Stateless JWTs**: Built a dual-token system using `python-jose`. It generates a short-lived **Access Token** (for protected routes) and a long-lived **Refresh Token** (for maintaining user sessions).

### 3. AI Agents & Document Processing
- **Legal Analyst & Orchestrator**: Uses `langchain`, `langchain-google-genai` (Gemini), and `langchain-openai` for multi-agent legal analysis and case orchestration.
- **Document Specialist**: Advanced document ingestion utilizing `pymupdf`, `unstructured[pdf]`, and `pytesseract` for robust OCR and PDF parsing.
- **Vector Database**: Integrated **ChromaDB** for document embeddings and fast similarity search.
- **Voice Transcription**: Built-in voice capabilities powered by `google-genai` (Gemini Whisper) for accurate transcription.

### 4. API Endpoints
The backend exposes modular API routes under `/api/v1/`:

- **Authentication (`/auth`)**:
  - `POST /register`, `POST /login`, `POST /google` (Google OAuth login)
  - `POST /refresh`, `POST /logout`
  - `GET /me` (Fetch authenticated user profile)
- **Chat (`/chat`)**: Chat interface for AI legal advice.
- **Cases (`/cases`)**: Case management endpoints for user cases.
- **Documents (`/documents`)**: Upload, parse, and analyze legal documents.
- **Voice (`/voice`)**: Voice processing and transcription endpoints.
- **Legal Agent (`/legal`)**: AI agent execution for legal specific reasoning.

---

## Running the Application

### 1. Environment Setup
Create a virtual environment and activate it:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

Install the dependencies:
```powershell
pip install -r requirements.txt
```

Set up your `.env` file using `.env.example` as a reference.

### 2. Start the Server
Launch the FastAPI development server. (It is configured to run on port **8100**).
```powershell
python -m app.main
```
*Note: Database migrations (`alembic upgrade head`) will run automatically on startup.*

### 3. View API Documentation
Open your browser and navigate to the Swagger UI:
```
http://localhost:8100/docs
```

### 4. Connect to Mobile via Ngrok
To expose this backend to your React Native app, start a secure tunnel on port 8100:
```powershell
ngrok http 8100
```
*Copy the generated `https://*.ngrok-free.app` URL and update the `BASE_URL` in your frontend's `.env` file.*
