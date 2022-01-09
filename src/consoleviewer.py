#!/usr/bin/env python3
import argparse
from savestate import OgreBattleSaveState


def as_bytes(data):
    return " ".join(["{:#04X}".format(d) for d in data])

class ConsoleViewer(object):

    def __init__(self, file, index):
        self.obss = OgreBattleSaveState(file, index)

    def show_unit(self, unit_index, infos):
        print(f"=( {unit_index:>3d} )==" + "="*50)
        for info in infos:
            data = self.obss.get_unit_info(unit_index, info)
            print("{:>20s}: {:<20s} [@{:#06x} raw: {:<10s}]".format(
                data.name,
                data.formatted,
                data.address,
                as_bytes(data.raw),
            ))
        print("-"*60)

    def show_misc(self, infos):
        for info in infos:
            data = self.obss.get_misc_info(info)
            print("{:>20s}: {:<10s} [@{:#06x} raw: {}]".format(
                data.name,
                data.formatted,
                data.address,
                as_bytes(data.raw),
            ))

    def update_unit(self, unit_index, info, new_value):
        old = self.obss.get_unit_info(unit_index, info)
        self.obss.set_unit_info(unit_index, info, new_value)
        new = self.obss.get_unit_info(unit_index, info)
        print("UNIT {} - {}: {} -> {} [@{:#06x} {} .. {}]".format(
            unit_index,
            info,
            old.formatted,
            new.formatted,
            old.address,
            as_bytes(old.raw),
            as_bytes(new.raw)))
        self.save()

    def update_misc(self, info, new_value):
        old = self.obss.get_misc_info(info)
        self.obss.set_misc_info(info, new_value)
        new = self.obss.get_misc_info(info)
        print("{}: {} -> {} [@{:#06x} {} .. {}]".format(
            info,
            old.formatted,
            new.formatted,
            old.address,
            as_bytes(old.raw),
            as_bytes(new.raw)))
        self.save()

    def show_checksum(self):
        current = self.obss.get_checksum()
        computed = self.obss.compute_checksum()
        print("{:>20s}: {} [raw: {}]".format(current.name, current.value, as_bytes(current.raw)))
        print("{:>20s}: {} [raw: {}]".format(computed.name, computed.value, as_bytes(computed.raw)))

    def save(self):
        self.obss.save()

    def custom(self):
        print("Write your temporary code here!")


def parse_args():
    """
    Reference CLI:

    ./consoleviewer.py <file> [--slot=N] show unit [--info={ALL,STR,...}, --info] <UNIT_INDEX> [<UNIT_INDEX>...]
    ./consoleviewer.py <file> [--slot=N] show misc {checksum, reputation, money}
    ./consoleviewer.py <file> [--slot=N] update unit <UNIT_INDEX> <INFO> <VALUE>
    ./consoleviewer.py <file> [--slot=N] update misc <INFO> <VALUE>
    ./consoleviewer.py <file> [--slot=N] fix-checksum [--dry-run]
    """
    parser = argparse.ArgumentParser(description="interact with SNES save state files for 'Ogre Battle: the March of the Black Queen'")
    parser.add_argument("-s", "--slot", default=0, type=int)
    parser.add_argument("FILE")

    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_show = subparsers.add_parser("show", description="visualize data in 'human readable' format")
    subparsers_show = parser_show.add_subparsers(dest="subcommand", required=True)

    parser_show_unit = subparsers_show.add_parser("unit")
    parser_show_unit.add_argument("-i", "--info", type=str, default=[], action="append", help="leave empty to display all unit infos")
    parser_show_unit.add_argument("UNIT_INDEX", type=int, nargs="+")

    parser_show_misc = subparsers_show.add_parser("misc")
    parser_show_misc.add_argument("-i", "--info", type=str, default=[], action="append", help="leave empty to display all misc infos")

    parser_update = subparsers.add_parser("update", description="modify data of save state")
    subparsers_update = parser_update.add_subparsers(dest="subcommand", required=True)

    parser_update_unit = subparsers_update.add_parser("unit")
    parser_update_unit.add_argument("UNIT_INDEX", type=int)
    parser_update_unit.add_argument("INFO", type=str)
    parser_update_unit.add_argument("VALUE", type=str)

    parser_update_misc = subparsers_update.add_parser("misc")
    parser_update_misc.add_argument("INFO", type=str)
    parser_update_misc.add_argument("VALUE", type=str)

    parser_fix_checksum = subparsers.add_parser("fix-checksum", description="show/solve problems related to the checksum")
    parser_fix_checksum.add_argument("-d", "--dry-run", action="store_true", help="show expected checksum but do not modify file")

    parser_custom = subparsers.add_parser("custom", description="entry-point to easily script some custom logic: no arguments and no code!")

    return parser.parse_args()

def main():
    args = parse_args()

    viewer = ConsoleViewer(args.FILE, args.slot)
    command = args.command

    if command == "show":
        subcommand = args.subcommand
        if subcommand == "unit":
            ALL_UNIT_INFOS = ("NAME", "CLASS", "LVL", "EXP", "HP", "STR", "AGI", "INT", "CHA", "ALI", "LUK", "COST", "ITEM",)
            for unit_index in args.UNIT_INDEX:
                viewer.show_unit(unit_index, args.info or ALL_UNIT_INFOS)
        elif subcommand == "misc":
            ALL_MISC_INFOS = ("MONEY", "REPUTATION", "CHECKSUM")
            viewer.show_misc(args.info or ALL_MISC_INFOS)

    elif command == "update":
        subcommand = args.subcommand
        if subcommand == "unit":
            viewer.update_unit(args.UNIT_INDEX, args.INFO, args.VALUE)
        elif subcommand == "misc":
            viewer.update_misc(args.INFO, args.VALUE)

    elif command == "fix-checksum":
        if args.dry_run:
            viewer.show_checksum()
        else:
            viewer.save()

    elif command == "custom":
        viewer.custom()


if __name__ == "__main__":
    main()
