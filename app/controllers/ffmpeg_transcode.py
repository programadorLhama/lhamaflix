import subprocess
from pathlib import Path

from app.configs.settings import settings


def run_ffmpeg_sync(video_id: str, input_path: Path) -> None:
    out_dir = settings.hls_dir / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    playlist = out_dir / "playlist.m3u8"

    cmd = [
        settings.ffmpeg_bin,
        "-y",
        "-i",
        str(input_path),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-hls_time",
        "6",
        "-hls_playlist_type",
        "vod",
        "-hls_segment_filename",
        str(out_dir / "segment_%03d.ts"),
        str(playlist),
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=3600,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[-2000:]
        raise RuntimeError(err or f"ffmpeg falhou com código {proc.returncode}")
