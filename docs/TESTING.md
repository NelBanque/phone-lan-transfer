# Manual transfer verification

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
