import re
from pathlib import Path

from app.configs.settings import settings
from app.view.schemas import HlsVideoItem, VideoItem


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


def list_hls_videos() -> list[HlsVideoItem]:
    hls_dir: Path = settings.hls_dir
    if not hls_dir.is_dir():
        return []

    items: list[HlsVideoItem] = []
    for playlist in sorted(hls_dir.glob("*/playlist.m3u8")):
        if not playlist.is_file():
            continue

        video_id = playlist.parent.name
        if re.fullmatch(settings.safe_id, video_id) is None:
            continue

        title = video_id.replace("_", " ").replace("-", " ").strip() or video_id
        items.append(
            HlsVideoItem(
                id=video_id,
                title=title,
                playlist_url=f"/hls/{video_id}/playlist.m3u8",
            )
        )
    return items
