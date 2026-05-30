FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY shared/ /app/shared/
COPY services/monitoring/ /app/services/monitoring/
RUN pip install --no-cache-dir -r /app/services/monitoring/requirements.txt
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8006
CMD ["uvicorn", "services.monitoring.main:app", "--host", "0.0.0.0", "--port", "8006"]
