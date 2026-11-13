"""Startup settings shared by the CLI and receiving application."""

from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_downloads_path

from phone_lan_transfer.storage import DEFAULT_MAX_FILE_BYTES


def default_destination() -> Path:
    """Return the system Downloads subfolder without creating it."""
    return user_downloads_path() / "Phone LAN Transfer"


@dataclass(frozen=True)
class TransferSettings:
    """Keep one destination and a positive per-file limit for a server run."""

    destination_directory: Path = field(default_factory=default_destination)
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES

    def __post_init__(self) -> None:
        if self.max_file_bytes <= 0:
            raise ValueError("File size limit must be positive")
        object.__setattr__(
            self,
            "destination_directory",
            self.destination_directory.expanduser().resolve(),
        )
