"""FastAPI application entry point."""

from fastapi import FastAPI

from phone_lan_transfer.access import generate_access_token


def create_app(access_token: str | None = None) -> FastAPI:
    """Create an application with one access token for its lifetime."""
    application = FastAPI(title="Phone LAN Transfer")
    application.state.access_token = access_token or generate_access_token()

    @application.get("/health")
    def health() -> dict[str, str]:
        """Report that the local server is running."""
        return {"status": "ok"}

    return application


app = create_app()
