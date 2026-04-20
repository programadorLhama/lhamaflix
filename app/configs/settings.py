import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    videos_dir: Path
    hls_dir: Path
    static_dir: Path
    db_path: Path
    ffmpeg_bin: str
    safe_id: re.Pattern[str]


def _load_settings() -> Settings:
    root_dir = Path(__file__).resolve().parent.parent.parent
    return Settings(
        root_dir=root_dir,
        videos_dir=Path(os.environ.get("VIDEOS_DIR", root_dir / "videos")),
        hls_dir=Path(os.environ.get("HLS_DIR", root_dir / "hls")),
        static_dir=Path(os.environ.get("STATIC_DIR", root_dir / "static")),
        db_path=Path(os.environ.get("DB_PATH", root_dir / "data" / "app.db")),
        ffmpeg_bin=os.environ.get("FFMPEG_BIN", "ffmpeg"),
        safe_id=re.compile(r"^[a-zA-Z0-9._-]+$"),
    )


settings = _load_settings()
