"""Command-line interface for starting Phone LAN Transfer."""

import argparse
import sys
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

import segno
import uvicorn

from phone_lan_transfer.access import generate_access_token
from phone_lan_transfer.config import TransferSettings, default_destination
from phone_lan_transfer.main import create_app
from phone_lan_transfer.network import detect_lan_ip, validate_lan_ip
from phone_lan_transfer.storage import DEFAULT_MAX_FILE_BYTES, prepare_destination

DEFAULT_HOST = "127.0.0.1"
LAN_HOST = "0.0.0.0"
DEFAULT_PORT = 8000


class ReadableHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Put option descriptions below their flags with space between entries."""

    def __init__(self, prog: str) -> None:
        super().__init__(prog, max_help_position=4)

    def _format_action(self, action: argparse.Action) -> str:
        return super()._format_action(action) + "\n"


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


def positive_bytes(value: str) -> int:
    """Parse a positive integer byte limit for incoming files."""
    try:
        limit = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("limit must be a positive integer") from error
    if limit <= 0:
        raise argparse.ArgumentTypeError("limit must be a positive integer")
    return limit


def gib_bytes(value: str) -> int:
    """Convert positive finite GiB to an exact whole-byte limit."""
    try:
        gib = Decimal(value)
        if not gib.is_finite() or not 0 < gib <= Decimal(2**53 - 1) / 1024**3:
            raise ValueError
        numerator, denominator = gib.as_integer_ratio()
        size, remainder = divmod(numerator * 1024**3, denominator)
        if remainder or size > 2**53 - 1:
            raise ValueError
        return size
    except (ValueError, InvalidOperation) as error:
        raise argparse.ArgumentTypeError(
            "use positive GiB representing whole bytes (for example 5 or 0.5)"
        ) from error


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="phonelt",
        allow_abbrev=False,
        description="Transfer files from a phone over a trusted local network.",
        formatter_class=ReadableHelpFormatter,
        epilog=(
            "Examples:\n"
            "  phonelt                      Start and show the phone QR\n"
            "  phonelt -m 10                Allow 10 GiB per file\n"
            '  phonelt -d "D:/Received"      Choose the receiving folder\n'
            "  phonelt --local-only         Disable access from other devices\n\n"
            "Keep both devices on the same trusted network. HTTP is unencrypted.\n"
            "Stop with Ctrl+C. The phone-lan-transfer command also works."
        ),
    )
    network = parser.add_mutually_exclusive_group()
    network.add_argument(
        "--lan",
        action="store_true",
        help="LAN mode (already the default; retained for compatibility)",
    )
    network.add_argument(
        "--local-only", action="store_true", help="listen only on this computer"
    )
    parser.add_argument(
        "-p",
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
    parser.add_argument(
        "-d",
        "--destination",
        type=Path,
        help="receiving folder (default: system Downloads/Phone LAN Transfer)",
    )
    limits = parser.add_mutually_exclusive_group()
    limits.add_argument(
        "-m",
        "--max-gib",
        type=gib_bytes,
        metavar="GIB",
        help="maximum per file in GiB, including decimals (default: 5)",
    )
    limits.add_argument(
        "--max-file-bytes",
        type=positive_bytes,
        help=f"per-file size limit in bytes (default: {DEFAULT_MAX_FILE_BYTES}, 5 GiB)",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> None:
    """Start LAN reception by default with a visible configuration summary."""
    parser = create_parser()
    if "-help" in (sys.argv[1:] if arguments is None else arguments):
        parser.error("use -h or --help")
    options = parser.parse_args(arguments)
    if options.lan_address is not None and options.local_only:
        parser.error("--lan-address cannot be combined with --local-only")

    host = DEFAULT_HOST if options.local_only else LAN_HOST
    limit = options.max_gib or options.max_file_bytes or DEFAULT_MAX_FILE_BYTES
    if limit > 2**53 - 1:
        parser.error("limit must be at most 9007199254740991 bytes for browser support")
    try:
        settings = TransferSettings(options.destination or default_destination(), limit)
        prepare_destination(settings.destination_directory)
    except (OSError, ValueError) as error:
        parser.error(
            f"Cannot prepare the receiving folder: {error}. "
            "Choose another folder with -d, or check its permissions and free space."
        )
    access_token = generate_access_token()
    application = create_app(access_token=access_token, settings=settings)

    print("\n  PHONE LAN TRANSFER")
    print("  ------------------")
    print("  From your phone, straight to your computer.\n")
    print(f"  Receiving folder: {settings.destination_directory}")
    print(f"  Maximum per file: {limit / 1024**3:g} GiB")
    print("\n  Help and examples: phonelt -h | Stop: Ctrl+C\n")
    if not options.local_only:
        print("  Local network reception | HTTP is unencrypted.")
        print("  Keep both devices on the same trusted network.\n")
        try:
            lan_ip = options.lan_address or detect_lan_ip()
        except RuntimeError as error:
            parser.error(f"{error}. Try --lan-address <computer IPv4> or --local-only")
        access_url = f"http://{lan_ip}:{options.port}/#token={access_token}"
        print("  Scan the QR code with your phone to choose and send files.")
        print("  Keep this terminal open while transferring.\n")
        print(f"  Or open this private link on your phone:\n  {access_url}\n")
        qr_code = segno.make_qr(access_url)
        try:
            qr_code.terminal(compact=True)
        except UnicodeEncodeError:
            print("QR unavailable in this terminal. Open the URL above on your phone.")
    else:
        print("Local-only mode: other devices cannot connect.")
        print(f"Health check: http://127.0.0.1:{options.port}/health")

    uvicorn.run(application, host=host, port=options.port)
