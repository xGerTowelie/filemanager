import os
import urwid
import subprocess
import argparse
import shutil

FOLDER_SYMBOL = "📁"
DEFAULT_LEFT_PANE_PATH = os.path.expanduser("~")
DEFAULT_RIGHT_PANE_PATH = os.path.expanduser("~")

overwrite_confirmed = False
copy_move_confirmed = False

parser = argparse.ArgumentParser(description="A simple file manager.")
parser.add_argument('path', nargs='?', default=DEFAULT_LEFT_PANE_PATH, help="Initial path for the left pane.")
args = parser.parse_args()

LAST_KEY = None
LEFT_PANE_PATH = args.path
RIGHT_PANE_PATH = DEFAULT_RIGHT_PANE_PATH


selected_items = set()

def jump_to_opposite(pane):
    listbox = left_listbox if pane == 0 else right_listbox
    current_item = listbox.body[listbox.focus_position].base_widget.text
    is_current_folder = current_item.startswith(FOLDER_SYMBOL) or current_item.startswith(f"* {FOLDER_SYMBOL}")
    
    for i, item in enumerate(listbox.body):
        item_text = item.base_widget.text
        is_folder = item_text.startswith(FOLDER_SYMBOL) or item_text.startswith(f"* {FOLDER_SYMBOL}")
        
        if is_current_folder != is_folder:
            listbox.focus_position = i
            break

def shorten_path(path):
    parts = path.split(os.sep)

    if len(parts) > 3:
        return f"...{os.sep}{parts[-2]}{os.sep}{parts[-1]}{os.sep}"
    else:
        return path

def copy_items(source_path, dest_path):
    for item in selected_items:
        dest_item = os.path.join(dest_path, os.path.basename(item))
        if os.path.exists(dest_item):
            raise FileExistsError(dest_item)
        if os.path.isdir(item):
            shutil.copytree(item, dest_item)
        else:
            shutil.copy2(item, dest_item)

def move_items(source_path, dest_path):
    for item in selected_items:
        dest_item = os.path.join(dest_path, os.path.basename(item))
        if os.path.exists(dest_item):
            raise FileExistsError(dest_item)
        shutil.move(item, dest_item)

def create_copy_move_dialog(operation):
    text = urwid.Text(f"Are you sure you want to {operation} {len(selected_items)} item(s)?")
    ok_button = urwid.Button("OK", on_press=lambda _: on_copy_move_confirm(True, operation))
    
    dialog_body = [
        text,
        urwid.Divider(),
        urwid.AttrMap(ok_button, None, focus_map='reversed')
    ]
    dialog = NavigableDialog(dialog_body)
    
    return urwid.Overlay(
        urwid.LineBox(dialog, title=f"Confirm {operation.capitalize()}"),
        columns,
        align='center',
        valign='middle',
        width=('relative', 30),
        height=('relative', 20),
        min_width=20,
        min_height=5
    )

def on_copy_move_confirm(confirmed, operation):
    global copy_move_confirmed, selected_items
    copy_move_confirmed = confirmed
    main_loop.widget = columns

    if confirmed:
        source_path = LEFT_PANE_PATH if current_focus == 0 else RIGHT_PANE_PATH
        dest_path = RIGHT_PANE_PATH if current_focus == 0 else LEFT_PANE_PATH
        
        try:
            if operation == "copy":
                copy_items(source_path, dest_path)
            elif operation == "move":
                move_items(source_path, dest_path)
        except FileExistsError:
            main_loop.widget = create_overwrite_dialog(operation)
            return

        update_directory(0, LEFT_PANE_PATH)
        update_directory(1, RIGHT_PANE_PATH)
        clear_selected_items()

def clear_selected_items():
    global selected_items
    selected_items.clear()
    update_directory(0, LEFT_PANE_PATH)
    update_directory(1, RIGHT_PANE_PATH)

def confirm_overwrite(item):
    main_loop.widget = create_overwrite_dialog(item)
    main_loop.run()
    return overwrite_confirmed

def on_overwrite_confirm(confirmed, operation):
    global main_loop
    if confirmed:
        source_path = LEFT_PANE_PATH if current_focus == 0 else RIGHT_PANE_PATH
        dest_path = RIGHT_PANE_PATH if current_focus == 0 else LEFT_PANE_PATH
        
        try:
            if operation == "copy":
                copy_items_force(source_path, dest_path)
            elif operation == "move":
                move_items_force(source_path, dest_path)
            update_directory(0, LEFT_PANE_PATH)
            update_directory(1, RIGHT_PANE_PATH)
            clear_selected_items()
        except Exception as e:
            error_dialog = create_error_dialog(str(e))
            main_loop.widget = error_dialog
            return

    main_loop.widget = columns
    
def create_error_dialog(error_message):
    text = urwid.Text(f"An error occurred: {error_message}")
    ok_button = urwid.Button("OK", on_press=lambda _: setattr(main_loop, 'widget', columns))
    
    dialog_body = [
        text,
        urwid.Divider(),
        urwid.AttrMap(ok_button, None, focus_map='reversed')
    ]
    dialog = NavigableDialog(dialog_body)
    
    return urwid.Overlay(
        urwid.LineBox(dialog, title="Error"),
        columns,
        align='center',
        valign='middle',
        width=('relative', 50),
        height=('relative', 30),
        min_width=20,
        min_height=5
    )

def copy_items_force(source_path, dest_path):
    for item in selected_items:
        dest_item = os.path.join(dest_path, os.path.basename(item))
        if os.path.isdir(item):
            shutil.copytree(item, dest_item, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest_item)

def move_items_force(source_path, dest_path):
    for item in selected_items:
        dest_item = os.path.join(dest_path, os.path.basename(item))
        if os.path.exists(dest_item):
            if os.path.isdir(dest_item):
                shutil.rmtree(dest_item)
            else:
                os.remove(dest_item)
        shutil.move(item, dest_item)

def confirm_overwrite(item):
    main_loop.widget = create_overwrite_dialog(item)
    main_loop.run()
    return overwrite_confirmed

def create_text_widget(text, path, focus=False):
    if path in selected_items:
        return urwid.AttrMap(urwid.Text('* ' + text), 'selected', focus_map='selected_focus')
    return urwid.AttrMap(urwid.Text(text), None, focus_map='reversed')

def create_overwrite_dialog(operation):
    text = urwid.Text(f"Some files already exist. Overwrite?")
    ok_button = urwid.Button("OK", on_press=lambda _: on_overwrite_confirm(True, operation))
    
    dialog_body = [
        text,
        urwid.Divider(),
        urwid.AttrMap(ok_button, None, focus_map='reversed')
    ]
    dialog = NavigableDialog(dialog_body)
    
    return urwid.Overlay(
        urwid.LineBox(dialog, title="Confirm Overwrite"),
        columns,
        align='center',
        valign='middle',
        width=('relative', 30),
        height=('relative', 20),
        min_width=20,
        min_height=5
    )

def get_directory_contents(path):
    try:
        items = os.listdir(path)
    except PermissionError:
        items = ["Permission denied"]
    except FileNotFoundError:
        items = ["Path not found"]
    
    directories = []
    files = []

    for item in items:
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            directories.append(item)
        else:
            files.append(item)
    
    directories.sort()
    files.sort()
    sorted_items = directories + files

    contents = []
    for item in sorted_items:
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            item_display = f"{FOLDER_SYMBOL} {item}"
        else:
            item_display = f"  {item}"
        contents.append(create_text_widget(item_display, item_path))
    
    return contents

def create_delete_dialog():
    selected_files_count = len(selected_items)
    confirmation_text = urwid.Text(f"Are you sure you want to delete {selected_files_count} file(s) and/or folder(s)?")
    confirm_button = urwid.Button("Yes", on_press=on_confirm_delete)
    cancel_button = urwid.Button("No", on_press=on_cancel_delete)
    
    dialog_body = [
        confirmation_text,
        urwid.Divider(),
        urwid.AttrMap(confirm_button, None, focus_map='reversed'),
        urwid.AttrMap(cancel_button, None, focus_map='reversed'),
    ]
    
    dialog = NavigableDialog(dialog_body)
    
    return urwid.Overlay(
        urwid.LineBox(dialog, title="Confirm Delete"),
        columns,
        align='center',
        valign='middle',
        width=('relative', 30),
        height=('relative', 20),
        min_width=20,
        min_height=5
    )

def create_action_dialog():
    action_items = ["Open in Terminal", "Open in Nvim", "Select/Deselect All"]
    action_widgets = []
    for action in action_items:
        button = urwid.Button(action, on_press=lambda b, a=action: on_action_select(a))
        action_widgets.append(urwid.AttrMap(button, None, focus_map='reversed'))

    dialog = NavigableDialog(action_widgets)
    return urwid.Overlay(
        urwid.LineBox(dialog, title="Select Action"),
        columns,
        align='center',
        valign='middle',
        width=('relative', 30),
        height=('relative', 30),
        min_width=20,
        min_height=8
    )

import shutil

def on_confirm_delete(button=None):
    global selected_items
    if not selected_items:
        main_loop.widget = columns
        return

    for item_path in selected_items:
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        except Exception as e:
            error_dialog = create_error_dialog(f"Error deleting {item_path}: {str(e)}")
            main_loop.widget = error_dialog
            return

    selected_items.clear()
    update_directory(0, LEFT_PANE_PATH)
    update_directory(1, RIGHT_PANE_PATH)
    main_loop.widget = columns

def on_cancel_delete(button=None):
    main_loop.widget = columns

def on_action_select(action):
    global selected_items
    current_path = LEFT_PANE_PATH if current_focus == 0 else RIGHT_PANE_PATH

    if action == "Open in Terminal":
        with open(os.path.expanduser("~/.last_fm_path"), "w") as f:
            f.write(current_path)
        raise urwid.ExitMainLoop()
    elif action == "Open in Nvim":
        if selected_items:
            item_path = list(selected_items)[0]
            subprocess.Popen(['nvim', item_path])
    elif action == "Select/Deselect All":
        toggle_select_all(current_focus)
    
    main_loop.widget = columns

def toggle_select_all(pane):
    global selected_items
    listbox = left_listbox if pane == 0 else right_listbox
    current_path = LEFT_PANE_PATH if pane == 0 else RIGHT_PANE_PATH

    all_items = set(os.path.join(current_path, item.base_widget.text.split(' ', 1)[-1].strip())
                    for item in listbox.body)

    if all_items.issubset(selected_items):
        selected_items -= all_items
    else:
        selected_items |= all_items

    for i, item in enumerate(listbox.body):
        item_path = os.path.join(current_path, item.base_widget.text.split(' ', 1)[-1].strip())
        is_folder = item.base_widget.text.startswith(FOLDER_SYMBOL) or item.base_widget.text.startswith(f"* {FOLDER_SYMBOL}")
        
        if item_path in selected_items:
            prefix = f"* {FOLDER_SYMBOL}" if is_folder else "*   "
        else:
            prefix = f"{FOLDER_SYMBOL} " if is_folder else "  "
        
        new_text = f"{prefix} {os.path.basename(item_path)}"
        item.original_widget.set_text(new_text)
        item._attr_map = {None: 'selected' if item_path in selected_items else None}
        item._focus_map = {None: 'selected_focus' if item_path in selected_items else 'reversed'}

def update_focus(pane, direction):
    listbox = left_listbox if pane == 0 else right_listbox
    body = listbox.body
    focus_widget, focus_position = body.get_focus()
    
    if focus_position is not None:
        new_position = max(0, min(len(body.contents) - 1, focus_position + direction))
        body.set_focus(new_position)
        body.set_focus(new_position)

def update_directory(pane, new_path):
    global LEFT_PANE_PATH, RIGHT_PANE_PATH, left_listbox, right_listbox, left_pane, right_pane
    if pane == 0:
        LEFT_PANE_PATH = new_path
        paths = get_directory_contents(LEFT_PANE_PATH)
        left_listbox.body[:] = paths
        left_pane.set_title(f"{shorten_path(LEFT_PANE_PATH)}")
    else:
        RIGHT_PANE_PATH = new_path
        paths = get_directory_contents(RIGHT_PANE_PATH)
        right_listbox.body[:] = paths
        right_pane.set_title(f"{shorten_path(RIGHT_PANE_PATH)}")
    
    if paths:
        if pane == 0:
            left_listbox.focus_position = 0
        else:
            right_listbox.focus_position = 0

def toggle_selection(pane):
    listbox = left_listbox if pane == 0 else right_listbox
    current_path = LEFT_PANE_PATH if pane == 0 else RIGHT_PANE_PATH
    focus_widget, focus_position = listbox.body.get_focus()
    if focus_widget and focus_position is not None:
        full_text = focus_widget.base_widget.text
        is_folder = full_text.startswith(FOLDER_SYMBOL) or full_text.startswith(f"* {FOLDER_SYMBOL}")
        
        if is_folder:
            item_name = full_text.split(' ', 2)[-1].strip()
        else:
            item_name = full_text.split(' ', 1)[-1].strip()
        
        item_path = os.path.join(current_path, item_name)
        
        if item_path in selected_items:
            selected_items.remove(item_path)
            prefix = f"{FOLDER_SYMBOL} " if is_folder else "  "
        else:
            selected_items.add(item_path)
            prefix = f"* {FOLDER_SYMBOL}" if is_folder else "*   "
        
        new_text = f"{prefix} {item_name}"
        focus_widget.original_widget.set_text(new_text)
        focus_widget._attr_map = {None: 'selected' if item_path in selected_items else None}
        focus_widget._focus_map = {None: 'selected_focus' if item_path in selected_items else 'reversed'}

class NavigableDialog(urwid.WidgetWrap):
    def __init__(self, body):
        self.listbox = urwid.ListBox(urwid.SimpleListWalker(body))
        super().__init__(self.listbox)

    def keypress(self, size, key):
        if key in ('j', 'down'):
            return self.listbox.keypress(size, 'down')
        elif key in ('k', 'up'):
            return self.listbox.keypress(size, 'up')
        elif key == 'enter':
            focus_widget, _ = self.listbox.body.get_focus()
            if isinstance(focus_widget, urwid.AttrMap) and isinstance(focus_widget.original_widget, urwid.Button):
                focus_widget.original_widget._emit('click')
            return None
        elif key == 'esc':
            self.cancel_action()
            return None
        return key

    def cancel_action(self):
        main_loop.widget = columns

class AddDialog(urwid.WidgetWrap):
    def __init__(self):
        self.edit = urwid.Edit("Enter file/directory name: ")
        self.ok_button = urwid.Button("OK", on_press=self.on_ok)
        self.cancel_button = urwid.Button("Cancel", on_press=self.on_cancel)
        
        pile = urwid.Pile([
            self.edit,
            urwid.Divider(),
            urwid.Columns([
                ('pack', self.ok_button),
                ('pack', self.cancel_button)
            ])
        ])
        
        super().__init__(urwid.LineBox(pile, title="Add File/Directory"))

    def on_ok(self, button):
        on_add_confirm(self.edit.edit_text)

    def on_cancel(self, button):
        main_loop.widget = columns

    def keypress(self, size, key):
        if key == 'enter':
            self.on_ok(None)
            return None
        elif key == 'esc':
            self.on_cancel(None)
            return None
        return super().keypress(size, key)

class RenameDialog(NavigableDialog):
    def __init__(self, old_name):
        self.edit = urwid.Edit("Enter new name: ", edit_text=old_name)
        super().__init__([self.edit, urwid.Divider()])

    def keypress(self, size, key):
        if key == 'enter':
            self.confirm_action()
        else:
            super().keypress(size, key)

    def confirm_action(self):
        on_rename_confirm(self.edit.get_edit_text())

def create_add_dialog():
    return urwid.Overlay(
        AddDialog(),
        columns,
        align='center',
        valign='middle',
        width=('relative', 50),
        height=('relative', 30),
        min_width=20,
        min_height=5
    )

def on_add_confirm(name):
    current_path = LEFT_PANE_PATH if current_focus == 0 else RIGHT_PANE_PATH
    new_path = os.path.join(current_path, name)
    
    try:
        if name.endswith('/'):
            os.makedirs(new_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            open(new_path, 'a').close()
        
        update_directory(current_focus, current_path)
    except OSError as e:
        error_dialog = create_error_dialog(f"Error creating {name}: {str(e)}")
        main_loop.widget = error_dialog
        return

    main_loop.widget = columns

def on_rename_confirm(new_name):
    focus_widget, _ = (left_listbox if current_focus == 0 else right_listbox).body.get_focus()
    old_name = focus_widget.base_widget.text.split(' ', 1)[-1].strip()
    current_path = LEFT_PANE_PATH if current_focus == 0 else RIGHT_PANE_PATH
    old_path = os.path.join(current_path, old_name)
    new_path = os.path.join(current_path, new_name)
    
    os.rename(old_path, new_path)
    update_directory(current_focus, current_path)
    main_loop.widget = columns

def maintain_focus_position(from_pane, to_pane):
    from_listbox = left_listbox if from_pane == 0 else right_listbox
    to_listbox = right_listbox if from_pane == 0 else left_listbox
    
    current_position = from_listbox.focus_position
    max_position = len(to_listbox.body) - 1
    
    if current_position > max_position:
        to_listbox.focus_position = max_position
    else:
        to_listbox.focus_position = current_position

def handle_input(key):
    global current_focus, LAST_KEY

    if isinstance(main_loop.widget, urwid.Overlay):
        return main_loop.widget.keypress((30, 20), key)

    elif key == 'c':
        if selected_items:
            main_loop.widget = create_copy_move_dialog("copy")

    elif key == 'm':
        if selected_items:
            main_loop.widget = create_copy_move_dialog("move")

    elif key == 'g':
        if LAST_KEY == 'g':
            listbox = left_listbox if current_focus == 0 else right_listbox
            listbox.focus_position = 0
            LAST_KEY = None

    elif key == 'G':
        listbox = left_listbox if current_focus == 0 else right_listbox
        listbox.focus_position = len(listbox.body) - 1


    elif key == '0':
        home_dir = os.path.expanduser("~")
        update_directory(current_focus, home_dir)           

    elif key == 'f':
        jump_to_opposite(current_focus)

    elif key == 'l':
        current_focus = 1
        columns.set_focus(1)
        maintain_focus_position(0, 1)

    elif key == 'h':
        current_focus = 0
        columns.set_focus(0)
        maintain_focus_position(1, 0)

    elif key in ('j', 'down'):
        update_focus(current_focus, 1)

    elif key in ('k', 'up'):
        update_focus(current_focus, -1)

    elif key == 'd':
        main_loop.widget = create_delete_dialog()

    elif key == 'o':
        main_loop.widget = create_action_dialog()

    elif key == 'l':
        current_focus = 1
        columns.set_focus(1)

    elif key == 'h':
        current_focus = 0
        columns.set_focus(0)

    elif key == 'enter':
        listbox = left_listbox if current_focus == 0 else right_listbox
        current_path = LEFT_PANE_PATH if current_focus == 0 else RIGHT_PANE_PATH
        focus_widget, focus_position = listbox.body.get_focus()
        if focus_widget and focus_position is not None:
            item_name = focus_widget.base_widget.text.split(' ', 1)[-1].strip()
            new_path = os.path.join(current_path, item_name)
            if os.path.isdir(new_path):
                update_directory(current_focus, new_path)

    elif key == 'backspace':
        current_path = LEFT_PANE_PATH if current_focus == 0 else RIGHT_PANE_PATH
        parent_path = os.path.dirname(current_path)
        if parent_path != current_path:
            update_directory(current_focus, parent_path)

    elif key == ' ':
        toggle_selection(current_focus)

    elif key == 'a':
        main_loop.widget = create_add_dialog()

    elif key == 'r':
        focus_widget, _ = (left_listbox if current_focus == 0 else right_listbox).body.get_focus()
        old_name = focus_widget.base_widget.text.split(' ', 1)[-1].strip()
        main_loop.widget = urwid.Overlay(RenameDialog(old_name), columns, align='center', valign='middle', width=('relative', 40), height=('relative', 20))

    elif key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

    LAST_KEY = key

left_paths = get_directory_contents(LEFT_PANE_PATH)
right_paths = get_directory_contents(RIGHT_PANE_PATH)

left_listbox = urwid.ListBox(urwid.SimpleListWalker(left_paths))
right_listbox = urwid.ListBox(urwid.SimpleListWalker(right_paths))

left_pane = urwid.LineBox(left_listbox, title=f"{shorten_path(LEFT_PANE_PATH)}")
right_pane = urwid.LineBox(right_listbox, title=f"{shorten_path(RIGHT_PANE_PATH)}")

columns = urwid.Columns([left_pane, right_pane])

current_focus = 0

if left_paths:
    left_listbox.body.set_focus(0)
if right_paths:
    right_listbox.body.set_focus(0)

palette = [
    ('reversed', 'standout', ''),
    ('selected', 'white', 'dark blue'),
    ('selected_focus', 'white', 'light blue'),
]

main_loop = urwid.MainLoop(columns, unhandled_input=handle_input, palette=palette)

if __name__ == "__main__":
    try:
        main_loop.run()
    finally:
        last_path_file = os.path.expanduser("~/.last_fm_path")
        if os.path.exists(last_path_file):
            with open(last_path_file, "r") as f:
                last_path = f.read().strip()
            os.remove(last_path_file)
            os.system(f"cd {last_path} && exec $SHELL")

