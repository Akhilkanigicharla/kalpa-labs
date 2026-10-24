# Free hosting options: Oracle Cloud Always Free VM, or a Hugging Face Docker Space (sleeps when idle).
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY voice/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY setups /setups
COPY voice /app
COPY core/models.json /app/models.json
ENV SETUPS_DIR=/setups
# This slim image has no torch, so its voice notes use Sarvam. Free Parler voice runs as a batch job
# (.github/workflows/telugu-voice.yml); add requirements-parler.txt here only after a test that it installs beside Pipecat.
ENV RECORDED_TTS=sarvam
EXPOSE 8080
CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8080"]
