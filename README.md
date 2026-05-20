---
title: Wakeel AI Backend
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Wakeel AI - Backend 🚀

This is the FastAPI backend for the Wakeel AI mobile application. It provides a robust, asynchronous API with comprehensive authentication and a modular project structure.

## What's Built So Far

We've successfully established the foundational architecture and fully implemented the authentication service layer. 

### 1. Core Architecture & Database
- **Framework**: Built on **FastAPI** to ensure high performance and automatic interactive API documentation (Swagger UI).
- **Asynchronous ORM**: Integrated **SQLAlchemy 2.0** with async support, currently running on a local SQLite database (`wakeel-ai.db`) for rapid development.
- **Version Control**: Set up **Alembic** to manage database schema migrations asynchronously.

### 2. User & Authentication Models
- **Universal User Model**: Created a flexible `User` model that seamlessly accommodates both standard manual signups and third-party social logins.
- **Security**: Upgraded from `passlib` to native `bcrypt` to resolve compatibility issues and securely hash user passwords.
- **Stateless JWTs**: Built a dual-token system using `python-jose`. It generates a short-lived **Access Token** (for protected routes) and a long-lived **Refresh Token** (for maintaining user sessions).

### 3. API Endpoints
The following endpoints are fully operational under the `/api/v1/auth/` prefix:
- `POST /register`: Accepts a user's name, email, optional phone, and password to create a new account.
- `POST /login`: Authenticates an existing user and returns JWTs.
- `POST /google`: Verifies a Google `id_token` sent from the mobile app via `google-auth`. It intelligently links to an existing account or creates a new user on the fly.
- `POST /refresh`: Validates a refresh token and issues a fresh access token without requiring the user to log in again.
- `POST /logout`: Confirms successful logout (relies on the client to destroy tokens locally).
- `GET /api/v1/me`: A protected endpoint to fetch the currently authenticated user's profile details.

---

## Running the Application

### 1. Environment Setup
Activate your Python virtual environment:
```powershell
.\venv\Scripts\activate
```

### 2. Start the Server
Launch the FastAPI development server. (It is currently configured to run on port **8100**).
```powershell
python -m app.main
```

### 3. View API Documentation
Open your browser and navigate to:
```
http://localhost:8100/docs
```

### 4. Connect to Mobile via Ngrok
To expose this backend to your React Native app, start a secure tunnel on port 8100:
```powershell
ngrok http 8100
```
*Copy the generated `https://*.ngrok-free.app` URL and update the `BASE_URL` in your frontend's `.env` file.*
