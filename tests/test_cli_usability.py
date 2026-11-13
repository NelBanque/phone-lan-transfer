"""Check public CLI options and safe startup behavior."""

import argparse

import pytest

from phone_lan_transfer import cli


@pytest.mark.parametrize(
    "value, expected", [("5", 5 * 1024**3), ("0.5", 512 * 1024**2)]
)
def test_gib_conversion(value, expected):
    assert cli.gib_bytes(value) == expected


@pytest.mark.parametrize(
    "value", ["0", "-1", "nan", "inf", "hello", "0.00000000001", "1e9999"]
)
def test_invalid_gib_values(value):
    with pytest.raises(argparse.ArgumentTypeError):
        cli.gib_bytes(value)


def test_short_options_reach_server(monkeypatch, tmp_path):
    applications = []
    monkeypatch.setattr(cli.uvicorn, "run", lambda app, **kw: applications.append(app))
    cli.main(["--local-only", "-m", "0.5", "-d", str(tmp_path)])
    settings = applications[0].state.transfer_settings
    assert settings.max_file_bytes == 512 * 1024**2
    assert settings.destination_directory == tmp_path


@pytest.mark.parametrize(
    "arguments",
    [
        ["-m", "5", "--max-file-bytes", "10"],
        ["--local-only", "--lan"],
        ["-help"],
        ["--max-file-bytes", "9007199254740992"],
    ],
)
def test_conflicting_or_invalid_options(arguments):
    with pytest.raises(SystemExit) as error:
        cli.main(arguments)
    assert error.value.code == 2


@pytest.mark.parametrize("option", ["-h", "--help"])
def test_help_needs_no_network(option, monkeypatch, capsys):
    monkeypatch.setattr(
        cli, "detect_lan_ip", lambda: pytest.fail("help needs no network")
    )
    with pytest.raises(SystemExit) as error:
        cli.main([option])
    assert error.value.code == 0
    output = capsys.readouterr().out
    for text in ("phonelt", "--destination", "--max-gib", "--local-only", "Examples:"):
        assert text in output


def test_qr_encoding_failure_keeps_url_and_server(monkeypatch, capsys):
    class BrokenQr:
        def terminal(self, **kwargs):
            raise UnicodeEncodeError("ascii", "\u2588", 0, 1, "unsupported")

    started = []
    monkeypatch.setattr(cli, "detect_lan_ip", lambda: "192.168.1.10")
    monkeypatch.setattr(cli.segno, "make_qr", lambda url: BrokenQr())
    monkeypatch.setattr(cli.uvicorn, "run", lambda app, **kw: started.append(kw))
    cli.main([])
    assert started[0]["host"] == cli.LAN_HOST
    output = capsys.readouterr().out
    assert "Open the URL above" in output
    assert "http://192.168.1.10:8000/#token=" in output


def test_failed_detection_gives_actionable_error(monkeypatch, capsys):
    def fail():
        raise RuntimeError("No LAN address")

    monkeypatch.setattr(cli, "detect_lan_ip", fail)
    with pytest.raises(SystemExit) as error:
        cli.main([])
    assert error.value.code == 2
    assert "--lan-address" in capsys.readouterr().err
