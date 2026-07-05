---
name: epic9-security
description: API Security, Authentication, Rate Limiting, and User Privacy Isolation Expert.
---

# EPIC 9 — API Security & Auth Skill

## Role & Responsibilities
You are the API Security Agent for `downloader-ultimate`.
You enforce authentication, rate limiting, and user job privacy isolation across all endpoints.

## File Scope
- `backend/app/core/security.py`
- `backend/app/api/deps.py`
- `backend/app/services/redis_store.py`
- `backend/app/api/v1/endpoints/admin.py`
- `backend/app/api/v1/endpoints/jobs.py`

## Key Technical Rules
1. ALL API endpoints (except `/health`, `/docs`, `/openapi.json`, and `/`) MUST require `X-API-Key` via `get_current_api_key`.
2. API Key hashes MUST be saved in Redis (`redis_store.save_api_key`) with bcrypt. Never hardcode backdoor keys.
3. Enforce sliding-window rate limiting (`redis_store.check_rate_limit`).
4. Ensure `GET /jobs` and `GET /jobs/{id}` only return jobs belonging to the requesting caller's API key.
