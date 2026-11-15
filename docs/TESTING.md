# Manual transfer verification

## Android to macOS: 2026-11-15

- Sender: Samsung Galaxy A05s (SM-A057G/DSN), Android 15, One UI 7.0, Chrome 149.0.7827.200 (device and software reported by the tester).
- Receiver: MacBook Air, macOS 26.0.1 (build 25A362).
- Network: the Mac and Galaxy were connected through a third phone's mobile hotspot, as reported by the tester. This verifies this local-network arrangement; it does not establish behavior on every Wi-Fi network.
- File: `transfer-integrity.zip`, 1,048,855 bytes.
- Preparation: the known test ZIP was served from the Mac over the trusted local network and downloaded to Android without extraction.
- Transfer: the tester selected the downloaded ZIP in Phone LAN Transfer and reported a completed upload. The received file was found in `Downloads/Phone LAN Transfer` on the Mac.
- Verification: SHA-256 and file size were compared on the Mac against the original test ZIP. Both files had the same size and digest:

```text
71bc9bdb690f9641a75b34861940f83d2ad115f06eafc0b0a309b2ed2ca74d01
```

Result: byte integrity passed for this ZIP transfer. The tester also reported successful photo and video transfers from Android to this Mac, without recorded file-level integrity checks or complete format details. This does not establish compatibility for every file type, Android browser, or large-file size. The temporary download server was stopped after verification.

## iPhone to Windows: 2026-11-12

- Sender: iPhone 16 Pro, Safari, iOS 26.7.1 (device and software reported by the tester).
- Receiver: Windows, OS build 26200.
- File: `transfer-integrity.zip`, 1,048,855 bytes.
- Preparation: a generated ZIP was copied to the iPhone before selection in the browser. It was not extracted for the test.
- Transfer: the tester reported completion through Phone LAN Transfer; the received ZIP was found on the Windows desktop.
- Verification: SHA-256 was calculated on Windows for the original and received ZIP. Both files had the same size and digest:

```text
71bc9bdb690f9641a75b34861940f83d2ad115f06eafc0b0a309b2ed2ca74d01
```

Result: byte integrity passed for this ZIP transfer. This does not establish compatibility for every file type, device, browser, or large-file size. Photo-picker conversion and original photo-library metadata were not tested.

## Reload access recovery: 2026-11-12

The tester reported that reload recovery, rejection after server restart, and access through the new QR worked on the iPhone. No automated Safari trace was captured.

Reloading while the server is stopped can leave Safari waiting for the page itself. Application request timeouts cannot display an error before the page and its script run. Recovery guidance is to start the server, open its current QR, and reload if the page still does not respond.
