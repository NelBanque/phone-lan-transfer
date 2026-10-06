"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from phone_lan_transfer.access import generate_access_token
from phone_lan_transfer.config import TransferSettings
from phone_lan_transfer.uploads import router as uploads_router

STATIC_DIRECTORY = Path(__file__).parent / "static"


def create_app(
    access_token: str | None = None,
    *,
    settings: TransferSettings | None = None,
) -> FastAPI:
    """Create an application with one token and transfer settings for its lifetime."""
    application = FastAPI(title="Phone LAN Transfer")
    application.state.access_token = access_token or generate_access_token()
    application.state.transfer_settings = settings or TransferSettings()
    application.include_router(uploads_router)
    application.mount(
        "/static",
        StaticFiles(directory=STATIC_DIRECTORY),
        name="static",
    )

    @application.get("/", response_class=FileResponse)
    def index() -> Path:
        """Serve the mobile transfer page."""
        return STATIC_DIRECTORY / "index.html"

    @application.get("/health")
    def health() -> dict[str, str]:
        """Report that the local server is running."""
        return {"status": "ok"}

    return application


app = create_app()
