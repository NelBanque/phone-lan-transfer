"""Temporary access token utilities."""

import secrets
from typing import Annotated

from fastapi import Header, HTTPException, Request, status

TOKEN_BYTES = 32


def generate_access_token() -> str:
    """Return a URL-safe access token with 256 bits of randomness."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def is_access_token_valid(
    authorization_header: str | None,
    expected_token: str,
) -> bool:
    """Return whether an Authorization header contains the expected token."""
    if authorization_header is None:
        return False

    scheme, separator, provided_token = authorization_header.partition(" ")
    if separator == "" or scheme.casefold() != "bearer":
        return False

    return secrets.compare_digest(provided_token, expected_token)


def require_access_token(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Reject requests that do not contain the current access token."""
    if not is_access_token_valid(authorization, request.app.state.access_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing access token",
        )
