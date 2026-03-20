FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg2 and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate ML model on startup if not present
RUN python -c "from pathlib import Path; \
    import sys; \
    sys.exit(0) if Path('app/ml/model.joblib').exists() else sys.exit(1)" 2>/dev/null \
    || python -m app.ml.train --generate 2>/dev/null || true

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
