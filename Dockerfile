
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r requirements.txt
COPY ./app ./app

# Create non-root user (UID 1000) and data directory with correct ownership
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g 1000 -M -s /sbin/nologin appuser && \
    mkdir -p /app/data && \
    chown -R 1000:1000 /app/data

USER 1000

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
