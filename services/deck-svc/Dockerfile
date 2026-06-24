FROM python:3.13-slim
RUN pip install uv

COPY libs/flashcards-common /libs/flashcards-common
RUN uv pip install --system /libs/flashcards-common

RUN uv pip install --system \
    "fastapi[standard]>=0.115" \
    "uvicorn[standard]>=0.30" \
    "sqlalchemy[asyncio]>=2.0" \
    "alembic>=1.13" \
    "asyncpg>=0.30"

WORKDIR /app
COPY services/deck-svc/src /app/src
COPY services/deck-svc/alembic /app/alembic
COPY services/deck-svc/alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "deck_svc.main:app", "--host", "0.0.0.0", "--port", "8002"]
