#!/usr/bin/env python3
import unittest
import tempfile

import savestate


class TestSavestate(unittest.TestCase):

    def test_checksum(self):
        with tempfile.NamedTemporaryFile(mode="w+b") as f:
            f.write(b"\xff")
            f.write(b"\x05\x05\x05")
            for i in range(0x0aa5):
                f.write(b"\x01")
            f.write(b"\x06\x06")
            f.write(b"\xa5\xa5\xa5")
            for i in range(0x0aa5):
                f.write(b"\xa1")
            f.write(b"\xa6\xa6")
            f.flush()
            slot0 = savestate.OgreBattleSaveState(f.name, 0)
            slot1 = savestate.OgreBattleSaveState(f.name, 1)

            checksum0 = slot0.compute_checksum()
            # 2725 == 0x0aa5 * 0x01
            self.assertEqual(checksum0.value, 2725)
            checksum1 = slot1.compute_checksum()
            # 45509 == 0x0aa5 * 0xa1
            self.assertEqual(checksum1.value, 45509)


if __name__ == "__main__":
    unittest.main()
