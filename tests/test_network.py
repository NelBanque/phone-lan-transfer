from typing import Self

import pytest

from phone_lan_transfer import network


class FakeSocket:
    def __init__(
        self,
        address: str = "192.168.1.10",
        connection_error: OSError | None = None,
    ) -> None:
        self.address = address
        self.connection_error = connection_error
        self.connected_to: tuple[str, int] | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def connect(self, address: tuple[str, int]) -> None:
        if self.connection_error is not None:
            raise self.connection_error
        self.connected_to = address

    def getsockname(self) -> tuple[str, int]:
        return (self.address, 54321)


def install_fake_socket(
    monkeypatch: pytest.MonkeyPatch,
    fake_socket: FakeSocket,
) -> None:
    monkeypatch.setattr(network.socket, "socket", lambda *args: fake_socket)


def test_detect_lan_ip_returns_default_route_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_socket = FakeSocket()
    install_fake_socket(monkeypatch, fake_socket)

    address = network.detect_lan_ip()

    assert address == "192.168.1.10"
    assert fake_socket.connected_to == network.ROUTE_PROBE


def test_detect_lan_ip_reports_network_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_socket(
        monkeypatch,
        FakeSocket(connection_error=OSError("network unavailable")),
    )

    with pytest.raises(RuntimeError, match="Could not determine"):
        network.detect_lan_ip()


@pytest.mark.parametrize("address", ["127.0.0.1", "0.0.0.0"])
def test_detect_lan_ip_rejects_unusable_address(
    monkeypatch: pytest.MonkeyPatch,
    address: str,
) -> None:
    install_fake_socket(monkeypatch, FakeSocket(address=address))

    with pytest.raises(RuntimeError, match="No usable LAN address"):
        network.detect_lan_ip()


def test_detect_lan_ip_rejects_invalid_ipv4(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_socket(monkeypatch, FakeSocket(address="not-an-ip"))

    with pytest.raises(RuntimeError, match="not valid IPv4"):
        network.detect_lan_ip()
