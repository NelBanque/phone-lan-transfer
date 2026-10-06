from pathlib import Path

import pytest

from phone_lan_transfer.storage import FileTooLargeError, save_file


def test_save_file_writes_chunks_and_creates_directory(tmp_path: Path) -> None:
    destination_directory = tmp_path / "received"

    saved_path = save_file(
        [b"hello ", b"world"], destination_directory, "greeting.txt", max_bytes=11
    )

    assert saved_path == destination_directory / "greeting.txt"
    assert saved_path.read_bytes() == b"hello world"


def test_save_file_does_not_overwrite_existing_file(tmp_path: Path) -> None:
    existing_path = tmp_path / "photo.jpg"
    existing_path.write_bytes(b"original")

    with pytest.raises(FileExistsError):
        save_file([b"replacement"], tmp_path, "photo.jpg")

    assert existing_path.read_bytes() == b"original"


def test_save_file_removes_partial_file_when_size_limit_is_exceeded(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileTooLargeError):
        save_file([b"first", b"second"], tmp_path, "large.bin", max_bytes=9)

    assert list(tmp_path.iterdir()) == []


def test_save_file_removes_partial_file_when_stream_fails(tmp_path: Path) -> None:
    def broken_chunks():
        yield b"partial"
        raise ConnectionError("connection lost")

    with pytest.raises(ConnectionError, match="connection lost"):
        save_file(broken_chunks(), tmp_path, "interrupted.bin")

    assert list(tmp_path.iterdir()) == []


def test_save_file_rejects_unsafe_name_before_creating_directory(
    tmp_path: Path,
) -> None:
    destination_directory = tmp_path / "received"

    with pytest.raises(ValueError):
        save_file([b"data"], destination_directory, "../outside.txt")

    assert not destination_directory.exists()
    assert not (tmp_path / "outside.txt").exists()


@pytest.mark.parametrize("max_bytes", [0, -1])
def test_save_file_rejects_nonpositive_limit(
    tmp_path: Path, max_bytes: int
) -> None:
    with pytest.raises(ValueError, match="positive"):
        save_file([b"data"], tmp_path / "received", "file.txt", max_bytes=max_bytes)

    assert not (tmp_path / "received").exists()
