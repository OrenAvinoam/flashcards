FROM python:3.13-slim
RUN pip install uv

COPY libs/flashcards-common /libs/flashcards-common
RUN uv pip install --system /libs/flashcards-common

RUN uv pip install --system \
    "fastapi[standard]>=0.115" \
    "uvicorn[standard]>=0.30" \
    "arq>=0.26" \
    "redis[asyncio]>=5.0" \
    "pypdf>=4.0" \
    "google-genai>=0.8" \
    "httpx>=0.27"

WORKDIR /app
COPY services/generation-svc/src /app/src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "generation_svc.main:app", "--host", "0.0.0.0", "--port", "8004"]
