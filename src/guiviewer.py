#!/usr/bin/env python3
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import simpledialog
import argparse

import savestate


FONT = "verbena 12"
FONT_BOLD = FONT + " bold"


class SelectorDialog(simpledialog.Dialog):
    """
    Simple dialog to let the user select an item from a list.

    TODO:
     - show the "original value" (the value before selection)
     - show the "current value" (the selection, which can be hidden if the list
        is very long)
     - show additional info stored inside savestate.ReadData if any
    """
    def __init__(self, parent=None, title="", data=None):
        self.data = data
        self.result = None
        super(SelectorDialog, self).__init__(parent=parent, title=title)

    def body(self, body):
        body.columnconfigure(0, weight=1)
        listbox = Listbox(body, height=10)
        listbox.grid(column=0, row=0, sticky=(N,E,S,W))
        scrollbar = ttk.Scrollbar(body, orient=VERTICAL, command=listbox.yview)
        scrollbar.grid(column=1, row=0, sticky=(N,S))
        listbox["yscrollcommand"] = scrollbar.set
        for i, el in enumerate(self.data):
            listbox.insert("end", el["name"])
        self.listbox = listbox
        return listbox

    def validate(self):
        if len(self.listbox.curselection()) == 0:
            return 0
        self.result = self.data[self.listbox.curselection()[0]]
        return 1


class EditorsFrame(ttk.Frame):
    """
    Base frame class that offers an automatic way to:
     - create standard input widgets (text-editors and list-selectors)
     - to store the widgets such that they can be later accessed
     - notify to the outer world when the input-widgets have been modified
       by the user by raising a `<<modified>>` virtual event which transport
       both the "name" of the modified input as well as its new value
    Every subclass should implement the `_create_body` method that should
    populate the frame with the necessary widget.

    The widgets are stored inside a dictionary `self.editors` with the current
    protocol:
     * <NAME> -> represents a `StringVar` (or a similar variable)
     * <NAME>_entry -> represents the ttk.Entry associated to the <NAME> var
     * <NAME>_label -> represents the label describing <NAME>_entry
    Every <NAME> variable is then connected to the `on_value_changed` method
    that in turn will raise the `<<modified>>` virtual event.

    No support for undo-redo.
    """
    def __init__(self, parent):
        super(EditorsFrame, self).__init__(parent)
        self._save_on_update = True
        self.editors = {}
        self.__images_ref = {}

        self._create_body()

        self.event_add("<<modified>>", "None")
        self.reset()

    def _create_body(self):
        raise NotImplementedError()

    def _create_selector_editor(self, label_text="", name="", column=0, row=0, columnspan=1, rowspan=1, data=None):
        if name.strip() == "":
            raise RuntimeError("Must specifiy a name for editor!")
        if name in self.editors:
            raise RuntimeError(f"Name '{name}' is already used!")
        if not data:
            raise RuntimeError(f"Cannot create selector for {name} with empty data!")
        else:
            for el in data:
                if "img" not in el:
                    continue
                img_name = "{}_{}".format(name, el["name"])
                img_data = el["img"]
                self.__images_ref[img_name] = PhotoImage(data=img_data).zoom(3)
        if label_text:
            label = ttk.Label(self, text=label_text)
            label.grid(column=column, row=row, sticky=E)
            column = column+1
        variable = StringVar()
        def callback(*args, **kwargs):
            self.on_value_changed(name, *args, **kwargs)
        variable.trace_add("write", callback)
        def command(name=name):
            result = SelectorDialog(None, f"select {name}", data=data).result
            if result:
                self.editors[name].set(result["name"])
        entry = ttk.Button(self, textvariable=variable, compound=TOP, command=command)
        sticky = (W, )
        if columnspan > 1:
            sticky = (W, E)
        if rowspan > 1:
            sticky = (W, N, E, S)
        entry.grid(column=column, columnspan=columnspan, row=row, rowspan=rowspan, sticky=sticky, ipady=10)
        if label_text:
            self.editors[f"{name}_label"] = label
        self.editors[f"{name}"] = variable
        self.editors[f"{name}_entry"] = entry

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
        entry = ttk.Entry(self, width=7, textvariable=variable)
        entry.grid(column=column+1, row=row, sticky=W, ipady=10)
        self.editors[f"{name}_label"] = label
        self.editors[f"{name}"] = variable
        self.editors[f"{name}_entry"] = entry

    def on_value_changed(self, name, *args, **kwargs):
        new_value = self.editors[name].get()
        img_name = f"{name}_{new_value}"
        if img_name in self.__images_ref:
            img = self.__images_ref[img_name]
            entry = self.editors[f"{name}_entry"]
            entry.configure(image=img)
        if not self._save_on_update:
            return
        Event.VirtualEventData = (name, new_value)
        self.event_generate("<<modified>>")

    def update(self, data):
        # `data` should be a list of `savestate.ReadData`
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


class CharacterInfoWidget(EditorsFrame):

    def _create_body(self):
        self.configure(padding="0 10 0 10")

        name = StringVar()
        name_entry = ttk.Label(self, textvariable=name)
        name_entry.grid(column=0, columnspan=6, row=0, sticky=(N, E, W))
        name_entry["style"] = "Title.TLabel"
        self.editors["NAME"] = name
        self.editors["NAME_entry"] = name_entry

        self._create_selector_editor("", "CLASS", 1, 1, columnspan=2, rowspan=3, data=savestate.CLASSES)
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
        self._create_selector_editor("Item:", "ITEM", 1, 8, columnspan=3, data=savestate.ITEMS)

        # some layout on main window
        for child in self.winfo_children():
            child.grid_configure(padx=2, pady=2, ipadx=3, ipady=3)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(5, weight=1)


class MiscInfoWidget(EditorsFrame):
    def _create_body(self):
        self.configure(padding="0 10 0 10")

        self._create_num_editor("Reputation:", "REPUTATION", 0, 1)
        self._create_num_editor("Funds:", "MONEY", 0, 2)

        for child in self.winfo_children():
            child.grid_configure(padx=2, pady=2, ipadx=3, ipady=3)
        self.columnconfigure(1, weight=1)


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

        main_view = ttk.Notebook(root)
        main_view.grid(column=0, row=2, sticky=(E, W))
        character_view = self.__build_character_view(main_view)
        formation_view = self.__build_formation_view(main_view)
        misc_view = self.__build_misc_view(main_view)
        main_view.add(character_view, text="Character")
        main_view.add(formation_view, text="Army formation")
        main_view.add(misc_view, text="Misc")

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
        selector = ttk.Spinbox(frame, from_=0, to=100, increment=1, textvariable=character_var, command=self.on_select_character)
        selector.grid(column=0, columnspan=3, row=0, sticky=(E, W))
        button_prev = ttk.Button(frame, text="<", style="ToolButton.TButton", command=lambda:self.on_advance_character(-1))
        button_prev.grid(column=0, row=1, sticky=(N, S))
        character_info = CharacterInfoWidget(frame)
        character_info.grid(column=1, row=1, sticky=(E, W))
        character_info.bind("<<modified>>", self.on_character_modified)
        button_next = ttk.Button(frame, text=">", style="ToolButton.TButton", command=lambda:self.on_advance_character(+1))
        button_next.grid(column=2, row=1, sticky=(N, S))

        self.character_var = character_var
        self.character_info = character_info
        return frame

    def __build_formation_view(self, parent):
        frame = ttk.Frame(parent)
        label = ttk.Label(frame, text="Not implemented yet :(")
        label.grid(column=0, row=0)

        return frame

    def __build_misc_view(self, parent):
        frame = ttk.Frame(parent)
        frame.columnconfigure(1, weight=1)
        misc_info = MiscInfoWidget(frame)
        misc_info.grid(column=1, row=1, sticky=(E, W))
        misc_info.bind("<<modified>>", self.on_misc_modified)

        self.misc_info = misc_info
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

    def __update_backend(self):
        file = self.file_var.get()[6:]
        slot = self.slot_var.get()
        self.obss = savestate.OgreBattleSaveState(file, slot)
        self.character_info.reset()

    def on_select_slot(self, *args, **kwargs):
        try:
            self.__update_backend()
            self.character_var.set(0)
            self.on_select_character()
            self.__show_misc_info()
        except Exception as e:
            print("ERROR 'on_select_slot': {}".format(e))

    def on_select_character(self):
        try:
            new_index = self.character_var.get()
        except Exception as e:
            self.warning_message("Could not select specified character")
            print("ERROR 'on_select_character': {}".format(e))
        else:
            self.__show_character_info(new_index)

    def on_advance_character(self, delta):
        try:
            current = self.character_var.get()
            new_index = current + delta
            self.character_var.set(new_index)
        except Exception as e:
            self.warning_message("Could not advance to next/prev character")
            print("ERROR 'on_advance_character': {}".format(e))
        else:
            self.__show_character_info(new_index)

    def __show_character_info(self, character_index):
        INFOS = ["NAME", "CLASS", "LVL", "EXP", "HP", "STR", "AGI", "INT", "CHA", "ALI", "LUK", "COST", "ITEM",]
        try:
            character_info = {}
            for key in INFOS:
                character_info[key] = self.obss.get_unit_info(character_index, key)
            self.character_info.update(character_info)
            character_name = character_info["NAME"].formatted
            self.success_message(f"Showing info for '{character_name}' (index {character_index})")
        except Exception as e:
            self.warning_message(f"Problems retrieving info for character at index {character_index}")
            print("ERROR '__show_character_info': {}".format(e))

    def __show_misc_info(self):
        INFOS = ["REPUTATION", "MONEY"]
        try:
            misc_info = {}
            for key in INFOS:
                misc_info[key] = self.obss.get_misc_info(key)
            self.misc_info.update(misc_info)
        except Exception as e:
            self.warning_message("Problems retrieving misc info")
            print("ERROR '__show_misc_info': {}".format(e))

    def on_character_modified(self, event, *args, **kwargs):
        try:
            (name, value) = event.VirtualEventData
            unit_index = self.character_var.get()
            self.obss.set_unit_info(unit_index, name, value)
            message = f"{name} successfully updated"
            self.success_message(message)
        except Exception as e:
            message = f"Error while updating {name}"
            self.warning_message(message)
            print("ERROR 'on_character_modified': {}".format(e))

    def on_misc_modified(self, event, *args, **kwargs):
        try:
            (name, value) = event.VirtualEventData
            self.obss.set_misc_info(name, value)
            message = f"{name} successfully updated"
            self.success_message(message)
        except Exception as e:
            message = f"Error while updating {name}"
            self.warning_message(message)
            print("ERROR 'on_misc_modified': {}".format(e))

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
