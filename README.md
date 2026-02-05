# DlpApi
An API wrapper for yt-dlp.

**Quick Start**
1. Install dependencies: `pip install -r requirements.txt`
2. Run the API: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. Open Swagger UI at `http://localhost:8000/docs`

**Configuration**
- Environment variables (highest priority):
  - `DLP_API_AUTH_TOKEN`
  - `DLP_API_DOWNLOAD_ROOT`
  - `DLP_API_LOG_LEVEL`
  - `DLP_API_CONFIG_FILE`
- Config file (default `config.json`):
```json
{
  "auth_token": "change-me",
  "download_root": "downloads",
  "log_level": "INFO"
}
```

If no auth token is configured, the API logs a warning and allows requests without a token.

**Download Endpoint**
`POST /download`
- `url`: media URL (required)
- `quality`: yt-dlp format selector (default `best`). Special value `bestaudioleastres` picks the lowest-res video stream plus the best audio stream.
- `resolution`: max height in pixels (optional). If provided, a height filter is applied; a fallback to `best` is used if no match is available.
- `output_format`: empty string to keep original format, or one of `mp4`, `mkv`, `mov`, `webm`, `avi`, `flv`, `gif`, `mp3`, `wav`, `m4a`, `aac`, `flac`, `opus`, `ogg`, `vorbis`, `alac`

**Example Request**
```bash
curl -X POST "http://localhost:8000/download" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "quality": "best",
    "resolution": 720,
    "output_format": "mp4"
  }'
```

**Response**
The endpoint returns the downloaded file as the response body. Response headers include:
- `X-Request-Id`
- `X-Output-Format` (echoes the requested output format)

The endpoint returns the downloaded file directly. It requires a bearer token only when one is configured.
