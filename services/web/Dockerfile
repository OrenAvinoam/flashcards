FROM python:3.13-slim
RUN pip install uv

COPY libs/flashcards-common /libs/flashcards-common
RUN uv pip install --system /libs/flashcards-common

RUN uv pip install --system \
    "fastapi[standard]>=0.115" \
    "uvicorn[standard]>=0.30" \
    "jinja2>=3.1" \
    "python-multipart>=0.0.9" \
    "itsdangerous>=2.1" \
    "httpx>=0.27"

WORKDIR /app
COPY services/web/src /app/src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]
