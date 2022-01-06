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
    assert(isinstance(data, (bytes, bytearray, )))
    size = len(data)
    res = 0
    for i in reversed(range(size)):
        res = (res << 8) | (data[i] & 0xFF)
    return res

def int_to_bytes(data):
    # type: (int) -> bytes
    if data < 0:
        raise RuntimeError("Cannot convert negative number to bytes!")
    res = []
    while True:
        res.append(data & 0xFF)
        data = data >> 8
        if data == 0x00:
            break
    return res

def bytes_to_num(data):
    # type: (bytes) -> str
    assert(isinstance(data, (bytes, bytearray, )))
    return str(bytes_to_int(data))

def num_to_bytes(data):
    # type: (str)-> bytes
    return int_to_bytes(int(data))

def bytes_to_str(data):
    # type: (bytes) -> str
    assert(isinstance(data, (bytes, bytearray, )))
    i = len(data)-1
    while i >= 0 and data[i] == 0:
        i = i-1
    return data[:i+1].decode("ascii")

def str_to_bytes(data):
    # type: (str) -> bytes
    # NOTE: 'ascii' can be a little too much conservative...
    # NOTE: we are returning `bytes`, and not an `array[int]`, so this function
    #       can create some problems since they are not exactly the same, but
    #       hopefully their interface is similar enough to make everything work
    return bytes(data, encoding="ascii")

def bytes_to_class(data):
    # type: (bytes) -> str
    assert(isinstance(data, (bytes, bytearray, )))
    res = findInsideList(CLASSES, "value", bytes_to_int(data), {"name": "unknown"})
    return res["name"]

def class_to_bytes(data):
    # type: (str) -> bytes
    res = findInsideList(CLASSES, "name", data, {"value": 0})
    return int_to_bytes(res["value"])

def bytes_to_name(data):
    # type: (bytes) -> str
    assert(isinstance(data, (bytes, bytearray, )))
    res = findInsideList(NAMES, "value", bytes_to_int(data), {"name": "unknown"})
    return res["name"]

def name_to_bytes(data):
    # type: (str) -> bytes
    res = findInsideList(NAMES, "name", data, {"value": 0})
    return int_to_bytes(res["value"])

def bytes_to_item(data):
    # type: (bytes) -> str
    assert(isinstance(data, (bytes, bytearray, )))
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

    START_ADDRESS = 0x0001
    SLOT_SIZE = 0xAAA
    OPINION_LEADER_NAME_REF = 0x07a4

    # offset, size, number of items, field name, deserialize func, serialize func
    UNIT_LAYOUT = [
        (0x0069, 1, 100, "CLASS", bytes_to_class, class_to_bytes),
        (0x0131, 1, 100, "LVL", bytes_to_num, num_to_bytes),
        (0x0195, 1, 100, "EXP", bytes_to_num, num_to_bytes),
        (0x01f9, 2, 100, "HP", bytes_to_num, num_to_bytes),
        (0x02c1, 1, 100, "STR", bytes_to_num, num_to_bytes),
        (0x0325, 1, 100, "AGI", bytes_to_num, num_to_bytes),
        (0x0389, 1, 100, "INT", bytes_to_num, num_to_bytes),
        (0x03ed, 1, 100, "CHA", bytes_to_num, num_to_bytes),
        (0x0451, 1, 100, "ALI", bytes_to_num, num_to_bytes),
        (0x04b5, 1, 100, "LUK", bytes_to_num, num_to_bytes),
        (0x0519, 2, 100, "COST", bytes_to_num, num_to_bytes),
        (0x05e1, 1, 100, "ITEM", bytes_to_item, item_to_bytes),
        (0x0645, 2, 100, "NAME", bytes_to_name, name_to_bytes),
        (0x070d, 1, 100, "GROUP ROSTER", bytes_to_num, num_to_bytes),
        (0x0771, 1, 25, "x9?", bytes_to_num, num_to_bytes),
    ]

    GROUPS_LAYOUT = [
        (0x078a, 1, 125, "units formation", bytes_to_num),
        (0x0807, 1, 125, "units barraks", bytes_to_num),
        (0x0000, 0, 0, "is group leader", bytes_to_num),
    ]

    MISC_LAYOUT = [
        (0x0aa8, 2, 1, "CHECKSUM", bytes_to_num, num_to_bytes),
        (0x0910, 8, 1, "LEADER_NAME", bytes_to_str, str_to_bytes),
        (0x092b, 3, 1, "MONEY", bytes_to_num, num_to_bytes),
        (0x092f, 1, 1, "REPUTATION", bytes_to_num, num_to_bytes),
    ]

    def __init__(self, file, index):
        if index not in (0, 1, 2):
            raise RuntimeError(f"Slot '{index}' does not exists in snes!")
        self.file = file
        self.index = index
        self.data = []
        with open(file, "rb") as f:
            start = (OgreBattleSaveState.START_ADDRESS +
                     OgreBattleSaveState.SLOT_SIZE*index)
            size = OgreBattleSaveState.SLOT_SIZE
            f.seek(start)
            self.data = bytearray(f.read(size))
            if len(self.data) != OgreBattleSaveState.SLOT_SIZE:
                raise RuntimeError(
                    f"problem reading slot {index} of file {file}: " +
                    f"read {len(self.data)} bytes instead of {size}")

        # update the name of the opinion leader
        offset, size, _1, info_name, serialize, _2 = self.MISC_LAYOUT[1]
        assert(info_name == "LEADER_NAME")
        try:
            leader_name = serialize(self.data[offset:offset+size])
        except Exception as e:
            # in case the slot is empty the bytes that should contain the
            # leader's name are filled with non-ascii bytes!
            leader_name = "unknown"
        NAMES.append({
            "value": self.OPINION_LEADER_NAME_REF,
            "name": leader_name,
        })

    def _find_info_entry(self, target, info_name):
        INFOS = {
            "UNIT": OgreBattleSaveState.UNIT_LAYOUT,
            "MISC": OgreBattleSaveState.MISC_LAYOUT,
        }
        if target not in INFOS:
            raise RuntimeError(f"Layout for '{target}' not found!")
        entry = [x for x in INFOS[target] if x[3] == info_name]
        if len(entry) != 1:
            raise RuntimeError(f"Found {len(entry)} of '{info_name}' inside '{target}'!")
        return entry[0]

    def get_info(self, info_target, info_name, stride=0):
        offset, size, max_stride, _1, deserialize, _2 = self._find_info_entry(info_target, info_name)
        if stride >= max_stride:
            raise IndexError(f"stride {stride} for '{info_name}' is capped at {max_stride}!")
        address = offset + stride*size
        abslute_address = (OgreBattleSaveState.START_ADDRESS +
                           self.index*OgreBattleSaveState.SLOT_SIZE) + address
        bytes_ = self.data[address:address+size]
        res = ReadData(
            name=info_name,
            value=bytes_to_int(bytes_),
            formatted=deserialize(bytes_),
            raw=bytes_,
            address=abslute_address,
        )
        return res

    def set_info(self, new_value, info_target, info_name, stride=0):
        offset, size, max_stride, _1, _2, serialize = self._find_info_entry(info_target, info_name)
        if stride >= max_stride:
            raise IndexError(f"stride {stride} for '{info_name}' is capped at {max_stride}!")
        address = offset + stride*size
        bytes_ = serialize(new_value)
        if len(bytes_) > size:
            raise RuntimeError(f"Bad size for '{info_name}': '{new_value}'->'{bytes_}'")
        # during serialization we do not know the expected number of bytes to
        # fill, but here we do. Hopefully padding with zeroes is always ok!
        while len(bytes_) < size:
            bytes_.append(0)
        self.data[address:address+size] = bytes_

    def get_unit_info(self, unit_index, info_name):
        return self.get_info("UNIT", info_name, stride=unit_index)

    def set_unit_info(self, unit_index, info_name, new_value):
        self.set_info(new_value, "UNIT", info_name, stride=unit_index)

    def get_misc_info(self, info_name):
        return self.get_info("MISC", info_name)

    def set_misc_info(self, info_name, new_value):
        self.set_info(new_value, "MISC", info_name)

    def get_checksum(self):
        return self.get_info("MISC", "CHECKSUM")

    def update_checksum(self):
        new_checksum = self.compute_checksum().value
        self.set_info(new_checksum, "MISC", "CHECKSUM")

    def compute_checksum(self):
        CHECKSUM_START_ADDRESS = 0x0003  # included
        CHECKSUM_END_ADDRESS = 0x0aa8  # excluded
        value = 0
        for i in range(CHECKSUM_START_ADDRESS, CHECKSUM_END_ADDRESS):
            value = (value + self.data[i]) & 0xFFFF
        res = ReadData(
            name="COMPUTED_CHECKSUM",
            value=value,
            formatted=str(value),
            raw=num_to_bytes(value),
            address=0,
        )
        return res

    def save(self):
        self.update_checksum()
        with open(self.file, "rb") as f:
            content = bytearray(f.read())
        start = OgreBattleSaveState.START_ADDRESS + self.index*OgreBattleSaveState.SLOT_SIZE
        end = start + OgreBattleSaveState.SLOT_SIZE
        content[start:end] = self.data
        with open(self.file, "wb") as f:
            f.write(bytes(content))
