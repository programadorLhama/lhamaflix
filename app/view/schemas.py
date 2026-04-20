from pydantic import BaseModel


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
