import asyncio

from fastapi import HTTPException

from app.controllers.ffmpeg_transcode import run_ffmpeg_sync
from app.controllers.video_paths import assert_playlist_under_hls_root, hls_playlist_path, resolve_video_path
from app.models import db_lock
from app.models import video_jobs as video_jobs_model
from app.view.schemas import HlsJobResponse


async def generate_hls_for_video(video_id: str) -> HlsJobResponse:
    # Força o ID a não ter espaços antes de qualquer operação de path
    clean_id = video_id.replace(" ", "_")
    
    input_path = resolve_video_path(video_id) # O arquivo original pode ter espaço
    playlist = hls_playlist_path(clean_id)     # A pasta HLS NÃO deve te
    assert_playlist_under_hls_root(playlist)

    if playlist.is_file():
        with db_lock:
            video_jobs_model.upsert_job_ready(video_id, input_path.name)
        return HlsJobResponse(
            video_id=video_id,
            status="ready",
            playlist_url=f"/hls/{video_id}/playlist.m3u8",
            message="HLS já existia; nenhuma transcodificação necessária.",
        )

    with db_lock:
        video_jobs_model.upsert_job_processing(video_id, input_path.name)

    loop = asyncio.get_running_loop()

    def job() -> None:
        try:
            run_ffmpeg_sync(video_id, input_path)
            with db_lock:
                video_jobs_model.update_job_ready(video_id)
        except Exception as e:  # noqa: BLE001
            msg = str(e)[:2000]
            with db_lock:
                video_jobs_model.update_job_error(video_id, msg)
            raise

    try:
        await loop.run_in_executor(None, job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not playlist.is_file():
        raise HTTPException(status_code=500, detail="playlist.m3u8 não foi criado")

    return HlsJobResponse(
        video_id=video_id,
        status="ready",
        playlist_url=f"/hls/{video_id}/playlist.m3u8",
        message="HLS gerado com sucesso.",
    )
