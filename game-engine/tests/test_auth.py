import base64
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from starlette.testclient import TestClient

from additions.auth import BasicAuthMiddleware

def create_test_app():
    app = FastAPI()
    app.add_middleware(BasicAuthMiddleware, username="admin", password="secretpassword")

    @app.get("/protected")
    async def protected_route():
        return PlainTextResponse("OK")

    @app.options("/protected")
    async def protected_options():
        return PlainTextResponse("CORS OK")

    return app

def test_auth_missing_header():
    client = TestClient(create_test_app())
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Basic realm='Restricted'"

def test_auth_invalid_credentials():
    client = TestClient(create_test_app())
    creds = base64.b64encode(b"admin:wrongpassword").decode()
    response = client.get("/protected", headers={"Authorization": f"Basic {creds}"})
    assert response.status_code == 401

def test_auth_valid_credentials():
    client = TestClient(create_test_app())
    creds = base64.b64encode(b"admin:secretpassword").decode()
    response = client.get("/protected", headers={"Authorization": f"Basic {creds}"})
    assert response.status_code == 200
    assert response.text == "OK"

def test_auth_options_bypass():
    client = TestClient(create_test_app())
    response = client.options("/protected")
    assert response.status_code == 200

def test_auth_malformed_base64():
    client = TestClient(create_test_app())
    response = client.get("/protected", headers={"Authorization": "Basic !!!invalid_base64!!!"})
    assert response.status_code == 401

def test_auth_no_colon_in_credentials():
    client = TestClient(create_test_app())
    creds = base64.b64encode(b"nocolonhere").decode()
    response = client.get("/protected", headers={"Authorization": f"Basic {creds}"})
    assert response.status_code == 401

def test_auth_wrong_scheme():
    client = TestClient(create_test_app())
    response = client.get("/protected", headers={"Authorization": "Bearer token123"})
    assert response.status_code == 401

def test_auth_wrong_username_correct_password():
    client = TestClient(create_test_app())
    creds = base64.b64encode(b"wrongadmin:secretpassword").decode()
    response = client.get("/protected", headers={"Authorization": f"Basic {creds}"})
    assert response.status_code == 401
