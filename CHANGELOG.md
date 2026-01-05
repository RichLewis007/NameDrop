# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **CHANGELOG.md**: Added comprehensive changelog following Keep a Changelog format
- **Reserved Names Detection**: LED indicators now check for Windows reserved names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
  - Case-insensitive checking (e.g., "con.txt", "CON", "Con" all detected)
  - Reserved names trigger purple LED (Restrictions)
- **Additional Restrictions Detection**: LED indicators now check for:
  - Maximum path length restrictions (260 chars for Windows/Cloud, 255 for macOS/Linux)
  - Filenames ending with space or period after extension (Windows restriction)
  - Filenames consisting solely of spaces (Windows restriction)
  - All additional restrictions trigger purple LED (Restrictions)
- **Development Script - Remove Virtual Environment**: Added "Remove virtual environment" menu item to `run.sh`
  - Shows which virtual environment directories will be deleted (`.venv`, `venv`, `env`, `.env`)
  - Displays directory sizes before deletion
  - Prompts for confirmation (y/N, defaults to No)
  - Optionally recreates the virtual environment after deletion
- **Project Restructure**: Restructured project to follow Python packaging best practices
  - Moved all source code to `src/namedrop/` directory (src-layout)
  - Moved UI files to `src/namedrop/ui/` directory
  - Added `__init__.py` for proper package structure
  - Updated imports to use relative imports
  - Added entry point in `pyproject.toml`: `namedrop = "namedrop.main:main"`
- **Qt Designer UI File Support**: Integrated Qt Designer UI file loading
  - Application now loads `main.ui` from `src/namedrop/ui/` directory
  - Uses PySide6 best practices with `QFile` and `QIODevice` for UI loading
  - Falls back to programmatic UI if UI file cannot be loaded
  - Custom widgets (DragDropWidget, FileNameDisplay, LEDIndicator) replace basic widgets from UI file
  - Missing sections added programmatically after UI file loads

### Changed

- **Development Script - Clean Cache**: Enhanced `clean_cache` function in `run.sh`
  - Now displays all cache files and directories that will be deleted before deletion
  - Shows counts for each type (**pycache** directories, _.pyc files, _.pyo files)
  - Lists all files/directories that will be deleted
  - Prompts for user confirmation (y/N, defaults to No) before deleting
- **Project Structure**: Restructured to src-layout following Python packaging best practices
  - Source files moved from root to `src/namedrop/`
  - UI files moved to `src/namedrop/ui/`
  - Updated `pyproject.toml` with build system configuration and entry points
  - Updated `menu.sh` to use `uv run namedrop` instead of `uv run python main.py`
  - Updated `README.md` with new usage instructions
- **UI File Loading**: Improved UI file loading implementation
  - Now uses `QFile` and `QIODevice` following PySide6 best practices
  - Better error handling with descriptive error messages
  - Proper resource management with file closing
- **Window Position Validation**: Enhanced window position validation to prevent Qt warnings
  - Validates and clamps window position before moving to prevent "outside known screen" warnings
  - Validates position when saving settings
  - Validates screen centering calculations
- **Development Script - Project Info**: Updated "Project info" menu item
  - Now shows Python version from uv-managed environment using `uv python find`
  - More accurate version information for the actual runtime environment
- **.gitignore**: Updated to reflect project structure changes
  - Removed `uv.lock` from ignored files (should be committed for reproducible builds)
  - Removed outdated comment about `main.ui` (now properly integrated)

## [0.2.0] - 2024-12-13

### Added

- **Development Script**: Added `run.sh` bash script with interactive menu for common development tasks
  - Menu options: Run, Check (lint), Format, Sync dependencies, Install dependencies, Test, Type check (mypy), Clean cache, Project info, Quit
  - Self-contained script with embedded UI functions (no external dependencies)
  - Uses fzf/gum for menu interface with fallback to basic numbered menu
  - Auto-checks for PySide6 dependency before running app
- **Platform Compatibility System**: Comprehensive platform compatibility checking and filtering
  - "Make compatible with:" section with platform buttons (Everything, Windows, macOS, Linux, Cloud Drives)
  - Real-time filename filtering based on selected platforms
  - Hover tooltips showing platform-specific restrictions
  - Click to apply filters, with combined restrictions display
  - RENAME button to apply compatibility-filtered names
- **LED Detection Indicators**: Visual platform compatibility status indicators
  - "Detecting.." section with LED lights for each platform (Windows, macOS, Linux, Cloud Drives)
  - Color-coded status: Green (OK), Yellow (non-standard chars), Red (Invalid chars), Orange (Problematic), Purple (Restrictions)
  - Real-time updates as filename changes
  - Checks for: excluded characters, problematic characters, position restrictions, reserved names, additional restrictions
- **Editable Filename Display**: Direct editing of filename with real-time highlighting
  - Filename display box is now editable
  - Real-time character highlighting updates as user types
  - Maintains highlighting for non-standard ASCII characters during editing
- **Leading/Trailing Character Validation**: Enhanced validation for problematic filename patterns
  - Dialog warning for leading/trailing spaces and periods
  - Option to automatically fix by removing offending characters
  - Integrated into all rename operations (REMOVE, REPLACE, Edit)
- **Allowed Characters Persistence**: User-defined allowed characters are now saved
  - "Allowed characters:" field changes are auto-saved immediately
  - Settings persist across application restarts
  - Characters in allowed list are excluded from highlighting and all rename operations
- **Documentation**: Comprehensive filename restrictions documentation
  - `docs/filename-restrictions.md` with detailed platform restrictions
  - Covers Windows, macOS, Linux, and major cloud platforms (AWS S3, Google Cloud, Azure, Dropbox, OneDrive)
  - Includes character restrictions, position restrictions, reserved names, and additional limitations

### Changed

- **Dependency Management**: Migrated from `requirements.txt` to `uv`-only dependency management
  - All dependencies now defined in `pyproject.toml`
  - PySide6 version constrained to `<6.10.0` for macOS 12.0 compatibility
  - Updated README to reflect uv-only installation
- **Platform Restrictions Data**: Enhanced platform restriction checking
  - Added reserved names checking (Windows: CON, PRN, AUX, NUL, COM1-9, LPT1-9)
  - Added additional restrictions checking (max path length, space/period after extension, spaces-only filenames)
  - Reserved names and additional restrictions trigger purple LED indicator
- **Filename Display**: Made filename display editable with real-time updates
  - Changed from read-only to editable QTextEdit
  - Real-time highlighting updates as user types
  - Cursor position preservation during highlighting updates

### Fixed

- **Space Character Handling**: Fixed issue where spaces were incorrectly being removed
  - Spaces are now properly recognized as allowed characters
  - Only leading/trailing spaces are restricted based on platform rules
  - Middle spaces are preserved in all rename operations
- **Ignore Characters**: Fixed ignore characters not being respected in compatibility filter
  - Characters in "Allowed characters:" field are now properly excluded from platform filtering
  - Ignore characters work correctly in all rename operations and highlighting
- **LED Indicator Updates**: Fixed LED indicators to update in all scenarios
  - LEDs now update when files are selected
  - LEDs update when filename is edited
  - LEDs update when platform compatibility filters are applied

## [0.1.0] - 2024-12-13

### Added

- Initial release of NameDrop
- Drag and drop file/folder interface
- Visual highlighting of non-standard ASCII characters
- Multiple rename operations:
  - Auto Rename (replace accented chars, remove other non-ASCII)
  - Remove bad characters
  - Replace bad characters (accented only)
  - Edit Name (manual editing)
  - Ignore File
- Safety features:
  - Optional backup creation
  - Preview dialog before renaming
  - Validation to prevent overwriting existing files
- Settings persistence:
  - Window position and screen
  - Checkbox states
  - Custom allowed characters list
- Always-on-top window option
