import os
import urwid
import subprocess
import argparse

# Define default paths
DEFAULT_LEFT_PANE_PATH = "/home/towelie/"
DEFAULT_RIGHT_PANE_PATH = "/home/towelie/"

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
    confirm_button = urwid.Button("Yes")
    cancel_button = urwid.Button("No")
    
    urwid.connect_signal(confirm_button, 'click', on_confirm_delete)
    urwid.connect_signal(cancel_button, 'click', on_cancel_delete)
    
    button_box = urwid.Pile([
        urwid.AttrMap(confirm_button, None, focus_map='reversed'),
        urwid.AttrMap(cancel_button, None, focus_map='reversed')
    ])
    
    dialog = urwid.Pile([
        confirmation_text,
        urwid.Divider(),
        button_box
    ])
    
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

def on_confirm_delete(button):
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

def on_cancel_delete(button):
    main_loop.widget = columns  # Close the dialog

def create_action_dialog():
    action_items = ["Open in Terminal", "Open in Nvim"]
    action_widgets = []
    for action in action_items:
        button = urwid.Button(action)
        urwid.connect_signal(button, 'click', lambda b, a=action: on_action_select(a))
        action_widgets.append(urwid.AttrMap(button, None, focus_map='reversed'))

    action_pile = urwid.Pile(action_widgets)
    return urwid.Overlay(
        urwid.LineBox(action_pile, title="Select Action"),
        columns,
        align='center',
        valign='middle',
        width=('relative', 30),
        height=('relative', 20),
        min_width=20,
        min_height=5
    )

def on_action_select(action):
    global selected_items
    if not selected_items:
        main_loop.widget = columns
        return

    # Perform the selected action on the first item in the selection
    item_path = list(selected_items)[0]
    if action == "Open in Terminal":
        subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'cd {os.path.dirname(item_path)}; exec bash'])
    elif action == "Open in Nvim":
        subprocess.Popen(['nvim', item_path])
    
    main_loop.widget = columns  # Close the dialog

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

def toggle_selection(pane):
    listbox = left_listbox if pane == 0 else right_listbox
    current_path = LEFT_PANE_PATH if pane == 0 else RIGHT_PANE_PATH
    focus_widget, focus_position = listbox.body.get_focus()
    if focus_widget and focus_position is not None:
        item_name = focus_widget.base_widget.text.split(' ', 1)[-1].strip()
        item_path = os.path.join(current_path, item_name)
        if item_path in selected_items:
            selected_items.remove(item_path)
        else:
            selected_items.add(item_path)
        new_widget = create_text_widget(focus_widget.base_widget.text, item_path)
        listbox.body[focus_position] = new_widget

def handle_input(key):
    global current_focus
    if key in ('j', 'down'):
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
    main_loop.run()
