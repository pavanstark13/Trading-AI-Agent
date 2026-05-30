FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared library
COPY shared/ /app/shared/

# Copy service
COPY services/market_data/ /app/services/market_data/

# Install dependencies
RUN pip install --no-cache-dir -r /app/services/market_data/requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

CMD ["uvicorn", "services.market_data.main:app", "--host", "0.0.0.0", "--port", "8001"]
