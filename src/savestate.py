import collections
import json

def extractJson(file_name):
    with open(file_name, "r") as f:
        return json.load(f)

ITEMS = extractJson("data/items.json")
CLASSES = extractJson("data/classes.json")
NAMES = extractJson("data/names.json")

def findInsideList(list_, key, value, default=None):
    for el in list_:
        if el[key] == value:
            return el
    return default

def bytes_to_int(data):
    # type: (bytes) -> int
    assert(isinstance(data, (bytes, )))
    size = len(data)
    res = 0
    for i in reversed(range(size)):
        res = (res << 8) | (data[i] & 0xFF)
    return res

def int_to_bytes(data):
    # type: (int) -> bytes
    res = []
    while True:
        res.append(data & 0xFF)
        data = data >> 8
        if data == 0x00:
            break
    return res

def bytes_to_num(data):
    # type: (bytes) -> str
    assert(isinstance(data, (bytes, )))
    return str(bytes_to_int(data))

def num_to_bytes(data):
    # type: (str)-> bytes
    return int_to_bytes(int(data))

def bytes_to_class(data):
    # type: (bytes) -> str
    assert(isinstance(data, (bytes, )))
    res = findInsideList(CLASSES, "value", bytes_to_int(data), {"name": "unknown"})
    return res["name"]

def class_to_bytes(data):
    # type: (str) -> bytes
    res = findInsideList(CLASSES, "name", data, {"value": 0})
    return int_to_bytes(res["value"])

def bytes_to_name(data):
    # type: (bytes) -> str
    assert(isinstance(data, (bytes, )))
    res = findInsideList(NAMES, "value", bytes_to_int(data), {"name": "unknown"})
    return res["name"]

def name_to_bytes(data):
    # type: (str) -> bytes
    res = findInsideList(NAMES, "name", data, {"value": 0})
    return int_to_bytes(res["value"])

def bytes_to_item(data):
    # type: (bytes) -> str
    assert(isinstance(data, (bytes, )))
    if bytes_to_int(data) == 0:
        return "none"
    res = findInsideList(ITEMS, "value", bytes_to_int(data), {"name": "unknown", "descr": ""})
    return res["name"]

def item_to_bytes(data):
    # type: (str) -> bytes
    if data == "none":
        return [0x00]
    res = findInsideList(ITEMS, "name", data, {"value": 0})
    return int_to_bytes(res["value"])

ReadData = collections.namedtuple("ReadData",
    ("name", "value", "formatted", "raw", "address"))


class OgreBattleSaveState(object):
    """
    Mapping the bytes inside the save state for "Ogre Battle: MofBQ".
    """

    SLOT_SIZE = 0xAAB

    # offset, size, number of items, field name, deserialize func, serialize func
    UNIT_LAYOUT = [
        (0x006a, 1, 100, "CLASS", bytes_to_class, class_to_bytes),
        (0x0132, 1, 100, "LVL", bytes_to_num, num_to_bytes),
        (0x0196, 1, 100, "EXP", bytes_to_num, num_to_bytes),
        (0x01fa, 2, 100, "HP", bytes_to_num, num_to_bytes),
        (0x02c2, 1, 100, "STR", bytes_to_num, num_to_bytes),
        (0x0326, 1, 100, "AGI", bytes_to_num, num_to_bytes),
        (0x038a, 1, 100, "INT", bytes_to_num, num_to_bytes),
        (0x03ee, 1, 100, "CHA", bytes_to_num, num_to_bytes),
        (0x0452, 1, 100, "ALI", bytes_to_num, num_to_bytes),
        (0x04b6, 1, 100, "LUK", bytes_to_num, num_to_bytes),
        (0x051a, 2, 100, "COST", bytes_to_num, num_to_bytes),
        (0x05e2, 1, 100, "ITEM", bytes_to_item, item_to_bytes),
        (0x0646, 2, 100, "NAME", bytes_to_name, name_to_bytes),
        (0x070e, 1, 100, "GROUP ROSTER", bytes_to_num, num_to_bytes),
        (0x0772, 1, 25, "x9?", bytes_to_num, num_to_bytes),
    ]

    GROUPS_LAYOUT = [
        (0x078b, 1, 125, "units formation", bytes_to_num),
        (0x0808, 1, 125, "units barraks", bytes_to_num)
    ]

    MISC_LAYOUT = [
        (0x0aa9, 2, 1, "CHECKSUM", bytes_to_num, num_to_bytes),
        (0x0000, 1, 1, "money", bytes_to_num, num_to_bytes),
        (0x0000, 1, 1, "reputation", bytes_to_num, num_to_bytes),
    ]

    def __init__(self, file, index):
        if index not in (0, 1, 2):
            raise RuntimeError(f"Slot '{index}' does not exists in snes!")
        self.file = file
        self.index = index
        self.data = []
        with open(file, "rb") as f:
            f.seek(OgreBattleSaveState.SLOT_SIZE*index)
            self.data = f.read(OgreBattleSaveState.SLOT_SIZE)

    def _find_unit_info_entry(self, info_name):
        entry = [x for x in OgreBattleSaveState.UNIT_LAYOUT if x[3] == info_name]
        if len(entry) != 1:
            raise RuntimeError(f"Cannot find entry for '{info_name}'")
        return entry[0]

    def get_unit_info(self, unit_index, info_name):
        offset, size, count_max, _1, serialize, _2 = self._find_unit_info_entry(info_name)
        if unit_index >= count_max:
            raise RuntimeError(f"Going out-of-bound using unit_index '{unit_index}' for '{name}': max items are {count_max}!")
        address = offset + unit_index*size
        bytes_ = self.data[address:address+size]
        res = ReadData(
            name=info_name,
            value=bytes_to_int(bytes_),
            formatted=serialize(bytes_),
            raw=bytes_,
            address=(self.index*OgreBattleSaveState.SLOT_SIZE) + address,
        )
        return res

    def set_unit_info(self, unit_index, info_name, new_value):
        offset, size, count_max, _1, _2, deserialize = self._find_unit_info_entry(info_name)
        if unit_index >= count_max:
            raise RuntimeError(f"Going out-of-bound using unit_index '{unit_index}' for '{name}': max items are {count_max}!")
        address = offset + unit_index*size
        bytes_ = deserialize(new_value)
        if len(bytes_) != size:
            raise RuntimeError(f"Bad size for '{info_name}': '{new_value}'->'{bytes_}'")
        self.data[address:address+size] = bytes_

    def get_checksum(self):
        address, size, _1, info_name, serialize, deserialize = OgreBattleSaveState.MISC_LAYOUT[0]
        assert(info_name == "CHECKSUM")
        bytes_ = self.data[address:address+size]
        res = ReadData(
            name=info_name,
            value=bytes_to_int(bytes_),
            formatted=serialize(bytes_),
            raw=bytes_,
            address=(self.index*OgreBattleSaveState.SLOT_SIZE) + address,
        )
        return res

    def compute_checksum(self):
        START_ADDRESS = 0x0004  # included
        END_ADDRESS = 0x0aa9  # excluded
        value = 0
        for i in range(START_ADDRESS, END_ADDRESS):
            value = (value + self.data[i]) & 0xFFFF
        res = ReadData(
            name="COMPUTED_CHECKSUM",
            value=value,
            formatted=str(value),
            raw=num_to_bytes(value),
            address=0,
        )
        return res

    def update_checksum(self):
        address, size, _1, info_name, serialize, deserialize = OgreBattleSaveState.MISC_LAYOUT[0]
        assert(info_name == "CHECKSUM")
        new_checksum = self.compute_checksum()
        bytes_ = serialize(new_checksum)
        self.data[address:address+size] = bytes_

    def save(self):
        with open(self.file, "rb") as f:
            content = f.read()
        start = self.index*OgreBattleSaveState.SLOT_SIZE
        end = start + OgreBattleSaveState.SLOT_SIZE
        content[start:end] = self.data
        with open(self.file, "wb") as f:
            f.write(bytes(content))
