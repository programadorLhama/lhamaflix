import asyncio
import os
import re
import sqlite3
import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = Path(os.environ.get("VIDEOS_DIR", ROOT_DIR / "videos"))
HLS_DIR = Path(os.environ.get("HLS_DIR", ROOT_DIR / "hls"))
STATIC_DIR = Path(os.environ.get("STATIC_DIR", ROOT_DIR / "static"))
DB_PATH = Path(os.environ.get("DB_PATH", ROOT_DIR / "data" / "app.db"))
FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")

SAFE_ID = re.compile(r"^[a-zA-Z0-9._-]+$")

app = FastAPI(title="HLS Streaming API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_db_lock = threading.Lock()


def ensure_dirs() -> None:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    HLS_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS video_jobs (
                video_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'none',
                error_message TEXT,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


class VideoItem(BaseModel):
    id: str
    filename: str
    path: str


class VideoListResponse(BaseModel):
    videos: list[VideoItem]


class HlsJobResponse(BaseModel):
    video_id: str
    status: str
    playlist_url: str | None = None
    message: str | None = None


def list_mp4_files() -> list[VideoItem]:
    if not VIDEOS_DIR.is_dir():
        return []
    items: list[VideoItem] = []
    for p in sorted(VIDEOS_DIR.glob("*.mp4")):
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


def resolve_video_path(video_id: str) -> Path:
    if not SAFE_ID.match(video_id):
        raise HTTPException(status_code=400, detail="video_id inválido")
    candidate = (VIDEOS_DIR / f"{video_id}.mp4").resolve()
    videos_root = VIDEOS_DIR.resolve()
    if not str(candidate).startswith(str(videos_root)) or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    return candidate


def hls_playlist_path(video_id: str) -> Path:
    return (HLS_DIR / video_id / "playlist.m3u8").resolve()


def run_ffmpeg_sync(video_id: str, input_path: Path) -> None:
    out_dir = HLS_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    playlist = out_dir / "playlist.m3u8"

    cmd = [
        FFMPEG_BIN,
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


@app.on_event("startup")
def on_startup() -> None:
    ensure_dirs()
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/videos", response_model=VideoListResponse)
def list_videos():
    """Lista arquivos .mp4 disponíveis na pasta configurada."""
    return VideoListResponse(videos=list_mp4_files())


@app.post("/api/videos/{video_id}/hls", response_model=HlsJobResponse)
async def generate_hls(video_id: str):
    """
    Gera pacote HLS (VOD) sob demanda para o vídeo indicado.
    Se já existir playlist.m3u8, retorna imediatamente como pronto.
    """
    input_path = resolve_video_path(video_id)
    playlist = hls_playlist_path(video_id)
    hls_root = HLS_DIR.resolve()
    if not str(playlist).startswith(str(hls_root)):
        raise HTTPException(status_code=400, detail="Caminho HLS inválido")

    if playlist.is_file():
        with _db_lock:
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO video_jobs (video_id, filename, status, error_message, updated_at)
                    VALUES (?, ?, 'ready', NULL, datetime('now'))
                    ON CONFLICT(video_id) DO UPDATE SET
                        status = 'ready',
                        error_message = NULL,
                        updated_at = datetime('now')
                    """,
                    (video_id, input_path.name),
                )
        return HlsJobResponse(
            video_id=video_id,
            status="ready",
            playlist_url=f"/hls/{video_id}/playlist.m3u8",
            message="HLS já existia; nenhuma transcodificação necessária.",
        )

    with _db_lock:
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO video_jobs (video_id, filename, status, error_message, updated_at)
                VALUES (?, ?, 'processing', NULL, datetime('now'))
                ON CONFLICT(video_id) DO UPDATE SET
                    status = 'processing',
                    error_message = NULL,
                    updated_at = datetime('now')
                """,
                (video_id, input_path.name),
            )

    loop = asyncio.get_running_loop()

    def job():
        try:
            run_ffmpeg_sync(video_id, input_path)
            with _db_lock:
                with get_db() as conn:
                    conn.execute(
                        """
                        UPDATE video_jobs
                        SET status = 'ready', error_message = NULL, updated_at = datetime('now')
                        WHERE video_id = ?
                        """,
                        (video_id,),
                    )
        except Exception as e:  # noqa: BLE001
            msg = str(e)[:2000]
            with _db_lock:
                with get_db() as conn:
                    conn.execute(
                        """
                        UPDATE video_jobs
                        SET status = 'error', error_message = ?, updated_at = datetime('now')
                        WHERE video_id = ?
                        """,
                        (msg, video_id),
                    )
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


@app.get("/api/videos/{video_id}/hls/status", response_model=HlsJobResponse)
def hls_status(video_id: str):
    """Consulta status do job HLS no SQLite (e existência do playlist)."""
    resolve_video_path(video_id)
    playlist = hls_playlist_path(video_id)
    with _db_lock:
        with get_db() as conn:
            row = conn.execute(
                "SELECT status, error_message FROM video_jobs WHERE video_id = ?",
                (video_id,),
            ).fetchone()
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


app.mount("/hls", StaticFiles(directory=str(HLS_DIR)), name="hls")
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
