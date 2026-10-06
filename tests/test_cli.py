from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from phone_lan_transfer import cli


@pytest.mark.parametrize(
    ("arguments", "expected_host", "expected_port"),
    [
        ([], cli.DEFAULT_HOST, cli.DEFAULT_PORT),
        (["--lan"], cli.LAN_HOST, cli.DEFAULT_PORT),
        (["--port", "9000"], cli.DEFAULT_HOST, 9000),
        (["--lan", "--port", "9000"], cli.LAN_HOST, 9000),
    ],
)
def test_main_starts_uvicorn_with_selected_network_options(
    monkeypatch: pytest.MonkeyPatch,
    arguments: Sequence[str],
    expected_host: str,
    expected_port: int,
) -> None:
    run_arguments: dict[str, Any] = {}

    def fake_run(application: Any, *, host: str, port: int) -> None:
        run_arguments.update(application=application, host=host, port=port)

    monkeypatch.setattr(cli, "generate_access_token", lambda: "test-token")
    monkeypatch.setattr(cli, "detect_lan_ip", lambda: "192.168.1.10")
    monkeypatch.setattr(cli.uvicorn, "run", fake_run)

    cli.main(arguments)

    assert run_arguments["application"].state.access_token == "test-token"
    assert run_arguments["host"] == expected_host
    assert run_arguments["port"] == expected_port


def test_main_displays_lan_access_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    qr_arguments: dict[str, Any] = {}

    class FakeQrCode:
        def terminal(self, *, compact: bool) -> None:
            qr_arguments["compact"] = compact

    def fake_make_qr(content: str) -> FakeQrCode:
        qr_arguments["content"] = content
        return FakeQrCode()

    monkeypatch.setattr(cli, "generate_access_token", lambda: "test-token")
    monkeypatch.setattr(cli, "detect_lan_ip", lambda: "192.168.1.10")
    monkeypatch.setattr(cli.segno, "make_qr", fake_make_qr)
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: None)

    cli.main(["--lan", "--port", "9000"])

    assert capsys.readouterr().out == (
        "Open this URL on your phone:\n"
        "http://192.168.1.10:9000/#token=test-token\n"
    )
    assert qr_arguments == {
        "content": "http://192.168.1.10:9000/#token=test-token",
        "compact": True,
    }


def test_main_uses_manual_lan_address(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    qr_content = ""

    class FakeQrCode:
        def terminal(self, *, compact: bool) -> None:
            pass

    def fake_make_qr(content: str) -> FakeQrCode:
        nonlocal qr_content
        qr_content = content
        return FakeQrCode()

    def fail_if_called() -> str:
        raise AssertionError("LAN detection should not run with a manual address")

    monkeypatch.setattr(cli, "generate_access_token", lambda: "test-token")
    monkeypatch.setattr(cli, "detect_lan_ip", fail_if_called)
    monkeypatch.setattr(cli.segno, "make_qr", fake_make_qr)
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: None)

    cli.main(["--lan", "--lan-address", "10.8.0.2"])

    assert "http://10.8.0.2:8000/#token=test-token" in capsys.readouterr().out
    assert qr_content == "http://10.8.0.2:8000/#token=test-token"


def test_main_does_not_detect_lan_ip_in_local_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called() -> str:
        raise AssertionError("LAN detection should not run in local-only mode")

    monkeypatch.setattr(cli, "detect_lan_ip", fail_if_called)
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: None)

    cli.main([])


@pytest.mark.parametrize("port", ["0", "65536", "not-a-number"])
def test_main_rejects_invalid_port(port: str) -> None:
    with pytest.raises(SystemExit):
        cli.main(["--port", port])


@pytest.mark.parametrize("address", ["not-an-ip", "127.0.0.1", "0.0.0.0"])
def test_main_rejects_invalid_lan_address(address: str) -> None:
    with pytest.raises(SystemExit):
        cli.main(["--lan", "--lan-address", address])


def test_main_rejects_lan_address_without_lan_mode() -> None:
    with pytest.raises(SystemExit):
        cli.main(["--lan-address", "192.168.1.10"])


def test_main_passes_transfer_settings_to_application(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    applications: list[Any] = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli.uvicorn,
        "run",
        lambda application, **kwargs: applications.append(application),
    )

    cli.main(["--destination", "received files", "--max-file-bytes", "1234"])

    settings = applications[0].state.transfer_settings
    assert settings.destination_directory == tmp_path / "received files"
    assert settings.max_file_bytes == 1234
    assert not settings.destination_directory.exists()


@pytest.mark.parametrize("limit", ["0", "-1", "1.5", "not-a-number"])
def test_main_rejects_invalid_file_limit_before_starting_server(
    monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    def fail_if_called(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Invalid settings must not start the server")

    monkeypatch.setattr(cli.uvicorn, "run", fail_if_called)
    with pytest.raises(SystemExit) as error:
        cli.main(["--max-file-bytes", limit])
    assert error.value.code == 2
