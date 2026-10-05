"""Validate destination filenames before writing uploaded files."""

WINDOWS_RESERVED_STEMS = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{digit}" for digit in "123456789\u00b9\u00b2\u00b3"}
    | {f"LPT{digit}" for digit in "123456789\u00b9\u00b2\u00b3"}
)
WINDOWS_FORBIDDEN_CHARACTERS = frozenset('<>:"/\\|?*')
MAX_FILENAME_BYTES = 255


def validate_destination_name(name: str) -> str:
    """Return a portable filename or reject an unsafe destination name."""
    if not name or name in {".", ".."}:
        raise ValueError("Destination filename is empty or reserved")

    if name != name.strip() or name.endswith("."):
        raise ValueError("Destination filename has surrounding space or a trailing dot")

    if any(
        character in WINDOWS_FORBIDDEN_CHARACTERS
        or ord(character) < 32
        or 127 <= ord(character) <= 159
        for character in name
    ):
        raise ValueError("Destination filename contains a forbidden character")

    if name.split(".", 1)[0].upper() in WINDOWS_RESERVED_STEMS:
        raise ValueError("Destination filename is reserved on Windows")

    try:
        encoded_name = name.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("Destination filename contains invalid Unicode") from error

    if len(encoded_name) > MAX_FILENAME_BYTES:
        raise ValueError("Destination filename exceeds 255 UTF-8 bytes")

    return name
