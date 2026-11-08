# Stage 1: cài thư viện và package của ứng dụng
FROM python:3.12-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv

COPY pyproject.toml ./
COPY src/ ./src/

RUN /opt/venv/bin/pip install --no-cache-dir .

# Stage 2: chạy ứng dụng
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --chown=app:app wsgi.py ./
COPY --chown=app:app migrations/ ./migrations/

USER app

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "wsgi:app"]