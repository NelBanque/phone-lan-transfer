# Manual transfer verification

## Per-file limit check (1 KiB)

On iPhone, with the receiver started using `phonelt --max-file-bytes 1024`,
selecting a video over the limit showed the file-size warning and disabled
Send. The warning displayed the shared error styling.

In a separate in-process check against the FastAPI app, an authenticated
upload supplied two 768-byte chunks without a Content-Length header. The app
returned HTTP 413 and the temporary receiving folder was empty afterward.
An upload of exactly 1,024 bytes then returned HTTP 201, and the saved bytes
matched the request body.

## Closing checks: 2026-11-17

The final application changes include the original interface with a gray
Clear saved button beside the selection summary, hiding the batch bar at 100%
while keeping save confirmation explicit, and working SVG/ICO favicons.
Chrome checks with a deliberately delayed HTTP response verified that the bar
disappears before confirmation, Saved appears only after the response, and
Clear saved leaves the received disk file untouched. The current regression
suite has 124 Python tests and 29 Node browser simulations.

The README now uses the final 50-second demo. It shows the transfer workflow.
The ZIP checks below provide the separate byte-integrity results. See
[demo assets](media/README.md) for the final recording details.

## Local receiver and recovery checks: 2026-11-16

The installed Windows user tool was reinstalled using runtime constraints
exported from `uv.lock`. All 21 installed distributions, including the project,
matched the tested development environment's versions.

A temporary loopback-only server verified CLI help outside the checkout,
rejection of a file used as the destination, startup folder preparation without
leftover probe files, page/assets/settings, unauthenticated rejection, exact
received bytes, repeated name collisions without overwrites, size-limit cleanup,
and cleanup after a real TCP disconnect partway through a request. Health and a
new upload succeeded afterward. The diagnostic server was stopped afterward.
These are local receiver checks, not another phone compatibility or integrity
claim.

Browser regression simulations use a controlled clock to cover inactivity
abort, long-running uploads with continuing progress, duplicate progress,
bounded waiting after 100%, batch pause with later files pending, late-response
rejection, and timer cleanup. Python tests cover destination creation, preserving
existing files, and startup failure on file paths, permission errors, or disk
space errors. Simulated browser tests do not establish mobile timer behavior
while a browser or device is suspended.

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
