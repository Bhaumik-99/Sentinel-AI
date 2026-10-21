"""Optional local voice adapters; install requirements-voice.txt to enable them."""
from pathlib import Path
import tempfile

def transcribe_audio(audio_bytes: bytes, filename: str, model_size: str) -> dict:
    try: from faster_whisper import WhisperModel
    except ImportError as exc: raise RuntimeError("Voice recognition is optional. Install backend/requirements-voice.txt.") from exc
    suffix=Path(filename).suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix) as temp:
        temp.write(audio_bytes); temp.flush()
        model=WhisperModel(model_size,device="cpu",compute_type="int8")
        segments,info=model.transcribe(temp.name,vad_filter=True,beam_size=3)
        text=" ".join(segment.text.strip() for segment in segments).strip()
    return {"text":text,"language":info.language,"language_probability":round(float(info.language_probability),3),"model":model_size}

def synthesize_speech(text: str) -> bytes:
    try: import pyttsx3
    except ImportError as exc: raise RuntimeError("Speech synthesis is optional. Install backend/requirements-voice.txt.") from exc
    engine=pyttsx3.init()
    with tempfile.NamedTemporaryFile(suffix=".wav",delete=False) as temp: output=temp.name
    try:
        engine.save_to_file(text,output); engine.runAndWait(); engine.stop()
        return Path(output).read_bytes()
    finally: Path(output).unlink(missing_ok=True)
