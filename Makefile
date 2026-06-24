.PHONY: up down logs migrate seed test lint tw-watch

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

test:
	cd libs/flashcards-common && uv run pytest tests/ -v
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
