# NameDrop

A PySide6 application to help rename files and folders with non-standard ASCII characters, making them compatible across different operating systems and cloud services.

## Features

- **Drag and Drop Interface**: Simply drag files or folders onto the window
- **Visual Highlighting**: Non-standard ASCII characters are highlighted in yellow for easy identification
- **Multiple Rename Options**:

  - **Auto Rename**: Replaces accented characters with unaccented equivalents and removes other non-ASCII characters
  - **Remove bad characters**: Strips all non-standard ASCII characters
  - **Replace bad characters**: Only replaces accented characters, keeps other characters
  - **Edit Name**: Manually edit the file name
  - **Ignore File**: Skip files you don't want to process

- **Safety Features**:

  - Optional backup creation before renaming
  - Preview dialog before renaming (can be disabled)
  - Validation to prevent overwriting existing files
  - Safe file operations to prevent data corruption

- **Customization**:
  - Configurable list of allowed special characters
  - Persistent settings (window position, screen, checkbox states)
  - Always-on-top window option

## Installation

1. Install Python >=3.12.12,<3.13 (required for PySide6 6.7.3 compatibility)

   Install the latest 3.12.x patch version using uv:

   ```bash
   uv python install 3.12
   ```

   If you already have 3.12.x installed and want to upgrade to the newest patch:

   ```bash
   uv python upgrade 3.12
   ```

   To pin the project to use Python 3.12 (latest patch available):

   ```bash
   uv python pin 3.12
   ```

2. Install dependencies using uv:

```bash
uv sync
```

## Usage

```bash
python main.py
```

1. Drag a file or folder onto the window
2. Review highlighted non-standard ASCII characters
3. Choose a rename option or edit manually
4. Approve the rename (if prompts are enabled)

## Settings

The application saves your preferences including:

- Window position and screen
- Checkbox states (prompt before rename, backup, ignore common chars)
- Custom allowed characters list

Settings are stored in your system's standard configuration location.

## Platform Restrictions

For detailed information about filename restrictions across different operating systems and file systems (Windows, macOS, Linux, Cloud Drives, FAT32), see [PLATFORM-RESTRICTIONS.md](PLATFORM-RESTRICTIONS.md).

## Author

**Rich Lewis**  
GitHub: [@RichLewis007](https://github.com/RichLewis007)
