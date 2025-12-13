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
        
        # File name display with highlighting
        layout.addWidget(QLabel("File name (non-standard ASCII highlighted):"))
        self.file_name_display = FileNameDisplay()
        layout.addWidget(self.file_name_display)
        
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

