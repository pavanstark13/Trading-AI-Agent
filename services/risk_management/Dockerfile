FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY shared/ /app/shared/
COPY services/risk_management/ /app/services/risk_management/
RUN pip install --no-cache-dir -r /app/services/risk_management/requirements.txt
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8003
CMD ["uvicorn", "services.risk_management.main:app", "--host", "0.0.0.0", "--port", "8003"]
