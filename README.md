# Filemanager

## Todos

- [ ] add bookmarks of popular directories (`b` to view and `B` to add)
- [ ] implement nvim only for files (come back to fm after if possible)
- [ ] implement tp command if global tp config is found

## Current Features

**General**:

- [x] press `q`, `Q` to exit
- [x] press `o` to open action dialog

**Navigation**:

- [x] `j`, `k`: up and down
- [x] `h`, `l`: for switching panes
- [x] `gg`, `G`: jump to fist/last
- [x] `f`: swapping between first folder/file
- [x] `enter`: jump into a folder
- [x] `backspace`: navigate back
- [x] `0`: jump into home directory

**File Interaction**:

- [x] `space`: toggle selection
- [x] `d`: delete selected
- [x] `m`: move to other pane
- [x] `c`: copy to other pane
- [x] `r`: rename
- [x] `a`: add new file or folder (also possible: `/temp/test.txt`)

## Installation

### Using pipenv (recommended)

Step 1: Clone the repository:

```bash
git clone https://github.com/xGerTowelie/filemanager.git
```

```bash
cd teleport
```

Step 2: Install dependencies using pipenv:

```bash
pipenv install
```

Step 3: Activate the virtual environment:

```bash
pipenv shell
```

Step 4: Run the file manager:

```bash
python fm.py
```
