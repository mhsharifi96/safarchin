# سفرچین (Safarchin)

Persian AI travel planning app. Describe a trip in natural language, answer a few short follow-up
questions, get a daily itinerary with places and routes on a map, pick accommodation, and keep adjusting
the plan conversationally.

- `backend/` — Django + DRF, Postgres, Redis, Celery, the LangChain planning agent.
- `frontend/` — Next.js (TypeScript, App Router), RTL/Persian/Jalali UI.
- `docs/` — `design-sync.md` (Stitch design-system sync: tokens used, screen→route mapping).
- `AGENT.md` — orientation notes for AI coding agents working in this repo (conventions, gotchas, how to
  run things). Worth reading before making non-trivial changes.

## Stack

Next.js + TypeScript · Django + DRF · PostgreSQL · Redis · Celery · `langchain-openai` · LangSmith · Tavily ·
Neshan (maps/places/routing).

## Quick start (local dev)

Two ways to run this — pick one (running both at once will fight over ports 3000/8000):

- **Everything in Docker:** `docker compose up -d` — Postgres, Redis, Django, Celery worker, and the
  Next.js dev server, each in a container with your source bind-mounted in (so edits still hot-reload).
  Copy `backend/.env.example` → `backend/.env` and `frontend/.env.local.example` → `frontend/.env.local`
  first.
- **Native (faster iteration, no rebuilds):** `./dev.sh` runs Postgres/Redis via Docker and the rest
  (Django, Celery, Next.js) as native processes on your machine, tailing all their logs. Or follow the
  manual steps below to run each piece yourself.

### 1. Infra (Postgres + Redis)

```bash
docker compose up -d db redis
```

Postgres is exposed on host port **5433** (not 5432, to avoid clashing with other local Postgres
containers), Redis on 6379. See `docker-compose.yml`.

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real API keys as you get them; safe defaults otherwise
python manage.py migrate
python manage.py test apps.accounts apps.trips   # 13 tests, run against real Postgres/Redis
python manage.py runserver 0.0.0.0:8000
```

In a second terminal, run the Celery worker (needed for itinerary generation):

```bash
cd backend && source .venv/bin/activate
celery -A config worker -l info
```

Emails (verification, password reset) print to the `runserver` console by default
(`EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`) — no SMTP setup needed for local dev.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000. The frontend calls the backend at `NEXT_PUBLIC_API_BASE_URL`
(`http://localhost:8000` by default) with `credentials: "include"` — session cookies + CSRF, no tokens in
localStorage.

## What works right now without any external API keys

Verified end-to-end (automated tests + manual curl/browser runs), against real Postgres/Redis, not mocks:

- Registration, email verification (console backend), login, logout, forgot/reset password — all with
  neutral error messages, rate limiting (Redis-backed DRF throttles), and real CSRF enforcement on
  authenticated mutations.
- Guest trip creation via an opaque Django session key, with ownership enforcement (a different
  session/user gets a 404, not a 403 — existence isn't leaked) and automatic transfer of guest trips to the
  account on register/login.
- Trip CRUD, `TripPreferences` kept as a single persisted object synced by both the chat endpoint and the
  editable-summary form.
- Celery pipeline: `POST /trips/{id}/generate/` enqueues a real Celery task, worker picks it up, and (without
  an LLM key) fails gracefully with a clear stored `error_message`, visible via polling — the plumbing is
  real, not stubbed out.
- Full Next.js RTL/Persian/Jalali UI: registration/login/trip-intake flow was driven through an actual
  browser (see `docs/design-sync.md`), Jalali date picker converts correctly (verified against today's real
  date), Persian digit formatting, LTR email/password fields inside the RTL page.

## What needs external credentials to actually do anything

Set these in `backend/.env` (see `backend/.env.example` for the full list):

| Variable | Enables | Where verified |
|---|---|---|
| `OPENAI_API_KEY` (+ `OPENAI_MODEL_NAME`, default `gpt-5.6-luna`) | The conversational intake agent and itinerary-generation agent (`langchain-openai`). Without it, both fail with an explicit, user-visible "not configured" message instead of crashing or faking a response. | `apps/planner/llm.py` |
| `TAVILY_API_KEY` | Web research tool the planning agent uses to find candidate places. | `apps/planner/tools/web_research.py` |
| `NESHAN_API_KEY` | Server-side Neshan Search/Geocoding/Reverse-geocoding/Routing/POI-details APIs used by the planning agent. Endpoint shapes were pulled from current Neshan docs (`platform.neshan.org/docs`), not guessed. | `apps/planner/tools/neshan.py` |
| `NEXT_PUBLIC_NESHAN_WEB_SDK_KEY` (frontend `.env.local`) | The actual map render (`@neshan-maps-platform/leaflet`). Without it, the UI shows an honest empty state, not a broken/blank map. | `frontend/src/components/trip/TripMap.tsx` |
| `LANGCHAIN_API_KEY` + `LANGCHAIN_TRACING_V2=true` | LangSmith tracing of the agent run. Optional — everything else works without it. | `config/settings.py` |
| SMTP vars (`EMAIL_BACKEND=...smtp.EmailBackend`, `SMTP_*`) | Real email delivery instead of the console backend. | `config/settings.py` |

**"5.6-luna"**: verified against current provider docs — `gpt-5.6-luna` is a real, current OpenAI model id,
not assumed. `OPENAI_MODEL_NAME` stays fully configurable via env either way; nothing is silently swapped in.

## Design / Stitch sync

The frontend is synced against the real Stitch project ("SafarChin Travel Planner" — Persian
Neo-Terracotta / Biophilic Mint design system): colors, radius/spacing/typography scale, fonts
(Vazirmatn + Bricolage Grotesque), and icons (Material Symbols Outlined) all come straight from Stitch's
own generated tokens, not approximations. See [`docs/design-sync.md`](docs/design-sync.md) for the exact
tokens, the screen→route/component mapping, and the couple of Stitch screens intentionally not carried
over (guest login, a tab-style bottom nav) because they don't map to existing routes/backend functionality.

## Known limitations

- Accommodation selection persists the choice and flips the trip back to "ready for generation" so the next
  itinerary generation call has it as real context (including for the agent's travel-time tool calls) — it
  does not instantly recompute routes without a regeneration pass.
- `docker-compose.yml` is dev-only (bind-mounted source, `runserver`/`next dev`, no `DEBUG=False` hardening).
  No production deployment config exists; nothing has been deployed anywhere.
