from __future__ import annotations

import logging

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import AppSettings

_security_scheme = HTTPBearer(auto_error=False)


def build_auth_dependency(settings: AppSettings):
    logger = logging.getLogger(__name__)
    if not settings.auth_token:
        logger.warning(
            "No auth token configured. API endpoints will be accessible without a token."
        )

    async def _auth_dependency(
        credentials: HTTPAuthorizationCredentials | None = Security(_security_scheme),
    ) -> None:
        if not settings.auth_token:
            return

        if not credentials or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid bearer token",
            )
        if credentials.credentials != settings.auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
            )

    return _auth_dependency
