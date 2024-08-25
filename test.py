import os
import urwid

# Define fixed paths for left and right panes
LEFT_PANE_PATH = "/home/towelie/projects/"  # Change this to a valid path on your system
RIGHT_PANE_PATH = "/home/towelie/.local/"  # Change this to a valid path on your system

def get_directory_contents(path):
    try:
        # List the files and directories in the specified path
        items = os.listdir(path)
    except PermissionError:
        items = ["Permission denied"]
    except FileNotFoundError:
        items = ["Path not found"]
    
    # Create a list of urwid.Text widgets for each item
    return [urwid.Text(item) for item in items]

# Get the directory contents for both panes
left_paths = get_directory_contents(LEFT_PANE_PATH)
right_paths = get_directory_contents(RIGHT_PANE_PATH)

# Create a list walker for each pane
left_listbox = urwid.ListBox(urwid.SimpleListWalker(left_paths))
right_listbox = urwid.ListBox(urwid.SimpleListWalker(right_paths))

# Add borders to the panes and embed the list boxes
left_pane = urwid.LineBox(left_listbox, title=f"Left Pane: {LEFT_PANE_PATH}")
right_pane = urwid.LineBox(right_listbox, title=f"Right Pane: {RIGHT_PANE_PATH}")

# Combine the two panes horizontally
columns = urwid.Columns([left_pane, right_pane])

# Create a main loop to render the UI
main_loop = urwid.MainLoop(columns)

# Run the main loop
if __name__ == "__main__":
    main_loop.run()

