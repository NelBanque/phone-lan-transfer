"""Startup settings shared by the CLI and receiving application."""

from dataclasses import dataclass
from pathlib import Path

from phone_lan_transfer.storage import DEFAULT_MAX_FILE_BYTES


@dataclass(frozen=True)
class TransferSettings:
    """Keep one destination and a positive per-file limit for a server run."""

    destination_directory: Path = Path("uploads")
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES

    def __post_init__(self) -> None:
        if self.max_file_bytes <= 0:
            raise ValueError("File size limit must be positive")
        object.__setattr__(
            self,
            "destination_directory",
            self.destination_directory.expanduser().resolve(),
        )
