from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

ALGORITHM = "HS256"
EXPIRY_HOURS = 24

_bearer = HTTPBearer()


class JWTUser(BaseModel):
    user_id: UUID
    email: str


def create_token(user_id: UUID, email: str, secret: str) -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(hours=EXPIRY_HOURS),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str) -> JWTUser:
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return JWTUser(user_id=UUID(payload["sub"]), email=payload["email"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def make_jwt_dependency(secret: str) -> "Callable[[HTTPAuthorizationCredentials], JWTUser]":
    def jwt_dependency(
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    ) -> JWTUser:
        return decode_token(credentials.credentials, secret)

    return jwt_dependency


# Lazily importable alias — services call jwt_dependency(secret) to get the dep
jwt_dependency = make_jwt_dependency


# Make the type hint importable without a forward-ref string
from collections.abc import Callable  # noqa: E402
