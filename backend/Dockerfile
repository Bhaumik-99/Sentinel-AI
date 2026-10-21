FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg libgl1 libglib2.0-0 espeak-ng && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-voice.txt ./
RUN pip install --no-cache-dir -r requirements-voice.txt
COPY app ./app
RUN mkdir -p uploads data
ENV SENTINEL_UPLOAD_DIR=/app/uploads
ENV SENTINEL_DB_PATH=/app/data/sentinel.db
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
