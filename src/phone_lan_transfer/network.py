"""Local network address utilities."""

import ipaddress
import socket

ROUTE_PROBE = ("192.0.2.1", 80)


def validate_lan_ip(address: str) -> str:
    """Return a usable LAN IPv4 address or raise a descriptive error."""
    try:
        parsed_address = ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError as error:
        raise ValueError("LAN address must be a valid IPv4 address") from error

    if (
        parsed_address.is_loopback
        or parsed_address.is_unspecified
        or parsed_address.is_multicast
        or parsed_address.is_reserved
    ):
        raise ValueError("LAN address must be a usable unicast IPv4 address")

    return address


def detect_lan_ip() -> str:
    """Return the IPv4 address used by the computer's default network route."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe_socket:
            probe_socket.connect(ROUTE_PROBE)
            address = probe_socket.getsockname()[0]
    except OSError as error:
        raise RuntimeError("Could not determine the computer's LAN address") from error

    try:
        return validate_lan_ip(address)
    except ValueError as error:
        raise RuntimeError("No usable LAN address was detected") from error
