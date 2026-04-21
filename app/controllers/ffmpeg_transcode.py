import subprocess
from pathlib import Path

from app.configs.settings import settings


def run_ffmpeg_sync(video_id: str, input_path: Path) -> None:
    # Garante ID consistente com paths estáticos HLS.
    safe_video_id = video_id.replace(" ", "_")

    out_dir = settings.hls_dir / safe_video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    playlist = out_dir / "playlist.m3u8"

    cmd = [
        settings.ffmpeg_bin,
        "-y",
        "-i",
        str(input_path),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-profile:a", "aac_low",
        "-b:a", "128k",
        "-ac", "2",
        "-ar", "48000",
        "-af", "aresample=async=1:first_pts=0",
        "-hls_time", "6",
        "-hls_playlist_type", "vod",
        "-hls_flags", "independent_segments",
        # Nomes de segmentos relativos evitam erros de URL/path.
        "-hls_segment_filename", str(out_dir / "segment_%03d.ts"),
        str(playlist),
    ]

    # Use check=True para simplificar a captura de erros
    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,
            check=True,  # Levanta CalledProcessError se o código não for 0.
        )
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip()[-2000:] if e.stderr else "Erro desconhecido no FFmpeg"
        raise RuntimeError(f"FFmpeg Error (Video: {video_id}): {err_msg}") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"FFmpeg Timeout: O processamento de {video_id} excedeu 1 hora.") from e