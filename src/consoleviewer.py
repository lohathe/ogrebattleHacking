import argparse
from savestate import OgreBattleSaveState


def as_bytes(data):
    return " ".join(["{:#04X}".format(d) for d in data])

class ConsoleViewer(object):

    def __init__(self, file, index):
        self.obss = OgreBattleSaveState(file, index)

    def show_unit(self, unit_index):
        print("="*60)
        for key in ("NAME", "CLASS", "LVL", "EXP", "HP", "STR", "AGI", "INT", "CHA", "ALI", "LUK", "COST", "ITEM",):
            data = self.obss.get_unit_info(unit_index, key)
            print("{:>20s}: {:<20s} [raw: {:<10s} @{:#06x}]".format(
                data.name,
                data.formatted,
                as_bytes(data.raw),
                data.address))
        print("-"*60)

    def show_checksum(self):
        current = self.obss.get_checksum()
        computed = self.obss.compute_checksum()
        print("{:>20s}: {} [raw: {}]".format(current.name, current.value, as_bytes(current.raw)))
        print("{:>20s}: {} [raw: {}]".format(computed.name, computed.value, as_bytes(computed.raw)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE")
    parser.add_argument("-s", "--slot", default=0, type=int)
    parser.add_argument("-u", "--unit-index", type=int, action="append")
    parser.add_argument("-c", "--checksum", action="store_true")
    args = parser.parse_args()

    viewer = ConsoleViewer(args.FILE, args.slot)
    for index in args.unit_index:
        viewer.show_unit(index)
    if args.checksum:
        viewer.show_checksum()


if __name__ == "__main__":
    main()
