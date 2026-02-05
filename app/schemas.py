from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


VIDEO_FORMATS = {
    "mp4",
    "mkv",
    "mov",
    "webm",
    "avi",
    "flv",
}
GIF_FORMATS = {"gif"}
AUDIO_FORMATS = {
    "mp3",
    "wav",
    "m4a",
    "aac",
    "flac",
    "opus",
    "ogg",
    "vorbis",
    "alac",
}
OUTPUT_FORMATS = VIDEO_FORMATS | AUDIO_FORMATS | GIF_FORMATS | {""}


class DownloadRequest(BaseModel):
    url: HttpUrl = Field(..., description="Media URL to download")
    quality: str = Field(
        default="best",
        description="yt-dlp format selector (e.g., best, bestvideo, bestaudio, worst)",
    )
    resolution: int | None = Field(
        default=None,
        description="Max height in pixels (e.g., 720). Defaults to source best.",
        ge=144,
        le=4320,
    )
    output_format: Literal[
        "",
        "mp4",
        "mkv",
        "mov",
        "webm",
        "avi",
        "flv",
        "gif",
        "mp3",
        "wav",
        "m4a",
        "aac",
        "flac",
        "opus",
        "ogg",
        "vorbis",
        "alac",
    ] = Field(
        default="",
        description="Desired output format. Empty string keeps original format.",
    )


class DownloadResponse(BaseModel):
    request_id: str
    filename: str
    bytes: int
    output_format: str
