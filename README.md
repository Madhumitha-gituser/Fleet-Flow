# FleetFlow – Logistics & Fleet Management Platform

A full-stack web application for managing fleets, drivers, shipments, and logistics operations. FleetFlow provides real-time vehicle tracking, route planning, maintenance scheduling, fuel monitoring, analytics, and an audit trail — all in one operations dashboard.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Major Features](#3-major-features)
4. [Technology Stack](#4-technology-stack)
5. [Architecture](#5-architecture)
6. [Database](#6-database)
7. [API Overview](#7-api-overview)
8. [Authentication](#8-authentication)
9. [Shipment Tracking](#9-shipment-tracking)
10. [Trip Management](#10-trip-management)
11. [Route Planning](#11-route-planning)
12. [ETA](#12-eta)
13. [WebSocket Real-Time Tracking](#13-websocket-real-time-tracking)
14. [Maintenance](#14-maintenance)
15. [Fuel Monitoring](#15-fuel-monitoring)
16. [Analytics](#16-analytics)
17. [Alerts](#17-alerts)
18. [Celery Background Jobs](#18-celery-background-jobs)
19. [Docker Setup](#19-docker-setup)
20. [Environment Variables](#20-environment-variables)
21. [Local Development Setup](#21-local-development-setup)
22. [Database Migration Setup](#22-database-migration-setup)
23. [Production Deployment](#23-production-deployment)
24. [Testing](#24-testing)

---

## 1. Project Overview

FleetFlow is a logistics and fleet management platform built with **FastAPI** (backend) and **React** (frontend). It centralises vehicle records, driver management, shipment tracking, trip lifecycle, route optimisation, maintenance scheduling, and operational analytics in a single dashboard.

---

## 2. Problem Statement

Logistics teams typically rely on disconnected spreadsheets, phone calls, and siloed software to manage vehicles, drivers, and deliveries. This leads to:

- No real-time visibility into vehicle or shipment location.
- Manual, error-prone maintenance scheduling.
- Fuel cost overruns due to lack of consumption tracking.
- Delayed delivery ETAs and poor customer communication.
- No audit trail for compliance or accountability.

FleetFlow solves these problems with a unified, real-time platform.

---

## 3. Major Features

| Feature | Description |
|---|---|
| **Vehicle Management** | Full CRUD for vehicle records including registration, model, status |
| **Driver Management** | Driver profiles, assignments, and attendance |
| **Shipment Tracking** | Create, update, and track shipments end-to-end |
| **Trip Management** | Trip lifecycle from scheduled → in-progress → completed |
| **Route Planning** | Real driving routes via OpenRouteService |
| **ETA Calculation** | Estimated arrival time based on route distance and speed |
| **Real-Time Tracking** | WebSocket-based live vehicle position simulation |
| **Maintenance** | Maintenance record management with scheduling |
| **Maintenance Alerts** | Automated alerts for upcoming/overdue maintenance (Celery) |
| **Fuel Monitoring** | Fuel consumption records and per-vehicle analytics |
| **Analytics** | Operational KPIs: fleet utilisation, fuel costs, delivery performance |
| **Dashboard** | Fleet and operations summary with live counts |
| **Reports** | Operational report generation |
| **Audit Logs** | Full audit trail of all create/update/delete actions |
| **User Management** | Role-based access control (Admin, Manager, Viewer) |

---

## 4. Technology Stack

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.12** | Runtime |
| **FastAPI** | REST API framework |
| **SQLAlchemy 2.0** | ORM |
| **Alembic** | Database migrations |
| **PostgreSQL** | Primary relational database |
| **psycopg2-binary** | PostgreSQL adapter |
| **python-jose** | JWT token encoding/decoding |
| **passlib + bcrypt** | Password hashing |
| **Celery 5** | Background task queue |
| **Redis 7** | Celery broker and result backend |
| **httpx** | Async HTTP client (ORS, Nominatim) |
| **websockets / Starlette** | WebSocket real-time tracking |
| **Uvicorn** | ASGI server |
| **python-dotenv** | Environment variable loading |

### Frontend
| Technology | Purpose |
|---|---|
| **React 18** | UI framework |
| **Vite 5** | Build tool |
| **React Router v7** | Client-side routing |
| **Axios** | HTTP client |
| **Leaflet + react-leaflet** | Interactive maps (OpenStreetMap tiles) |
| **Recharts** | Charts and analytics visualisation |
| **lucide-react** | Icon library |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Docker** | Containerisation |
| **Docker Compose** | Multi-service orchestration |
| **Nginx** | Frontend static file serving |
| **OpenRouteService (ORS)** | Driving route calculation |
| **Nominatim (OpenStreetMap)** | Geocoding (address → coordinates) |

> **Note:** This project uses **OpenStreetMap** (via Nominatim and Leaflet) and **OpenRouteService** for all mapping and routing. It does **not** use Google Maps.

---

## 5. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Docker Compose                           │
│                                                                  │
│  ┌──────────────┐     HTTP/WS     ┌──────────────────────────┐  │
│  │   Frontend   │ ─────────────── │       Backend            │  │
│  │  React/Vite  │                 │  FastAPI + Uvicorn       │  │
│  │  Nginx :80   │                 │  :8000                   │  │
│  └──────────────┘                 └──────────┬───────────────┘  │
│                                              │                   │
│                              ┌───────────────┼───────────────┐  │
│                              │               │               │  │
│                    ┌─────────▼──┐   ┌────────▼──────┐        │  │
│                    │ PostgreSQL │   │     Redis     │        │  │
│                    │    :5432   │   │     :6379     │        │  │
│                    └────────────┘   └───────┬───────┘        │  │
│                                             │                 │  │
│                              ┌──────────────┴──────────────┐ │  │
│                              │  Celery Worker + Beat        │ │  │
│                              │  (maintenance alerts)        │ │  │
│                              └─────────────────────────────┘ │  │
└──────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
             ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
             │ OpenRoute   │ │  Nominatim  │ │  OpenStreet │
             │ Service API │ │    (OSM)    │ │   Map Tiles │
             └─────────────┘ └─────────────┘ └─────────────┘
```

### Request flow
1. User browser → Nginx (port 80) → React SPA
2. React → FastAPI backend (port 8000) via Axios over HTTP
3. WebSocket tracking → `ws://backend:8000/ws/tracking/{trip_id}`
4. FastAPI → PostgreSQL (SQLAlchemy)
5. Celery Worker ← Redis broker ← beat schedule
6. FastAPI → ORS API (route planning), Nominatim (geocoding)

---

## 6. Database

**PostgreSQL 16** with **SQLAlchemy 2.0 ORM** and **Alembic** migrations.

### Schema (tables)
| Table | Description |
|---|---|
| `users` | Authentication accounts with roles |
| `drivers` | Driver profiles (license, phone, status) |
| `vehicles` | Vehicle records (plate, model, status) |
| `driver_assignments` | Links drivers to vehicles for a date range |
| `driver_attendance` | Daily check-in/check-out records |
| `shipments` | Shipment records with tracking numbers |
| `trips` | Trip records linking vehicles, drivers, and shipments |
| `maintenance` | Maintenance records with type, cost, dates |
| `maintenance_alerts` | Auto-generated alerts for upcoming maintenance |
| `fuel_records` | Fuel fill-up records per vehicle |
| `audit_logs` | Immutable audit trail of all mutations |

### Key relationships
- A `trip` links one `vehicle`, one `driver`, and one `shipment`.
- `maintenance_alerts` are generated automatically by Celery Beat.
- All create/update/delete operations write an `audit_log` entry.

---

## 7. API Overview

Base URL: `http://localhost:8000` (local) or your deployed backend URL.

Interactive documentation (auto-generated by FastAPI):
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoint groups

| Prefix | Router | Description |
|---|---|---|
| `/auth` | `auth.py` | Register, Login |
| `/users` | `users.py` | User management |
| `/drivers` | `driver.py` | Driver CRUD + performance |
| `/vehicles` | `vehicle.py` | Vehicle CRUD |
| `/shipments` | `shipment.py` | Shipment CRUD + tracking status |
| `/trips` | `trip.py` | Trip CRUD + route + ETA |
| `/driver-assignments` | `driver_assignment.py` | Assignment management |
| `/driver-attendance` | `driver_attendance.py` | Attendance records |
| `/maintenance` | `maintenance.py` | Maintenance CRUD |
| `/maintenance-alerts` | `maintenance_alerts.py` | Alert listing |
| `/fuel-records` | `fuel_record.py` | Fuel record CRUD |
| `/analytics` | `analytics.py` | Operations + fuel analytics |
| `/dashboard` | `dashboard.py` | Summary + fleet overview |
| `/reports` | `reports.py` | Report generation |
| `/audit-logs` | `audit_log.py` | Audit trail |
| `/ws/tracking/{trip_id}` | `websocket/router.py` | WebSocket real-time tracking |

---

## 8. Authentication

- **JWT (JSON Web Tokens)** using `python-jose` (HS256 algorithm).
- Passwords hashed with **bcrypt** via `passlib`.
- Token validity: **8 hours**.
- Token is stored in `localStorage` by the frontend and sent as `Authorization: Bearer <token>` on every API request.
- Role-based access control: `Admin`, `Manager`, `Viewer`.
- The JWT secret is read from the `JWT_SECRET_KEY` environment variable.

### Login flow
```
POST /auth/login  { "email": "...", "password": "..." }
→ { "access_token": "...", "token_type": "bearer" }
```

---

## 9. Shipment Tracking

- Each shipment has a unique **tracking number** (e.g. `FLT100003`).
- Status lifecycle: `Pending → In Transit → Delivered / Cancelled`.
- `GET /shipments/{tracking_number}/status` returns current status.
- Status changes broadcast to all WebSocket clients watching the associated trip.

---

## 10. Trip Management

- A trip links a `vehicle`, `driver`, and `shipment`.
- Status lifecycle: `Scheduled → In Progress → Completed / Cancelled`.
- The backend auto-geocodes pickup/destination addresses to lat/lon using **Nominatim**.
- Route geometry (polyline) is fetched from **OpenRouteService** when the trip is created.

---

## 11. Route Planning

- **Service:** OpenRouteService (ORS) — `app/services/route_service.py`.
- **Geocoding:** Nominatim (OpenStreetMap) — `app/services/geocoding_service.py`.
- `GET /trips/{id}/route` returns distance (km), estimated duration (min), and encoded polyline.
- The frontend renders the route on a **Leaflet** map.
- ORS API key is configured via `ORS_API_KEY` environment variable.

---

## 12. ETA

- `GET /trips/{id}/eta` calculates estimated time of arrival.
- **Service:** `app/services/eta_service.py`.
- Calculation is based on route distance and an assumed average speed.

---

## 13. WebSocket Real-Time Tracking

- Endpoint: `ws://host:8000/ws/tracking/{trip_id}?token=<jwt>`
- **Authentication:** JWT passed as a query parameter (browsers cannot set WebSocket headers).
- **Connection manager:** `app/websocket/connection_manager.py` — manages active connections per trip.
- **Simulation:** `app/websocket/simulation.py` — broadcasts location updates along the route polyline every ~3 seconds.
- **Message types:**
  - `location_update` — `{ type, trip_id, latitude, longitude, timestamp }`
  - `status_update` — `{ type, trip_id, tracking_number, status, updated_at }`
- Frontend: `Tracking.jsx` page with Leaflet map.

---

## 14. Maintenance

- Full CRUD for maintenance records: `GET/POST /maintenance/`, `PUT/PATCH /maintenance/{id}`.
- Each record tracks: vehicle, type (oil change, tyre rotation, etc.), scheduled/completed date, cost, status, notes.
- `GET /maintenance/vehicle/{vehicle_id}` — all maintenance for a specific vehicle.
- `PATCH /maintenance/{id}/cancel` — cancel a scheduled maintenance record.

---

## 15. Fuel Monitoring

- Full CRUD at `/fuel-records/`.
- Each record: vehicle, date, litres, cost per litre, total cost, odometer reading, station.
- `GET /analytics/fuel` — aggregate fuel analytics (total cost, average consumption, per-vehicle breakdown).
- Frontend: `FuelRecords.jsx` with charts (Recharts).

---

## 16. Analytics

- `GET /analytics/operations` — fleet utilisation, trip completion rates, on-time delivery rates, driver performance.
- `GET /analytics/fuel` — fuel cost trends and consumption per vehicle.
- `GET /dashboard/summary` — high-level counts (active vehicles, active trips, pending shipments).
- `GET /dashboard/fleet` — fleet status breakdown.
- Frontend: `FleetAnalytics.jsx` with Recharts visualisations.

---

## 17. Alerts

- **Maintenance alerts** (`/maintenance-alerts/`) — list of upcoming and overdue maintenance.
- Alerts are generated automatically by the **Celery Beat** periodic task.
- Alert threshold: configurable via `MAINTENANCE_ALERT_REMINDER_DAYS` (default: 7 days).
- Frontend displays alerts in the dashboard and maintenance views.

---

## 18. Celery Background Jobs

**Confirmed implemented** in `app/celery.py`.

| Item | Value |
|---|---|
| App name | `fleetflow` |
| Broker | Redis (`CELERY_BROKER_URL`) |
| Result backend | Redis (`CELERY_RESULT_BACKEND`) |
| Task | `app.celery.check_due_maintenance_alerts` |
| Schedule | Every `MAINTENANCE_ALERT_CHECK_INTERVAL_MINUTES` minutes (default: 60) |
| What it does | Queries vehicles for upcoming maintenance and creates `MaintenanceAlert` records |

### Local development without Redis
Set `CELERY_TASK_ALWAYS_EAGER=true` in `.env` to run tasks synchronously without a broker.

### Running workers manually (local, without Docker)
```bash
# Worker
celery -A app.celery:celery_app worker --loglevel=info

# Beat scheduler (separate terminal)
celery -A app.celery:celery_app beat --loglevel=info
```

---

## 19. Docker Setup

### Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose plugin)
- A `.env` file at the project root (copy from `.env.example`)

### Quick start
```bash
# 1. Clone the repository
git clone https://github.com/springboardmentor553-maker/Fleet-Management-Logistics-Tracking-Platform.git
cd Fleet-Management-Logistics-Tracking-Platform

# 2. Create environment file
cp .env.example .env
# Edit .env and fill in POSTGRES_PASSWORD, JWT_SECRET_KEY, ORS_API_KEY, etc.

# 3. Build and start all services
docker compose up --build

# 4. Run database migrations (first run only)
docker compose exec backend alembic upgrade head

# 5. Access the application
# Frontend:  http://localhost
# Backend:   http://localhost:8000
# API docs:  http://localhost:8000/docs
```

### Services started by `docker compose up`

| Service | Container | Port | Description |
|---|---|---|---|
| `postgres` | `fleetflow_postgres` | 5432 | PostgreSQL 16 |
| `redis` | `fleetflow_redis` | 6379 | Redis 7 |
| `backend` | `fleetflow_backend` | 8000 | FastAPI (Uvicorn) |
| `celery` | `fleetflow_celery_worker` | — | Celery worker |
| `beat` | `fleetflow_celery_beat` | — | Celery Beat scheduler |
| `frontend` | `fleetflow_frontend` | 80 | React app (Nginx) |

### File structure for Docker
```
Fleet-Management-Logistics-Tracking-Platform/
├── docker-compose.yml          ← orchestrates all services
├── .env.example                ← copy to .env (never commit .env)
├── backend/
│   ├── Dockerfile              ← Python 3.12-slim + Uvicorn
│   ├── .dockerignore
│   └── app/
├── frontend/
│   ├── Dockerfile              ← Node 20 build + Nginx serve
│   ├── .dockerignore
│   └── nginx.conf              ← SPA routing + gzip + caching
```

---

## 20. Environment Variables

### Root `.env` (used by docker-compose)

| Variable | Required | Description |
|---|---|---|
| `POSTGRES_DB` | No | Database name (default: `fleetflow_db`) |
| `POSTGRES_USER` | No | DB user (default: `fleetflow`) |
| `POSTGRES_PASSWORD` | **Yes** | DB password — choose a strong value |
| `JWT_SECRET_KEY` | **Yes** | JWT signing secret — use `secrets.token_hex(32)` |
| `CORS_ALLOWED_ORIGINS` | No | Comma-separated frontend URLs (blank = localhost dev defaults) |
| `VITE_API_BASE_URL` | **Yes** | Public backend URL baked into the React bundle |
| `VITE_ORS_API_KEY` | No | ORS API key exposed to the frontend (optional) |
| `ORS_API_KEY` | No | ORS key for the backend route service |
| `NOMINATIM_USER_AGENT` | No | Nominatim user-agent string |
| `CELERY_BROKER_URL` | No | Redis broker URL (default: `redis://redis:6379/0`) |
| `CELERY_RESULT_BACKEND` | No | Redis result backend URL |
| `MAINTENANCE_ALERT_REMINDER_DAYS` | No | Days ahead to generate maintenance alerts (default: 7) |
| `MAINTENANCE_ALERT_CHECK_INTERVAL_MINUTES` | No | Celery Beat interval (default: 60) |

### Backend `backend/.env` (local development only)

| Variable | Description |
|---|---|
| `DATABASE_URL` | Full PostgreSQL connection string |
| `JWT_SECRET_KEY` | JWT secret |
| `ORS_API_KEY` | OpenRouteService API key |
| `NOMINATIM_USER_AGENT` | Nominatim user-agent |
| `CELERY_BROKER_URL` | `memory://` for local dev (no Redis needed) |
| `CELERY_RESULT_BACKEND` | `cache+memory://` for local dev |
| `CELERY_TASK_ALWAYS_EAGER` | `true` to run tasks synchronously |

### Frontend `frontend/.env` (local development only)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend API base URL |
| `VITE_ORS_API_KEY` | ORS API key (used for frontend map calls if any) |

---

## 21. Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 14+ running locally
- (Optional) Redis for Celery

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env: set DATABASE_URL, JWT_SECRET_KEY, ORS_API_KEY

# Run database migrations
alembic upgrade head

# Start the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: `http://localhost:8000`  
API docs at: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env   # or create manually
# Edit .env: VITE_API_BASE_URL=http://127.0.0.1:8000

# Start the dev server
npm run dev
```

Frontend runs at: `http://localhost:5173`

### Celery (optional for local dev)

```bash
# Option 1 — run tasks eagerly (no Redis needed)
# Set CELERY_TASK_ALWAYS_EAGER=true in backend/.env

# Option 2 — real Celery + Redis
# Install Redis locally then:
cd backend
celery -A app.celery:celery_app worker --loglevel=info
celery -A app.celery:celery_app beat --loglevel=info
```

---

## 22. Database Migration Setup

FleetFlow uses **Alembic** for schema migrations.

```bash
cd backend

# Apply all pending migrations
alembic upgrade head

# Create a new migration after modifying models
alembic revision --autogenerate -m "describe your change"

# Roll back one migration
alembic downgrade -1

# View migration history
alembic history

# Check current revision
alembic current
```

> **Docker:** Run migrations inside the container after starting services:
> ```bash
> docker compose exec backend alembic upgrade head
> ```

The `alembic/env.py` reads `DATABASE_URL` from the environment — no hardcoded credentials.

---

## 23. Production Deployment

> **Note:** Docker Desktop was not available during development, so containers were not started locally. All configuration has been validated statically. Runtime testing requires Docker.

### What is deployment-ready
- ✅ `backend/Dockerfile` — Python 3.12-slim, no secrets baked in
- ✅ `frontend/Dockerfile` — Multi-stage Node 20 build + Nginx
- ✅ `docker-compose.yml` — All 6 services with healthchecks
- ✅ `.env.example` — Full variable reference
- ✅ `backend/app/utils/security.py` — JWT secret from env
- ✅ `backend/app/main.py` — CORS from env
- ✅ `frontend/nginx.conf` — SPA routing + gzip + cache headers
- ✅ Root `.gitignore` — `.env` excluded

### Deployment steps

#### Step 1 — Provision infrastructure
Choose one:
- **VPS (Recommended):** DigitalOcean, Hetzner, Linode — install Docker Engine
- **AWS:** EC2 + RDS (PostgreSQL) + ElastiCache (Redis)
- **Google Cloud:** Cloud Run (backend) + Cloud SQL (PostgreSQL) + Memorystore (Redis)
- **Railway / Render:** Each service as a separate deploy

#### Step 2 — Configure environment
```bash
# On the server:
cp .env.example .env
# Fill in:
#   POSTGRES_PASSWORD=<strong-random>
#   JWT_SECRET_KEY=<output of: python -c "import secrets; print(secrets.token_hex(32))">
#   VITE_API_BASE_URL=https://api.yourdomain.com
#   CORS_ALLOWED_ORIGINS=https://yourdomain.com
#   ORS_API_KEY=<your ORS key>
```

#### Step 3 — Build and start
```bash
docker compose up --build -d
```

#### Step 4 — Run migrations
```bash
docker compose exec backend alembic upgrade head
```

#### Step 5 — Configure a reverse proxy (recommended)
Set up **Nginx** or **Caddy** on the host to:
- Terminate TLS (HTTPS)
- Proxy `/` to the frontend container (port 80)
- Proxy `/api/` or `api.yourdomain.com` to the backend container (port 8000)
- Proxy WebSocket connections (`/ws/`) to the backend

#### Step 6 — Verify
```bash
# Check all containers running
docker compose ps

# Check backend health
curl http://localhost:8000/

# Check frontend
curl http://localhost/
```

### Vercel (frontend) + Render (API) + Neon (database)

Vercel hosts static React well. FastAPI, WebSockets, and Alembic belong on **Render** (or similar). Use **Neon** for PostgreSQL.

1. **Neon** — Create a project, copy the pooled URI (`…-pooler…neon.tech…?sslmode=require`). Run migrations once the API can connect (`alembic upgrade head` runs automatically on Render when `RUN_MIGRATIONS=true`).
2. **Render** — Deploy the backend from `render.yaml` (or a Docker web service with context `backend`). Set:
   - `DATABASE_URL` = Neon URI
   - `JWT_SECRET_KEY` = long random secret
   - `ENVIRONMENT=production`
   - `RUN_MIGRATIONS=true`
   - `CELERY_TASK_ALWAYS_EAGER=true` (skip Redis/Celery on the free tier)
   - `FRONTEND_URL` and `CORS_ALLOWED_ORIGINS` = `https://your-app.vercel.app`
3. Confirm `https://your-render-service.onrender.com/health` returns `"database": "up"`.
4. **Vercel** — Root directory `frontend`. Environment variable `VITE_API_URL=https://your-render-service.onrender.com` (no trailing slash). Redeploy after changing it — Vite inlines the value at build time.
5. Sign out and sign in again so the JWT includes a normalized role (`Admin`, not `admin`).

### What still requires manual steps before production
1. **TLS/HTTPS** — Obtain a certificate (Let's Encrypt / Caddy) and configure the reverse proxy.
2. **Domain DNS** — Point your domain to the server IP.
3. **ORS API key** — Register at https://openrouteservice.org and add to `.env`.
4. **JWT secret** — Generate and keep secret: `python -c "import secrets; print(secrets.token_hex(32))"`.
5. **Strong DB password** — Never use a weak password in production.
6. **Firewall** — Expose only ports 80 and 443 externally; keep 5432, 6379, 8000 internal.
7. **Backups** — Configure PostgreSQL backups (e.g. `pg_dump` cron, managed DB snapshots).

---

## 24. Testing

### Backend tests

```bash
cd backend

# Install test dependencies (included in requirements.txt)
# pytest, pytest-asyncio

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest test_maintenance.py -v
pytest tests/ -v
```

Existing test files:
- `backend/test_maintenance.py` — maintenance service tests
- `backend/test_shipment_query.py` — shipment query tests
- `backend/tests/` — additional test suite

### Frontend tests

The frontend currently uses Vite's build process for validation.  
To verify the build compiles without errors:

```bash
cd frontend
npm install
npm run build
```

### API testing

Use the built-in **Swagger UI** at `http://localhost:8000/docs` to test all endpoints interactively, or import the OpenAPI spec into **Postman**.

### Static configuration validation (performed without Docker)

The following were verified statically:
- ✅ `docker-compose.yml` — valid YAML structure
- ✅ `backend/Dockerfile` — references `app.main:app` (correct)
- ✅ `frontend/Dockerfile` — uses `npm ci` + `npm run build` (matches `package.json`)
- ✅ `DATABASE_URL` — consistently uses `postgres` service name in compose
- ✅ `CELERY_BROKER_URL` — consistently uses `redis` service name in compose
- ✅ `JWT_SECRET_KEY` — read from env in `security.py` (no hardcoded secret in compose)
- ✅ `CORS_ALLOWED_ORIGINS` — read from env in `main.py`
- ✅ `VITE_API_BASE_URL` — passed as Docker build ARG → ENV → Vite bundle
- ✅ No real secrets in any committed file
- ✅ `.env` files excluded from git via `.gitignore`

### Tests that require Docker runtime (not performed — Docker not installed)
- Container build success
- Container startup and healthchecks
- Inter-service communication
- Database connection from backend container
- Celery worker connecting to Redis
- WebSocket end-to-end in container environment
- Frontend → backend API calls in container network

---

*Generated for FleetFlow v1.0.0 — August 2026*
