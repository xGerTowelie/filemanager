# Filemanager

## Todos
- [ ] pressing `m` to move files and folders to other pane
- [ ] add dialog breaks if folder and file are provided "test/test.txt"
- [ ] rename and add dialog can only be accepted via mouse
- [ ] press `esc`` to cancel selection
- [ ] press `esc` to cancel dialog
- [ ] fix pane title
- [ ] add favorites, add them to over action menu, press `f` to quick navigate

## Current Features
- [x] press `q` to exit
- [x] navigation on `j`, `k` for up and down
- [x] navigation on `h`, `l` for switching panes
- [x] press `enter` to navigate into a folder
- [x] press `backspace` to navigate back
- [x] press `space` to toggle selection of files/folders
- [x] press `d` to delete selected files/folders
- [x] press `o` to open action dialog


## Installation

### Using pipenv (recommended)

1. Clone the repository:
```bash
git clone https://github.com/xGerTowelie/filemanager.git
```

```bash
cd teleport
```

2. Install dependencies using pipenv:
```bash
pipenv install
```

3. Activate the virtual environment:

```bash
pipenv shell
```
4. Run the file manager:

```bash
python fm.py
```
