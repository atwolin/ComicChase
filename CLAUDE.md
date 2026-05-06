# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ComicChase is a manga tracking platform that compares Japan/Taiwan publishing progress so readers can track translation delays. It is a monorepo with a Django backend and a React frontend, orchestrated via Docker Compose.

## Common Commands

All Docker operations default to `ENV=local`. Swap with `ENV=vm` or `ENV=gcr-test` for other targets.

```bash
make rebuild          # build images and start all services
make up               # start services (detached)
make down             # stop services
make shell            # shell into the backend container
make manage cmd="<x>" # run a Django management command
make test             # run backend tests
make logs             # tail all container logs
make clean            # remove all containers and volumes
```

### Backend (Django) — inside the container or with a virtualenv

```bash
python manage.py test                       # all tests
python manage.py test comic.tests.TestFoo   # single test
ruff check src/                             # lint
ruff format --check src/                    # format check
ruff format src/                            # auto-format
```

### Frontend (React/Vite)

```bash
cd ui
npm run dev           # dev server (port 3001 → proxied to backend :8002)
npm run build         # production build
npm run build:vm      # VM-targeted build
npm run lint          # ESLint
npm run lint:fix      # ESLint auto-fix
npm run format        # Prettier
npm run test          # Vitest (unit)
npm run test:coverage # coverage report
```

## Architecture

### Services (docker-compose.yml)

| Service | Purpose | Port |
|---------|---------|------|
| `db` | PostgreSQL 16 | 5434 (local) |
| `rabbitmq` | Message broker | 5672 / 15672 |
| `celery` | General task worker | — |
| `crawler` | Dedicated scraping queue | — |
| `beat` | Scheduled tasks | — |
| `flower` | Celery dashboard | 5555 |
| `backend` | Django REST API | 8002 (local) |
| `frontend` | Vite dev server | 3001 (local) |
| `selenium` | Headless browser for scrapers | 4444 |

### Backend (`app/src/`)

Django 5.2 + Django REST Framework. Settings are environment-split under `config/settings/` (`base.py`, `local.py`, `vm.py`, `gcr.py`).

Key Django apps:

- **`comic/`** — core models (manga series and volumes), serializers, API views, filters
- **`subscriptions/`** — user subscription tracking; Celery tasks for notifications via AWS SES
- **`comic_scrapers/`** — Scrapy spiders (`books_jp.py`, `books_tw.py`, `eslite.py`) with a `base_selenium_spider.py` for JS-heavy pages; `pipelines.py` writes scraped data to the database
- **`accounts/`** — user management via django-allauth
- **`apis/`** — shared API utilities

API schema is auto-generated with **DRF Spectacular** (OpenAPI); the frontend consumes the generated types from `ui/src/api/generated/`.

### Frontend (`ui/src/`)

React 18 + TypeScript + Vite + TailwindCSS. Key layout:

- `api/` — Axios client + OpenAPI-generated types
- `components/` — shared UI (SeriesCard, Navbar, SearchBar, …)
- `pages/` — route-level components
- `hooks/` / `contexts/` — React Query data-fetching hooks and Context providers
- `config/` — environment/feature flags

Vite proxies `/api/*` to the backend (`http://localhost:8002`) in dev mode.

### Async / Background Jobs

Celery workers connect to RabbitMQ. Two queues:
- **`celery`** — general tasks (email notifications, subscription checks)
- **`crawler`** — scraping tasks (runs Scrapy spiders)

Beat schedule lives in `config/settings/base.py`.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

- `SECRET_KEY`, `DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `DB_HOST/PORT`, `POSTGRES_*` — PostgreSQL
- `CELERY_BROKER_URL` — RabbitMQ (`amqp://...`)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SES_REGION` — email via SES
- `UID`, `GID` — Docker user mapping (run `id` to get values)

## Linting & Formatting

Pre-commit hooks enforce:
- **Ruff** for Python (lint + format)
- **ESLint + Prettier** for TypeScript/React

CI (`backend-ci.yml`, `frontend-ci.yml`) runs the same checks on every push.
