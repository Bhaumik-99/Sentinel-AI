# Sentinel AI — Video Intelligence Workbench

Sentinel AI is an end-to-end video analytics prototype built to demonstrate computer vision, object tracking, evidence-grounded retrieval, API design, and a React dashboard. It is designed as an engineering project for experimentation—not as a safety-certified surveillance product.

## What works

- **Video ingestion:** upload MP4, MOV, AVI, MKV, or WEBM clips (default 250 MB limit).
- **Computer vision:** YOLO object detection with confidence scores and bounding boxes.
- **Tracking:** Ultralytics ByteTrack IDs where the tracker returns an ID.
- **Event storage:** timestamp, frame number, label, confidence, tracking ID, and bounding box stored in SQLite.
- **Event explorer:** filter events by video and class label.
- **Evidence-grounded questions:** deterministic retrieval with timestamped evidence.
- **Generative AI agent:** optional local Ollama language model with allow-listed event-search and video-summary tools; the UI can switch back to deterministic retrieval.
- **Model training:** reproducible YOLO fine-tuning and validation entrypoint that writes measured metrics to JSON.
- **Voice AI:** optional local Whisper speech recognition and local text-to-speech endpoints, with browser voice fallbacks when available.
- **Browser voice controls:** microphone input and spoken answers when supported by the browser; microphone permission is required.
- **Video management:** delete a video and its event records.
- **Engineering basics:** API validation, upload size limits, Docker configuration, tests, experiment template, and continuous integration.

## Architecture

```text
React + Vite dashboard
   | REST / JSON + multipart upload
   v
FastAPI service ---- /api/ask ----> evidence-grounded retrieval
   |
   +---- OpenCV frame sampling
   |        |
   |        v
   |      YOLO detection + ByteTrack
   |        |
   |        v
   +---- SQLite video metadata + timestamped events
```

Sentinel offers two question modes: deterministic event retrieval (no language model required) and an optional tool-using local language-model agent. The agent can search stored detections and read video metadata; it cannot inspect raw footage or infer actions not represented by events. Local voice endpoints use faster-whisper and pyttsx3 when the optional dependencies are installed. Browser speech remains a fallback. Fine-tuning requires a labeled dataset; this repository does not include one or claim pretrained-model metrics as custom results.

## Requirements

- Python 3.11 recommended
- Node.js 20 or later
- A machine that can run the selected Ultralytics model; a compatible NVIDIA GPU can accelerate inference, but a CPU can also run smaller models more slowly.
- Internet access on the first model run if the configured YOLO weights are not cached.

## Local setup

### 1. Backend

From the repository root:

**Windows PowerShell**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:SENTINEL_MODEL="yolov8n.pt"
$env:SENTINEL_SAMPLE_INTERVAL="0.5"
uvicorn app.main:app --reload
```

**macOS / Linux**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
export SENTINEL_MODEL=yolov8n.pt
export SENTINEL_SAMPLE_INTERVAL=0.5
uvicorn app.main:app --reload
```

The API runs at [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The backend creates the database and upload directory automatically.

### 2. Frontend

Open a second terminal at the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). If the backend is not running, the dashboard displays a disconnected status.

Optional frontend API override: copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_BASE` before starting Vite.

### 3. Docker Compose

From the repository root:

```bash
docker compose up --build
```

Then open [http://localhost:5173](http://localhost:5173). Docker Compose stores uploaded videos and the SQLite database in named volumes. The default Compose setup uses CPU inference unless the container is explicitly configured for GPU access.

## System architecture

```mermaid
flowchart TD
    U[User] --> UI[React + Vite Dashboard]
    UI -->|Upload video / REST requests| API[FastAPI Backend]

    subgraph Processing[Video processing pipeline]
        API --> UP[Validate and store upload]
        UP --> CV[OpenCV frame sampling]
        CV --> DET[YOLO object detection]
        DET --> TRACK[ByteTrack object tracking]
        TRACK --> EVT[Timestamped detection events]
    end

    EVT --> DB[(SQLite database)]
    API -->|List and filter| DB

    UI -->|Question about footage| ASK[Evidence-grounded query service]
    ASK --> DB
    DB -->|Matching detections and timestamps| ASK
    ASK -->|Answer with evidence| UI

    UI -->|Microphone input| SPEECH[Browser speech recognition]
    SPEECH -->|Transcribed question| ASK
    ASK -->|Text answer| TTS[Browser speech synthesis]
    TTS -->|Spoken answer| U

    API --> HEALTH[Health and statistics endpoints]
    HEALTH --> UI
```

## Enable the local generative AI agent

Install [Ollama](https://ollama.com/) and start its local service. In a terminal, pull a tool-capable model:

```bash
ollama pull qwen2.5:3b
```

The backend defaults to `http://127.0.0.1:11434` and `qwen2.5:3b`. Configure a different local model with `SENTINEL_LLM_BASE_URL` and `SENTINEL_LLM_MODEL`. The dashboard's **Local LLM Agent** switch calls `POST /api/agent/ask`; turn it off to use the deterministic retrieval endpoint. If Ollama is not running, the API returns a setup hint and does not send video data to a hosted provider.

The agent has an explicit, small tool allow-list for searching stored detections and reading video metadata. It does not execute arbitrary shell commands or have unrestricted computer access.

## Enable local voice models

```bash
cd backend
pip install -r requirements-voice.txt
```

Restart the API. The microphone button records audio and calls `POST /api/voice/transcribe` using faster-whisper on the CPU; answer playback tries `POST /api/voice/speak` using pyttsx3 and falls back to browser speech if local speech is unavailable. First use may download Whisper model weights. Microphone capture normally requires localhost or HTTPS and user permission. To use only browser speech, do not install the optional voice dependencies.

Voice recognition model can be changed with `SENTINEL_VOICE_MODEL` (default `base`). Uploads are limited by `SENTINEL_MAX_AUDIO_MB` (default 25 MB).

## Fine-tune the object detector

Prepare a labeled dataset in the Ultralytics format described in [datasets/sentinel/README.md](datasets/sentinel/README.md). Dataset images and videos are intentionally not included in Git.

```bash
cd backend
pip install -r requirements-ml.txt
python train_yolo.py --data ../datasets/sentinel/data.yaml --model yolov8n.pt --epochs 50 --imgsz 640 --batch 8
```

For a compatible NVIDIA GPU, install the PyTorch build matching your CUDA setup and pass `--device 0`; otherwise use `--device cpu`. The script trains, validates, and writes `sentinel_metrics.json` plus plots to the run directory. These metrics are meaningful only for your dataset and validation split. To use the fine-tuned model in the video pipeline, set `SENTINEL_MODEL` to the resulting `best.pt` checkpoint path before starting the backend. Training has not been run as part of the repository commit because no labeled dataset was provided.

## API reference

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/api/videos` | List processed videos |
| POST | `/api/videos` | Upload and process a video; multipart field: `file` |
| DELETE | `/api/videos/{video_id}` | Delete a video and its event records |
| GET | `/api/events?video_id=1&label=person` | Search timestamped detections |
| GET | `/api/stats` | Basic counts and frequent labels |
| POST | `/api/ask` | Deterministic question answering from stored detection evidence |
| POST | `/api/agent/ask` | Optional Ollama agent with allow-listed retrieval tools |
| POST | `/api/voice/transcribe` | Optional local speech-to-text; multipart field: `file` |
| POST | `/api/voice/speak` | Optional local text-to-speech; JSON field: `text` |

Example question request:

```json
{
  "question": "When was a person detected?",
  "video_id": 1
}
```

Use `POST /api/ask` with a JSON body and `Content-Type: application/json`.

## Configuration

Settings use environment variables with the `SENTINEL_` prefix.

| Variable | Default | Description |
|---|---|---|
| `SENTINEL_MODEL` | `yolov8n.pt` | Ultralytics model/checkpoint |
| `SENTINEL_DB_PATH` | `./sentinel.db` | SQLite database path |
| `SENTINEL_UPLOAD_DIR` | `./uploads` | Video storage directory |
| `SENTINEL_SAMPLE_INTERVAL` | `0.5` | Target interval between sampled frames in seconds |
| `SENTINEL_MAX_VIDEO_MB` | `250` | Maximum upload size |

The frame sampler reads the clip sequentially and runs inference at the configured interval. For long videos, processing can take several minutes. The current implementation is synchronous per upload and is intended for a single-user demonstration, not high-throughput production.

## Tests and quality checks

Backend unit tests:

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

Frontend production build:

```bash
cd frontend
npm install
npm run build
```

GitHub Actions runs backend unit tests and the frontend production build on pushes and pull requests to `main`.

## Experiment methodology

Use [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) to record the dataset, hardware, model, inference interval, precision, recall, mean average precision, processing speed, memory use, and failure cases. Compare runs only when the evaluation split and conditions are controlled. Do not put unmeasured accuracy or latency claims in a portfolio or resume.

Suggested experiments:
1. Compare YOLO nano and small models on the same held-out clips.
2. Compare 0.25, 0.5, and 1.0-second sampling intervals.
3. Evaluate precision and recall by object class and lighting condition.
4. Measure tracking identity switches and missed detections.
5. Profile CPU versus GPU inference with the same resolution and test set.

## Known limitations and next steps

- No trained temporal action-recognition model yet; YOLO fine-tuning is provided but must be run on your own labeled dataset.
- The local LLM agent and local voice endpoints require optional local services and dependencies; they are not automatically downloaded or started by the application.
- No dataset, model accuracy claim, or inference benchmark is bundled; measure these on representative held-out footage.
- No authentication, user accounts, rate limiting, persistent job queue, or production retention controls.
- SQLite and the synchronous inference workflow are suitable for a local prototype, not multi-tenant scale.
- Add representative dataset evaluation, annotated video playback, background jobs, authentication, deployment monitoring, and documented benchmark results before production use.

## Responsible use

Use footage you have permission to process. Provide appropriate notice and follow applicable privacy and data-retention requirements. Detection is probabilistic; do not use this prototype as the sole basis for decisions affecting people's safety, employment, access, or rights.
