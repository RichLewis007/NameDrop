#!/usr/bin/env python3
"""
NameDrop - A PySide6 application to rename files/folders with non-standard ASCII characters

Author: Rich Lewis
GitHub: @RichLewis007
"""

import sys
import os
import random
import string
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QMessageBox,
    QGroupBox,
    QTextEdit,
    QScrollArea,
    QDialog,
    QDialogButtonBox,
    QSizePolicy,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import (
    Qt,
    QSettings,
    QPoint,
    QSize,
    QRect,
    Signal,
    QStandardPaths,
    QFile,
    QIODevice,
)
from PySide6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QColor,
    QTextCharFormat,
    QFont,
    QTextCursor,
    QPainter,
    QBrush,
    QPen,
)

from .file_operations import FileOperations
from .character_utils import CharacterUtils


# Platform compatibility data
PLATFORM_RESTRICTIONS = {
    "Everything": {
        "name": "Everything (All Platforms)",
        "excluded_chars": set(
            '<>:"|?*\\/'
        ),  # No spaces - spaces are allowed, only position matters
        "problematic_chars": set("!@#$%^&()[]{};,=+"),  # No spaces
        "excluded_positions": ["trailing_space", "trailing_period", "leading_space"],
        "reserved_names": set(),  # Windows reserved names (case-insensitive check done separately)
        "max_path_length": 260,  # Windows default MAX_PATH
        "max_filename_length": 255,  # Conservative limit for all platforms
        "additional_restrictions": ["no_space_period_after_ext", "no_spaces_only"],
        "description": "Most restrictive - ensures compatibility with Windows, macOS, Linux, and all cloud platforms",
    },
    "Windows": {
        "name": "Windows OS",
        "excluded_chars": set(
            '<>:"|?*\\/'
        ),  # No spaces - spaces are allowed, only position matters
        "problematic_chars": set(),
        "excluded_positions": ["trailing_space", "trailing_period"],
        "reserved_names": {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
            ".",
            "..",
        },  # Reserved directory names
        "max_path_length": 260,  # MAX_PATH default
        "max_filename_length": 255,  # Filename length limit
        "additional_restrictions": ["no_space_period_after_ext", "no_spaces_only"],
        "description": "Windows file system restrictions. Trailing spaces and periods are automatically stripped.",
    },
    "macOS": {
        "name": "macOS",
        "excluded_chars": set(":/"),  # No spaces
        "problematic_chars": set(),
        "excluded_positions": [],
        "reserved_names": set(),
        "max_path_length": 255,  # Filename length limit
        "max_filename_length": 255,  # Filename length limit
        "additional_restrictions": [],
        "description": "macOS allows most characters. Only colon (:) and forward slash (/) are forbidden.",
    },
    "Linux": {
        "name": "Linux",
        "excluded_chars": set("/"),  # No spaces
        "problematic_chars": set(),
        "excluded_positions": [],
        "reserved_names": set(),
        "max_path_length": 255,  # Filename length limit (bytes)
        "max_filename_length": 255,  # Filename length limit (bytes)
        "additional_restrictions": [],
        "description": "Linux is very permissive. Only forward slash (/) is forbidden.",
    },
    "Cloud": {
        "name": "Cloud Drives",
        "excluded_chars": set(
            '<>:"|?*\\/'
        ),  # No spaces - spaces are allowed, only position matters
        "problematic_chars": set("!@#$%^&()[]{};,=+"),  # No spaces
        "excluded_positions": ["trailing_space", "trailing_period"],
        "reserved_names": {
            "CON",
            "PRN",
            "AUX",
            "NUL",  # Windows reserved names (OneDrive follows Windows)
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
            ".",
            "..",
        },  # Reserved directory names
        "max_path_length": 260,  # Windows-based cloud services
        "max_filename_length": 255,  # Filename length limit
        "additional_restrictions": ["no_space_period_after_ext", "no_spaces_only"],
        "description": "Cloud platforms (OneDrive, Dropbox, etc.) typically follow Windows restrictions for compatibility.",
    },
    "FAT32": {
        "name": "FAT32",
        "excluded_chars": set('<>:"|?*\\/'),  # Same as Windows
        "problematic_chars": set(),
        "excluded_positions": ["trailing_space", "trailing_period"],
        "reserved_names": {
            "CON",
            "PRN",
            "AUX",
            "NUL",  # Same as Windows
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
            ".",
            "..",
        },  # Reserved directory names
        "max_path_length": 260,  # Similar to Windows
        "max_filename_length": 255,  # LFN (Long File Name) limit, 8.3 format is 11 chars (8+3)
        "additional_restrictions": ["no_space_period_after_ext", "no_spaces_only"],
        "description": "FAT32 file system (common on USB drives). Windows rejects names ending with space or period. Supports LFN up to 255 characters. Uses 8.3 format (8+3=11 chars) for compatibility.",
    },
}


class LeadingTrailingIssueDialog(QDialog):
    """Dialog to show leading/trailing space/period issues and offer to fix"""

    def __init__(self, file_name: str, issues: list, parent=None):
        super().__init__(parent)
        self.file_name = file_name
        self.issues = issues
        self.fixed_name = None
        self.setWindowTitle("Filename Issue Detected")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("The filename has the following issues:"))

        # List issues
        issues_text = QLabel("\n".join(f"• {issue}" for issue in self.issues))
        issues_text.setStyleSheet(
            "padding: 10px; background-color: #fff3e0; font-size: 11pt;"
        )
        layout.addWidget(issues_text)

        # Show current name
        layout.addWidget(QLabel("Current filename:"))
        current_label = QLabel(f'"{self.file_name}"')
        current_label.setStyleSheet(
            "font-size: 12pt; padding: 5px; background-color: #f0f0f0; font-family: monospace;"
        )
        layout.addWidget(current_label)

        # Show fixed name if we can fix it
        if self.can_fix():
            fixed = self.get_fixed_name()
            layout.addWidget(QLabel("Fixed filename:"))
            fixed_label = QLabel(f'"{fixed}"')
            fixed_label.setStyleSheet(
                "font-size: 12pt; padding: 5px; background-color: #e8f5e9; font-family: monospace;"
            )
            layout.addWidget(fixed_label)

        buttons = QDialogButtonBox()
        if self.can_fix():
            fix_btn = buttons.addButton(
                "Fix by removing offending character(s)", QDialogButtonBox.AcceptRole
            )
            fix_btn.clicked.connect(self.accept_fix)
        cancel_btn = buttons.addButton("Cancel", QDialogButtonBox.RejectRole)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def can_fix(self):
        """Check if we can fix the issues"""
        return (
            len(self.file_name.strip(" .")) > 0
        )  # Make sure there's something left after stripping

    def get_fixed_name(self):
        """Get the fixed name"""
        return self.file_name.strip(" .")

    def accept_fix(self):
        """Accept the fix"""
        self.fixed_name = self.get_fixed_name()
        self.accept()


class RenamePreviewDialog(QDialog):
    """Dialog to show rename preview and get user approval"""

    def __init__(self, old_name: str, new_name: str, parent=None):
        super().__init__(parent)
        self.old_name = old_name
        self.new_name = new_name
        self.setWindowTitle("Confirm Rename")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Original name:"))
        old_label = QLabel(self.old_name)
        old_label.setStyleSheet(
            "font-size: 12pt; padding: 5px; background-color: #f0f0f0;"
        )
        layout.addWidget(old_label)

        layout.addWidget(QLabel("New name:"))
        new_label = QLabel(self.new_name)
        new_label.setStyleSheet(
            "font-size: 12pt; padding: 5px; background-color: #e8f5e9;"
        )
        layout.addWidget(new_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)


class LEDIndicator(QLabel):
    """Realistic LED light indicator"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.color = QColor(128, 128, 128)  # Default gray (off)
        self.setStyleSheet("background-color: transparent;")

    def set_color(self, color_name):
        """Set LED color by name"""
        colors = {
            "green": QColor(0, 255, 0),
            "yellow": QColor(255, 255, 0),
            "red": QColor(255, 0, 0),
            "orange": QColor(255, 165, 0),
            "purple": QColor(128, 0, 128),
            "gray": QColor(128, 128, 128),
            "off": QColor(80, 80, 80),
        }
        self.color = colors.get(color_name.lower(), QColor(128, 128, 128))
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Draw the LED with a realistic look"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw outer ring (dark)
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawEllipse(2, 2, 16, 16)

        # Draw LED body with gradient effect
        if self.color.name() != "#808080":  # Not gray/off
            # Create gradient for 3D effect
            gradient = QBrush(self.color)
            painter.setBrush(gradient)
            painter.setPen(QPen(QColor(0, 0, 0, 0)))  # No border
            painter.drawEllipse(4, 4, 12, 12)

            # Add highlight for 3D effect
            highlight_color = QColor(255, 255, 255, 100)
            painter.setBrush(QBrush(highlight_color))
            painter.drawEllipse(5, 5, 5, 5)
        else:
            # Gray/off state
            painter.setBrush(QBrush(self.color))
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.drawEllipse(4, 4, 12, 12)


class FileNameDisplay(QTextEdit):
    """Widget to display and edit file name with highlighted non-standard ASCII characters"""

    text_edited = Signal(str)  # Signal emitted when user edits the text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(False)  # Make it editable
        self.setMaximumHeight(100)
        self.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        self.app_reference = None  # Will store reference to parent app
        self.ignore_chars = set()
        self.char_utils = None
        self._updating = False  # Flag to prevent recursive updates

        # Connect text change signal to update highlighting
        self.textChanged.connect(self.on_text_changed)

    def set_app_reference(self, app):
        """Set reference to parent app to access ignore_chars and char_utils"""
        self.app_reference = app
        if app:
            self.char_utils = app.char_utils

    def on_text_changed(self):
        """Update highlighting when text changes"""
        if self._updating:
            return

        text = self.toPlainText()
        if self.app_reference:
            ignore_chars = self.app_reference.get_ignore_chars()
            bad_chars = (
                self.char_utils.find_non_standard_ascii(text, ignore_chars)
                if self.char_utils
                else set()
            )
            bad_chars = bad_chars - ignore_chars
            self.update_highlighting(text, bad_chars, ignore_chars)
            self.text_edited.emit(text)

    def set_file_name(self, file_name: str, bad_chars: set, ignore_chars: set):
        """Display file name with bad characters highlighted"""
        self._updating = True  # Prevent recursive updates
        self.ignore_chars = ignore_chars

        # Add length restriction highlighting if platforms are selected
        if self.app_reference and self.app_reference.selected_platforms:
            length_bad_chars = self.app_reference.get_length_restriction_chars(
                file_name
            )
            bad_chars = bad_chars | length_bad_chars

        # Only update if the text is different to avoid cursor jumping
        current_text = self.toPlainText()
        if current_text != file_name:
            self.clear()
            self.update_highlighting(file_name, bad_chars, ignore_chars)

        self._updating = False

    def update_highlighting(self, file_name: str, bad_chars: set, ignore_chars: set):
        """Update highlighting for the given text"""
        # Set updating flag to prevent recursion
        self._updating = True

        # Store cursor position
        cursor = self.textCursor()
        old_position = cursor.position()

        # Clear and rebuild with highlighting
        self.clear()

        cursor = self.textCursor()
        format_normal = QTextCharFormat()
        format_normal.setFont(QFont("Arial", 18, QFont.Bold))

        format_highlight = QTextCharFormat()
        format_highlight.setBackground(QColor(255, 255, 0))  # Yellow highlight
        format_highlight.setFont(QFont("Arial", 18, QFont.Bold))

        # Check for length restrictions if app reference is available
        length_exceeded_chars = set()
        max_length = None
        if self.app_reference and self.app_reference.selected_platforms:
            length_exceeded_chars = self.app_reference.get_length_restriction_chars(
                file_name
            )
            # Find the most restrictive max_filename_length
            for platform_key in self.app_reference.selected_platforms:
                platform = PLATFORM_RESTRICTIONS.get(platform_key)
                if platform:
                    max_len = platform.get("max_filename_length")
                    if max_len and (max_length is None or max_len < max_length):
                        max_length = max_len

        for i, char in enumerate(file_name):
            # Highlight if character is in bad_chars (and not in ignore_chars) OR exceeds length limit
            should_highlight = char in bad_chars
            if should_highlight and ignore_chars:
                should_highlight = char not in ignore_chars

            # Also highlight if this character position exceeds length limit
            if not should_highlight and max_length and i >= max_length:
                should_highlight = True

            if should_highlight:
                cursor.insertText(char, format_highlight)
            else:
                cursor.insertText(char, format_normal)

        # Restore cursor position if possible
        if old_position <= len(file_name):
            cursor.setPosition(min(old_position, len(file_name)))
            self.setTextCursor(cursor)

        # Clear updating flag
        self._updating = False

    def get_text(self):
        """Get the current text from the display"""
        return self.toPlainText()


class PlatformButton(QPushButton):
    """Custom button that emits hover signals"""

    hover_entered = Signal(str)  # platform_key
    hover_left = Signal()

    def __init__(self, platform_key, text, parent=None):
        super().__init__(text, parent)
        self.platform_key = platform_key

    def enterEvent(self, event):
        super().enterEvent(event)
        self.hover_entered.emit(self.platform_key)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.hover_left.emit()


class DragDropWidget(QWidget):
    """Widget that accepts drag and drop of files/folders"""

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setStyleSheet("""
            QWidget {
                border: 3px dashed #aaa;
                border-radius: 10px;
                background-color: #f5f5f5;
            }
            QWidget:hover {
                border-color: #0066cc;
                background-color: #e3f2fd;
            }
        """)

        layout = QVBoxLayout()
        label = QLabel("Drag files or folders here")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16pt; color: #666;")
        layout.addWidget(label)
        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.files_dropped.emit(files)
        event.acceptProposedAction()


class NameDropApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.settings = QSettings("NameDrop", "NameDrop")
        self.current_file_path = None
        self.current_file_name = None
        self.processed_files = set()  # Track ignored files
        self.selected_platforms = set()  # Track selected platform compatibility buttons
        self.platform_selection_order = []  # Track order of platform selection (most recent first)
        self.compatibility_filtered_name = (
            None  # Store the filtered name based on selected platforms
        )

        self.char_utils = CharacterUtils()
        self.file_ops = FileOperations()

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the user interface from UI file"""
        # Load UI file using best practices for PySide6
        ui_file_path = Path(__file__).parent / "ui" / "main.ui"
        if ui_file_path.exists():
            loader = QUiLoader()
            ui_file = QFile(str(ui_file_path))

            if not ui_file.open(QIODevice.ReadOnly):
                print(f"Error: Cannot open UI file: {ui_file.errorString()}")
                self._init_ui_programmatic()
                return

            try:
                # Load the UI file - QUiLoader will create a QMainWindow from the UI file
                # We need to extract the central widget since we're already a QMainWindow
                loaded_ui = loader.load(ui_file, None)
                ui_file.close()

                if loaded_ui and hasattr(loaded_ui, "centralwidget"):
                    # Store reference to prevent garbage collection
                    self.ui = loaded_ui
                    # Extract the central widget from the loaded QMainWindow
                    central_widget = loaded_ui.centralwidget
                    # Reparent to our main window
                    central_widget.setParent(self)
                    self.setCentralWidget(central_widget)
                    layout = central_widget.layout()
                    # Hide the loaded QMainWindow - we only need its central widget
                    loaded_ui.hide()
                else:
                    raise Exception("Failed to load UI file or missing centralwidget")

                # Replace drag_drop widget with custom DragDropWidget
                drag_drop_index = None
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if (
                        item
                        and item.widget()
                        and item.widget().objectName() == "drag_drop"
                    ):
                        drag_drop_index = i
                        old_widget = item.widget()
                        break

                if drag_drop_index is not None:
                    layout.removeWidget(old_widget)
                    old_widget.deleteLater()
                    self.drag_drop = DragDropWidget()
                    self.drag_drop.files_dropped.connect(self.on_files_dropped)
                    layout.insertWidget(drag_drop_index, self.drag_drop)
                else:
                    # Fallback: create drag_drop if not found
                    self.drag_drop = DragDropWidget()
                    self.drag_drop.files_dropped.connect(self.on_files_dropped)
                    layout.insertWidget(1, self.drag_drop)

                # Replace file_name_display with custom FileNameDisplay
                file_name_display = self.ui.findChild(QTextEdit, "file_name_display")
                if file_name_display:
                    file_name_index = layout.indexOf(file_name_display)
                    layout.removeWidget(file_name_display)
                    file_name_display.deleteLater()
                    self.file_name_display = FileNameDisplay()
                    self.file_name_display.set_app_reference(self)
                    self.file_name_display.text_edited.connect(self.on_filename_edited)
                    layout.insertWidget(file_name_index, self.file_name_display)
                else:
                    self.file_name_display = FileNameDisplay()
                    self.file_name_display.set_app_reference(self)
                    self.file_name_display.text_edited.connect(self.on_filename_edited)
                    layout.addWidget(self.file_name_display)

                # Get button references
                self.random_btn = self.ui.findChild(QPushButton, "random_btn")
                self.rename_btn = self.ui.findChild(QPushButton, "rename_btn")

                # Connect button signals
                if self.random_btn:
                    self.random_btn.clicked.connect(self.generate_random_filename)
                if self.rename_btn:
                    self.rename_btn.setEnabled(False)
                    self.rename_btn.clicked.connect(self.rename_current_display)

                # Replace LED widgets with LEDIndicator widgets
                self._replace_led_widgets()

            except Exception as e:
                print(f"Error loading UI file: {e}")
                # Fallback to programmatic UI
                self._init_ui_programmatic()
                return  # Don't add missing sections, they're already in the programmatic UI
        else:
            # Fallback to programmatic UI if file doesn't exist
            self._init_ui_programmatic()
            return  # Don't add missing sections, they're already in the programmatic UI

        # Add missing sections that aren't in the UI file (only if UI file loaded successfully)
        if hasattr(self, "ui"):
            self._add_missing_sections()

        self.setWindowTitle("NameDrop")
        self.resize(800, 700)

    def _replace_led_widgets(self):
        """Replace QWidget LEDs with LEDIndicator widgets"""
        detection_group = self.ui.findChild(QGroupBox, "detection_group")
        if not detection_group:
            return

        detection_layout = detection_group.layout()
        platforms_layout = detection_layout.itemAt(0).layout()

        # Map of platform keys to UI widget names
        platform_map = {
            "Windows": ("windows_led", "windows_label"),
            "macOS": ("macos_led", "macos_label"),
            "Linux": ("linux_led", "linux_label"),
            "Cloud": ("cloud_led", "cloud_label"),
            "FAT32": ("fat32_led", "fat32_label"),
        }

        self.platform_leds = {}
        for platform_key, (led_name, label_name) in platform_map.items():
            led_widget = self.ui.findChild(QWidget, led_name)
            if led_widget:
                # Find parent layout
                parent = led_widget.parent()
                if parent:
                    layout = None
                    for i in range(platforms_layout.count()):
                        item = platforms_layout.itemAt(i)
                        if item and item.layout():
                            for j in range(item.layout().count()):
                                sub_item = item.layout().itemAt(j)
                                if sub_item and sub_item.widget() == led_widget:
                                    layout = item.layout()
                                    break
                            if layout:
                                break

                    if layout:
                        index = layout.indexOf(led_widget)
                        layout.removeWidget(led_widget)
                        led_widget.deleteLater()
                        led = LEDIndicator()
                        led.set_color("gray")
                        layout.insertWidget(index, led)
                        self.platform_leds[platform_key] = led

        # Replace legend LEDs
        legend_layout = detection_layout.itemAt(1).layout()
        legend_leds = {
            "green_led": "green",
            "yellow_led": "yellow",
            "red_led": "red",
            "orange_led": "orange",
            "purple_led": "purple",
        }

        for led_name, color in legend_leds.items():
            led_widget = self.ui.findChild(QWidget, led_name)
            if led_widget:
                # Find parent layout
                for i in range(legend_layout.count()):
                    item = legend_layout.itemAt(i)
                    if item and item.layout():
                        for j in range(item.layout().count()):
                            sub_item = item.layout().itemAt(j)
                            if sub_item and sub_item.widget() == led_widget:
                                layout = item.layout()
                                index = layout.indexOf(led_widget)
                                layout.removeWidget(led_widget)
                                led_widget.deleteLater()
                                led = LEDIndicator()
                                led.set_color(color)
                                led.setFixedSize(16, 16)
                                layout.insertWidget(index, led)
                                break

    def _add_missing_sections(self):
        """Add sections that are missing from the UI file"""
        if not hasattr(self, "ui"):
            return
        central_widget = self.ui.centralwidget
        if not central_widget:
            return
        layout = central_widget.layout()
        if not layout:
            return

        # Find detection_group to insert after it
        detection_group = self.ui.findChild(QGroupBox, "detection_group")
        detection_index = layout.indexOf(detection_group) if detection_group else -1

        # Platform compatibility section
        compatibility_group = QGroupBox("Make compatible with:")
        compatibility_layout = QVBoxLayout()

        # Platform buttons (horizontal)
        buttons_layout = QHBoxLayout()
        self.platform_buttons = {}
        platform_keys = ["Everything", "Windows", "macOS", "Linux", "Cloud", "FAT32"]

        for platform_key in platform_keys:
            btn = PlatformButton(
                platform_key, PLATFORM_RESTRICTIONS[platform_key]["name"]
            )
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 15px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background-color: #f5f5f5;
                }
                QPushButton:hover {
                    background-color: #e3f2fd;
                    border-color: #0066cc;
                }
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                    border-color: #45a049;
                }
            """)
            btn.clicked.connect(
                lambda checked, key=platform_key: self.on_platform_button_clicked(
                    key, checked
                )
            )
            btn.hover_entered.connect(self.on_platform_button_hover)
            btn.hover_left.connect(self.on_platform_button_leave)
            buttons_layout.addWidget(btn)
            self.platform_buttons[platform_key] = btn

        buttons_layout.addStretch()
        compatibility_layout.addLayout(buttons_layout)

        # Information display area
        self.compatibility_info_label = QLabel(
            "Hover over a platform button to see restrictions, or click to apply filters."
        )
        self.compatibility_info_label.setWordWrap(True)
        self.compatibility_info_label.setTextFormat(Qt.RichText)
        self.compatibility_info_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                min-height: 80px;
            }
        """)
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.compatibility_info_label)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(100)
        scroll_area.setMaximumHeight(200)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        compatibility_layout.addWidget(scroll_area)

        compatibility_group.setLayout(compatibility_layout)
        insert_index = detection_index + 1 if detection_index >= 0 else layout.count()
        layout.insertWidget(insert_index, compatibility_group)

        # Ignore common characters group
        ignore_group = QGroupBox("Ignore Common Special Characters")
        ignore_layout = QVBoxLayout()
        self.ignore_common_check = QCheckBox("Ignore common special characters")
        self.ignore_common_check.setChecked(True)
        self.ignore_common_check.stateChanged.connect(self.on_file_selected)
        ignore_layout.addWidget(self.ignore_common_check)

        self.ignore_chars_edit = QLineEdit(self.char_utils.get_common_allowed_chars())
        self.ignore_chars_edit.setPlaceholderText(
            "Characters to ignore (separated by spaces)"
        )
        self.ignore_chars_edit.textChanged.connect(self.save_allowed_chars)
        self.ignore_chars_edit.textChanged.connect(self.on_file_selected)
        ignore_layout.addWidget(QLabel("Allowed characters:"))
        ignore_layout.addWidget(self.ignore_chars_edit)
        ignore_group.setLayout(ignore_layout)
        layout.insertWidget(insert_index + 1, ignore_group)

        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        self.prompt_check = QCheckBox("Prompt before renaming")
        self.prompt_check.setChecked(True)
        options_layout.addWidget(self.prompt_check)

        self.backup_check = QCheckBox("Always make backup first")
        self.backup_check.setChecked(True)
        options_layout.addWidget(self.backup_check)

        options_group.setLayout(options_layout)
        layout.insertWidget(insert_index + 2, options_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.ignore_btn = QPushButton("Ignore File")
        self.ignore_btn.clicked.connect(self.ignore_file)
        self.ignore_btn.setEnabled(False)
        button_layout.addWidget(self.ignore_btn)

        self.auto_rename_btn = QPushButton("Auto Rename")
        self.auto_rename_btn.clicked.connect(self.auto_rename)
        self.auto_rename_btn.setEnabled(False)
        button_layout.addWidget(self.auto_rename_btn)

        self.remove_btn = QPushButton("REMOVE bad characters")
        self.remove_btn.clicked.connect(self.remove_bad_chars)
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)

        self.replace_btn = QPushButton("REPLACE bad characters")
        self.replace_btn.clicked.connect(self.replace_bad_chars)
        self.replace_btn.setEnabled(False)
        button_layout.addWidget(self.replace_btn)

        self.edit_btn = QPushButton("Edit Name")
        self.edit_btn.clicked.connect(self.edit_name)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)

        layout.insertLayout(insert_index + 3, button_layout)

        # Status label
        self.status_label = QLabel("Ready - Drop a file or folder")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e3f2fd;")
        layout.insertWidget(insert_index + 4, self.status_label)

    def _init_ui_programmatic(self):
        """Fallback: Initialize UI programmatically if UI file can't be loaded"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Title
        title = QLabel("NameDrop")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # Drag and drop area
        self.drag_drop = DragDropWidget()
        self.drag_drop.files_dropped.connect(self.on_files_dropped)
        layout.addWidget(self.drag_drop)

        # File name display with highlighting and RENAME button
        filename_header_layout = QHBoxLayout()
        filename_header_layout.addWidget(
            QLabel("File name (non-standard ASCII highlighted):")
        )
        filename_header_layout.addStretch()
        self.random_btn = QPushButton("RANDOM")
        self.random_btn.setStyleSheet("""
            QPushButton {
                font-size: 14pt;
                font-weight: bold;
                padding: 10px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.random_btn.clicked.connect(self.generate_random_filename)
        filename_header_layout.addWidget(self.random_btn)
        self.rename_btn = QPushButton("RENAME")
        self.rename_btn.setStyleSheet("""
            QPushButton {
                font-size: 16pt;
                font-weight: bold;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.rename_btn.setEnabled(False)
        # RENAME button can rename either compatibility-filtered name or manually edited name
        self.rename_btn.clicked.connect(self.rename_current_display)
        filename_header_layout.addWidget(self.rename_btn)
        layout.addLayout(filename_header_layout)

        self.file_name_display = FileNameDisplay()
        self.file_name_display.set_app_reference(self)  # Give it reference to app
        self.file_name_display.text_edited.connect(self.on_filename_edited)
        layout.addWidget(self.file_name_display)

        # Detection section with LED indicators
        detection_group = QGroupBox("Detecting..")
        detection_layout = QVBoxLayout()

        # Platform indicators with LEDs
        platforms_layout = QVBoxLayout()
        self.platform_leds = {}
        platform_names = [
            ("Windows", "Windows"),
            ("macOS", "macOS"),
            ("Linux", "Linux"),
            ("Cloud", "Cloud Drives"),
            ("FAT32", "FAT32"),
        ]

        for key, label_text in platform_names:
            platform_row = QHBoxLayout()
            platform_label = QLabel(label_text + ":")
            platform_label.setMinimumWidth(100)
            platform_row.addWidget(platform_label)

            led = LEDIndicator()
            led.set_color("gray")  # Start as off/gray
            platform_row.addWidget(led)
            platform_row.addStretch()

            platforms_layout.addLayout(platform_row)
            self.platform_leds[key] = led

        detection_layout.addLayout(platforms_layout)

        # Legend/key
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Key:"))

        legend_items = [
            ("Green", "green", "OK"),
            ("Yellow", "yellow", "non-standard chars"),
            ("Red", "red", "Invalid chars"),
            ("Orange", "orange", "Problematic"),
            ("Purple", "purple", "Restrictions"),
        ]

        for color_name, color_code, description in legend_items:
            legend_item = QHBoxLayout()
            led = LEDIndicator()
            led.set_color(color_code)
            led.setFixedSize(16, 16)
            legend_item.addWidget(led)
            legend_item.addWidget(QLabel(f"{color_name}: {description}"))
            legend_layout.addLayout(legend_item)
            legend_layout.addSpacing(10)

        legend_layout.addStretch()
        detection_layout.addLayout(legend_layout)

        detection_group.setLayout(detection_layout)
        layout.addWidget(detection_group)

        # Platform compatibility section
        compatibility_group = QGroupBox("Make compatible with:")
        compatibility_layout = QVBoxLayout()

        # Platform buttons (horizontal)
        buttons_layout = QHBoxLayout()
        self.platform_buttons = {}
        platform_keys = ["Everything", "Windows", "macOS", "Linux", "Cloud", "FAT32"]

        for platform_key in platform_keys:
            btn = PlatformButton(
                platform_key, PLATFORM_RESTRICTIONS[platform_key]["name"]
            )
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 15px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    background-color: #f5f5f5;
                }
                QPushButton:hover {
                    background-color: #e3f2fd;
                    border-color: #0066cc;
                }
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                    border-color: #45a049;
                }
            """)
            btn.clicked.connect(
                lambda checked, key=platform_key: self.on_platform_button_clicked(
                    key, checked
                )
            )
            btn.hover_entered.connect(self.on_platform_button_hover)
            btn.hover_left.connect(self.on_platform_button_leave)
            buttons_layout.addWidget(btn)
            self.platform_buttons[platform_key] = btn

        buttons_layout.addStretch()
        compatibility_layout.addLayout(buttons_layout)

        # Information display area (shows excluded/problematic characters) - scrollable
        self.compatibility_info_label = QLabel(
            "Hover over a platform button to see restrictions, or click to apply filters."
        )
        self.compatibility_info_label.setWordWrap(True)
        self.compatibility_info_label.setTextFormat(Qt.RichText)  # Enable HTML
        self.compatibility_info_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                min-height: 80px;
            }
        """)
        # Wrap in scroll area for long content
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.compatibility_info_label)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(100)
        scroll_area.setMaximumHeight(200)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        compatibility_layout.addWidget(scroll_area)

        compatibility_group.setLayout(compatibility_layout)
        layout.addWidget(compatibility_group)

        # Ignore common characters group
        ignore_group = QGroupBox("Ignore Common Special Characters")
        ignore_layout = QVBoxLayout()
        self.ignore_common_check = QCheckBox("Ignore common special characters")
        self.ignore_common_check.setChecked(True)
        self.ignore_common_check.stateChanged.connect(self.on_file_selected)
        ignore_layout.addWidget(self.ignore_common_check)

        self.ignore_chars_edit = QLineEdit(self.char_utils.get_common_allowed_chars())
        self.ignore_chars_edit.setPlaceholderText(
            "Characters to ignore (separated by spaces)"
        )
        # Auto-save when text changes so it persists even if app crashes
        self.ignore_chars_edit.textChanged.connect(self.save_allowed_chars)
        # Update display when ignore chars change (but only if we have a file selected)
        # Note: We use on_file_selected which will safely update the display
        self.ignore_chars_edit.textChanged.connect(self.on_file_selected)
        ignore_layout.addWidget(QLabel("Allowed characters:"))
        ignore_layout.addWidget(self.ignore_chars_edit)
        ignore_group.setLayout(ignore_layout)
        layout.addWidget(ignore_group)

        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        self.prompt_check = QCheckBox("Prompt before renaming")
        self.prompt_check.setChecked(True)
        options_layout.addWidget(self.prompt_check)

        self.backup_check = QCheckBox("Always make backup first")
        self.backup_check.setChecked(True)
        options_layout.addWidget(self.backup_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.ignore_btn = QPushButton("Ignore File")
        self.ignore_btn.clicked.connect(self.ignore_file)
        self.ignore_btn.setEnabled(False)
        button_layout.addWidget(self.ignore_btn)

        self.auto_rename_btn = QPushButton("Auto Rename")
        self.auto_rename_btn.clicked.connect(self.auto_rename)
        self.auto_rename_btn.setEnabled(False)
        button_layout.addWidget(self.auto_rename_btn)

        self.remove_btn = QPushButton("REMOVE bad characters")
        self.remove_btn.clicked.connect(self.remove_bad_chars)
        self.remove_btn.setEnabled(False)
        button_layout.addWidget(self.remove_btn)

        self.replace_btn = QPushButton("REPLACE bad characters")
        self.replace_btn.clicked.connect(self.replace_bad_chars)
        self.replace_btn.setEnabled(False)
        button_layout.addWidget(self.replace_btn)

        self.edit_btn = QPushButton("Edit Name")
        self.edit_btn.clicked.connect(self.edit_name)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)

        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("Ready - Drop a file or folder")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e3f2fd;")
        layout.addWidget(self.status_label)

        self.setWindowTitle("NameDrop")
        self.resize(800, 700)

    def load_settings(self):
        """Load saved settings"""
        # Window position and size
        pos = self.settings.value("window_position", QPoint(100, 100))
        size = self.settings.value("window_size", QSize(800, 700))
        screen = self.settings.value("screen", 0, type=int)

        # Validate and clamp window position BEFORE moving to prevent Qt warnings
        screens = QApplication.screens()
        if screens:
            primary_screen = screens[0]
            screen_rect = primary_screen.geometry()

            # Clamp position to ensure window top-left corner is within screen bounds
            # This prevents Qt warnings about positions outside known screens
            x = max(
                screen_rect.left(), min(pos.x(), screen_rect.right() - size.width())
            )
            y = max(
                screen_rect.top(), min(pos.y(), screen_rect.bottom() - size.height())
            )
            pos = QPoint(x, y)

        self.move(pos)
        self.resize(size)

        # Move to saved screen if available
        if screens and 0 <= screen < len(screens):
            screen_geometry = screens[screen].geometry()
            window_geometry = self.frameGeometry()
            window_geometry.moveCenter(screen_geometry.center())
            new_pos = window_geometry.topLeft()

            # Validate the new position before moving
            x = max(
                screen_geometry.left(),
                min(new_pos.x(), screen_geometry.right() - window_geometry.width()),
            )
            y = max(
                screen_geometry.top(),
                min(new_pos.y(), screen_geometry.bottom() - window_geometry.height()),
            )
            self.move(QPoint(x, y))

        # Checkbox states
        self.prompt_check.setChecked(
            self.settings.value("prompt_before_rename", True, type=bool)
        )
        self.backup_check.setChecked(
            self.settings.value("always_backup", True, type=bool)
        )
        self.ignore_common_check.setChecked(
            self.settings.value("ignore_common_chars", True, type=bool)
        )

        # Ignore characters
        ignore_chars = self.settings.value(
            "ignore_chars", self.char_utils.get_common_allowed_chars()
        )
        self.ignore_chars_edit.setText(ignore_chars)

    def save_allowed_chars(self):
        """Save allowed characters immediately when changed"""
        self.settings.setValue("ignore_chars", self.ignore_chars_edit.text())
        self.settings.sync()  # Force immediate write to disk

    def save_settings(self):
        """Save current settings"""
        pos = self.pos()
        size = self.size()
        window_geometry = self.frameGeometry()

        # Validate and clamp position before saving to prevent invalid positions
        screens = QApplication.screens()
        if screens:
            # Check if window center is within any screen
            window_center = window_geometry.center()
            is_valid = False
            for screen in screens:
                if screen.geometry().contains(window_center):
                    is_valid = True
                    break

            # If window is outside all screens, clamp position to primary screen
            if not is_valid and screens:
                primary_screen = screens[0]
                screen_rect = primary_screen.geometry()

                # Clamp position to ensure window is visible
                x = max(
                    screen_rect.left(),
                    min(pos.x(), screen_rect.right() - window_geometry.width()),
                )
                y = max(
                    screen_rect.top(),
                    min(pos.y(), screen_rect.bottom() - window_geometry.height()),
                )
                pos = QPoint(x, y)

        self.settings.setValue("window_position", pos)
        self.settings.setValue("window_size", size)

        # Find which screen the window is on (using current geometry)
        screen_num = 0
        if screens:
            current_geometry = self.frameGeometry()
            for i, screen in enumerate(screens):
                if screen.geometry().contains(current_geometry.center()):
                    screen_num = i
                    break
        self.settings.setValue("screen", screen_num)

        self.settings.setValue("prompt_before_rename", self.prompt_check.isChecked())
        self.settings.setValue("always_backup", self.backup_check.isChecked())
        self.settings.setValue(
            "ignore_common_chars", self.ignore_common_check.isChecked()
        )
        self.settings.setValue("ignore_chars", self.ignore_chars_edit.text())

    def closeEvent(self, event):
        """Save settings when closing"""
        self.save_settings()
        event.accept()

    def on_files_dropped(self, files):
        """Handle dropped files"""
        if not files:
            return

        # Filter to only existing files/folders
        valid_files = [f for f in files if os.path.exists(f)]

        if not valid_files:
            self.status_label.setText("Error: No valid files found")
            self.status_label.setStyleSheet(
                "padding: 5px; background-color: #ffebee; color: #c62828;"
            )
            return

        # Handle first file (could be extended to support batch processing)
        file_path = valid_files[0]
        if len(valid_files) > 1:
            self.status_label.setText(
                f"Processing first of {len(valid_files)} files. Drop again for next file."
            )
            self.status_label.setStyleSheet("padding: 5px; background-color: #fff3e0;")

        if os.path.exists(file_path):
            self.current_file_path = file_path
            self.current_file_name = os.path.basename(file_path)
            self.compatibility_filtered_name = None
            # Reset platform selections when new file is dropped
            for btn in self.platform_buttons.values():
                btn.setChecked(False)
            self.selected_platforms = set()
            self.platform_selection_order = []
            self.update_compatibility_info()
            self.on_file_selected()
        else:
            self.status_label.setText(f"Error: File not found - {file_path}")
            self.status_label.setStyleSheet(
                "padding: 5px; background-color: #ffebee; color: #c62828;"
            )

    def on_file_selected(self):
        """Analyze selected file and update display"""
        if not self.current_file_path:
            return

        # Check if file was ignored
        if self.current_file_path in self.processed_files:
            self.status_label.setText("This file has been ignored")
            self.status_label.setStyleSheet("padding: 5px; background-color: #fff3e0;")
            self.ignore_btn.setEnabled(False)
            self.auto_rename_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)
            self.replace_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.file_name_display.set_file_name(self.current_file_name, set(), set())
            return

        # Get ignore characters - include all characters from the field
        ignore_chars = self.get_ignore_chars()

        # Find bad characters (excluding ignore_chars)
        bad_chars = self.char_utils.find_non_standard_ascii(
            self.current_file_name, ignore_chars
        )

        # Remove any ignore_chars from bad_chars to ensure they're never highlighted
        bad_chars = bad_chars - ignore_chars

        # Update LED indicators
        self.update_platform_leds(self.current_file_name)

        # Apply compatibility filter if platforms are selected
        if self.selected_platforms:
            self.apply_compatibility_filter()
        else:
            # Add length restriction highlighting if needed
            if self.selected_platforms:
                length_bad_chars = self.get_length_restriction_chars(
                    self.current_file_name
                )
                bad_chars = bad_chars | length_bad_chars
            # Update display
            self.file_name_display.set_file_name(
                self.current_file_name, bad_chars, ignore_chars
            )

        # Enable buttons if there are bad characters
        has_bad_chars = bool(bad_chars - ignore_chars)
        self.auto_rename_btn.setEnabled(has_bad_chars)
        self.remove_btn.setEnabled(has_bad_chars)
        self.replace_btn.setEnabled(has_bad_chars)
        self.edit_btn.setEnabled(True)
        self.ignore_btn.setEnabled(True)

        if has_bad_chars:
            self.status_label.setText(
                f"Found {len(bad_chars - ignore_chars)} non-standard ASCII character(s)"
            )
            self.status_label.setStyleSheet("padding: 5px; background-color: #fff3e0;")
        else:
            self.status_label.setText(
                "File name contains only standard ASCII characters"
            )
            self.status_label.setStyleSheet("padding: 5px; background-color: #e8f5e9;")

    def ignore_file(self):
        """Add current file to ignored list"""
        if self.current_file_path:
            self.processed_files.add(self.current_file_path)
            self.status_label.setText("File ignored")
            self.status_label.setStyleSheet("padding: 5px; background-color: #fff3e0;")
            self.ignore_btn.setEnabled(False)
            self.auto_rename_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)
            self.replace_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)

    def update_display_for_ignore_chars_change(self):
        """Update the display when ignore characters change (to avoid recursion)"""
        if not self.current_file_name:
            return

        # Get ignore characters - include all characters from the field
        ignore_chars = self.get_ignore_chars()

        # Find bad characters (excluding ignore_chars)
        bad_chars = self.char_utils.find_non_standard_ascii(
            self.current_file_name, ignore_chars
        )

        # Remove any ignore_chars from bad_chars to ensure they're never highlighted
        bad_chars = bad_chars - ignore_chars

        # Update LED indicators
        self.update_platform_leds(self.current_file_name)

        # Apply compatibility filter if platforms are selected
        if self.selected_platforms:
            self.apply_compatibility_filter()
        else:
            # Add length restriction highlighting if needed
            if self.selected_platforms:
                length_bad_chars = self.get_length_restriction_chars(
                    self.current_file_name
                )
                bad_chars = bad_chars | length_bad_chars
            # Update display
            self.file_name_display.set_file_name(
                self.current_file_name, bad_chars, ignore_chars
            )

    def get_ignore_chars(self):
        """Get set of characters to ignore"""
        ignore_chars = set()
        if self.ignore_common_check.isChecked():
            ignore_text = self.ignore_chars_edit.text()
            # Include all characters from the field, including spaces if they're in the field
            ignore_chars = set(char for char in ignore_text)
        return ignore_chars

    def get_length_restriction_chars(self, file_name: str):
        """Get set of characters that exceed length restrictions for selected platforms"""
        if not self.selected_platforms or not file_name:
            return set()

        # Find the most restrictive max_filename_length from selected platforms
        min_max_length = None
        for platform_key in self.selected_platforms:
            platform = PLATFORM_RESTRICTIONS.get(platform_key)
            if platform:
                max_len = platform.get("max_filename_length")
                if max_len and (min_max_length is None or max_len < min_max_length):
                    min_max_length = max_len

        # If filename exceeds the limit, highlight characters beyond the limit
        if min_max_length and len(file_name) > min_max_length:
            # Return set of characters at positions beyond the limit
            # We'll highlight by position, not by character value
            return set(file_name[min_max_length:])

        return set()

    def get_combined_restrictions(self, platforms):
        """Get combined restrictions from selected platforms"""
        if not platforms:
            return {
                "excluded_chars": set(),
                "problematic_chars": set(),
                "excluded_positions": [],
            }

        excluded_chars = set()
        problematic_chars = set()
        excluded_positions = []

        for platform_key in platforms:
            platform = PLATFORM_RESTRICTIONS[platform_key]
            excluded_chars.update(platform["excluded_chars"])
            problematic_chars.update(platform["problematic_chars"])
            excluded_positions.extend(platform["excluded_positions"])

        # Remove duplicates from excluded_positions
        excluded_positions = list(set(excluded_positions))

        return {
            "excluded_chars": excluded_chars,
            "problematic_chars": problematic_chars,
            "excluded_positions": excluded_positions,
        }

    def format_restrictions_info(self, platforms):
        """Format restriction information for display in selection order (most recent first)"""
        if not platforms:
            return "No platforms selected."

        lines = []
        # Display in selection order (most recently selected first)
        # The platform_selection_order list already has most recent first
        # Filter to only show platforms that are currently selected
        display_order = [p for p in self.platform_selection_order if p in platforms]
        # Add any platforms that are selected but not in the order list (shouldn't happen, but safety)
        for p in platforms:
            if p not in display_order:
                display_order.insert(0, p)  # Add to front if missing

        for platform_key in display_order:
            platform = PLATFORM_RESTRICTIONS[platform_key]
            lines.append(f"<b>{platform['name']}:</b>")

            # Excluded characters
            if platform["excluded_chars"]:
                excluded_list = sorted(platform["excluded_chars"])
                excluded_display = " ".join(
                    f"<code>{c}</code>" if c != " " else "<code>space</code>"
                    for c in excluded_list
                )
                lines.append(f"  • <b>Excluded characters:</b> {excluded_display}")

            # Problematic characters
            if platform["problematic_chars"]:
                problematic_list = sorted(platform["problematic_chars"])
                problematic_display = " ".join(
                    f"<code>{c}</code>" for c in problematic_list
                )
                lines.append(
                    f"  • <b>Problematic characters:</b> {problematic_display}"
                )

            # Position restrictions
            position_descriptions = {
                "trailing_space": "Trailing space",
                "trailing_period": "Trailing period",
                "leading_space": "Leading space",
                "leading_period": "Leading period",
            }
            if platform["excluded_positions"]:
                positions = [
                    position_descriptions.get(p, p)
                    for p in platform["excluded_positions"]
                ]
                lines.append(
                    f"  • <b>Position restrictions:</b> {', '.join(positions)}"
                )

            # Reserved names
            if platform.get("reserved_names"):
                reserved_list = sorted(platform["reserved_names"])
                reserved_display = ", ".join(
                    f"<code>{name}</code>" for name in reserved_list[:10]
                )  # Show first 10
                if len(reserved_list) > 10:
                    reserved_display += f" <i>(and {len(reserved_list) - 10} more)</i>"
                lines.append(f"  • <b>Reserved names:</b> {reserved_display}")

            # Length restrictions
            length_info = []
            if platform.get("max_filename_length"):
                length_info.append(
                    f"Max filename: {platform['max_filename_length']} characters"
                )
            if platform.get("max_path_length"):
                length_info.append(
                    f"Max path: {platform['max_path_length']} characters"
                )
            if length_info:
                lines.append(
                    f"  • <b>Length restrictions:</b> {', '.join(length_info)}"
                )

            # Additional restrictions
            if platform.get("additional_restrictions"):
                addl_desc = {
                    "no_space_period_after_ext": "Cannot end with space/period before extension",
                    "no_spaces_only": "Cannot consist solely of spaces",
                }
                addl_list = [
                    addl_desc.get(r, r) for r in platform["additional_restrictions"]
                ]
                lines.append(
                    f"  • <b>Additional restrictions:</b> {', '.join(addl_list)}"
                )

            lines.append(f"  • <i>{platform['description']}</i>")
            lines.append("")

        return "<br>".join(lines)

    def on_platform_button_hover(self, platform_key):
        """Show platform restrictions on hover"""
        platform = PLATFORM_RESTRICTIONS[platform_key]
        info = f"<b>{platform['name']}:</b><br><br>"

        if platform["excluded_chars"]:
            excluded_list = sorted(platform["excluded_chars"])
            excluded_display = " ".join(
                f"<code>{c}</code>" if c != " " else "<code>space</code>"
                for c in excluded_list
            )
            info += f"<b>Excluded characters:</b> {excluded_display}<br>"

        if platform["problematic_chars"]:
            problematic_list = sorted(platform["problematic_chars"])
            problematic_display = " ".join(
                f"<code>{c}</code>" for c in problematic_list
            )
            info += f"<b>Problematic characters:</b> {problematic_display}<br>"

        position_descriptions = {
            "trailing_space": "Trailing space",
            "trailing_period": "Trailing period",
            "leading_space": "Leading space",
            "leading_period": "Leading period",
        }
        if platform["excluded_positions"]:
            positions = [
                position_descriptions.get(p, p) for p in platform["excluded_positions"]
            ]
            info += f"<b>Position restrictions:</b> {', '.join(positions)}<br>"

        # Reserved names
        if platform.get("reserved_names"):
            reserved_list = sorted(platform["reserved_names"])
            reserved_display = ", ".join(
                f"<code>{name}</code>" for name in reserved_list[:10]
            )
            if len(reserved_list) > 10:
                reserved_display += f" <i>(and {len(reserved_list) - 10} more)</i>"
            info += f"<b>Reserved names:</b> {reserved_display}<br>"

        # Length restrictions
        length_info = []
        if platform.get("max_filename_length"):
            length_info.append(
                f"Max filename: {platform['max_filename_length']} characters"
            )
        if platform.get("max_path_length"):
            length_info.append(f"Max path: {platform['max_path_length']} characters")
        if length_info:
            info += f"<b>Length restrictions:</b> {', '.join(length_info)}<br>"

        # Additional restrictions
        if platform.get("additional_restrictions"):
            addl_desc = {
                "no_space_period_after_ext": "Cannot end with space/period before extension",
                "no_spaces_only": "Cannot consist solely of spaces",
            }
            addl_list = [
                addl_desc.get(r, r) for r in platform["additional_restrictions"]
            ]
            info += f"<b>Additional restrictions:</b> {', '.join(addl_list)}<br>"

        info += f"<br><i>{platform['description']}</i>"
        self.compatibility_info_label.setText(info)

    def on_platform_button_leave(self):
        """Clear hover info or show selected platforms"""
        if self.selected_platforms:
            self.update_compatibility_info()
        else:
            self.compatibility_info_label.setText(
                "Hover over a platform button to see restrictions, or click to apply filters."
            )

    def on_platform_button_clicked(self, platform_key, checked):
        """Handle platform button click"""
        if platform_key == "Everything":
            # "Everything" checks all other buttons
            if checked:
                # Check all other platform buttons
                for key in self.platform_buttons:
                    if key != "Everything":
                        self.platform_buttons[key].setChecked(True)
                self.selected_platforms = set(self.platform_buttons.keys())
                # Update selection order - "Everything" first, then others
                self.platform_selection_order = ["Everything"] + [
                    k for k in self.platform_buttons.keys() if k != "Everything"
                ]
            else:
                # Uncheck all buttons
                for btn in self.platform_buttons.values():
                    btn.setChecked(False)
                self.selected_platforms = set()
                self.platform_selection_order = []
        else:
            # Uncheck "Everything" if selecting specific platforms
            if checked:
                self.platform_buttons["Everything"].setChecked(False)
                if "Everything" in self.selected_platforms:
                    self.selected_platforms.remove("Everything")
                    # Remove "Everything" from selection order
                    if "Everything" in self.platform_selection_order:
                        self.platform_selection_order.remove("Everything")
                self.selected_platforms.add(platform_key)
                # Add to front of selection order (most recent first)
                if platform_key in self.platform_selection_order:
                    self.platform_selection_order.remove(platform_key)
                self.platform_selection_order.insert(0, platform_key)
            else:
                self.selected_platforms.discard(platform_key)
                # Remove from selection order
                if platform_key in self.platform_selection_order:
                    self.platform_selection_order.remove(platform_key)
                # If all specific platforms are unchecked, uncheck "Everything" too
                if not self.selected_platforms:
                    self.platform_buttons["Everything"].setChecked(False)
                    self.platform_selection_order = []

        self.update_compatibility_info()
        self.apply_compatibility_filter()

    def update_compatibility_info(self):
        """Update the compatibility info display"""
        if self.selected_platforms:
            info = self.format_restrictions_info(self.selected_platforms)
            self.compatibility_info_label.setText(info)
        else:
            self.compatibility_info_label.setText(
                "Hover over a platform button to see restrictions, or click to apply filters."
            )

    def apply_compatibility_filter(self):
        """Apply compatibility filter to the current filename"""
        if not self.current_file_name:
            self.compatibility_filtered_name = None
            self.rename_btn.setEnabled(False)
            return

        if not self.selected_platforms:
            self.compatibility_filtered_name = None
            self.rename_btn.setEnabled(False)
            if self.current_file_name:
                # Show original filename
                ignore_chars = self.get_ignore_chars()
                bad_chars = self.char_utils.find_non_standard_ascii(
                    self.current_file_name, ignore_chars
                )
                self.file_name_display.set_file_name(
                    self.current_file_name, bad_chars, ignore_chars
                )
            return

        restrictions = self.get_combined_restrictions(self.selected_platforms)
        ignore_chars = self.get_ignore_chars()  # Get characters to ignore
        filtered_name = self.current_file_name

        # Remove excluded characters (spaces are NOT excluded - they're allowed in filenames)
        # Only remove leading/trailing spaces based on position restrictions
        # Don't remove characters that are in the ignore_chars list
        for char in restrictions["excluded_chars"]:
            # Never remove spaces - they're allowed characters, only position matters
            # Never remove characters that are in the ignore list
            if char != " " and char not in ignore_chars:
                filtered_name = filtered_name.replace(char, "")

        # Remove problematic characters (spaces are NOT problematic)
        # Don't remove characters that are in the ignore_chars list
        for char in restrictions["problematic_chars"]:
            # Never remove spaces - they're allowed characters
            # Never remove characters that are in the ignore list
            if char != " " and char not in ignore_chars:
                filtered_name = filtered_name.replace(char, "")

        # Handle position restrictions - only remove spaces at specific positions
        if "trailing_space" in restrictions["excluded_positions"]:
            filtered_name = filtered_name.rstrip(" ")
        if "trailing_period" in restrictions["excluded_positions"]:
            # Remove trailing periods but keep the one before extension (if it exists)
            # Split filename and extension
            if "." in filtered_name:
                name_part, ext_part = filtered_name.rsplit(".", 1)
                # Remove trailing periods from name part only
                name_part = name_part.rstrip(".")
                filtered_name = (
                    name_part + "." + ext_part
                    if name_part or ext_part
                    else filtered_name.rstrip(".")
                )
            else:
                # No extension, remove all trailing periods
                filtered_name = filtered_name.rstrip(".")
        if "leading_space" in restrictions["excluded_positions"]:
            filtered_name = filtered_name.lstrip(" ")
        if "leading_period" in restrictions["excluded_positions"]:
            filtered_name = filtered_name.lstrip(".")

        self.compatibility_filtered_name = filtered_name

        # Update display with filtered name
        ignore_chars = self.get_ignore_chars()  # Get ignore chars once

        if filtered_name != self.current_file_name:
            # Show what was removed
            # Find characters that were removed
            removed_chars = set()
            for char in self.current_file_name:
                if char not in filtered_name:
                    removed_chars.add(char)

            # Show filtered name with removed characters highlighted
            bad_chars = self.char_utils.find_non_standard_ascii(
                filtered_name, ignore_chars
            )
            bad_chars.update(
                removed_chars
            )  # Also highlight removed chars if they appear in original
            # Remove ignore_chars from bad_chars to ensure they're never highlighted
            bad_chars = bad_chars - ignore_chars
            self.file_name_display.set_file_name(filtered_name, bad_chars, ignore_chars)
            self.rename_btn.setEnabled(True)
        else:
            # No changes needed
            bad_chars = self.char_utils.find_non_standard_ascii(
                filtered_name, ignore_chars
            )
            # Remove ignore_chars from bad_chars to ensure they're never highlighted
            bad_chars = bad_chars - ignore_chars
            self.file_name_display.set_file_name(filtered_name, bad_chars, ignore_chars)
            self.rename_btn.setEnabled(False)

        # Update LED indicators with filtered name
        self.update_platform_leds(filtered_name)

    def update_platform_leds(self, file_name: str = None):
        """Update LED indicators based on filename compatibility with each platform"""
        if file_name is None:
            file_name = (
                self.file_name_display.get_text()
                if hasattr(self.file_name_display, "get_text")
                else self.current_file_name
            )

        if not file_name:
            # No filename, set all to gray
            for led in self.platform_leds.values():
                led.set_color("gray")
            return

        ignore_chars = self.get_ignore_chars()

        # Check each platform
        for platform_key, led in self.platform_leds.items():
            platform = PLATFORM_RESTRICTIONS.get(platform_key)
            if not platform:
                led.set_color("gray")
                continue

            # Check for invalid/excluded characters
            excluded_chars = platform["excluded_chars"] - ignore_chars
            problematic_chars = platform["problematic_chars"] - ignore_chars
            excluded_positions = platform["excluded_positions"]
            reserved_names = platform.get("reserved_names", set())
            max_path_length = platform.get("max_path_length", None)
            additional_restrictions = platform.get("additional_restrictions", [])

            has_excluded = any(char in file_name for char in excluded_chars)
            has_problematic = any(char in file_name for char in problematic_chars)
            has_position_issues = False
            has_reserved_name = False
            has_additional_restrictions = False

            # Check reserved names (case-insensitive for Windows/Cloud)
            if reserved_names:
                # Get filename without extension for reserved name check
                if "." in file_name:
                    name_without_ext = file_name.rsplit(".", 1)[0].upper()
                else:
                    name_without_ext = file_name.upper()

                # Check if name matches any reserved name (case-insensitive)
                if name_without_ext in {name.upper() for name in reserved_names}:
                    has_reserved_name = True

            # Check position restrictions
            if "trailing_space" in excluded_positions and file_name.endswith(" "):
                has_position_issues = True
            if "trailing_period" in excluded_positions:
                # Check for trailing periods (but not the extension separator)
                if "." in file_name:
                    name_part = file_name.rsplit(".", 1)[0]
                    if name_part.endswith(".") or file_name.endswith("."):
                        has_position_issues = True
                elif file_name.endswith("."):
                    has_position_issues = True
            if "leading_space" in excluded_positions and file_name.startswith(" "):
                has_position_issues = True
            if "leading_period" in excluded_positions and file_name.startswith("."):
                has_position_issues = True

            # Check additional restrictions
            if "no_space_period_after_ext" in additional_restrictions:
                # Filename cannot end with a space or period followed by an extension
                if "." in file_name:
                    name_part, ext_part = file_name.rsplit(".", 1)
                    if name_part.endswith(" ") or name_part.endswith("."):
                        has_additional_restrictions = True

            if "no_spaces_only" in additional_restrictions:
                # Filename cannot consist solely of spaces
                if file_name.strip() == "" and file_name:
                    has_additional_restrictions = True

            # Check filename length restrictions
            max_filename_length = platform.get("max_filename_length", None)
            if max_filename_length and len(file_name) > max_filename_length:
                has_additional_restrictions = True

            # Check path length (for full path, we'd need the parent path, but for filename we check if it's reasonable)
            # Note: This is a simplified check - full path length would require parent directory
            if (
                max_path_length and len(file_name) > max_path_length - 50
            ):  # Leave room for path
                has_additional_restrictions = True

            # Check for non-standard ASCII (excluding ignore_chars)
            bad_chars = (
                self.char_utils.find_non_standard_ascii(file_name, ignore_chars)
                - ignore_chars
            )

            # Determine LED color based on priority: Red > Purple > Orange > Yellow > Green
            # Purple includes: position issues, reserved names, additional restrictions
            if has_excluded:
                led.set_color("red")  # Invalid chars
            elif (
                has_position_issues or has_reserved_name or has_additional_restrictions
            ):
                led.set_color(
                    "purple"
                )  # Restrictions (position, reserved names, additional)
            elif has_problematic:
                led.set_color("orange")  # Problematic
            elif bad_chars:
                led.set_color("yellow")  # Non-standard chars
            else:
                led.set_color("green")  # OK

    def generate_random_filename(self):
        """Generate a random filename with various problematic characters for testing"""
        # Characters to include in random filename
        excluded_chars = list('<>:"|?*\\/')
        problematic_chars = list("!@#$%^&()[]{};,=+")
        non_ascii_chars = [
            "é",
            "ñ",
            "ü",
            "à",
            "ç",
            "ö",
            "ä",
            "ß",
            "ø",
            "å",
            "æ",
            "œ",
            "€",
            "£",
            "¥",
        ]
        safe_chars = list(string.ascii_letters + string.digits + "._- ")

        # Build random filename parts
        parts = []

        # Sometimes add leading space or period
        if random.random() < 0.2:
            parts.append(" " if random.random() < 0.5 else ".")

        # Add some safe characters
        parts.append("".join(random.choices(safe_chars, k=random.randint(3, 8))))

        # Add some excluded characters
        if random.random() < 0.7:
            parts.append(
                "".join(random.choices(excluded_chars, k=random.randint(1, 3)))
            )

        # Add more safe characters
        parts.append("".join(random.choices(safe_chars, k=random.randint(2, 6))))

        # Add problematic characters
        if random.random() < 0.6:
            parts.append(
                "".join(random.choices(problematic_chars, k=random.randint(1, 3)))
            )

        # Add non-ASCII characters
        if random.random() < 0.5:
            parts.append(
                "".join(random.choices(non_ascii_chars, k=random.randint(1, 3)))
            )

        # Add more safe characters
        parts.append("".join(random.choices(safe_chars, k=random.randint(2, 5))))

        # Sometimes add trailing space or period
        if random.random() < 0.2:
            parts.append(" " if random.random() < 0.5 else ".")

        # Combine parts
        random_name = "".join(parts)

        # Sometimes add an extension
        if random.random() < 0.7:
            extensions = ["txt", "pdf", "doc", "jpg", "png", "mp3", "zip"]
            random_name += "." + random.choice(extensions)

        # Sometimes make it too long
        if random.random() < 0.3:
            random_name += "".join(
                random.choices(string.ascii_letters, k=random.randint(200, 260))
            )

        # Update the display with the random filename
        ignore_chars = self.get_ignore_chars()
        bad_chars = (
            self.char_utils.find_non_standard_ascii(random_name, ignore_chars)
            - ignore_chars
        )

        # Also add all excluded and problematic characters that appear in the random filename
        # This ensures all problematic characters are highlighted, not just non-standard ASCII
        all_excluded_chars = set('<>:"|?*\\/')
        all_problematic_chars = set("!@#$%^&()[]{};,=+")

        # Find which excluded/problematic chars are actually in the random_name
        for char in random_name:
            if char in all_excluded_chars or char in all_problematic_chars:
                bad_chars.add(char)

        # Remove ignore_chars from bad_chars
        bad_chars = bad_chars - ignore_chars

        # Add length restriction highlighting if platforms are selected
        if self.selected_platforms:
            length_bad_chars = self.get_length_restriction_chars(random_name)
            bad_chars = bad_chars | length_bad_chars

        self.file_name_display.set_file_name(random_name, bad_chars, ignore_chars)

        # Update LED indicators
        self.update_platform_leds(random_name)

        # Enable rename button since we have a new name
        self.rename_btn.setEnabled(True)

        # Clear current file path so this is just a test name
        self.current_file_path = None
        self.current_file_name = random_name

    def on_filename_edited(self, new_text: str):
        """Handle when user edits the filename in the display"""
        # Update the rename button state based on whether text has changed
        if new_text != self.current_file_name:
            self.rename_btn.setEnabled(True)
        else:
            # Check if compatibility filter would enable it
            if (
                self.selected_platforms
                and self.compatibility_filtered_name
                and self.compatibility_filtered_name != self.current_file_name
            ):
                self.rename_btn.setEnabled(True)
            else:
                self.rename_btn.setEnabled(False)

        # Update LED indicators
        self.update_platform_leds(new_text)

    def rename_current_display(self):
        """Perform rename using the current text in the display (either edited or filtered)"""
        if not self.current_file_path:
            return

        # Get the current text from the display
        new_name = self.file_name_display.get_text()

        if not new_name or new_name == self.current_file_name:
            if self.selected_platforms and self.compatibility_filtered_name:
                # Try using compatibility filtered name
                new_name = self.compatibility_filtered_name
                if new_name == self.current_file_name:
                    QMessageBox.information(
                        self,
                        "No Changes",
                        "The filename is already compatible with the selected platforms.",
                    )
                    return
            else:
                QMessageBox.information(
                    self, "No Changes", "The filename hasn't been changed."
                )
                return

        # Show preview if prompting is enabled
        if self.prompt_check.isChecked():
            dialog = RenamePreviewDialog(self.current_file_name, new_name, self)
            if dialog.exec() != QDialog.Accepted:
                return

        # Determine the operation description
        if new_name == self.compatibility_filtered_name:
            operation = "Platform compatibility filter"
        else:
            operation = "Manual edit"

        self.perform_rename(new_name, operation)

    def rename_with_compatibility_filter(self):
        """Perform rename using the compatibility filtered name (legacy method)"""
        if not self.compatibility_filtered_name or not self.current_file_path:
            return

        if self.compatibility_filtered_name == self.current_file_name:
            QMessageBox.information(
                self,
                "No Changes",
                "The filename is already compatible with the selected platforms.",
            )
            return

        # Show preview if prompting is enabled
        if self.prompt_check.isChecked():
            dialog = RenamePreviewDialog(
                self.current_file_name, self.compatibility_filtered_name, self
            )
            if dialog.exec() != QDialog.Accepted:
                return

        self.perform_rename(
            self.compatibility_filtered_name, "Platform compatibility filter"
        )

    def check_leading_trailing_issues(self, file_name: str):
        """Check for leading/trailing spaces and periods, return list of issues"""
        issues = []
        if file_name.startswith(" "):
            issues.append("Filename starts with a space")
        if file_name.endswith(" "):
            issues.append("Filename ends with a space")
        if file_name.startswith("."):
            issues.append("Filename starts with a period")
        if file_name.endswith("."):
            issues.append("Filename ends with a period")
        # Check for reserved directory names
        if file_name == "." or file_name == "..":
            issues.append(f"Filename '{file_name}' is a reserved directory name")
        return issues

    def perform_rename(self, new_name: str, operation_description: str):
        """Perform the actual rename operation"""
        if not self.current_file_path or not new_name:
            return False

        # Check for leading/trailing spaces and periods
        issues = self.check_leading_trailing_issues(new_name)
        if issues:
            dialog = LeadingTrailingIssueDialog(new_name, issues, self)
            result = dialog.exec()
            if result == QDialog.Accepted and dialog.fixed_name:
                new_name = dialog.fixed_name
                # Re-validate the fixed name
                if not new_name.strip():
                    QMessageBox.warning(
                        self,
                        "Invalid Name",
                        "After removing leading/trailing characters, the filename is empty.",
                    )
                    return False
            else:
                # User cancelled
                return False

        # Validate new name
        if not new_name.strip():
            QMessageBox.warning(self, "Invalid Name", "File name cannot be empty.")
            return False

        old_path = Path(self.current_file_path)
        parent_dir = old_path.parent
        new_path = parent_dir / new_name

        # Check if new name already exists
        if new_path.exists() and new_path != old_path:
            QMessageBox.warning(
                self,
                "Rename Failed",
                f"A file or folder named '{new_name}' already exists.",
            )
            return False

        # Validate filename
        if not self.file_ops.is_valid_filename(new_name):
            QMessageBox.warning(
                self,
                "Invalid Name",
                "The file name contains invalid characters for file systems.",
            )
            return False

        # Create backup if requested
        if self.backup_check.isChecked():
            backup_path = parent_dir / f"BACKUP of {old_path.name}"
            if not self.file_ops.create_backup(old_path, backup_path):
                QMessageBox.warning(
                    self, "Backup Failed", "Could not create backup. Rename cancelled."
                )
                return False

        # Perform rename
        if self.file_ops.rename_file(old_path, new_path):
            self.current_file_path = str(new_path)
            self.current_file_name = new_name
            self.status_label.setText(f"Successfully renamed: {operation_description}")
            self.status_label.setStyleSheet(
                "padding: 5px; background-color: #e8f5e9; color: #2e7d32;"
            )
            self.on_file_selected()  # Refresh display
            return True
        else:
            QMessageBox.critical(
                self,
                "Rename Failed",
                "An error occurred while renaming the file. The file may be in use or you may not have permission.",
            )
            return False

    def auto_rename(self):
        """Auto rename: replace accented chars and remove other bad chars"""
        if not self.current_file_path:
            return

        ignore_chars = self.get_ignore_chars()
        new_name = self.char_utils.auto_fix_name(self.current_file_name, ignore_chars)

        if new_name == self.current_file_name:
            QMessageBox.information(
                self, "No Changes Needed", "The file name is already clean."
            )
            return

        # Show preview if prompting is enabled
        if self.prompt_check.isChecked():
            dialog = RenamePreviewDialog(self.current_file_name, new_name, self)
            if dialog.exec() != QDialog.Accepted:
                return

        self.perform_rename(new_name, "Auto Rename")

    def remove_bad_chars(self):
        """Remove all bad characters from name"""
        if not self.current_file_path:
            return

        ignore_chars = self.get_ignore_chars()
        new_name = self.char_utils.remove_bad_chars(
            self.current_file_name, ignore_chars
        )

        if new_name == self.current_file_name:
            QMessageBox.information(
                self, "No Changes Needed", "The file name is already clean."
            )
            return

        # Show preview if prompting is enabled
        if self.prompt_check.isChecked():
            dialog = RenamePreviewDialog(self.current_file_name, new_name, self)
            if dialog.exec() != QDialog.Accepted:
                return

        self.perform_rename(new_name, "Remove bad characters")

    def replace_bad_chars(self):
        """Replace only accented characters with unaccented equivalents"""
        if not self.current_file_path:
            return

        ignore_chars = self.get_ignore_chars()
        new_name = self.char_utils.replace_accented_chars(
            self.current_file_name, ignore_chars
        )

        if new_name == self.current_file_name:
            QMessageBox.information(
                self, "No Changes Needed", "The file name is already clean."
            )
            return

        # Show preview if prompting is enabled
        if self.prompt_check.isChecked():
            dialog = RenamePreviewDialog(self.current_file_name, new_name, self)
            if dialog.exec() != QDialog.Accepted:
                return

        self.perform_rename(new_name, "Replace bad characters")

    def edit_name(self):
        """Allow user to manually edit the file name"""
        if not self.current_file_path:
            return

        # Create dialog for editing
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit File Name")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Edit file name:"))
        edit_field = QLineEdit(self.current_file_name)
        edit_field.selectAll()
        layout.addWidget(edit_field)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.Accepted:
            new_name = edit_field.text().strip()
            if new_name and new_name != self.current_file_name:
                # Validate new name doesn't exist
                old_path = Path(self.current_file_path)
                parent_dir = old_path.parent
                new_path = parent_dir / new_name

                if new_path.exists() and new_path != old_path:
                    QMessageBox.warning(
                        self,
                        "Invalid Name",
                        f"A file or folder named '{new_name}' already exists.",
                    )
                    return

                if self.file_ops.is_valid_filename(new_name):
                    # Show preview if prompting is enabled
                    if self.prompt_check.isChecked():
                        preview = RenamePreviewDialog(
                            self.current_file_name, new_name, self
                        )
                        if preview.exec() != QDialog.Accepted:
                            return

                    self.perform_rename(new_name, "Manual edit")
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid Name",
                        "The file name contains invalid characters.",
                    )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NameDrop")

    window = NameDropApp()
    window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
