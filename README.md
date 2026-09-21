# iPhone LAN Transfer

Transfer photos and videos from an iPhone to a Windows PC over a local network, without installing an app on the iPhone.

## Why I built this

I have often needed a simple way to move photos and videos from my iPhone to my computer. Instead of only looking for an existing tool, I decided to build one myself. This project gives me a practical problem through which to learn software engineering: breaking a task into small parts, evaluating technical choices, and understanding the solution well enough to explain and improve it.

> **Project status:** Planning. The application is not implemented yet. This repository documents its intended scope and will grow in small, reviewed milestones.

## Demo

_A short GIF showing the QR code, iPhone upload page, and saved files will be added after the MVP is working._

## Planned features

- A local web server on the PC and a QR code that opens the upload page in Safari.
- A fresh access token each time the server starts.
- Multiple photo and video uploads with visible progress and errors.
- Streaming writes, unique safe filenames, and a configurable file size limit.
- Command-line options for the port and destination folder.

## Installation and usage

Installation and usage commands will be added when the first runnable milestone is available. The planned environment is Python 3.11+ on Windows, with an iPhone and PC connected to the same local network.

## Architecture

The Windows PC will host a local FastAPI server. The iPhone will open a single HTML, CSS, and JavaScript page in Safari by scanning a QR code, then upload files directly to the PC. A diagram and component notes will be added to `docs/ARCHITECTURE.md` when implementation begins.

## Known limitations and security

- This tool is intended only for trusted local networks. Do not expose its server to the internet.
- The iPhone and PC must be able to reach each other on the same network. Guest, hotel, and university networks may block device-to-device connections.
- Windows Firewall may ask for permission when the server first starts.
- The planned HTTP connection is unencrypted. Other devices with the ability to observe traffic on the network may see uploaded files or the access token. The threat model will be documented in `docs/SECURITY.md`.

## Roadmap

1. Repository setup and a minimal server.
2. QR access and a browser upload page.
3. Safe streaming uploads, tests, and CI: MVP (`v0.1.0`).
4. Optional HEIC conversion, EXIF date organization, and duplicate detection.
5. Local administration page and Windows executable.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
