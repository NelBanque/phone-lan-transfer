"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="Phone LAN Transfer")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the local server is running."""
    return {"status": "ok"}
