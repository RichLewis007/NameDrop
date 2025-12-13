#!/usr/bin/env python3
"""
NameDrop - A PySide6 application to rename files/folders with non-standard ASCII characters
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QHBoxLayout, QLabel, QPushButton, QCheckBox, 
                                QLineEdit, QMessageBox, QGroupBox, QTextEdit,
                                QScrollArea, QDialog, QDialogButtonBox, QSizePolicy)
from PySide6.QtCore import Qt, QSettings, QPoint, QSize, Signal, QStandardPaths
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QColor, QTextCharFormat, QFont, QTextCursor

from file_operations import FileOperations
from character_utils import CharacterUtils


# Platform compatibility data
PLATFORM_RESTRICTIONS = {
    "Everything": {
        "name": "Everything (All Platforms)",
        "excluded_chars": set('<>:"|?*\\/'),  # No spaces - spaces are allowed, only position matters
        "problematic_chars": set('!@#$%^&()[]{};,=+'),  # No spaces
        "excluded_positions": ["trailing_space", "trailing_period", "leading_space"],
        "description": "Most restrictive - ensures compatibility with Windows, macOS, Linux, and all cloud platforms"
    },
    "Windows": {
        "name": "Windows OS",
        "excluded_chars": set('<>:"|?*\\/'),  # No spaces - spaces are allowed, only position matters
        "problematic_chars": set(),
        "excluded_positions": ["trailing_space", "trailing_period"],
        "description": "Windows file system restrictions. Trailing spaces and periods are automatically stripped."
    },
    "macOS": {
        "name": "macOS",
        "excluded_chars": set(':/'),  # No spaces
        "problematic_chars": set(),
        "excluded_positions": [],
        "description": "macOS allows most characters. Only colon (:) and forward slash (/) are forbidden."
    },
    "Linux": {
        "name": "Linux",
        "excluded_chars": set('/'),  # No spaces
        "problematic_chars": set(),
        "excluded_positions": [],
        "description": "Linux is very permissive. Only forward slash (/) is forbidden."
    },
    "Cloud": {
        "name": "Cloud Drives",
        "excluded_chars": set('<>:"|?*\\/'),  # No spaces - spaces are allowed, only position matters
        "problematic_chars": set('!@#$%^&()[]{};,=+'),  # No spaces
        "excluded_positions": ["trailing_space", "trailing_period"],
        "description": "Cloud platforms (OneDrive, Dropbox, etc.) typically follow Windows restrictions for compatibility."
    }
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
        issues_text.setStyleSheet("padding: 10px; background-color: #fff3e0; font-size: 11pt;")
        layout.addWidget(issues_text)
        
        # Show current name
        layout.addWidget(QLabel("Current filename:"))
        current_label = QLabel(f'"{self.file_name}"')
        current_label.setStyleSheet("font-size: 12pt; padding: 5px; background-color: #f0f0f0; font-family: monospace;")
        layout.addWidget(current_label)
        
        # Show fixed name if we can fix it
        if self.can_fix():
            fixed = self.get_fixed_name()
            layout.addWidget(QLabel("Fixed filename:"))
            fixed_label = QLabel(f'"{fixed}"')
            fixed_label.setStyleSheet("font-size: 12pt; padding: 5px; background-color: #e8f5e9; font-family: monospace;")
            layout.addWidget(fixed_label)
        
        buttons = QDialogButtonBox()
        if self.can_fix():
            fix_btn = buttons.addButton("Fix by removing offending character(s)", QDialogButtonBox.AcceptRole)
            fix_btn.clicked.connect(self.accept_fix)
        cancel_btn = buttons.addButton("Cancel", QDialogButtonBox.RejectRole)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def can_fix(self):
        """Check if we can fix the issues"""
        return len(self.file_name.strip(' .')) > 0  # Make sure there's something left after stripping
    
    def get_fixed_name(self):
        """Get the fixed name"""
        return self.file_name.strip(' .')
    
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
        old_label.setStyleSheet("font-size: 12pt; padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(old_label)
        
        layout.addWidget(QLabel("New name:"))
        new_label = QLabel(self.new_name)
        new_label.setStyleSheet("font-size: 12pt; padding: 5px; background-color: #e8f5e9;")
        layout.addWidget(new_label)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)


class FileNameDisplay(QTextEdit):
    """Widget to display file name with highlighted non-standard ASCII characters"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(100)
        self.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        
    def set_file_name(self, file_name: str, bad_chars: set, ignore_chars: set):
        """Display file name with bad characters highlighted"""
        self.clear()
        
        cursor = self.textCursor()
        format_normal = QTextCharFormat()
        format_normal.setFont(QFont("Arial", 18, QFont.Bold))
        
        format_highlight = QTextCharFormat()
        format_highlight.setBackground(QColor(255, 255, 0))  # Yellow highlight
        format_highlight.setFont(QFont("Arial", 18, QFont.Bold))
        
        for char in file_name:
            if char in bad_chars and char not in ignore_chars:
                cursor.insertText(char, format_highlight)
            else:
                cursor.insertText(char, format_normal)


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
        self.compatibility_filtered_name = None  # Store the filtered name based on selected platforms
        
        self.char_utils = CharacterUtils()
        self.file_ops = FileOperations()
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the user interface"""
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
        filename_header_layout.addWidget(QLabel("File name (non-standard ASCII highlighted):"))
        filename_header_layout.addStretch()
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
        self.rename_btn.clicked.connect(self.rename_with_compatibility_filter)
        filename_header_layout.addWidget(self.rename_btn)
        layout.addLayout(filename_header_layout)
        
        self.file_name_display = FileNameDisplay()
        layout.addWidget(self.file_name_display)
        
        # Platform compatibility section
        compatibility_group = QGroupBox("Make compatible with:")
        compatibility_layout = QVBoxLayout()
        
        # Platform buttons (horizontal)
        buttons_layout = QHBoxLayout()
        self.platform_buttons = {}
        platform_keys = ["Everything", "Windows", "macOS", "Linux", "Cloud"]
        
        for platform_key in platform_keys:
            btn = PlatformButton(platform_key, PLATFORM_RESTRICTIONS[platform_key]["name"])
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
            btn.clicked.connect(lambda checked, key=platform_key: self.on_platform_button_clicked(key, checked))
            btn.hover_entered.connect(self.on_platform_button_hover)
            btn.hover_left.connect(self.on_platform_button_leave)
            buttons_layout.addWidget(btn)
            self.platform_buttons[platform_key] = btn
        
        buttons_layout.addStretch()
        compatibility_layout.addLayout(buttons_layout)
        
        # Information display area (shows excluded/problematic characters) - scrollable
        self.compatibility_info_label = QLabel("Hover over a platform button to see restrictions, or click to apply filters.")
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
        self.ignore_chars_edit.setPlaceholderText("Characters to ignore (separated by spaces)")
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
        
        self.move(pos)
        self.resize(size)
        
        # Move to saved screen if available
        screens = QApplication.screens()
        if 0 <= screen < len(screens):
            screen_geometry = screens[screen].geometry()
            window_geometry = self.frameGeometry()
            window_geometry.moveCenter(screen_geometry.center())
            self.move(window_geometry.topLeft())
        
        # Checkbox states
        self.prompt_check.setChecked(self.settings.value("prompt_before_rename", True, type=bool))
        self.backup_check.setChecked(self.settings.value("always_backup", True, type=bool))
        self.ignore_common_check.setChecked(self.settings.value("ignore_common_chars", True, type=bool))
        
        # Ignore characters
        ignore_chars = self.settings.value("ignore_chars", self.char_utils.get_common_allowed_chars())
        self.ignore_chars_edit.setText(ignore_chars)
        
    def save_settings(self):
        """Save current settings"""
        self.settings.setValue("window_position", self.pos())
        self.settings.setValue("window_size", self.size())
        
        # Find which screen the window is on
        screen_num = 0
        screens = QApplication.screens()
        for i, screen in enumerate(screens):
            if screen.geometry().contains(self.frameGeometry().center()):
                screen_num = i
                break
        self.settings.setValue("screen", screen_num)
        
        self.settings.setValue("prompt_before_rename", self.prompt_check.isChecked())
        self.settings.setValue("always_backup", self.backup_check.isChecked())
        self.settings.setValue("ignore_common_chars", self.ignore_common_check.isChecked())
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
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffebee; color: #c62828;")
            return
        
        # Handle first file (could be extended to support batch processing)
        file_path = valid_files[0]
        if len(valid_files) > 1:
            self.status_label.setText(f"Processing first of {len(valid_files)} files. Drop again for next file.")
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
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffebee; color: #c62828;")
            
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
        
        # Get ignore characters
        ignore_chars = set()
        if self.ignore_common_check.isChecked():
            ignore_text = self.ignore_chars_edit.text()
            ignore_chars = set(char for char in ignore_text if char.strip())
        
        # Find bad characters
        bad_chars = self.char_utils.find_non_standard_ascii(self.current_file_name, ignore_chars)
        
        # Apply compatibility filter if platforms are selected
        if self.selected_platforms:
            self.apply_compatibility_filter()
        else:
            # Update display
            self.file_name_display.set_file_name(self.current_file_name, bad_chars, ignore_chars)
        
        # Enable buttons if there are bad characters
        has_bad_chars = bool(bad_chars - ignore_chars)
        self.auto_rename_btn.setEnabled(has_bad_chars)
        self.remove_btn.setEnabled(has_bad_chars)
        self.replace_btn.setEnabled(has_bad_chars)
        self.edit_btn.setEnabled(True)
        self.ignore_btn.setEnabled(True)
        
        if has_bad_chars:
            self.status_label.setText(f"Found {len(bad_chars - ignore_chars)} non-standard ASCII character(s)")
            self.status_label.setStyleSheet("padding: 5px; background-color: #fff3e0;")
        else:
            self.status_label.setText("File name contains only standard ASCII characters")
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
            
    def get_ignore_chars(self):
        """Get set of characters to ignore"""
        ignore_chars = set()
        if self.ignore_common_check.isChecked():
            ignore_text = self.ignore_chars_edit.text()
            ignore_chars = set(char for char in ignore_text if char.strip())
        return ignore_chars
    
    def get_combined_restrictions(self, platforms):
        """Get combined restrictions from selected platforms"""
        if not platforms:
            return {"excluded_chars": set(), "problematic_chars": set(), "excluded_positions": []}
        
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
            "excluded_positions": excluded_positions
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
                excluded_display = " ".join(f"<code>{c}</code>" if c != " " else "<code>space</code>" for c in excluded_list)
                lines.append(f"  • <b>Excluded characters:</b> {excluded_display}")
            
            # Problematic characters
            if platform["problematic_chars"]:
                problematic_list = sorted(platform["problematic_chars"])
                problematic_display = " ".join(f"<code>{c}</code>" for c in problematic_list)
                lines.append(f"  • <b>Problematic characters:</b> {problematic_display}")
            
            # Position restrictions
            position_descriptions = {
                "trailing_space": "Trailing space",
                "trailing_period": "Trailing period",
                "leading_space": "Leading space",
                "leading_period": "Leading period"
            }
            if platform["excluded_positions"]:
                positions = [position_descriptions.get(p, p) for p in platform["excluded_positions"]]
                lines.append(f"  • <b>Position restrictions:</b> {', '.join(positions)}")
            
            lines.append(f"  • <i>{platform['description']}</i>")
            lines.append("")
        
        return "<br>".join(lines)
    
    def on_platform_button_hover(self, platform_key):
        """Show platform restrictions on hover"""
        platform = PLATFORM_RESTRICTIONS[platform_key]
        info = f"<b>{platform['name']}:</b><br><br>"
        
        if platform["excluded_chars"]:
            excluded_list = sorted(platform["excluded_chars"])
            excluded_display = " ".join(f"<code>{c}</code>" if c != " " else "<code>space</code>" for c in excluded_list)
            info += f"<b>Excluded characters:</b> {excluded_display}<br>"
        
        if platform["problematic_chars"]:
            problematic_list = sorted(platform["problematic_chars"])
            problematic_display = " ".join(f"<code>{c}</code>" for c in problematic_list)
            info += f"<b>Problematic characters:</b> {problematic_display}<br>"
        
        position_descriptions = {
            "trailing_space": "Trailing space",
            "trailing_period": "Trailing period",
            "leading_space": "Leading space",
            "leading_period": "Leading period"
        }
        if platform["excluded_positions"]:
            positions = [position_descriptions.get(p, p) for p in platform["excluded_positions"]]
            info += f"<b>Position restrictions:</b> {', '.join(positions)}<br>"
        
        info += f"<br><i>{platform['description']}</i>"
        self.compatibility_info_label.setText(info)
    
    def on_platform_button_leave(self):
        """Clear hover info or show selected platforms"""
        if self.selected_platforms:
            self.update_compatibility_info()
        else:
            self.compatibility_info_label.setText("Hover over a platform button to see restrictions, or click to apply filters.")
    
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
                self.platform_selection_order = ["Everything"] + [k for k in self.platform_buttons.keys() if k != "Everything"]
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
            self.compatibility_info_label.setText("Hover over a platform button to see restrictions, or click to apply filters.")
    
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
                bad_chars = self.char_utils.find_non_standard_ascii(self.current_file_name, ignore_chars)
                self.file_name_display.set_file_name(self.current_file_name, bad_chars, ignore_chars)
            return
        
        restrictions = self.get_combined_restrictions(self.selected_platforms)
        filtered_name = self.current_file_name
        
        # Remove excluded characters (spaces are NOT excluded - they're allowed in filenames)
        # Only remove leading/trailing spaces based on position restrictions
        for char in restrictions["excluded_chars"]:
            # Never remove spaces - they're allowed characters, only position matters
            if char != " ":
                filtered_name = filtered_name.replace(char, "")
        
        # Remove problematic characters (spaces are NOT problematic)
        for char in restrictions["problematic_chars"]:
            # Never remove spaces - they're allowed characters
            if char != " ":
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
                filtered_name = name_part + "." + ext_part if name_part or ext_part else filtered_name.rstrip(".")
            else:
                # No extension, remove all trailing periods
                filtered_name = filtered_name.rstrip(".")
        if "leading_space" in restrictions["excluded_positions"]:
            filtered_name = filtered_name.lstrip(" ")
        if "leading_period" in restrictions["excluded_positions"]:
            filtered_name = filtered_name.lstrip(".")
        
        self.compatibility_filtered_name = filtered_name
        
        # Update display with filtered name
        if filtered_name != self.current_file_name:
            # Show what was removed
            ignore_chars = self.get_ignore_chars()
            # Find characters that were removed
            removed_chars = set()
            for char in self.current_file_name:
                if char not in filtered_name:
                    removed_chars.add(char)
            
            # Show filtered name with removed characters highlighted
            bad_chars = self.char_utils.find_non_standard_ascii(filtered_name, ignore_chars)
            bad_chars.update(removed_chars)  # Also highlight removed chars if they appear in original
            self.file_name_display.set_file_name(filtered_name, bad_chars, ignore_chars)
            self.rename_btn.setEnabled(True)
        else:
            # No changes needed
            ignore_chars = self.get_ignore_chars()
            bad_chars = self.char_utils.find_non_standard_ascii(filtered_name, ignore_chars)
            self.file_name_display.set_file_name(filtered_name, bad_chars, ignore_chars)
            self.rename_btn.setEnabled(False)
    
    def rename_with_compatibility_filter(self):
        """Perform rename using the compatibility filtered name"""
        if not self.compatibility_filtered_name or not self.current_file_path:
            return
        
        if self.compatibility_filtered_name == self.current_file_name:
            QMessageBox.information(self, "No Changes", "The filename is already compatible with the selected platforms.")
            return
        
        # Show preview if prompting is enabled
        if self.prompt_check.isChecked():
            dialog = RenamePreviewDialog(self.current_file_name, self.compatibility_filtered_name, self)
            if dialog.exec() != QDialog.Accepted:
                return
        
        self.perform_rename(self.compatibility_filtered_name, "Platform compatibility filter")
    
    def check_leading_trailing_issues(self, file_name: str):
        """Check for leading/trailing spaces and periods, return list of issues"""
        issues = []
        if file_name.startswith(' '):
            issues.append("Filename starts with a space")
        if file_name.endswith(' '):
            issues.append("Filename ends with a space")
        if file_name.startswith('.'):
            issues.append("Filename starts with a period")
        if file_name.endswith('.'):
            issues.append("Filename ends with a period")
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
                    QMessageBox.warning(self, "Invalid Name", 
                                      "After removing leading/trailing characters, the filename is empty.")
                    return False
            else:
                # User cancelled
                return False
        
        # Validate new name
        if not new_name.strip():
            QMessageBox.warning(self, "Invalid Name", 
                              "File name cannot be empty.")
            return False
            
        old_path = Path(self.current_file_path)
        parent_dir = old_path.parent
        new_path = parent_dir / new_name
        
        # Check if new name already exists
        if new_path.exists() and new_path != old_path:
            QMessageBox.warning(self, "Rename Failed", 
                              f"A file or folder named '{new_name}' already exists.")
            return False
        
        # Validate filename
        if not self.file_ops.is_valid_filename(new_name):
            QMessageBox.warning(self, "Invalid Name", 
                              "The file name contains invalid characters for file systems.")
            return False
        
        # Create backup if requested
        if self.backup_check.isChecked():
            backup_path = parent_dir / f"BACKUP of {old_path.name}"
            if not self.file_ops.create_backup(old_path, backup_path):
                QMessageBox.warning(self, "Backup Failed", 
                                  "Could not create backup. Rename cancelled.")
                return False
        
        # Perform rename
        if self.file_ops.rename_file(old_path, new_path):
            self.current_file_path = str(new_path)
            self.current_file_name = new_name
            self.status_label.setText(f"Successfully renamed: {operation_description}")
            self.status_label.setStyleSheet("padding: 5px; background-color: #e8f5e9; color: #2e7d32;")
            self.on_file_selected()  # Refresh display
            return True
        else:
            QMessageBox.critical(self, "Rename Failed", 
                               "An error occurred while renaming the file. The file may be in use or you may not have permission.")
            return False
            
    def auto_rename(self):
        """Auto rename: replace accented chars and remove other bad chars"""
        if not self.current_file_path:
            return
            
        ignore_chars = self.get_ignore_chars()
        new_name = self.char_utils.auto_fix_name(self.current_file_name, ignore_chars)
        
        if new_name == self.current_file_name:
            QMessageBox.information(self, "No Changes Needed", 
                                  "The file name is already clean.")
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
        new_name = self.char_utils.remove_bad_chars(self.current_file_name, ignore_chars)
        
        if new_name == self.current_file_name:
            QMessageBox.information(self, "No Changes Needed", 
                                  "The file name is already clean.")
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
        new_name = self.char_utils.replace_accented_chars(self.current_file_name, ignore_chars)
        
        if new_name == self.current_file_name:
            QMessageBox.information(self, "No Changes Needed", 
                                  "The file name is already clean.")
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
                    QMessageBox.warning(self, "Invalid Name", 
                                      f"A file or folder named '{new_name}' already exists.")
                    return
                
                if self.file_ops.is_valid_filename(new_name):
                    # Show preview if prompting is enabled
                    if self.prompt_check.isChecked():
                        preview = RenamePreviewDialog(self.current_file_name, new_name, self)
                        if preview.exec() != QDialog.Accepted:
                            return
                    
                    self.perform_rename(new_name, "Manual edit")
                else:
                    QMessageBox.warning(self, "Invalid Name", 
                                      "The file name contains invalid characters.")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NameDrop")
    
    window = NameDropApp()
    window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

