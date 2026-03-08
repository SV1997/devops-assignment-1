# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pytest pytest-cov

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

COPY --from=builder /usr/local/lib /usr/local/lib
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

ENTRYPOINT ["sh", "-c", "python -c 'from app import init_db; init_db()' && python app.py"]
