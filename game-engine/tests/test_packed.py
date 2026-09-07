import os
import brotli
import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from utils.packer_brotli import pack_folder
import additions.packed as packed

@pytest.mark.asyncio
async def test_resolve_packed_source_local():
    res = await packed.resolve_packed_source("local_archive.bin")
    assert res == "local_archive.bin"

@pytest.mark.asyncio
async def test_packed_file_serving(tmp_path, monkeypatch):
    source_dir = tmp_path / "vcsky"
    source_dir.mkdir()

    txt_file = source_dir / "sample.txt"
    txt_file.write_text("Sample file text for testing packed archive")

    # Add a pre-compressed .br file
    uncompressed_br_data = b"Pre-compressed brotli content"
    raw_br_content = brotli.compress(uncompressed_br_data)
    br_file = source_dir / "asset.data.br"
    br_file.write_bytes(raw_br_content)

    archive_path = tmp_path / "packed.bin"
    pack_folder(str(source_dir), str(archive_path))

    # Initialize archive
    archive = await packed.init_packed_archive(str(archive_path))
    assert archive is not None
    assert packed.is_initialized()

    app = FastAPI()

    @app.get("/file/{path:path}")
    async def serve_file(request: Request, path: str):
        res = await packed.get_packed_file(path, request)
        if res is None:
            return "Not Found", 404
        return res

    client = TestClient(app)

    # Test request for regular file with client accepting br
    res_br = client.get("/file/vcsky/sample.txt", headers={"Accept-Encoding": "br"})
    assert res_br.status_code == 200
    assert res_br.headers.get("Content-Encoding") == "br"
    assert res_br.headers.get("Cross-Origin-Opener-Policy") == "same-origin"

    # Test request for regular file with client NOT accepting br
    res_plain = client.get("/file/vcsky/sample.txt", headers={"Accept-Encoding": "identity"})
    assert res_plain.status_code == 200
    assert "Content-Encoding" not in res_plain.headers
    assert res_plain.text == "Sample file text for testing packed archive"

    # Test request for .br file with client accepting br
    # Note: TestClient/httpx automatically decompresses when Content-Encoding: br is present
    res_br_file = client.get("/file/vcsky/asset.data.br", headers={"Accept-Encoding": "br"})
    assert res_br_file.status_code == 200
    assert res_br_file.content == uncompressed_br_data

    # Test request for non-existent file
    res_404 = client.get("/file/vcsky/missing.txt")
    assert res_404.status_code == 200
    assert res_404.json() == ["Not Found", 404]

@pytest.mark.asyncio
async def test_packed_streaming(tmp_path):
    source_dir = tmp_path / "vcsky"
    source_dir.mkdir()

    file1 = source_dir / "stream.txt"
    file1.write_text("Stream text " * 50)

    archive_path = tmp_path / "stream_packed.bin"
    pack_folder(str(source_dir), str(archive_path))

    await packed.init_packed_archive(str(archive_path))

    app = FastAPI()

    @app.get("/stream/{path:path}")
    async def stream_file(request: Request, path: str):
        res = await packed.get_packed_file_streaming(path, request)
        if res is None:
            return "Not Found", 404
        return res

    client = TestClient(app)
    res = client.get("/stream/vcsky/stream.txt", headers={"Accept-Encoding": "identity"})
    assert res.status_code == 200
    assert res.text == "Stream text " * 50
