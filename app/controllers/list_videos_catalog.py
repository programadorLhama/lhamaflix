from pathlib import Path

from app.configs.settings import settings
from app.view.schemas import VideoItem


def list_mp4_files() -> list[VideoItem]:
    videos_dir: Path = settings.videos_dir
    if not videos_dir.is_dir():
        return []
    items: list[VideoItem] = []
    for p in sorted(videos_dir.glob("*.mp4")):
        if not p.is_file():
            continue
        stem = p.stem
        items.append(
            VideoItem(
                id=stem,
                filename=p.name,
                path=str(p.resolve()),
            )
        )
    return items
