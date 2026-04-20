from fastapi import APIRouter

from app.controllers.hls_generation import generate_hls_for_video
from app.controllers.hls_status_query import hls_job_status
from app.controllers.list_videos_catalog import list_mp4_files
from app.view.schemas import HlsJobResponse, VideoListResponse

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("", response_model=VideoListResponse)
def list_videos():
    """Lista arquivos .mp4 disponíveis na pasta configurada."""
    return VideoListResponse(videos=list_mp4_files())


@router.post("/{video_id}/hls", response_model=HlsJobResponse)
async def generate_hls(video_id: str):
    """
    Gera pacote HLS (VOD) sob demanda para o vídeo indicado.
    Se já existir playlist.m3u8, retorna imediatamente como pronto.
    """
    return await generate_hls_for_video(video_id)


@router.get("/{video_id}/hls/status", response_model=HlsJobResponse)
def hls_status(video_id: str):
    """Consulta status do job HLS no SQLite (e existência do playlist)."""
    return hls_job_status(video_id)
