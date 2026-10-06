from pathlib import Path

import pytest

from phone_lan_transfer.config import TransferSettings
from phone_lan_transfer.main import create_app
from phone_lan_transfer.storage import DEFAULT_MAX_FILE_BYTES


def test_default_settings_resolve_destination_without_creating_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)

    application = create_app(access_token="test-token")
    settings = application.state.transfer_settings

    assert settings.destination_directory == tmp_path / "uploads"
    assert settings.max_file_bytes == DEFAULT_MAX_FILE_BYTES
    assert not settings.destination_directory.exists()


@pytest.mark.parametrize("limit", [0, -1])
def test_application_settings_reject_nonpositive_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        TransferSettings(max_file_bytes=limit)
