#!/usr/bin/env python3
from tkinter import *
from tkinter import ttk
import argparse

import savestate


class UnitWidget(ttk.Frame):

    def __init__(self, parent):
        super(UnitWidget, self).__init__(parent)
        self.configure(padding="10 10 10 10")
        self._save_on_update = True

        self.editors = {}

        name = StringVar()
        name_entry = ttk.Label(self, textvariable=name)
        name_entry.grid(column=0, columnspan=4, row=0, sticky=(N, E, W))
        name_entry["style"] = "Title.TLabel"
        self.editors["NAME"] = name
        self.editors["NAME_entry"] = name_entry

        unitclass = StringVar()
        unitclass_entry = ttk.Label(self, textvariable=unitclass)
        unitclass_entry.grid(column=0, columnspan=2, row=1, rowspan=3, sticky=(N, E, S, W))
        self.editors["CLASS"] = unitclass
        self.editors["CLASS_entry"] = unitclass_entry

        self._create_num_editor("Lvl:", "LVL", 2, 1)
        self._create_num_editor("Exp:", "EXP", 2, 2)
        self._create_num_editor("Cost:", "COST", 2, 3)
        self._create_num_editor("Hp:", "HP", 0, 4)
        self._create_num_editor("Str:", "STR", 0, 5)
        self._create_num_editor("Cha:", "CHA", 2, 5)
        self._create_num_editor("Agi:", "AGI", 0, 6)
        self._create_num_editor("Ali:", "ALI", 2, 6)
        self._create_num_editor("Int:", "INT", 0, 7)
        self._create_num_editor("Luk:", "LUK", 2, 7)

        self.event_add("<<modified>>", "None")

        self.reset()

    def _create_num_editor(self, label_text="", name="", column=0, row=0):
        if name.strip() == "":
            raise RuntimeError("Must specifiy a name for editor!")
        if name in self.editors:
            raise RuntimeError(f"Name '{name}' is already used!")

        label = ttk.Label(self, text=label_text)
        label.grid(column=column, row=row, sticky=E)
        variable = StringVar()
        def callback(*args, **kwargs):
            self.on_value_changed(name, *args, **kwargs)
        variable.trace_add("write", callback)
        entry = ttk.Entry(self, width=5, textvariable=variable)
        entry.grid(column=column+1, row=row, sticky=W)
        self.editors[f"{name}_label"] = label
        self.editors[f"{name}"] = variable
        self.editors[f"{name}_entry"] = entry

    def on_value_changed(self, name, *args, **kwargs):
        if not self._save_on_update:
            return
        Event.VirtualEventData = (name, self.editors[name].get())
        self.event_generate("<<modified>>")

    def update(self, data):
        self._save_on_update = False
        for key, value in data.items():
            if key not in self.editors:
                print(f"could not find editor for {key}")
                continue
            self.editors[key].set(value.formatted)
        self._save_on_update = True

    def reset(self):
        self._save_on_update = False
        for editor_name in self.editors:
            if isinstance(self.editors[editor_name], StringVar):
                self.editors[editor_name].set("")
        self._save_on_update = True


class OgreBattleSaveStateGUI():

    def __init__(self, file):
        self.file = file
        self.slot = 0
        self.obss = None

        root = Tk()
        root.title("Ogre Battle: MotBQ - Save State Editor")

        # file name reference
        file_label = ttk.Label(root, text=file)
        file_label.grid(column=0, columnspan=3, row=0, sticky=(E, W))

        # slot selector
        self.slot_var = StringVar(value=0)
        slot_1 = ttk.Radiobutton(root, variable=self.slot_var, command=self.on_select_slot, text="SLOT 1", value=0)
        slot_1.grid(column=0, row=1, sticky=W)
        slot_2 = ttk.Radiobutton(root, variable=self.slot_var, command=self.on_select_slot, text="SLOT 2", value=1)
        slot_2.grid(column=1, row=1, sticky=W)
        slot_3 = ttk.Radiobutton(root, variable=self.slot_var, command=self.on_select_slot, text="SLOT 3", value=2)
        slot_3.grid(column=2, row=1, sticky=W)

        # unit selector
        self.unit_selctor_var = StringVar(value=0)
        unit_selector = ttk.Spinbox(root, from_=0, to=100, increment=1, textvariable=self.unit_selctor_var, command=self.on_select_unit)
        unit_selector.grid(column=0, columnspan=3, row=2, sticky=(E, W))
        self.unit_viewer = UnitWidget(root)
        self.unit_viewer.grid(column=0, columnspan=3, row=3, sticky=(N, E, S, W))
        self.unit_viewer.bind("<<modified>>", self.on_unit_modified)

        # save button
        save = ttk.Button(root, text="SAVE", command=self.on_save)
        save.grid(column=2, row=4, sticky=(E, W))

        # status bar
        status_bar = StringVar()
        status_bar_entry = ttk.Label(root, textvariable=status_bar)
        status_bar_entry.grid(column=0, columnspan=3, row=5, sticky=(E, W))
        self.status_bar = status_bar

        # display something sensible
        self.on_select_slot()
        self.on_select_unit()

        root.mainloop()

    def _update_backend(self):
        self.obss = savestate.OgreBattleSaveState(self.file, self.slot)
        self.unit_viewer.reset()

    def on_select_slot(self, *args, **kwargs):
        try:
            new_index = int(self.slot_var.get())
            self.slot = new_index
            self._update_backend()
        except Exception as e:
            print("ERROR 'on_select_slot': {}".format(e))

    def on_select_unit(self, *args, **kwargs):
        try:
            new_index = int(self.unit_selctor_var.get())
            new_unit_data = {}
            for key in ("NAME", "CLASS", "LVL", "EXP", "HP", "STR", "AGI", "INT", "CHA", "ALI", "LUK", "COST", "ITEM",):
                new_unit_data[key] = self.obss.get_unit_info(new_index, key)
            self.unit_viewer.update(new_unit_data)
        except Exception as e:
            print("ERROR 'on_select_unit': {}".format(e))

    def on_unit_modified(self, event, *args, **kwargs):
        try:
            (name, value) = event.VirtualEventData
            unit_index = int(self.unit_selctor_var.get())
            self.obss.set_unit_info(unit_index, name, value)
            message = f"{name} successfully updated"
        except Exception as e:
            message = f"Error while updating {name}"
            print("ERROR 'on_unit_modified': {}".format(e))
        self.update_status_bar(message)

    def on_save(self):
        self.update_status_bar("ERROR: 'save' function not implemented")

    def update_status_bar(self, message):
        self.status_bar.set(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="data/OgreBattle_MotBQ.srm")
    args = parser.parse_args()
    OgreBattleSaveStateGUI(args.file)


if __name__ == "__main__":
    main()
