import errno
from pathlib import Path

import anyio
import pytest
from fastapi.testclient import TestClient

from phone_lan_transfer import storage
from phone_lan_transfer.config import TransferSettings
from phone_lan_transfer.main import create_app

AUTHORIZATION = {"Authorization": "Bearer test-token"}


def upload_client(destination: Path, limit: int = 10) -> TestClient:
    return TestClient(
        create_app(
            access_token="test-token",
            settings=TransferSettings(destination, limit),
        )
    )


def test_upload_saves_exact_bytes_at_configured_destination(tmp_path: Path) -> None:
    destination = tmp_path / "received"
    response = upload_client(destination).post(
        "/uploads",
        params={"destination_name": "photo.jpg"},
        content=b"\x00\xffphoto",
        headers=AUTHORIZATION,
    )

    assert response.status_code == 201
    assert response.json() == {"status": "saved", "destination_name": "photo.jpg"}
    assert (destination / "photo.jpg").read_bytes() == b"\x00\xffphoto"


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong-token"}])
def test_unauthorized_upload_does_not_create_destination(
    tmp_path: Path, headers: dict[str, str]
) -> None:
    destination = tmp_path / "received"
    response = upload_client(destination).post(
        "/uploads",
        params={"destination_name": "file.txt"},
        content=b"data",
        headers=headers,
    )
    assert response.status_code == 401
    assert not destination.exists()


def test_upload_rejects_unsafe_name_without_writing(tmp_path: Path) -> None:
    destination = tmp_path / "received"
    response = upload_client(destination).post(
        "/uploads",
        params={"destination_name": "../outside.txt"},
        content=b"data",
        headers=AUTHORIZATION,
    )
    assert response.status_code == 400
    assert not destination.exists()
    assert not (tmp_path / "outside.txt").exists()


def test_upload_preserves_existing_file_on_collision(tmp_path: Path) -> None:
    existing = tmp_path / "file.txt"
    existing.write_bytes(b"original")
    response = upload_client(tmp_path).post(
        "/uploads",
        params={"destination_name": "file.txt"},
        content=b"new",
        headers=AUTHORIZATION,
    )
    assert response.status_code == 409
    assert existing.read_bytes() == b"original"


def test_upload_enforces_configured_limit_without_content_length(
    tmp_path: Path,
) -> None:
    response = upload_client(tmp_path, limit=5).post(
        "/uploads",
        params={"destination_name": "large.bin"},
        content=iter([b"abc", b"def"]),
        headers=AUTHORIZATION,
    )
    assert response.status_code == 413
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "ending,limit,expected_status",
    [
        ("complete", 6, 201),
        ("complete", 5, 413),
        ("disconnect", 6, 400),
    ],
)
def test_upload_handles_separate_network_chunks_and_disconnect_cleanup(
    tmp_path: Path,
    ending: str,
    limit: int,
    expected_status: int,
) -> None:
    application = create_app(
        access_token="test-token", settings=TransferSettings(tmp_path, limit)
    )
    incoming = [
        {"type": "http.request", "body": b"abc", "more_body": True},
        (
            {"type": "http.disconnect"}
            if ending == "disconnect"
            else {"type": "http.request", "body": b"def", "more_body": False}
        ),
    ]
    outgoing = []

    async def receive():
        return incoming.pop(0)

    async def send(message):
        outgoing.append(message)

    async def run_request():
        await application(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": "/uploads",
                "raw_path": b"/uploads",
                "query_string": b"destination_name=stream.bin",
                "headers": [(b"authorization", b"Bearer test-token")],
                "client": ("127.0.0.1", 1234),
                "server": ("127.0.0.1", 8000),
                "root_path": "",
            },
            receive,
            send,
        )

    anyio.run(run_request)

    assert outgoing[0]["status"] == expected_status
    if expected_status == 201:
        assert (tmp_path / "stream.bin").read_bytes() == b"abcdef"
    else:
        assert list(tmp_path.iterdir()) == []


def test_upload_accepts_file_exactly_at_limit(tmp_path: Path) -> None:
    response = upload_client(tmp_path, limit=5).post(
        "/uploads",
        params={"destination_name": "exact.bin"},
        content=b"12345",
        headers=AUTHORIZATION,
    )
    assert response.status_code == 201
    assert (tmp_path / "exact.bin").read_bytes() == b"12345"


@pytest.mark.parametrize(
    "error_number,expected_status", [(errno.ENOSPC, 507), (errno.EACCES, 500)]
)
def test_upload_reports_storage_failure_without_leaking_local_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_number: int,
    expected_status: int,
) -> None:
    def failed_open(*args, **kwargs):
        raise OSError(error_number, "private path details", str(tmp_path))

    monkeypatch.setattr(storage, "open", failed_open, raising=False)
    response = upload_client(tmp_path).post(
        "/uploads",
        params={"destination_name": "file.txt"},
        content=b"data",
        headers=AUTHORIZATION,
    )
    assert response.status_code == expected_status
    assert "private path details" not in response.text
    assert list(tmp_path.iterdir()) == []
