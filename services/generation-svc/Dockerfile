FROM python:3.13-slim
RUN pip install uv
WORKDIR /workspace
COPY libs/flashcards-common /workspace/libs/flashcards-common
COPY services/generation-svc /workspace/services/generation-svc
COPY pyproject.toml /workspace/pyproject.toml
WORKDIR /workspace/services/generation-svc
RUN uv pip install --system -e /workspace/libs/flashcards-common && \
    uv pip install --system -e .
CMD ["uvicorn", "generation_svc.main:app", "--host", "0.0.0.0", "--port", "8004"]
