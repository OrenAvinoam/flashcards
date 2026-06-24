.PHONY: up down logs migrate seed test lint tw-watch \
        dev-infra dev-migrate dev-seed \
        dev-auth dev-deck dev-scheduler dev-generation dev-worker dev-web

# ── Docker Compose (full stack) ──────────────────────────────────────────────

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f

migrate:
	docker compose run --rm auth-svc alembic upgrade head
	docker compose run --rm deck-svc alembic upgrade head

seed:
	docker compose run --rm auth-svc python -m auth_svc.seed
	docker compose run --rm deck-svc python -m deck_svc.seed

# ── Local dev (Python runs natively, only Postgres+Redis in Docker) ──────────
# Prerequisites:
#   1. uv installed  (winget install astral-sh.uv)
#   2. cp .env.local.example .env  (and fill in secrets)
#   3. make dev-infra          ← start Postgres + Redis
#   4. make dev-migrate        ← run Alembic migrations
#   5. make dev-seed           ← load demo data
#   6. Open 5 terminals and run dev-auth, dev-deck, dev-scheduler,
#      dev-generation (+ dev-worker), dev-web

dev-infra:
	docker compose up postgres redis -d

dev-migrate:
	cd services/auth-svc && uv run alembic upgrade head
	cd services/deck-svc && uv run alembic upgrade head

dev-seed:
	cd services/auth-svc && uv run python -m auth_svc.seed
	cd services/deck-svc && uv run python -m deck_svc.seed

dev-auth:
	cd services/auth-svc && uv run uvicorn auth_svc.main:app --port 8001 --reload

dev-deck:
	cd services/deck-svc && uv run uvicorn deck_svc.main:app --port 8002 --reload

dev-scheduler:
	cd services/scheduler-svc && uv run uvicorn scheduler_svc.main:app --port 8003 --reload

dev-generation:
	cd services/generation-svc && uv run uvicorn generation_svc.main:app --port 8004 --reload

dev-worker:
	cd services/generation-svc && uv run python -m arq generation_svc.worker.WorkerSettings

dev-web:
	cd services/web && uv run uvicorn web.main:app --port 8000 --reload

# ── Quality ──────────────────────────────────────────────────────────────────

test:
	cd services/auth-svc && uv run pytest tests/ -v
	cd services/deck-svc && uv run pytest tests/ -v
	cd services/scheduler-svc && uv run pytest tests/ -v
	cd services/generation-svc && uv run pytest tests/ -v
	cd services/web && uv run pytest tests/ -v

lint:
	uv run ruff check libs/ services/
	uv run ruff format --check libs/ services/
	cd libs/flashcards-common && uv run mypy src/
	cd services/auth-svc && uv run mypy src/
	cd services/deck-svc && uv run mypy src/
	cd services/scheduler-svc && uv run mypy src/
	cd services/generation-svc && uv run mypy src/
	cd services/web && uv run mypy src/

tw-watch:
	cd services/web && ./tailwindcss -i src/web/static/css/input.css -o src/web/static/css/app.css --watch
