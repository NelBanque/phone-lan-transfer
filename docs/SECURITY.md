# Security

Phone LAN Transfer is designed for temporary transfers over a personal or
trusted Wi-Fi network. When it is used on a protected home network with trusted
devices, its temporary access controls make it suitable for its intended local
use. It must not be exposed to the internet.

## Main protections

- A new random access token will be created each time the server starts.
- LAN access will require an explicit startup option.
- Protected requests will require the temporary token.
- Uploads will use size limits, safe filenames, unique destinations, and
  streaming writes.
- Stopping the server will invalidate the token and end the transfer session.

## Important limitation

The first version will use HTTP, so network traffic will not be encrypted. Use
the application only on a personal or trusted Wi-Fi network protected with a
modern security mode, such as WPA2 or WPA3, and only with devices you trust.
Avoid public, guest, hotel, university, or other shared networks.

## Safe use

1. Start LAN mode only when you are ready to transfer files.
2. Keep the QR code and access link private.
3. Accept firewall access only for a trusted or private network.
4. Stop the server when the transfer is complete.
5. Never configure router port forwarding or a public tunnel for this service.

More detailed engineering trade-offs are recorded in `docs/DECISIONS.md` as
they are implemented and tested.
