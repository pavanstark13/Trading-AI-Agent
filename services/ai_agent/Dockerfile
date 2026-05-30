FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY shared/ /app/shared/
COPY services/ai_agent/ /app/services/ai_agent/
RUN pip install --no-cache-dir -r /app/services/ai_agent/requirements.txt
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8005
CMD ["uvicorn", "services.ai_agent.main:app", "--host", "0.0.0.0", "--port", "8005"]
