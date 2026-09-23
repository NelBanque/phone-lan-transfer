from collections.abc import Sequence
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
    monkeypatch.setattr(cli.uvicorn, "run", fake_run)

    cli.main(arguments)

    assert run_arguments["application"].state.access_token == "test-token"
    assert run_arguments["host"] == expected_host
    assert run_arguments["port"] == expected_port


@pytest.mark.parametrize("port", ["0", "65536", "not-a-number"])
def test_main_rejects_invalid_port(port: str) -> None:
    with pytest.raises(SystemExit):
        cli.main(["--port", port])
