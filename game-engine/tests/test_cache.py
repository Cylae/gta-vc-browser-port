import os
import brotli
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from starlette.testclient import TestClient

from additions.cache import (
    get_local_file,
    _client_accepts_brotli,
    _get_file_headers,
    _get_media_type,
    proxy_and_cache
)

def test_get_file_headers():
    headers = _get_file_headers("test.wasm")
    assert headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert headers["Cross-Origin-Embedder-Policy"] == "require-corp"
    assert "Content-Encoding" not in headers

    br_headers = _get_file_headers("test.wasm.br")
    assert br_headers["Content-Encoding"] == "br"
    assert br_headers["Content-Type"] == "application/octet-stream"

def test_get_media_type():
    assert _get_media_type("game.wasm") == "application/wasm"
    assert _get_media_type("game.wasm.br") == "application/wasm"
    assert _get_media_type("archive.br") == "application/octet-stream"
    assert _get_media_type("image.png") is None

def test_get_local_file_nonexistent():
    res = get_local_file("nonexistent_file_path_xyz.txt")
    assert res is None

def test_get_local_file_normal(tmp_path):
    test_file = tmp_path / "hello.txt"
    test_file.write_text("Hello Vice City")

    req = Request(scope={"type": "http", "headers": []})
    res = get_local_file(str(test_file), req)
    assert isinstance(res, FileResponse)
    assert res.headers["Cross-Origin-Opener-Policy"] == "same-origin"

def test_get_local_file_brotli_decompression(tmp_path):
    raw_data = b"Decompressed content vice city"
    br_data = brotli.compress(raw_data)

    br_file = tmp_path / "data.bin.br"
    br_file.write_bytes(br_data)

    # Client does not accept brotli -> should return StreamingResponse decompressing on the fly
    req_no_br = Request(scope={"type": "http", "headers": [(b"accept-encoding", b"gzip, deflate")]})
    res = get_local_file(str(br_file), req_no_br)
    assert isinstance(res, StreamingResponse)

    client = TestClient(FastAPI())
    # Test client response content from generator
    app = FastAPI()
    @app.get("/test")
    def test_route(request: Request):
        return get_local_file(str(br_file), request)

    c = TestClient(app)
    r = c.get("/test", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert r.content == raw_data

    # Client accepts brotli -> should return raw FileResponse with Content-Encoding: br
    # Note: TestClient/httpx automatically decompresses Content-Encoding: br headers
    r_br = c.get("/test", headers={"Accept-Encoding": "gzip, br"})
    assert r_br.status_code == 200
    assert r_br.content == raw_data
