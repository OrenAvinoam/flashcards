FROM python:3.13-slim
RUN pip install uv

COPY libs/flashcards-common /libs/flashcards-common
RUN uv pip install --system /libs/flashcards-common

RUN uv pip install --system \
    "fastapi[standard]>=0.115" \
    "uvicorn[standard]>=0.30" \
    "redis[asyncio]>=5.0" \
    "fsrs>=1.0"

WORKDIR /app
COPY services/scheduler-svc/src /app/src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "scheduler_svc.main:app", "--host", "0.0.0.0", "--port", "8003"]
