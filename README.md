# Phone LAN Transfer

[![CI](https://github.com/NelBanque/phone-lan-transfer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/NelBanque/phone-lan-transfer/actions/workflows/ci.yml)

Send files from your phone to your computer over a local network. Run `phonelt` on your computer, scan its QR code, and send files from your phone's browser.

I built this to send photos, videos, and documents from my phone to my computer without installing a mobile app. Created by **Nel Banqué**.

## Demo

[![iPhone to Windows demo showing file selection, renaming, and batch sending](docs/media/phone-lan-transfer-demo.gif)](docs/media/phone-lan-transfer-demo.mp4)

[Watch the full 50-second demo](docs/media/phone-lan-transfer-demo.mp4)

## Install from scratch

1. Install [Python 3.11 or newer](https://www.python.org/downloads/), [Git](https://git-scm.com/install/) and [uv](https://docs.astral.sh/uv/getting-started/installation/). On Windows, enable the option to add Python to PATH if the installer offers it. Open a new terminal after installing the tools.
2. Clone the repository and install the command.

   ```sh
   git clone https://github.com/NelBanque/phone-lan-transfer.git
   cd phone-lan-transfer
   python scripts/install_tool.py
   ```

   Use `python3` if that's how your terminal invokes Python. The installer uses the dependency versions in `uv.lock` and installs `phonelt` for your user account.
3. Verify the installation.

   ```sh
   phonelt --help
   ```

   If the terminal can't find `phonelt`, run `uv tool update-shell`, reopen the terminal, and try again.

The command uses the source in your checkout. Keep the folder in place, and run the installer again if you move it or update `uv.lock`.

## Send your first files

1. Connect your phone and computer to the same trusted local network.
2. Run `phonelt` on your computer. If the firewall prompts you, allow access on your trusted private network. Keep the terminal open.
3. Scan the QR code with your phone and tap **Choose files**. Open **Review all files** to preview supported photos and videos and edit destination names.
4. Tap **Send** for one file or **Send all** to send the selection in order. Wait for **Saved** before closing the page.
5. Find your files in **Downloads → Phone LAN Transfer**, or in the folder printed in the terminal if you specified another destination. Press **Ctrl+C** in the terminal when you're done.

The defaults are **5 GiB per file** and port **8000**. This example sets a custom folder, limit, and port.

```sh
phonelt -d "Received files" -m 10 -p 9000
```

Run `phonelt --help` for all options. If a save isn't confirmed, check the destination folder before retrying. Existing files are protected against overwrites.

## How it works

Your phone's browser sends each file directly to a FastAPI server running on your computer. A new token in the QR link authorizes transfers for that session. The server validates the destination name, writes the file in chunks, and confirms the save after writing and closing the file. See [architecture and file journey](docs/ARCHITECTURE.md).

Use the app on a trusted local network. Transfers use unencrypted HTTP. Keep the receiver off the public internet. See [security guidance](docs/SECURITY.md).

## Tested devices and development

ZIP transfers were verified byte for byte using SHA-256 on **iPhone/Safari → Windows** and **Android/Chrome → macOS**. See [test results](docs/TESTING.md) for device versions, the scope of the checks, and how the browser and server handle the per-file limit.

To run the development checks from the checkout, use these commands. The last one requires [Node.js](https://nodejs.org/).

```sh
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
node --test tests/browser-settings.test.cjs
```

## License

[MIT License](LICENSE). Copyright © 2026 Nel Banqué.
