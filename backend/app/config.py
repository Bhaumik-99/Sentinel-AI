from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SENTINEL_", env_file=".env", extra="ignore")
    model: str = "yolov8n.pt"
    db_path: str = "./sentinel.db"
    upload_dir: str = "./uploads"
    sample_interval: float = 0.5
    max_video_mb: int = 250
    # Optional local Ollama endpoint. No external LLM is called unless configured.
    llm_base_url: str = "http://127.0.0.1:11434"
    llm_model: str = "qwen2.5:3b"
    llm_timeout_seconds: int = 45
    voice_model: str = "base"
    max_audio_mb: int = 25

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

settings = Settings()
