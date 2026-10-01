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
    assert "sessionStorage" not in response.text


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
