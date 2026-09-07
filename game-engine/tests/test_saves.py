import os
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from additions.saves import router

def create_test_app():
    app = FastAPI()
    app.include_router(router)
    return app

def test_get_token():
    client = TestClient(create_test_app())
    response = client.get("/token/get?id=abc12")
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "abc12"
    assert data["premium"] is True

def test_upload_and_download_save(tmp_path, monkeypatch):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    monkeypatch.setattr("additions.saves.SAVES_DIR", str(saves_dir))

    client = TestClient(create_test_app())

    file_content = b"DUMMY SAVE DATA"
    upload_res = client.post(
        "/saves/upload",
        data={"token": "tok123", "fileName": "slot1.sav"},
        files={"file": ("slot1.sav", file_content, "application/octet-stream")}
    )
    assert upload_res.status_code == 200
    assert upload_res.json() == {"success": True}

    expected_file = saves_dir / "tok123_slot1.sav"
    assert expected_file.exists()
    assert expected_file.read_bytes() == file_content

    download_res = client.get("/saves/download/tok123/slot1.sav")
    assert download_res.status_code == 200
    assert download_res.content == file_content

def test_download_nonexistent_save(tmp_path, monkeypatch):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    monkeypatch.setattr("additions.saves.SAVES_DIR", str(saves_dir))

    client = TestClient(create_test_app())
    download_res = client.get("/saves/download/tok123/nonexistent.sav")
    assert download_res.status_code == 404

def test_path_traversal_protection(tmp_path, monkeypatch):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    monkeypatch.setattr("additions.saves.SAVES_DIR", str(saves_dir))

    client = TestClient(create_test_app())

    # Attempting path traversal in fileName and token
    upload_res = client.post(
        "/saves/upload",
        data={"token": "../../bad_token", "fileName": "../../../etc/passwd"},
        files={"file": ("passwd", b"root:x:0:0", "text/plain")}
    )
    assert upload_res.status_code == 200
    # Token "../../bad_token" is sanitized to "bad_token" and fileName to "passwd"
    expected_file = saves_dir / "bad_token_passwd"
    assert expected_file.exists()
    assert not (tmp_path / "passwd").exists()
    assert not (tmp_path / "bad_token_passwd").exists()

def test_invalid_and_empty_filename_upload(tmp_path, monkeypatch):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    monkeypatch.setattr("additions.saves.SAVES_DIR", str(saves_dir))

    client = TestClient(create_test_app())

    # Upload with filename that reduces to empty after sanitization
    upload_res = client.post(
        "/saves/upload",
        data={"token": "tok1", "fileName": "..."},
        files={"file": ("test.sav", b"data", "application/octet-stream")}
    )
    assert upload_res.status_code == 400

def test_download_save_invalid_filename(tmp_path, monkeypatch):
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    monkeypatch.setattr("additions.saves.SAVES_DIR", str(saves_dir))

    client = TestClient(create_test_app())
    download_res = client.get("/saves/download/tok1/...")
    assert download_res.status_code == 400
