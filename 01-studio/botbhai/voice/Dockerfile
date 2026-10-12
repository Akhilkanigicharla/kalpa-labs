# Free hosting options: Oracle Cloud Always Free VM, or a Hugging Face Docker Space (sleeps when idle).
FROM python:3.12-slim
WORKDIR /app
COPY voice/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY setups /setups
COPY voice /app
ENV SETUPS_DIR=/setups
EXPOSE 8080
CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8080"]
