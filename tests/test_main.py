from fastapi.testclient import TestClient

from phone_lan_transfer.main import create_app

client = TestClient(create_app(access_token="test-token"))


def test_index_returns_browser_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert '<meta name="viewport"' in response.text
    assert 'src="/static/app.js"' in response.text
    assert 'href="/static/styles.css"' in response.text
    assert 'href="/favicon.ico"' in response.text
    assert 'href="/static/favicon.svg"' in response.text


def test_stylesheet_is_served() -> None:
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert "@media (max-width: 420px)" in response.text


def test_browser_script_is_served() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "window.location.hash" in response.text
    assert "window.history.replaceState" in response.text
    assert "localStorage" not in response.text
    assert "sessionStorage" in response.text


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_favicon_assets_are_served_without_authentication() -> None:
    icon = client.get("/favicon.ico")
    assert icon.status_code == 200
    assert icon.headers["content-type"] == "image/x-icon"
    assert icon.content[:4] == b"\x00\x00\x01\x00"
    svg = client.get("/static/favicon.svg")
    assert svg.status_code == 200
    assert svg.headers["content-type"].startswith("image/svg+xml")
    assert b'viewBox="0 0 60 60"' in svg.content
