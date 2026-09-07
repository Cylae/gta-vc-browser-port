import os
import pytest
from utils.packer_brotli import (
    encode_uleb128,
    decode_uleb128,
    compress_brotli,
    decompress_brotli,
    pack_folder,
    unpack_file,
    PackedArchive
)

def test_uleb128_encoding_decoding():
    values = [0, 1, 127, 128, 255, 300, 16384, 1000000]
    for val in values:
        encoded = encode_uleb128(val)
        decoded, bytes_read = decode_uleb128(encoded)
        assert decoded == val
        assert bytes_read == len(encoded)

def test_brotli_compression_decompression():
    raw_data = b"Hello Vice City! " * 100
    compressed = compress_brotli(raw_data)
    decompressed = decompress_brotli(compressed)
    assert decompressed == raw_data

@pytest.mark.asyncio
async def test_pack_unpack_archive(tmp_path):
    # Setup test folder structure
    source_dir = tmp_path / "vcsky"
    source_dir.mkdir(parents=True)

    file1 = source_dir / "test.txt"
    file1.write_text("Hello from Vice City test file!")

    archive_bin = tmp_path / "test.bin"
    unpacked_dir = tmp_path / "unpacked"

    pack_folder(str(source_dir), str(archive_bin))
    assert archive_bin.exists()

    archive = PackedArchive(str(archive_bin))
    await archive.init()

    files = archive.list_files()
    assert "vcsky/test.txt" in files

    async with archive.open("vcsky/test.txt") as f:
        content = f.read()
        assert content == b"Hello from Vice City test file!"

    unpack_file(str(archive_bin), str(unpacked_dir))
    unpacked_file = unpacked_dir / "vcsky" / "test.txt"
    assert unpacked_file.exists()
    assert unpacked_file.read_text() == "Hello from Vice City test file!"
