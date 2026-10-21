# Sentinel AI — Video Intelligence Agent

An extensible MVP for video analytics: object detection, tracking, timestamped event storage, evidence-grounded search, and a web dashboard.

## Features

- Video upload and processing with YOLO object detection.
- Object tracking with Ultralytics ByteTrack.
- Timestamped detections stored in SQLite.
- Search events by object class and video.
- Evidence-grounded question answering over stored detections.
- FastAPI backend and React + Vite frontend.
- Docker setup, basic tests, and an experiment log template.

> Prototype only; not a safety-certified surveillance system. Do not use as the sole basis for high-impact decisions.

## Quick start

### Backend (Python 3.11 recommended)

```bash
cd backend
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The first inference may download YOLO weights. Open `http://127.0.0.1:8000/docs` for API docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Docker

From the project root run `docker compose up --build`.

## API

- `GET /health`
- `GET /api/videos`
- `POST /api/videos` — multipart upload with field `file`
- `GET /api/events?video_id=1&label=person`
- `POST /api/ask` — JSON body `{\"question\":\"When was a person detected?\",\"video_id\":1}`

## Architecture

FastAPI stores uploads, OpenCV samples frames, YOLO detects objects and ByteTrack associates detections. Timestamped records include class, confidence, bounding box, frame, and track ID. The query layer responds only from stored detector evidence rather than inventing scene descriptions.

## Experiments

Use `docs/EXPERIMENTS.md` to compare model checkpoints and sampling intervals, recording precision, recall, mean average precision, processing FPS, memory, and error analysis. Only publish measured values. See each folder's README and code for implementation details.

## Current scope and next research steps

This MVP implements detection, tracking, event storage, filtering, and retrieval. It does not yet include temporal action recognition, a generative language model, or voice interaction. Add these as separately evaluated modules. Before public deployment, implement authentication, access control, upload limits, retention policies, and monitoring.
