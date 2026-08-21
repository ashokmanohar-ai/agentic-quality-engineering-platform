"""Lightweight local JWT authentication; replaceable by enterprise OIDC."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict

from app.config import get_settings
from app.models import Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class Principal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    tenant_id: str
    role: Role


def create_token(principal: Principal) -> str:
    settings = get_settings()
    claims = principal.model_dump(mode="json") | {
        "sub": principal.username,
        "exp": datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes),
    }
    encoded = jwt.encode(claims, settings.jwt_secret, algorithm="HS256")
    return encoded.decode() if isinstance(encoded, bytes) else encoded


def current_principal(token: Annotated[str, Depends(oauth2_scheme)]) -> Principal:
    try:
        claims = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        return Principal.model_validate(
            {key: claims[key] for key in ("username", "tenant_id", "role")}
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token") from exc
