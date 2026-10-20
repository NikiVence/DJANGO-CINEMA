"""Reproducible PNG version of the simple, code-drawn cinema emblem."""
import struct
import zlib
from pathlib import Path


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def make_logo():
    rows = bytearray()
    for y in range(64):
        rows.append(0)
        for x in range(64):
            color = (217, 243, 107, 255)
            if 16 <= x < 48 and 18 <= y < 46:
                color = (25, 32, 28, 255)
            if 27 <= x <= 41 and abs(y - 32) <= (41 - x) * 8 / 14:
                color = (217, 243, 107, 255)
            if (19 <= x <= 23 or 41 <= x <= 45) and y in (21, 22, 42, 43):
                color = (217, 243, 107, 255)
            rows.extend(color)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(rows)))
    png += chunk(b"IEND", b"")
    Path(__file__).with_name("logo.png").write_bytes(png)


if __name__ == "__main__":
    make_logo()
