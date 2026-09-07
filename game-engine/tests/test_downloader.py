import os
import pytest
from utils.downloader_brotli import format_size, format_time, UnpackStats, download_and_unpack_async
from utils.packer_brotli import pack_folder

def test_format_size():
    assert format_size(500) == "500.00 B"
    assert format_size(1500) == "1.46 KB"
    assert format_size(1048576) == "1.00 MB"

def test_format_time():
    assert format_time(30) == "30.0s"
    assert format_time(125) == "2m 5.0s"
    assert format_time(3665) == "1h 1m"

def test_unpack_stats():
    stats = UnpackStats()
    stats.start_folder("test_folder", 2)
    assert stats.current_folder == "test_folder"
    assert stats.files_in_current_folder == 2

    stats.file_unpacked("file1.txt", 100, 200)
    assert stats.total_files == 1
    assert stats.total_bytes == 200
    assert stats.total_compressed_bytes == 100

    stats.file_copied("file2.txt", 150)
    assert stats.total_files == 2
    assert stats.total_bytes == 350
    assert stats.copied_files == 1

@pytest.mark.asyncio
async def test_download_and_unpack_local_mock(tmp_path, monkeypatch):
    # Prepare a packed archive
    src_dir = tmp_path / "vcsky"
    src_dir.mkdir(parents=True)
    (src_dir / "a.txt").write_text("Alpha file content")
    (src_dir / "b.txt").write_text("Beta file content")

    archive_bin = tmp_path / "mock.bin"
    pack_folder(str(src_dir), str(archive_bin))

    out_dir = tmp_path / "unpacked_output"

    # Mock httpx.AsyncClient to read from local file
    class MockStreamResponse:
        def __init__(self, file_path):
            self.file_path = file_path
            self.status_code = 200
            self.headers = {"content-length": str(os.path.getsize(file_path))}

        def raise_for_status(self):
            pass

        async def aiter_bytes(self, chunk_size=65536):
            with open(self.file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    yield chunk

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def stream(self, method, url):
            return MockStreamResponse(str(archive_bin))

    monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

    await download_and_unpack_async("http://example.com/mock.bin", str(out_dir))

    assert (out_dir / "vcsky" / "a.txt").exists()
    assert (out_dir / "vcsky" / "a.txt").read_text() == "Alpha file content"
    assert (out_dir / "vcsky" / "b.txt").exists()
    assert (out_dir / "vcsky" / "b.txt").read_text() == "Beta file content"
