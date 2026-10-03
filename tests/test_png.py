"""Trailing-background crop preserves all non-background pixels."""
import struct
import unittest
import zlib
from src.services.png import SIGNATURE,_chunk,crop_background


class PNGTests(unittest.TestCase):
    def test_crop_removes_only_uniform_bottom_rows(self):
        header=struct.pack('>IIBBBBB',3,6,8,2,0,0,0)
        background=b'\xdc\xe6\xdd'*3
        foreground=b'\x00'*9
        pixels=b''.join(b'\x00'+r for r in [background,foreground,foreground,background,background,background])
        raw=SIGNATURE+_chunk(b'IHDR',header)+_chunk(b'IDAT',zlib.compress(pixels))+_chunk(b'IEND',b'')
        result=crop_background(raw,padding=1)
        self.assertEqual(struct.unpack('>IIBBBBB',result[16:29])[:2],(3,4))
        self.assertEqual(crop_background(result,padding=1),result)
        bad=bytearray(raw);bad[40]^=1
        with self.assertRaises(ValueError):crop_background(bytes(bad))

    def test_foreground_in_last_row_is_never_cropped(self):
        header=struct.pack('>IIBBBBB',1,2,8,2,0,0,0)
        raw=SIGNATURE+_chunk(b'IHDR',header)+_chunk(b'IDAT',zlib.compress(b'\0\xff\xff\xff\0\0\0\0'))+_chunk(b'IEND',b'')
        self.assertEqual(crop_background(raw),raw)
