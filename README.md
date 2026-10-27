# Phone LAN Transfer

Transfer files from a mobile device directly to a computer over a local network, without installing a mobile app.

## Why I built this

I have often needed a simple way to move photos, videos, and other files from my iPhone to my computer. Instead of only looking for an existing tool, I decided to build one myself. The project now targets modern mobile browsers and desktop operating systems while keeping iPhone with Safari to Windows as the first reference combination. This gives me a practical problem through which to learn software engineering: breaking a task into small parts, evaluating technical choices, and understanding the solution well enough to explain and improve it.

> **Project status:** Early development. The local server, temporary access
> token, explicit LAN mode, terminal QR code, and responsive browser page are
> implemented. The browser can select, preview supported media, rename pending
> files, and remove them. An authenticated streaming upload endpoint is
> implemented and tested. The browser can send individual files and show
> confirmed saves, errors, and manual retries. A first manual phone-to-Windows
> transfer succeeded. Percentage progress and broader compatibility testing
> remain pending.

## Demo

_A short GIF showing the QR code, mobile upload page, and saved files will be added after the MVP is working._

## Planned features

- A local web server on the computer and a QR code that opens the upload page in a mobile browser.
- A fresh access token each time the server starts.
- Multiple file uploads with visible progress and errors.
- Streaming writes, unique safe filenames, and a configurable file size limit.
- Command-line options for the port and destination folder.

## Installation and usage

The current development server requires Python 3.11+ and
[`uv`](https://docs.astral.sh/uv/). Prepare the environment and start the
local-only server with:

```bash
uv sync
uv run phone-lan-transfer
```

Open <http://127.0.0.1:8000/health> to verify that the server returns
`{"status":"ok"}`. This default mode accepts connections only from the same
computer.

To listen for other devices on a trusted local network, start explicit LAN
mode:

```bash
uv run phone-lan-transfer --lan
```

Use `--port 9000` to select a different port. LAN mode prints both an access
URL and a terminal QR code for the phone. The root URL serves a responsive
browser page that reads the temporary link and lets you select, review, and
remove files. Images and videos can be previewed when the browser supports
their formats. You can set a destination name while keeping the file extension;
the phone's original file is not renamed. The page validates the token by
requesting the active file-size limit and warns about files that exceed it.
Destination-name feedback checks the full name against the server's 255-byte
UTF-8 rule and identifies reserved names and forbidden characters. The server
still validates every upload independently.
Use each file's Send button to transfer it. Names cannot be edited while
sending or after a confirmed save. Failed files offer Retry; existing names
require correction. If a save cannot be confirmed after a connection failure,
check the receiving folder before retrying. A retry never overwrites an
existing file. Do not use LAN mode on a public or
untrusted network.

If automatic address detection selects the wrong interface on a computer with
a VPN or multiple network connections, set the phone-facing IPv4 address
manually:

```bash
uv run phone-lan-transfer --lan --lan-address 192.168.1.25
```

This changes the address printed in the access URL and encoded in the QR code.
The server still listens on all IPv4 interfaces in explicit LAN mode.

Set the receiving folder and per-file byte limit at startup:

```bash
uv run phone-lan-transfer --destination "received files" --max-file-bytes 5368709120
```

The defaults are `./uploads` (relative to the startup directory) and 5 GiB per
file. The limit must be a positive integer number of bytes. Startup does not
create the folder or check whether it is writable. The upload endpoint uses
these settings; the browser displays the active limit and sends individual files.

### Development upload API

`GET /transfer-settings` returns the active per-file limit in bytes, for example
`{"max_file_bytes":5368709120}`. It requires the current Bearer token and does
not expose the receiving folder. The browser queries it before enabling file
selection. Connection errors offer a retry; invalid tokens require reopening
the current QR link. The page displays the limit and flags oversized files.

`POST /uploads?destination_name=<URL-encoded filename>` accepts one file as
the raw request body. Send the current token in `Authorization: Bearer <token>`.
This is not a multipart form upload. The server reads network chunks directly
into the configured receiving folder and enforces the limit while writing,
even when the request has no `Content-Length` header.

After the write and file close succeed, the response is HTTP 201 with
`{"status":"saved","destination_name":"photo.jpg"}`. This does not guarantee
durability across power loss. Errors include 400 for an invalid name or an
interrupted upload, 401 for invalid authentication, 409 for an existing name,
413 for exceeding the limit, 507 for insufficient disk space, and 500 for other
storage failures. A missing destination name returns 422. Handled write or
connection failures remove the partial file; an abrupt process or power loss
may still leave one. A disconnected phone may not receive the error response.

The API has automated Windows tests, including separate network chunks and
disconnect cleanup. On 2026-10-27, a user manually sent a file from a phone
through the browser and confirmed receipt on Windows. The phone OS, browser
version, file format, and byte-for-byte integrity were not recorded; this is
an initial smoke test rather than a compatibility claim.

## Architecture

The receiving computer will host a local FastAPI server. A phone or tablet will open a single HTML, CSS, and JavaScript page in a modern browser by scanning a QR code, then upload files directly into a local folder on the computer. The MVP will treat uploads as files rather than restricting them to particular media types, so it can transfer photos, videos, PDFs, documents, archives, and other formats. A diagram and component notes will be added to `docs/ARCHITECTURE.md` when implementation begins.

The core is designed for mobile devices with modern browsers and for Windows, macOS, and Linux receivers. This includes combinations such as iPhone to Windows, Android to macOS, or a tablet to Linux. Compatibility will be claimed only after each combination is tested. The first reference combination is iPhone with Safari to Windows.

## Development checks

Run `uv run pytest` and `uv run ruff check .` for the Python checks.
With Node.js installed, run `node --test tests/browser-settings.test.cjs` to
check the browser settings flow with simulated network responses and page elements.
These checks do not replace testing in a real mobile browser.

## Known limitations and security

- This tool is intended only for trusted local networks. Do not expose its server to the internet.
- The mobile device and computer must be able to reach each other on the same network. Guest, hotel, and university networks may block device-to-device connections.
- The receiving computer's firewall may ask for permission or require a local-network rule when the server first starts.
- File selection, available file providers, paths, permissions, and firewall behavior can vary across browsers and operating systems.
- Transferred files should be treated as untrusted unless they come from a device and source you trust.
- The planned HTTP connection is unencrypted. Other devices with the ability to observe traffic on the network may see uploaded files or the access token. The threat model will be documented in `docs/SECURITY.md`.

## Roadmap

1. Repository setup and a minimal server.
2. QR access and a browser upload page.
3. Safe streaming uploads, tests, and CI: MVP (`v0.1.0`).
4. Compatibility testing for Android browsers and macOS and Linux receivers.
5. Optional HEIC conversion, EXIF date organization, and duplicate detection.
6. Local administration page and platform-specific desktop packages.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
