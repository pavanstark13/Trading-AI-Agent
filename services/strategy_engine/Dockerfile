FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY services/strategy_engine/ /app/services/strategy_engine/

RUN pip install --no-cache-dir -r /app/services/strategy_engine/requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8002

CMD ["uvicorn", "services.strategy_engine.main:app", "--host", "0.0.0.0", "--port", "8002"]
