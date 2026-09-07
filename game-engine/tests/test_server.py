import os
import pytest
from fastapi.testclient import TestClient
from server import (
    app,
    _md5_hash,
    _is_url,
    _is_md5_hash,
    _get_unpacked_dir,
    _check_unpacked_exists
)

def test_md5_hash_and_helpers():
    h = _md5_hash("hello")
    assert len(h) == 32
    assert _is_md5_hash(h) is True
    assert _is_md5_hash("invalid_hash") is False

    assert _is_url("http://example.com/test.bin") is True
    assert _is_url("https://example.com/test.bin") is True
    assert _is_url("local/path/test.bin") is False

def test_get_unpacked_dir():
    # Valid md5 hash
    md5 = "098f6bcd4621d373cade4e832627b4f6"
    assert _get_unpacked_dir(md5) == os.path.join("unpacked", md5)

    # String name
    path = _get_unpacked_dir("my_folder")
    assert path.startswith("unpacked" + os.sep)

def test_check_unpacked_exists(tmp_path):
    unpacked_dir = tmp_path / "unpacked_sample"
    assert _check_unpacked_exists(str(unpacked_dir)) is False

    vcsky = unpacked_dir / "vcsky"
    vcsky.mkdir(parents=True)
    assert _check_unpacked_exists(str(unpacked_dir)) is False

    f = vcsky / "game.wasm"
    f.write_text("dummy")
    assert _check_unpacked_exists(str(unpacked_dir)) is True

def test_read_index_404_when_dist_missing(monkeypatch, tmp_path):
    # Ensure current directory does not have dist/index.html
    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 404
    assert res.text == "index.html not found"

def test_read_index_when_dist_exists(monkeypatch, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    index_html = dist / "index.html"
    index_html.write_text("<html>new URLSearchParams(window.location.search).get(\"custom_saves\") === \"1\"</html>")

    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert res.headers["Cross-Origin-Embedder-Policy"] == "require-corp"
    assert '"0" === "1"' in res.text
