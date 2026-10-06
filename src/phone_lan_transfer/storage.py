"""Save incoming file chunks without overwriting an existing file."""

import os
from collections.abc import Iterable
from pathlib import Path

from phone_lan_transfer.filenames import validate_destination_name

DEFAULT_MAX_FILE_BYTES = 5 * 1024**3


class FileTooLargeError(ValueError):
    """The incoming file exceeded the configured byte limit."""


def save_file(
    chunks: Iterable[bytes],
    destination_directory: Path,
    destination_name: str,
    *,
    max_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> Path:
    """Write chunks to a new file and remove it if the transfer fails."""
    name = validate_destination_name(destination_name)
    if max_bytes <= 0:
        raise ValueError("File size limit must be positive")

    destination_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = destination_directory / name

    def private_opener(path: str, flags: int) -> int:
        return os.open(path, flags, 0o600)

    output = open(destination, "xb", opener=private_opener)
    bytes_written = 0
    try:
        with output:
            for chunk in chunks:
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise FileTooLargeError("File exceeds the configured size limit")
                output.write(chunk)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise

    return destination
