#!/usr/bin/env python3
import unittest
import tempfile

import savestate


class TestSavestate(unittest.TestCase):

    def test_checksum(self):
        with tempfile.NamedTemporaryFile(mode="w+b") as f:
            f.write(b"\xff")
            f.write(b"\x05\x05\x05")
            for _ in range(0x0aa5):
                f.write(b"\x01")
            f.write(b"\x06\x06")
            f.write(b"\xa5\xa5\xa5")
            for _ in range(0x0aa5):
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

    def test_unit(self):
        values = [
            # absolute address, name, slot index, unit index, value, raw, formatted
            (0x006b, "CLASS", 0,  1, 8, [8], "Ninja"),
            (0x0134, "LVL",   0,  2, 2, [2], "2"),
            (0x0199, "EXP",   0,  3, 60, [60], "60"),
            (0x0202, "HP",    0,  4, 257, [0x01,0x01], "257"),
            (0x02c7, "STR",   0,  5, 1, [1], "1"),
            (0x0362, "AGI",   0, 60, 2, [2], "2"),
            (0x0e34, "INT",   1,  0, 3, [3], "3"),
            (0x0e99, "CHA",   1,  1, 4, [4], "4"),
            (0x0efe, "ALI",   1,  2, 5, [5], "5"),
            (0x0f63, "LUK",   1,  3, 6, [6], "6"),
            (0x0fcc, "COST",  1,  4, 1000, [0xe8,0x03], "1000"),
            (0x1091, "ITEM",  1,  5, 1, [0x01], "Sonic Blad"),
            (0x1168, "NAME",  1, 60, 36156, [0x3c, 0x8d], "ARNOLD"),
        ]
        data = []
        for _ in range(1 + 0x0aaa*2):
            data.append(0)
        for address, _1, _2, _3, _4, raw, _5 in values:
            data[address:address+len(raw)] = raw[:]

        #with tempfile.NamedTemporaryFile(mode="w+b") as f:
        with open("dump", "w+b") as f:
            f.write(bytes(data))
            f.flush()

            for value in values:
                expected_address, info_name, slot_index, unit_index, expected_value, _, expected_formatted = value
                obss = savestate.OgreBattleSaveState(f.name, slot_index)
                obtained_value = obss.get_unit_info(unit_index, info_name)
                self.assertEqual(obtained_value.address, expected_address)
                self.assertEqual(obtained_value.value, expected_value)
                self.assertEqual(obtained_value.formatted, expected_formatted)

if __name__ == "__main__":
    unittest.main()
