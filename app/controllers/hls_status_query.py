from app.controllers.video_paths import hls_playlist_path, resolve_video_path
from app.models import db_lock
from app.models import video_jobs as video_jobs_model
from app.view.schemas import HlsJobResponse


def hls_job_status(video_id: str) -> HlsJobResponse:
    resolve_video_path(video_id)
    playlist = hls_playlist_path(video_id)
    with db_lock:
        row = video_jobs_model.fetch_job_row(video_id)
    if playlist.is_file():
        return HlsJobResponse(
            video_id=video_id,
            status="ready",
            playlist_url=f"/hls/{video_id}/playlist.m3u8",
        )
    if row:
        return HlsJobResponse(
            video_id=video_id,
            status=row["status"],
            message=row["error_message"],
        )
    return HlsJobResponse(video_id=video_id, status="none", message="Nenhum job registrado ainda.")
