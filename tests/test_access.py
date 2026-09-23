import base64

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from phone_lan_transfer.access import (
    TOKEN_BYTES,
    generate_access_token,
    is_access_token_valid,
    require_access_token,
)


def test_access_token_is_url_safe_and_has_expected_random_bytes() -> None:
    token = generate_access_token()
    padding = "=" * (-len(token) % 4)

    decoded_token = base64.urlsafe_b64decode(token + padding)

    assert len(decoded_token) == TOKEN_BYTES


def test_access_token_changes_between_calls() -> None:
    first_token = generate_access_token()
    second_token = generate_access_token()

    assert first_token != second_token


def test_expected_bearer_token_is_valid() -> None:
    assert is_access_token_valid("Bearer expected-token", "expected-token")


@pytest.mark.parametrize(
    "authorization_header",
    [
        None,
        "",
        "expected-token",
        "Basic expected-token",
        "Bearer",
        "Bearer wrong-token",
    ],
)
def test_invalid_authorization_header_is_rejected(
    authorization_header: str | None,
) -> None:
    assert not is_access_token_valid(authorization_header, "expected-token")


def create_protected_test_client() -> TestClient:
    test_app = FastAPI()
    test_app.state.access_token = "expected-token"

    @test_app.get("/protected", dependencies=[Depends(require_access_token)])
    def protected() -> dict[str, str]:
        return {"status": "authorized"}

    return TestClient(test_app)


def test_protected_request_accepts_expected_token() -> None:
    client = create_protected_test_client()

    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer expected-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "authorized"}


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer wrong-token"},
    ],
)
def test_protected_request_rejects_invalid_token(headers: dict[str, str]) -> None:
    client = create_protected_test_client()

    response = client.get("/protected", headers=headers)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing access token"}
