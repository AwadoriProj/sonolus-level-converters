import gzip
import json
import os
import zlib
from typing import IO

from .errors import AwadoriFormatError

GZIP_MAGIC = b"\x1f\x8b"


def read_source(source: os.PathLike | IO[bytes] | bytes | str) -> bytes | str:
    if isinstance(source, (os.PathLike, str)):
        with open(source, "rb") as file:
            return file.read()
    if isinstance(source, (bytes, bytearray, memoryview)):
        return bytes(source)
    return source.read()


def decode_document(raw: bytes | str) -> dict:
    if isinstance(raw, bytes) and raw[:2] == GZIP_MAGIC:
        try:
            raw = gzip.decompress(raw)
        except (OSError, EOFError, zlib.error) as error:
            raise AwadoriFormatError("invalid gzip stream") from error
    try:
        document = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AwadoriFormatError("invalid JSON") from error
    if not isinstance(document, dict):
        raise AwadoriFormatError("root: expected an object")
    return document
