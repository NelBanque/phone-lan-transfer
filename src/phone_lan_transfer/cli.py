"""Command-line interface for starting Phone LAN Transfer."""

import argparse
from collections.abc import Sequence

import segno
import uvicorn

from phone_lan_transfer.access import generate_access_token
from phone_lan_transfer.main import create_app
from phone_lan_transfer.network import detect_lan_ip, validate_lan_ip

DEFAULT_HOST = "127.0.0.1"
LAN_HOST = "0.0.0.0"
DEFAULT_PORT = 8000


def valid_port(value: str) -> int:
    """Return a valid TCP port or raise an argparse error."""
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def valid_lan_address(value: str) -> str:
    """Return a usable LAN IPv4 address or raise an argparse error."""
    try:
        return validate_lan_ip(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Transfer files from a phone over a trusted local network.",
    )
    parser.add_argument(
        "--lan",
        action="store_true",
        help="allow connections from other devices on the local network",
    )
    parser.add_argument(
        "--port",
        type=valid_port,
        default=DEFAULT_PORT,
        help=f"server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--lan-address",
        type=valid_lan_address,
        help="IPv4 address to show in the LAN access URL instead of detecting it",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> None:
    """Start the server in local-only or explicit LAN mode."""
    parser = create_parser()
    options = parser.parse_args(arguments)
    if options.lan_address is not None and not options.lan:
        parser.error("--lan-address requires --lan")

    host = LAN_HOST if options.lan else DEFAULT_HOST
    access_token = generate_access_token()
    application = create_app(access_token=access_token)

    if options.lan:
        lan_ip = options.lan_address or detect_lan_ip()
        access_url = f"http://{lan_ip}:{options.port}/#token={access_token}"
        print(f"Open this URL on your phone:\n{access_url}")
        qr_code = segno.make_qr(access_url)
        qr_code.terminal(compact=True)

    uvicorn.run(application, host=host, port=options.port)
