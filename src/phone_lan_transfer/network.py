"""Local network address utilities."""

import ipaddress
import socket

ROUTE_PROBE = ("192.0.2.1", 80)


def detect_lan_ip() -> str:
    """Return the IPv4 address used by the computer's default network route."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe_socket:
            probe_socket.connect(ROUTE_PROBE)
            address = probe_socket.getsockname()[0]
    except OSError as error:
        raise RuntimeError("Could not determine the computer's LAN address") from error

    try:
        parsed_address = ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError as error:
        raise RuntimeError("The detected LAN address is not valid IPv4") from error

    if parsed_address.is_loopback or parsed_address.is_unspecified:
        raise RuntimeError("No usable LAN address was detected")

    return address
