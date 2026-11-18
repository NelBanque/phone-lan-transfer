# Engineering Decisions

These records summarize the choices behind Phone LAN Transfer in roughly the order the features were developed. See [Architecture](ARCHITECTURE.md) for the current file flow.

## 1. Run the receiver on the computer

- **Decision** Serve a browser interface from the receiving computer and transfer general files directly over the local network.
- **Why** A phone can send photos, videos, or documents without installing an app or using a cloud relay.
- **Alternative** Build native senders or add a browser inbox on the receiving computer.
- **Trade-off** Both devices need a network path to each other. Compatibility is verified one device and browser combination at a time.

## 2. Use a small Python web stack

- **Decision** Use FastAPI and Uvicorn with separate HTML, CSS, and JavaScript assets. Manage the project with `uv`, `pyproject.toml`, and a `src/` layout.
- **Why** FastAPI provides typed routes and in-process HTTP testing. The lockfile makes dependency versions reproducible.
- **Alternative** Use Flask or the standard library with manually managed requirements.
- **Trade-off** Contributors need `uv` and familiarity with the ASGI stack. The package must include the browser assets.

## 3. Use HTTP on trusted networks

- **Decision** Serve transfers over local HTTP.
- **Why** Phones can open the link without installing or trusting a local certificate.
- **Alternative** Generate a local HTTPS certificate.
- **Trade-off** Traffic is unencrypted. Use the receiver on a trusted local network. See [Security](SECURITY.md).

## 4. Put a temporary token in the QR link

- **Decision** Generate a fresh token per server run, put it in the URL fragment, and require it as a Bearer token for protected requests.
- **Why** The fragment stays out of the initial HTTP request. The browser can read it and authorize subsequent requests.
- **Alternative** Put the token in the query string or use a persistent password.
- **Trade-off** Anyone with the current QR link can use the token until the server stops.

## 5. Display the connection QR and a text fallback

- **Decision** Render the QR in the terminal with Segno and print the access URL alongside it. Allow `--lan-address` to override the address in the link.
- **Why** QR scanning is quick, and the override helps when automatic detection picks a VPN or the wrong interface.
- **Alternative** Require users to type the address or bind the listener to the advertised address.
- **Trade-off** Terminal QR rendering depends on Unicode support. The override changes the advertised address while the LAN listener still binds to all IPv4 interfaces.

## 6. Use the native picker and keep selection in memory

- **Decision** Use the browser's multiple-file picker, with optional inline previews and editable destination names. Keep network guidance in an expandable section.
- **Why** Users can choose, review, and remove files before explicitly sending them.
- **Alternative** Build a custom picker or upload immediately after selection.
- **Trade-off** Reloading clears the selection. Preview support depends on the browser and file format.

## 7. Validate filenames and create files exclusively

- **Decision** Check portable filenames server-side, including a 255-byte UTF-8 limit. Open each destination exclusively and remove partial files on handled failures.
- **Why** The server controls the destination and protects existing files. The browser mirrors the naming checks for immediate feedback.
- **Alternative** Trust the browser, silently rename collisions, or publish temporary files using hard links.
- **Trade-off** An incomplete file can be visible during a transfer and may remain after an abrupt stop. Exclusive creation works on destinations without hard-link support.

## 8. Stream one raw file per authenticated request

- **Decision** Send one raw file body per upload, with the destination name in the query string. Bridge network reads to a disk-writing worker with AnyIO and enforce a configurable per-file limit.
- **Why** The receiver writes and counts bytes as they arrive. The browser sends the bytes it was given without recompression or conversion.
- **Alternative** Buffer the body in memory or use multipart spooling.
- **Trade-off** The client URL-encodes the filename, and the server coordinates the async request stream with synchronous disk writes. A phone's picker can supply a converted file.

## 9. Report progress and save confirmation separately

- **Decision** Use `XMLHttpRequest` for upload progress and `fetch` for settings. Track each file as pending, sending, saved, or failed. Show **Saved** after validating the HTTP 201 response.
- **Why** A user can see how much was sent and which files the receiver confirmed.
- **Alternative** Show a single overall result or mark a file saved at 100% upload progress.
- **Trade-off** A lost response leaves the save uncertain. The user checks the receiving folder before retrying.

## 10. Recover access after a page reload

- **Decision** Remove the token from the visible URL and keep it in `sessionStorage`. A new QR token takes priority. An HTTP 401 clears stored access.
- **Why** Reloading the current tab can recover access while the same server session is active.
- **Alternative** Keep the token only in memory or persist it in `localStorage`.
- **Trade-off** Same-origin scripts can read session storage. Browser session restoration can retain it, and blocked storage requires reopening the QR after a reload.

## 11. Make LAN reception the default CLI workflow

- **Decision** Start LAN reception with `phonelt`, with `--local-only` for loopback. Keep immutable per-run settings and default to Downloads/Phone LAN Transfer and 5 GiB per file.
- **Why** The usual transfer starts with one command. Platformdirs locates Downloads, and the CLI converts GiB values to whole bytes.
- **Alternative** Require a LAN flag and use a fixed path and byte limit.
- **Trade-off** LAN mode listens on all IPv4 interfaces. The CLI prints the destination and network guidance at startup.

## 12. Send batches sequentially

- **Decision** Send pending files one at a time through the same path as an individual upload. Weight total progress by bytes and retain each save result.
- **Why** A batch is convenient and users can still identify the outcome of each file.
- **Alternative** Upload in parallel or report only one result for the batch.
- **Trade-off** Files wait their turn. An uncertain connection pauses the queue and retries are manual.

## 13. Test the destination before displaying the QR

- **Decision** Create the destination if needed, then write, flush, and remove a temporary probe at CLI startup.
- **Why** An unusable folder produces immediate feedback before someone tries to upload from a phone.
- **Alternative** Discover folder problems on the first upload.
- **Trade-off** Startup performs a small disk operation. The upload still handles subsequent storage failures.

## 14. Use separate inactivity and confirmation deadlines

- **Decision** Refresh a two-minute upload timer when the browser reports new bytes. Start a separate two-minute confirmation timer when the body finishes sending.
- **Why** A large transfer can continue while it makes progress, and a stalled request gets a bounded wait.
- **Alternative** Set one deadline for the entire request.
- **Trade-off** Browser suspension can delay timers. An expired confirmation leaves the same uncertainty as a lost response.

## 15. Install the CLI from the locked checkout

- **Decision** Export runtime constraints from `uv.lock` and install the checkout as an editable user tool.
- **Why** The installed `phonelt` uses the runtime dependency versions selected for development.
- **Alternative** Install from a Git URL and resolve dependencies at installation time.
- **Trade-off** Keep the checkout in place and rerun the installer after moving it or updating the lockfile.

## 16. Keep the transfer interface focused

- **Decision** Keep one English interface, hide the batch bar at 100% sent, and show a separate confirmation status. **Clear saved** removes confirmed entries from the browser list while keeping the received files.
- **Why** The list stays useful during long batches and makes the remaining work visible.
- **Alternative** Keep completed progress visible or add controls for deleting files on the receiver.
- **Trade-off** The page is focused on sending. Saved files are managed on the receiving computer, and translations require a complete localized interface.
