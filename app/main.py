from __future__ import annotations

import logging
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse

from .config import load_settings
from .downloader import cleanup_request_dir, download_and_convert
from .logging_config import configure_logging
from .schemas import DownloadRequest, OUTPUT_FORMATS
from .security import build_auth_dependency

settings = load_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

settings.download_root.mkdir(parents=True, exist_ok=True)

auth_dependency = build_auth_dependency(settings)

app = FastAPI(
    title="DLP API",
    description="FastAPI wrapper for yt-dlp downloads with optional auth.",
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/download")
async def download_media(
    payload: DownloadRequest,
    background_tasks: BackgroundTasks,
    _: None = Depends(auth_dependency),
):
    if payload.output_format not in OUTPUT_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported output format",
        )

    try:
        request_id, output_path = download_and_convert(
            url=str(payload.url),
            quality=payload.quality,
            resolution=payload.resolution,
            output_format=payload.output_format,
            download_root=settings.download_root,
        )
    except Exception as exc:
        logger.exception("Download failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    background_tasks.add_task(cleanup_request_dir, output_path.parent)

    return FileResponse(
        path=output_path,
        filename=output_path.name,
        media_type="application/octet-stream",
        headers={
            "X-Request-Id": request_id,
            "X-Output-Format": payload.output_format,
        },
    )
