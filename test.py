import os
import urwid

# Define fixed paths for left and right panes
LEFT_PANE_PATH = "/home/towelie/projects/"  # Change this to a valid path on your system
RIGHT_PANE_PATH = "/etc"  # Change this to a valid path on your system

# Define symbols
FOLDER_SYMBOL = "📁"  # You can also use "" or any other Nerd Font symbol

def create_text_widget(text, focus=False):
    return urwid.AttrMap(urwid.Text(text), None, focus_map='reversed')

def get_directory_contents(path):
    try:
        # List the files and directories in the specified path
        items = os.listdir(path)
    except PermissionError:
        items = ["Permission denied"]
    except FileNotFoundError:
        items = ["Path not found"]
    
    # Separate directories and files
    directories = []
    files = []

    for item in items:
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            directories.append(item)
        else:
            files.append(item)
    
    # Sort directories and files alphabetically
    directories.sort()
    files.sort()

    # Combine sorted directories and files
    sorted_items = directories + files

    # Create urwid.Text widgets for each item with appropriate symbols
    contents = []
    for item in sorted_items:
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            item_display = f"{FOLDER_SYMBOL} {item}"
        else:
            item_display = f"  {item}"
        contents.append(create_text_widget(item_display))
    
    return contents

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

def update_focus(pane, direction):
    listbox = left_listbox if pane == 0 else right_listbox
    body = listbox.body
    focus_widget, focus_position = body.get_focus()
    
    if focus_position is not None:
        # Update focus position
        new_position = max(0, min(len(body.contents) - 1, focus_position + direction))
        body.set_focus(new_position)
        # Scroll the ListBox if necessary
        body.set_focus(new_position)

def update_directory(new_path):
    global LEFT_PANE_PATH, left_listbox, left_pane
    LEFT_PANE_PATH = new_path
    left_paths = get_directory_contents(LEFT_PANE_PATH)
    left_listbox.body[:] = left_paths
    left_pane.set_title(f"Left Pane: {LEFT_PANE_PATH}")

# Function to handle keypresses for navigation
def handle_input(key):
    global current_focus
    if key in ('j', 'down'):
        update_focus(current_focus, 1)
    elif key in ('k', 'up'):
        update_focus(current_focus, -1)
    elif key == 'l':
        current_focus = 1
        columns.set_focus(1)
    elif key == 'h':
        current_focus = 0
        columns.set_focus(0)
    elif key == 'enter':
        if current_focus == 0:  # Only handle Enter for the left pane
            focus_widget, focus_position = left_listbox.body.get_focus()
            if focus_widget and focus_position is not None:
                item_name = focus_widget.base_widget.text.split(' ', 1)[-1]
                new_path = os.path.join(LEFT_PANE_PATH, item_name)
                if os.path.isdir(new_path):
                    update_directory(new_path)
    elif key == 'backspace':
        if current_focus == 0:  # Only handle Backspace for the left pane
            parent_path = os.path.dirname(LEFT_PANE_PATH)
            if parent_path != LEFT_PANE_PATH:  # Prevent going above the root directory
                update_directory(parent_path)
    elif key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

# Initialize focus for both panes
if left_paths:
    left_listbox.body.set_focus(0)
if right_paths:
    right_listbox.body.set_focus(0)

# Create a main loop to render the UI
main_loop = urwid.MainLoop(columns, unhandled_input=handle_input, palette=[('reversed', 'standout', '')])

# Run the main loop
if __name__ == "__main__":
    main_loop.run()

