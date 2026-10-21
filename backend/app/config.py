from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SENTINEL_", env_file=".env", extra="ignore")
    model: str = "yolov8n.pt"
    db_path: str = "./sentinel.db"
    upload_dir: str = "./uploads"
    sample_interval: float = 0.5
    max_video_mb: int = 250

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

settings = Settings()
