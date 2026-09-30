# AGENT.md

Guidance for AI coding agents working in this repo. See `README.md` for the human-facing overview and
`docs/design-sync.md` for the frontend design-system traceability.

## What this is

سفرچین (Safarchin) — a Persian AI travel-planning app. User describes a trip in natural language, a
LangChain agent asks follow-up questions and (with real API keys) produces a daily itinerary with
geocoded places/routes on a map and accommodation suggestions. Everything is RTL/Persian-first
(Jalali calendar, Persian digits, `dir="rtl"`).

## Layout

- `backend/` — Django 5 + DRF, Postgres, Redis, Celery, the LangChain planning agent (`apps/planner`).
- `frontend/` — Next.js 16 (App Router, TypeScript), Tailwind v4, RTL/Persian/Jalali UI.
- `docs/design-sync.md` — the frontend's design tokens, synced from a Stitch project; screen→route mapping.
- `docker-compose.yml` — Postgres, Redis, backend, Celery worker, frontend. All dev-mode (bind-mounted
  source, `runserver`/`next dev`, not production builds).
- `dev.sh` — runs the whole stack natively (no Docker for the app processes) in one foreground command;
  starts Postgres/Redis via `docker compose up -d --wait db redis`, then Django, Celery, and Next.js as
  background jobs with logs in `.dev-logs/`, Ctrl+C stops everything.

## Running things

Two ways to run the full stack — don't run both at once, they'll fight over ports 3000/8000:

- **All-in-Docker:** `docker compose up -d` (or `--build` after dependency changes).
- **Native (faster iteration):** `./dev.sh`, or start pieces individually:
  ```bash
  docker compose up -d --wait db redis
  cd backend && .venv/bin/python manage.py runserver 0.0.0.0:8000
  cd backend && .venv/bin/celery -A config worker -l info --pool=solo   # --pool=solo needed on macOS
  cd frontend && npm run dev
  ```

Before assuming nothing is running, check first — `docker compose ps`, `lsof -iTCP:3000 -iTCP:8000 -sTCP:LISTEN`.

## Backend conventions

- Settings load `.env` once at process start via `django-environ` (`config/settings.py`). **Editing `.env`
  requires restarting the process** — the dev-server autoreloader only watches `.py` files.
- Celery broker/result env vars are deliberately *not* named `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` —
  Celery special-cases those exact names at app-init and they silently win over
  `config_from_object(settings)`. Use `REDIS_URL` / `CELERY_BROKER_REDIS_URL` as already defined.
- Task results go through `django_celery_results` (django-db backend), not Redis.
- Redis runs on host port **6380**, not 6379 (same reasoning as Postgres on 5433) — something else on the
  machine can silently bind 6379 and reset every connection with a confusing `ConnectionResetError` deep in
  `django_redis`/`kombu`, breaking sessions, throttling, and the Celery broker all at once. If you ever see
  that error, `lsof -nP -iTCP:6379 -sTCP:LISTEN` before assuming Docker/Redis itself is broken.
- Everything that needs a real external API key (OpenAI via `langchain-openai`, Tavily, Neshan) fails with an
  explicit, user-visible error message when the key is missing — never silently stubbed/faked. Preserve that
  behavior; don't add a mock fallback that could look like a real result.
- Tests: `python manage.py test apps.accounts apps.trips` (needs real Postgres/Redis — `docker compose up -d
  db redis` first).

## Frontend conventions

- Tailwind v4, tokens defined as CSS custom properties + `@theme inline` in `src/app/globals.css` — no
  `tailwind.config.js`. Custom radius/spacing/typography scale names come straight from the Stitch design
  system (`rounded-DEFAULT`/`rounded-lg`/`rounded-full`, `space-xs`…`space-xl`, `text-headline-lg`, etc.) —
  see `docs/design-sync.md` before inventing a new one-off value.
- Fonts: Vazirmatn (body/Persian) + Bricolage Grotesque (headlines, falls back to Vazirmatn for Persian
  glyphs) via `next/font/google` in `layout.tsx`. Icons: Material Symbols Outlined, loaded via a `<link>` in
  `layout.tsx`'s `<head>`, used as `<span className="material-symbols-outlined">icon_name</span>`.
- Global CSS (including third-party stylesheets like Leaflet's) must be statically imported from
  `layout.tsx` — a dynamic `import(".css")` inside a client component does not reliably work in the App
  Router and was the cause of a real blank-map bug here once already. Don't reintroduce that pattern.
- `TripMap.tsx` mounts its Leaflet map instance exactly **once** (empty-deps effect) and updates
  markers/view imperatively in a second effect. Do not go back to re-creating `new L.Map(...)` whenever
  props change — with an unstable `places` array reference (e.g. rebuilt inline on every render) that causes
  "Map container is already initialized" races. If you touch it, make sure whatever computes the `places`
  array passed in is `useMemo`'d.
- Emails/passwords/phone fields must render LTR even inside the RTL page (`ltr` prop on `Input`, `.ltr-field`
  class) — don't drop that when touching auth forms.
- `lib/jalali.ts` / `lib/persian.ts` handle Jalali↔Gregorian conversion and Persian-digit formatting. The
  backend always stores/returns plain Gregorian ISO dates — conversion happens only at this frontend
  boundary, never add a second conversion point.

## Before finishing frontend UI work

Actually load the page in a browser (or at minimum verify the compiled CSS/HTML output) — type-checking and
a production build catch compile errors, not rendering/runtime issues like the blank-map bug above. `npx tsc
--noEmit`, `npm run lint`, and `npm run build` are cheap sanity checks to run after any non-trivial change,
but they are not a substitute for looking at the page.

## Git / commits

Only commit or push when explicitly asked. This repo pushes directly to `main` (solo project, no PR flow) —
confirm scope before anything destructive (`--force`, `reset --hard`, etc.), but a normal `commit` + `push`
to `main` on explicit request is the established workflow here.
