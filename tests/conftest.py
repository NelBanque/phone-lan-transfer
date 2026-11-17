"""Keep default receiving folders inside each test's temporary directory."""

import pytest

from phone_lan_transfer import config


@pytest.fixture(autouse=True)
def isolate_downloads(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "user_downloads_path", lambda: tmp_path / "Downloads")
