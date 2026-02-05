from __future__ import annotations

import logging
import os
import shutil
import subprocess
import uuid
from pathlib import Path

from yt_dlp import YoutubeDL

from .schemas import AUDIO_FORMATS, GIF_FORMATS, VIDEO_FORMATS

logger = logging.getLogger(__name__)


def _build_format_selector(quality: str, resolution: int | None) -> str:
    base = (quality or "best").strip()
    if base == "best":
        base = "bestvideo*+bestaudio/best"

    if not resolution:
        return base

    if base == "bestvideo*+bestaudio/best":
        return (
            f"bestvideo*[height<=?{resolution}]+bestaudio/"
            f"best[height<=?{resolution}]/best"
        )

    if "+" not in base and "/" not in base:
        if "audio" in base or base in {"ba", "bestaudio"}:
            return base
        return f"{base}[height<=?{resolution}]/best"

    parts = []
    for alt in base.split("/"):
        subparts = []
        for sel in alt.split("+"):
            if any(key in sel for key in ("bestvideo", "bv", "best")) and "audio" not in sel:
                subparts.append(f"{sel}[height<=?{resolution}]")
            else:
                subparts.append(sel)
        parts.append("+".join(subparts))
    return "/".join(parts) + "/best"


def _select_bestaudio_leastres_format(url: str) -> str:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats") or []
    audio_formats = [
        f
        for f in formats
        if f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")
    ]
    video_formats = [
        f
        for f in formats
        if f.get("vcodec") not in (None, "none") and f.get("height") is not None
    ]

    if not audio_formats and not video_formats:
        return "best"

    def audio_rank(fmt: dict) -> tuple[float, float]:
        abr = fmt.get("abr") or 0.0
        tbr = fmt.get("tbr") or 0.0
        return (abr, tbr)

    def video_rank(fmt: dict) -> tuple[int, float]:
        height = fmt.get("height") or 10_000
        tbr = fmt.get("tbr") or 0.0
        return (height, tbr)

    best_audio = max(audio_formats, key=audio_rank, default=None)
    least_res_video = min(video_formats, key=video_rank, default=None)

    if least_res_video and best_audio:
        return f"{least_res_video['format_id']}+{best_audio['format_id']}"
    if least_res_video:
        return str(least_res_video["format_id"])
    if best_audio:
        return str(best_audio["format_id"])
    return "best"


def _run_ffmpeg(input_path: Path, output_path: Path, output_format: str) -> None:
    audio_codec_map = {
        "mp3": "libmp3lame",
        "wav": "pcm_s16le",
        "m4a": "aac",
        "aac": "aac",
        "flac": "flac",
        "opus": "libopus",
        "ogg": "libvorbis",
        "vorbis": "libvorbis",
        "alac": "alac",
    }
    video_codec_map = {
        "mp4": ("libx264", "aac"),
        "mkv": ("libx264", "aac"),
        "mov": ("libx264", "aac"),
        "avi": ("libx264", "aac"),
        "flv": ("libx264", "aac"),
        "webm": ("libvpx-vp9", "libopus"),
    }

    cmd = ["ffmpeg", "-y", "-i", str(input_path)]
    if output_format in AUDIO_FORMATS:
        cmd += ["-vn", "-c:a", audio_codec_map[output_format]]
    elif output_format in GIF_FORMATS:
        cmd += ["-vf", "fps=15,scale=640:-1:flags=lanczos", "-loop", "0"]
    else:
        vcodec, acodec = video_codec_map[output_format]
        cmd += ["-c:v", vcodec, "-c:a", acodec]

    cmd.append(str(output_path))
    logger.info("Running ffmpeg: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def _pick_latest_file(folder: Path, stem: str) -> Path:
    candidates = [p for p in folder.iterdir() if p.is_file() and p.name.startswith(stem)]
    if not candidates:
        raise FileNotFoundError("No downloaded files were produced.")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def download_and_convert(
    url: str,
    quality: str,
    resolution: int | None,
    output_format: str,
    download_root: Path,
) -> tuple[str, Path]:
    request_id = uuid.uuid4().hex
    request_dir = download_root / request_id
    request_dir.mkdir(parents=True, exist_ok=True)

    if quality.strip().lower() == "bestaudioleastres":
        format_selector = _select_bestaudio_leastres_format(url)
    else:
        format_selector = _build_format_selector(quality, resolution)
    output_template = str(request_dir / f"{request_id}.%(ext)s")

    ydl_opts = {
        "format": format_selector,
        "outtmpl": output_template,
        "noplaylist": True,
        "retries": 3,
        "quiet": True,
        "no_warnings": True,
    }

    logger.info("Starting download for %s", url)
    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    downloaded = _pick_latest_file(request_dir, request_id)

    if not output_format:
        return request_id, downloaded

    desired_path = request_dir / f"{request_id}.{output_format}"
    if downloaded.suffix.lower().lstrip(".") != output_format:
        _run_ffmpeg(downloaded, desired_path, output_format)
    else:
        desired_path = downloaded

    if downloaded != desired_path:
        try:
            os.remove(downloaded)
        except OSError:
            logger.warning("Failed to remove intermediate file: %s", downloaded)

    return request_id, desired_path


def cleanup_request_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
