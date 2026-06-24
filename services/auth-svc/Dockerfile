FROM python:3.13-slim
RUN pip install uv

# Install shared library
COPY libs/flashcards-common /libs/flashcards-common
RUN uv pip install --system /libs/flashcards-common

# Install service dependencies
RUN uv pip install --system \
    "fastapi[standard]>=0.115" \
    "uvicorn[standard]>=0.30" \
    "sqlalchemy[asyncio]>=2.0" \
    "alembic>=1.13" \
    "asyncpg>=0.30" \
    "argon2-cffi>=23.1"

WORKDIR /app
COPY services/auth-svc/src /app/src
COPY services/auth-svc/alembic /app/alembic
COPY services/auth-svc/alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "auth_svc.main:app", "--host", "0.0.0.0", "--port", "8001"]
