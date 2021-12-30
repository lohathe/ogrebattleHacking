#!/usr/bin/env python3
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import argparse

import savestate


FONT = "verbena 12"
FONT_BOLD = FONT + " bold"

class CharacterInfoWidget(ttk.Frame):

    def __init__(self, parent):
        super(CharacterInfoWidget, self).__init__(parent)
        self.configure(
            padding="0 10 0 10",
        )
        self._save_on_update = True

        self.editors = {}

        name = StringVar()
        name_entry = ttk.Label(self, textvariable=name)
        name_entry.grid(column=0, columnspan=6, row=0, sticky=(N, E, W))
        name_entry["style"] = "Title.TLabel"
        self.editors["NAME"] = name
        self.editors["NAME_entry"] = name_entry

        unitclass = StringVar()
        unitclass_entry = ttk.Label(self, textvariable=unitclass)
        unitclass_entry.grid(column=1, columnspan=2, row=1, rowspan=3, sticky=(N, E, S, W))
        self.editors["CLASS"] = unitclass
        self.editors["CLASS_entry"] = unitclass_entry

        self._create_num_editor("Lvl:", "LVL", 3, 1)
        self._create_num_editor("Exp:", "EXP", 3, 2)
        self._create_num_editor("Cost:", "COST", 3, 3)
        self._create_num_editor("Hp:", "HP", 1, 4)
        self._create_num_editor("Str:", "STR", 1, 5)
        self._create_num_editor("Cha:", "CHA", 3, 5)
        self._create_num_editor("Agi:", "AGI", 1, 6)
        self._create_num_editor("Ali:", "ALI", 3, 6)
        self._create_num_editor("Int:", "INT", 1, 7)
        self._create_num_editor("Luk:", "LUK", 3, 7)

        self.event_add("<<modified>>", "None")

        # some layout on main window
        for child in self.winfo_children():
            child.grid_configure(padx=2, pady=2, ipadx=3, ipady=3)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(5, weight=1)

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
        entry.grid(column=column+1, row=row, sticky=W, ipady=10)
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
        self.obss = None
        # random container for images...otherwise images are garbage-collected
        # by python and never displayed in the GUI :(
        self.__images_ref = []

        root = Tk()
        root.title("Ogre Battle: MotBQ - Save State Editor")
        root.geometry("800x600")
        style = ttk.Style()
        style.configure("ToolButton.TButton", relief=FLAT, borderwidth=2, padding=2)
        style.configure("Success.TLabel", foreground="#297f00", font=FONT_BOLD)
        style.configure("Error.TLabel", foreground="#7f0000", font=FONT_BOLD)
        style.configure("Title.TLabel", foreground="#ffffff", background="#555555", font=FONT_BOLD, anchor=CENTER)

        toolbar = self.__build_toolbar(root)
        toolbar.grid(column=0, row=0, sticky=(E, W))

        slot_selector = self.__build_slot_selector(root)
        slot_selector.grid(column=0, row=1, sticky=(E, W))

        character_view = self.__build_character_view(root)
        character_view.grid(column=0, row=2, sticky=(E, W))

        status_bar = self.__build_status_bar(root)
        status_bar.grid(column=0, row=3, sticky=(N, E, W))

        # some layout on main window
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)
        for child in root.winfo_children():
            child.grid_configure(padx=5, pady=5)

        # display something sensible
        self.file_var.set(f"file: {file}")
        self.on_select_slot()

        root.mainloop()


    def __build_toolbar(self, parent):
        actions = [
            ("OPEN", "data/icon_open.gif", self.on_open),
            ("SAVE", "data/icon_save.gif", self.on_save),
        ]
        COL_COUNT = len(actions)

        frame = ttk.Frame(parent)
        frame.columnconfigure(COL_COUNT, weight=1)
        for i, (action_name, action_icon, action_callback) in enumerate(actions):
            icon = PhotoImage(file=action_icon)
            button = ttk.Button(frame,
                image=icon, text=action_name, compound=TOP,
                style="ToolButton.TButton",
                command=action_callback)
            button.grid(column=i, row=0, padx=2, pady=4)
            self.__images_ref.append(icon)
        separator = ttk.Separator(frame, orient=HORIZONTAL)
        separator.grid(column=0, columnspan=COL_COUNT+1, row=1, sticky=(E, W))

        return frame

    def __build_slot_selector(self, parent):
        frame = ttk.LabelFrame(parent, text="savestate", labelanchor="n")
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(4, weight=1)
        file_var = StringVar(value="file: None")
        file_name_label = ttk.Label(frame, textvariable=file_var, anchor=CENTER)
        frame.configure(labelwidget=file_name_label)
        slot_var = IntVar(value=0)
        slot_1 = ttk.Radiobutton(frame, variable=slot_var, command=self.on_select_slot, text="SLOT 1", value=0)
        slot_1.grid(column=1, row=1, padx=5, pady=5)
        slot_2 = ttk.Radiobutton(frame, variable=slot_var, command=self.on_select_slot, text="SLOT 2", value=1)
        slot_2.grid(column=2, row=1, padx=5, pady=5)
        slot_3 = ttk.Radiobutton(frame, variable=slot_var, command=self.on_select_slot, text="SLOT 3", value=2)
        slot_3.grid(column=3, row=1, padx=5, pady=5)

        self.file_var = file_var
        self.slot_var = slot_var
        return frame

    def __build_character_view(self, parent):
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)
        character_var = IntVar(value=0)
        selector = ttk.Spinbox(frame, from_=0, to=100, increment=1, textvariable=character_var, command=self.on_select_unit)
        selector.grid(column=0, columnspan=3, row=0, sticky=(E, W))
        character_info = CharacterInfoWidget(frame)
        character_info.grid(column=1, row=1, sticky=(E, W))
        character_info.bind("<<modified>>", self.on_unit_modified)

        self.character_var = character_var
        self.character_info = character_info
        return frame

    def __build_status_bar(self, parent):
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        separator = ttk.Separator(frame, orient=HORIZONTAL)
        separator.grid(column=0, row=0, sticky=(E, W))
        status_bar = StringVar()
        status_bar_entry = ttk.Label(frame, textvariable=status_bar)
        status_bar_entry.grid(column=0, row=1, sticky=(N, E, W))

        self.status_bar = status_bar
        self.status_bar_entry = status_bar_entry
        return frame

    def _update_backend(self):
        file = self.file_var.get()[6:]
        slot = self.slot_var.get()
        self.obss = savestate.OgreBattleSaveState(file, slot)
        self.character_info.reset()

    def on_select_slot(self, *args, **kwargs):
        try:
            self._update_backend()
            self.character_var.set(0)
            self.on_select_unit()
        except Exception as e:
            print("ERROR 'on_select_slot': {}".format(e))

    def on_select_unit(self, *args, **kwargs):
        try:
            new_index = self.character_var.get()
            new_unit_data = {}
            for key in ("NAME", "CLASS", "LVL", "EXP", "HP", "STR", "AGI", "INT", "CHA", "ALI", "LUK", "COST", "ITEM",):
                new_unit_data[key] = self.obss.get_unit_info(new_index, key)
            self.character_info.update(new_unit_data)
        except Exception as e:
            print("ERROR 'on_select_unit': {}".format(e))

    def on_unit_modified(self, event, *args, **kwargs):
        try:
            (name, value) = event.VirtualEventData
            unit_index = self.character_var.get()
            self.obss.set_unit_info(unit_index, name, value)
            message = f"{name} successfully updated"
            self.success_message(message)
        except Exception as e:
            message = f"Error while updating {name}"
            self.warning_message(message)
            print("ERROR 'on_unit_modified': {}".format(e))

    def on_save(self):
        try:
            self.obss.save()
            self.success_message("Save completed!")
        except Exception as e:
            self.warning_message("ERROR: problem persisting changes")
            print("ERROR 'on_save': {}".format(e))

    def on_open(self):
        new_file = filedialog.askopenfilename()
        if new_file:
            self.file_var.set(f"file: {new_file}")
            self.slot_var.set(0)
            self.on_select_slot()
            self.success_message("Changed file!")
        else:
            self.warning_message("New file not opened")

    def warning_message(self, message):
        self.status_bar_entry.config(style="Error.TLabel")
        self.status_bar.set(message)

    def success_message(self, message):
        self.status_bar_entry.config(style="Success.TLabel")
        self.status_bar.set(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="data/OgreBattle_MotBQ.srm")
    args = parser.parse_args()
    OgreBattleSaveStateGUI(args.file)


if __name__ == "__main__":
    main()
