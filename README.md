# Phone LAN Transfer

Transfer photos and videos from a mobile device to a computer over a local network, without installing a mobile app.

## Why I built this

I have often needed a simple way to move photos and videos from my iPhone to my computer. Instead of only looking for an existing tool, I decided to build one myself. The project now targets modern mobile browsers and desktop operating systems while keeping iPhone with Safari to Windows as the first reference combination. This gives me a practical problem through which to learn software engineering: breaking a task into small parts, evaluating technical choices, and understanding the solution well enough to explain and improve it.

> **Project status:** Early development. A minimal FastAPI server, temporary
> access token, and explicit LAN mode are implemented; the QR code and file
> transfer are not implemented yet.

## Demo

_A short GIF showing the QR code, mobile upload page, and saved files will be added after the MVP is working._

## Planned features

- A local web server on the computer and a QR code that opens the upload page in a mobile browser.
- A fresh access token each time the server starts.
- Multiple photo and video uploads with visible progress and errors.
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

Use `--port 9000` to select a different port. LAN mode currently exposes only
the development endpoints; phone access through a QR code will be added in the
next step. Do not use LAN mode on a public or untrusted network.

## Architecture

The receiving computer will host a local FastAPI server. A phone or tablet will open a single HTML, CSS, and JavaScript page in a modern browser by scanning a QR code, then upload files directly to the computer. A diagram and component notes will be added to `docs/ARCHITECTURE.md` when implementation begins.

The core is designed for mobile devices with modern browsers and for Windows, macOS, and Linux receivers. This includes combinations such as iPhone to Windows, Android to macOS, or a tablet to Linux. Compatibility will be claimed only after each combination is tested. The first reference combination is iPhone with Safari to Windows.

## Known limitations and security

- This tool is intended only for trusted local networks. Do not expose its server to the internet.
- The mobile device and computer must be able to reach each other on the same network. Guest, hotel, and university networks may block device-to-device connections.
- The receiving computer's firewall may ask for permission or require a local-network rule when the server first starts.
- File selection, media formats, paths, permissions, and firewall behavior can vary across browsers and operating systems.
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
