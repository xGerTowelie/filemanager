import os
import urwid
import subprocess
import argparse
import shutil

# Define default paths
DEFAULT_LEFT_PANE_PATH = "/home/towelie/"
DEFAULT_RIGHT_PANE_PATH = "/home/towelie/"
overwrite_confirmed = False
copy_move_confirmed = False

# Parse command-line arguments
parser = argparse.ArgumentParser(description="A simple file manager.")
parser.add_argument('path', nargs='?', default=DEFAULT_LEFT_PANE_PATH, help="Initial path for the left pane.")
args = parser.parse_args()

# Set paths based on arguments
LEFT_PANE_PATH = args.path
RIGHT_PANE_PATH = DEFAULT_RIGHT_PANE_PATH

# Define symbols
FOLDER_SYMBOL = "📁"

selected_items = set()

def copy_items(source_path, dest_path):
    for item in selected_items:
        dest_item = os.path.join(dest_path, os.path.basename(item))
        if os.path.exists(dest_item):
            if not confirm_overwrite(dest_item):
                continue
        if os.path.isdir(item):
            shutil.copytree(item, dest_item, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest_item)

def move_items(source_path, dest_path):
    for item in selected_items:
        dest_item = os.path.join(dest_path, os.path.basename(item))
        if os.path.exists(dest_item):
            if not confirm_overwrite(dest_item):
                continue
        shutil.move(item, dest_item)

def create_overwrite_dialog(item):
    text = urwid.Text(f"'{os.path.basename(item)}' already exists. Overwrite?")
    yes_button = urwid.Button("Yes", on_press=lambda _: on_overwrite_confirm(True))
    no_button = urwid.Button("No", on_press=lambda _: on_overwrite_confirm(False))
    
    buttons = urwid.Columns([
        ('weight', 1, urwid.AttrMap(yes_button, None, focus_map='reversed')),
        ('weight', 1, urwid.AttrMap(no_button, None, focus_map='reversed')),
    ])
    
    dialog_body = [text, urwid.Divider(), buttons]
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

def create_copy_move_dialog(operation):
    text = urwid.Text(f"Are you sure you want to {operation} {len(selected_items)} item(s)?")
    yes_button = urwid.Button("Yes", on_press=lambda _: on_copy_move_confirm(True, operation))
    no_button = urwid.Button("No", on_press=lambda _: on_copy_move_confirm(False, operation))
    
    buttons = urwid.Columns([
        ('weight', 1, urwid.AttrMap(yes_button, None, focus_map='reversed')),
        ('weight', 1, urwid.AttrMap(no_button, None, focus_map='reversed')),
    ])
    
    dialog_body = [text, urwid.Divider(), buttons]
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
    main_loop.widget = columns  # Close the dialog

    if confirmed:
        source_path = LEFT_PANE_PATH if current_focus == 0 else RIGHT_PANE_PATH
        dest_path = RIGHT_PANE_PATH if current_focus == 0 else LEFT_PANE_PATH
        
        if operation == "copy":
            copy_items(source_path, dest_path)
        elif operation == "move":
            move_items(source_path, dest_path)
        
        update_directory(0, LEFT_PANE_PATH)
        update_directory(1, RIGHT_PANE_PATH)
        selected_items.clear()

def create_overwrite_dialog(item):
    text = urwid.Text(f"'{os.path.basename(item)}' already exists. Overwrite?")
    yes_button = urwid.Button("Yes", on_press=lambda _: on_overwrite_confirm(True))
    no_button = urwid.Button("No", on_press=lambda _: on_overwrite_confirm(False))
    
    buttons = urwid.Columns([
        ('weight', 1, urwid.AttrMap(yes_button, None, focus_map='reversed')),
        ('weight', 1, urwid.AttrMap(no_button, None, focus_map='reversed')),
    ])
    
    dialog_body = [text, urwid.Divider(), buttons]
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

def confirm_overwrite(item):
    main_loop.widget = create_overwrite_dialog(item)
    main_loop.run()
    return overwrite_confirmed

def on_overwrite_confirm(confirmed):
    global overwrite_confirmed
    overwrite_confirmed = confirmed
    raise urwid.ExitMainLoop()

def confirm_overwrite(item):
    main_loop.widget = create_overwrite_dialog(item)
    main_loop.run()
    return overwrite_confirmed

def on_overwrite_confirm(confirmed):
    global overwrite_confirmed
    overwrite_confirmed = confirmed
    raise urwid.ExitMainLoop()

def create_text_widget(text, path, focus=False):
    if path in selected_items:
        return urwid.AttrMap(urwid.Text('* ' + text), 'selected', focus_map='selected_focus')
    return urwid.AttrMap(urwid.Text(text), None, focus_map='reversed')

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

def on_confirm_delete(button=None):
    global selected_items
    if not selected_items:
        main_loop.widget = columns
        return

    for item_path in selected_items:
        try:
            if os.path.isdir(item_path):
                os.rmdir(item_path)
            else:
                os.remove(item_path)
        except Exception as e:
            print(f"Error deleting {item_path}: {e}")
    
    selected_items.clear()
    update_directory(0, LEFT_PANE_PATH)  # Refresh the left pane
    update_directory(1, RIGHT_PANE_PATH)  # Refresh the right pane
    main_loop.widget = columns  # Close the dialog

def on_cancel_delete(button=None):
    main_loop.widget = columns  # Close the dialog

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
    
    main_loop.widget = columns  # Close the dialog

def toggle_select_all(pane):
    global selected_items
    listbox = left_listbox if pane == 0 else right_listbox
    current_path = LEFT_PANE_PATH if pane == 0 else RIGHT_PANE_PATH

    all_items = set(os.path.join(current_path, item.base_widget.text.split(' ', 1)[-1].strip())
                    for item in listbox.body)

    if all_items.issubset(selected_items):
        # If all items are selected, deselect all
        selected_items -= all_items
    else:
        # Otherwise, select all
        selected_items |= all_items

    # Update the display
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
        left_pane.set_title(f"Left Pane: {LEFT_PANE_PATH}")
    else:
        RIGHT_PANE_PATH = new_path
        paths = get_directory_contents(RIGHT_PANE_PATH)
        right_listbox.body[:] = paths
        right_pane.set_title(f"Right Pane: {RIGHT_PANE_PATH}")
    
    # Select the first item after updating the directory
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
        main_loop.widget = columns  # Close the dialog

class AddDialog(NavigableDialog):
    def __init__(self):
        self.edit = urwid.Edit("Enter file/directory name: ")
        super().__init__([self.edit, urwid.Divider()])

    def keypress(self, size, key):
        if key == 'enter':
            self.confirm_action()
        else:
            super().keypress(size, key)

    def confirm_action(self):
        on_add_confirm(self.edit.edit_text)

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

def on_add_confirm(name):
    current_path = LEFT_PANE_PATH if current_focus == 0 else RIGHT_PANE_PATH
    new_path = os.path.join(current_path, name)
    
    if name.endswith('/'):
        os.makedirs(new_path, exist_ok=True)
    else:
        open(new_path, 'a').close()
    
    update_directory(current_focus, current_path)
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

def handle_input(key):
    global current_focus

    if isinstance(main_loop.widget, urwid.Overlay):
        return main_loop.widget.keypress((30, 20), key)

    elif key == 'c':
        if selected_items:
            main_loop.widget = create_copy_move_dialog("copy")

    elif key == 'm':
        if selected_items:
            main_loop.widget = create_copy_move_dialog("move")

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
        main_loop.widget = urwid.Overlay(AddDialog(), columns, align='center', valign='middle', width=('relative', 40), height=('relative', 20))

    elif key == 'r':
        focus_widget, _ = (left_listbox if current_focus == 0 else right_listbox).body.get_focus()
        old_name = focus_widget.base_widget.text.split(' ', 1)[-1].strip()
        main_loop.widget = urwid.Overlay(RenameDialog(old_name), columns, align='center', valign='middle', width=('relative', 40), height=('relative', 20))

    elif key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

# Get the directory contents for both panes
left_paths = get_directory_contents(LEFT_PANE_PATH)
right_paths = get_directory_contents(RIGHT_PANE_PATH)

# Create ListBox widgets for each pane
left_listbox = urwid.ListBox(urwid.SimpleListWalker(left_paths))
right_listbox = urwid.ListBox(urwid.SimpleListWalker(right_paths))

# Add borders to the panes and embed the ListBoxes
left_pane = urwid.LineBox(left_listbox, title=f"Left Pane: {LEFT_PANE_PATH}")
right_pane = urwid.LineBox(right_listbox, title=f"Right Pane: {RIGHT_PANE_PATH}")

# Combine the two panes horizontally
columns = urwid.Columns([left_pane, right_pane])

# Track current focus (0 for left pane, 1 for right pane)
current_focus = 0

# Initialize focus for both panes
if left_paths:
    left_listbox.body.set_focus(0)
if right_paths:
    right_listbox.body.set_focus(0)

palette = [
    ('reversed', 'standout', ''),
    ('selected', 'white', 'dark blue'),
    ('selected_focus', 'white', 'light blue'),
]

# Create a main loop to render the UI
main_loop = urwid.MainLoop(columns, unhandled_input=handle_input, palette=palette)

# Run the main loop
if __name__ == "__main__":
    try:
        main_loop.run()
    finally:
        # Check if we need to open a terminal
        last_path_file = os.path.expanduser("~/.last_fm_path")
        if os.path.exists(last_path_file):
            with open(last_path_file, "r") as f:
                last_path = f.read().strip()
            os.remove(last_path_file)
            os.system(f"cd {last_path} && exec $SHELL")

