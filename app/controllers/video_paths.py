import re
from pathlib import Path

from fastapi import HTTPException

from app.configs.settings import settings


def resolve_video_path(video_id: str) -> Path:
    if re.fullmatch(settings.safe_id, video_id) is None:
        raise HTTPException(status_code=400, detail="video_id inválido")
    candidate = (settings.videos_dir / f"{video_id}.mp4").resolve()
    videos_root = settings.videos_dir.resolve()
    if not str(candidate).startswith(str(videos_root)) or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    return candidate


def hls_playlist_path(video_id: str) -> Path:
    return (settings.hls_dir / video_id / "playlist.m3u8").resolve()


def assert_playlist_under_hls_root(playlist: Path) -> None:
    hls_root = settings.hls_dir.resolve()
    if not str(playlist).startswith(str(hls_root)):
        raise HTTPException(status_code=400, detail="Caminho HLS inválido")
