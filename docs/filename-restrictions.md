# Filename Character Restrictions Across Operating Systems and Cloud Platforms

This document provides authoritative information about filename character restrictions on major operating systems and cloud storage platforms.

<style>
.char-box {
  display: inline-block;
  background-color: #e0e0e0;
  border-radius: 4px;
  padding: 4px 8px;
  margin: 2px;
  font-family: monospace;
  font-size: 14px;
}
</style>

## Windows

### Invalid Characters

Windows does not allow the following characters in filenames:

<span class="char-box">&lt;</span> <span class="char-box">&gt;</span> <span class="char-box">:</span> <span class="char-box">"</span> <span class="char-box">|</span> <span class="char-box">?</span> <span class="char-box">\*</span> <span class="char-box">\</span> <span class="char-box">/</span>

(and control characters 0x00-0x1F)

### Reserved Names

Windows reserves the following names (case-insensitive):

- `CON`, `PRN`, `AUX`, `NUL`
- `COM1` through `COM9`
- `LPT1` through `LPT9`
- `.` and `..` (reserved directory names)

These cannot be used as filenames, even with extensions (e.g., `CON.txt` is invalid).

### Leading/Trailing Restrictions

- **Trailing spaces**: NOT ALLOWED - Windows file system (NTFS) automatically strips trailing spaces and periods from filenames. You cannot create a file with trailing spaces/periods on Windows.
- **Trailing periods**: NOT ALLOWED - Windows automatically strips trailing periods from filenames (the period before the file extension is preserved, but any trailing periods after the extension are stripped)
- **Leading spaces**: ALLOWED - Windows allows leading spaces in filenames, but they can cause issues:
  - Command line requires quotes to access: `" file.txt"`
  - Some applications may have trouble with them
  - Can cause cross-platform compatibility issues
- **Leading periods**: ALLOWED - Used for hidden files (e.g., `.gitignore`, `.env`). These work on Windows, macOS, and Linux.

### Additional Restrictions

- Maximum path length: 260 characters (MAX_PATH) by default, or 32,767 characters with long path support enabled
- Filenames cannot end with a space or period followed by an extension
- Filenames cannot consist solely of spaces

**Source**: [Microsoft Learn - Naming Files, Paths, and Namespaces](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)

---

## macOS

### Invalid Characters

macOS (HFS+ and APFS) has minimal restrictions:

<span class="char-box">:</span> <span class="char-box">/</span>

(colon is used as path separator in Classic Mac OS; forward slash is reserved for path separators; null byte `\0` is a control character)

### Leading/Trailing Restrictions

- **Trailing spaces**: Allowed but can cause cross-platform compatibility issues
- **Trailing periods**: Allowed
- **Leading spaces**: Allowed
- **Leading periods**: Allowed (used for hidden files like `.DS_Store`)

### Additional Notes

- macOS is case-insensitive by default (case-preserving)
- Maximum filename length: 255 characters (Unicode)
- macOS is generally more permissive than Windows

**Source**: [Apple Developer - File System Details](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html)

---

## Linux

### Invalid Characters

Linux has minimal restrictions:

<span class="char-box">/</span>

(forward slash is reserved for path separators; null byte `\0` is a control character; most other characters are allowed, including spaces, periods, and special characters)

### Leading/Trailing Restrictions

- **Trailing spaces**: Allowed
- **Trailing periods**: Allowed
- **Leading spaces**: Allowed
- **Leading periods**: Allowed (used for hidden files)

### Additional Notes

- Linux is case-sensitive
- Maximum filename length: 255 bytes (UTF-8 encoded)
- Very permissive filesystem compared to Windows and macOS

**Source**: [Filesystem Hierarchy Standard](https://en.wikipedia.org/wiki/Filesystem_Hierarchy_Standard)

---

## Cloud Storage Platforms

### AWS S3

**Invalid Characters:**

- No specific invalid characters, but object keys are stored as UTF-8 encoded strings

**Restrictions:**

- Maximum key length: 1,024 bytes (UTF-8)
- Object keys can contain any UTF-8 character
- However, some characters may require URL encoding in requests
- Best practice: Avoid control characters and characters that need encoding

**Leading/Trailing:**

- **Trailing spaces**: Allowed (but discouraged due to URL encoding issues)
- **Trailing periods**: Allowed
- **Leading spaces**: Allowed (but discouraged)
- **Leading periods**: Allowed

**Source**: [AWS S3 Object Key Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html)

---

### Google Cloud Storage

**Invalid Characters:**

- No explicitly invalid characters
- Object names are UTF-8 encoded strings

**Restrictions:**

- Maximum object name length: 1,024 bytes (UTF-8)
- Object names can contain any UTF-8 character
- Some characters require URL encoding

**Leading/Trailing:**

- **Trailing spaces**: Allowed
- **Trailing periods**: Allowed
- **Leading spaces**: Allowed
- **Leading periods**: Allowed

**Source**: [Google Cloud Storage Object Naming](https://cloud.google.com/storage/docs/naming-objects)

---

### Microsoft Azure Blob Storage

**Invalid Characters:**

- Forward slash `/` (reserved for virtual directory structure)
- Some control characters may cause issues

**Restrictions:**

- Blob names are case-sensitive
- Maximum length: 1,024 characters
- Can contain any combination of characters

**Leading/Trailing:**

- **Trailing spaces**: Allowed but can cause issues with some tools
- **Trailing periods**: Allowed
- **Leading spaces**: Allowed but can cause issues
- **Leading periods**: Allowed

**Source**: [Azure Blob Storage Naming and Referencing](https://learn.microsoft.com/en-us/rest/api/storageservices/naming-and-referencing-containers--blobs--and-metadata)

---

### Dropbox

**Invalid Characters:**

- Forward slash `/` (reserved for path separators)
- Backslash `\` (on Windows)
- Null byte and control characters

**Restrictions:**

- Maximum filename length: 255 characters
- Case-sensitive on Linux/macOS, case-insensitive on Windows
- Follows the restrictions of the underlying operating system

**Leading/Trailing:**

- **Trailing spaces**: Not recommended (Windows compatibility)
- **Trailing periods**: Not recommended (Windows compatibility)
- **Leading spaces**: Allowed but not recommended
- **Leading periods**: Allowed (hidden files)

**Source**: [Dropbox Help - File Names](https://help.dropbox.com/files-folders/restore-delete/file-names)

---

### OneDrive

**Invalid Characters:**
Same as Windows:

<span class="char-box">&lt;</span> <span class="char-box">&gt;</span> <span class="char-box">:</span> <span class="char-box">"</span> <span class="char-box">|</span> <span class="char-box">?</span> <span class="char-box">\*</span> <span class="char-box">\</span> <span class="char-box">/</span>

**Restrictions:**

- Follows Windows naming conventions
- Maximum path length: 260 characters (Windows default)

**Leading/Trailing:**

- **Trailing spaces**: NOT ALLOWED (Windows restriction)
- **Trailing periods**: NOT ALLOWED (Windows restriction)
- **Leading spaces**: Technically allowed but discouraged
- **Leading periods**: Allowed

**Source**: [Microsoft OneDrive - File and Folder Names](https://support.microsoft.com/en-us/office/restrictions-and-limitations-in-onedrive-and-sharepoint-64883a5d-228e-48f5-b3d2-eb39e07630db)

---

## FAT32

FAT32 is a file system commonly used on USB drives and older storage devices. When used with Windows, it follows Windows naming restrictions.

### Invalid Characters

Same as Windows:

<span class="char-box">&lt;</span> <span class="char-box">&gt;</span> <span class="char-box">:</span> <span class="char-box">"</span> <span class="char-box">|</span> <span class="char-box">?</span> <span class="char-box">\*</span> <span class="char-box">\</span> <span class="char-box">/</span>

### Reserved Names

Same as Windows (case-insensitive):

- `CON`, `PRN`, `AUX`, `NUL`
- `COM1` through `COM9`
- `LPT1` through `LPT9`
- `.` and `..` (reserved directory names)

### Leading/Trailing Restrictions

- **Trailing spaces**: NOT ALLOWED - Windows rejects names ending with a space (e.g., "MyFolder ")
- **Trailing periods**: NOT ALLOWED - Windows rejects names ending with a period (e.g., "file.")

### Additional Restrictions

- Maximum filename length: 255 characters (LFN limit)
- For maximum compatibility with older systems, consider the 8.3 format (11 characters total: 8 for name + 3 for extension)
- Filenames cannot end with a space or period followed by an extension
- Filenames cannot consist solely of spaces

**Source**: [Microsoft Learn - Naming Files, Paths, and Namespaces](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)

---

## Summary of Cross-Platform Best Practices

### Universal Restrictions (Most Restrictive)

To ensure compatibility across all platforms, avoid:

1. **Invalid characters**: <span class="char-box">&lt;</span> <span class="char-box">&gt;</span> <span class="char-box">:</span> <span class="char-box">"</span> <span class="char-box">|</span> <span class="char-box">?</span> <span class="char-box">\*</span> <span class="char-box">\</span> <span class="char-box">/</span>
2. **Control characters**: 0x00-0x1F, 0x7F (null bytes, etc.)
3. **Trailing spaces**: NOT allowed on Windows/FAT32
4. **Trailing periods**: NOT allowed on Windows/FAT32
5. **Reserved names**: Windows reserved names (CON, PRN, etc.) and `.` / `..`

### Recommendations

**Safe characters for cross-platform compatibility (Recommended Portable Filename Charset):**

If you want near-zero surprises across Windows/macOS/Linux/tools:

✅ **Use:**

- Letters: `A-Z`, `a-z`
- Numbers: `0-9`
- Special characters: `.` (period), `_` (underscore), `-` (hyphen)
- Spaces: Spaces are fine, **just not at the end**

❌ **Avoid:**

- All other punctuation marks
- Non-ASCII characters (accented letters, symbols, etc.)
- Leading or trailing spaces
- Leading or trailing periods (except for hidden files like `.gitignore`)

**Characters to avoid:**

- Special punctuation: <span class="char-box">!</span> <span class="char-box">@</span> <span class="char-box">#</span> <span class="char-box">$</span> <span class="char-box">%</span> <span class="char-box">^</span> <span class="char-box">&</span> <span class="char-box">(</span> <span class="char-box">)</span> <span class="char-box">[</span> <span class="char-box">]</span> <span class="char-box">{</span> <span class="char-box">}</span> <span class="char-box">;</span> <span class="char-box">,</span> <span class="char-box">=</span> <span class="char-box">+</span>
- Accented characters: `é, ñ, ü, etc.` (can cause issues on some systems)
- Unicode symbols and emoji (compatibility issues)

### NameDrop Implementation Notes

The current implementation correctly handles:

- ✅ **Trailing spaces**: Validation is correct - Windows does not allow these, and macOS/Linux files with trailing spaces will fail when transferred to Windows or OneDrive
- ✅ **Trailing periods**: Validation is correct - Windows does not allow these, critical for Windows compatibility
- ✅ **Leading spaces**: Validation is correct - While technically allowed on Windows, they cause problems in command-line usage and cross-platform file transfers. Warning users is appropriate.
- ✅ **Leading periods**: Current implementation flags this, but it's actually allowed on all platforms (used for hidden files). However, warning users is reasonable for awareness, as some users may not intend to create hidden files.

**Important Note on Leading Periods**: Leading periods are actually valid on all platforms and are commonly used for hidden files (e.g., `.gitignore`, `.env`). The current implementation flags these, which provides a good safety check to ensure users don't accidentally create hidden files, but users who intentionally want hidden files should be able to proceed. This is a design choice - warning about leading periods is reasonable for a file renaming tool focused on cross-platform compatibility, as some users may not realize they're creating hidden files.

**Note**: The validation is appropriately strict for maximum cross-platform compatibility. Since Windows is the most restrictive platform, ensuring Windows compatibility automatically ensures compatibility with OneDrive and most cloud platforms that follow Windows conventions.

## Verification of Current Implementation

Based on authoritative sources:

1. **Trailing spaces**: ✅ CORRECT - Windows does not allow these. Files cannot have trailing spaces on Windows, so validation is essential.

2. **Trailing periods**: ✅ CORRECT - Windows does not allow these (except the period before the file extension). Critical for Windows compatibility.

3. **Leading spaces**: ✅ CORRECT to warn - While technically allowed on Windows, they cause significant issues:

   - Require quotes in command line
   - Can break scripts and batch files
   - Cause problems in cross-platform transfers
   - Many applications handle them poorly

4. **Leading periods**: ⚠️ WORKS BUT NOTE - Leading periods are actually valid and commonly used (hidden files). The current implementation warns users, which is good for awareness, but these should be allowed if the user confirms they want a hidden file. This is a reasonable UX choice for a file renaming utility.

**Recommendation**: The current validation is appropriate for Windows compatibility, which is the most restrictive platform. Users working primarily on macOS/Linux should be aware that trailing spaces/periods are allowed on those platforms but will cause issues if files are transferred to Windows or uploaded to OneDrive.

---

## References

1. Microsoft Learn - [Naming Files, Paths, and Namespaces](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file)
2. Apple Developer - [File System Programming Guide](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/)
3. AWS Documentation - [Object Keys](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html)
4. Google Cloud - [Object Naming](https://cloud.google.com/storage/docs/naming-objects)
5. Microsoft Azure - [Naming and Referencing](https://learn.microsoft.com/en-us/rest/api/storageservices/naming-and-referencing-containers--blobs--and-metadata)
6. Dropbox Help - [File Names](https://help.dropbox.com/files-folders/restore-delete/file-names)
7. Microsoft Support - [OneDrive Restrictions](https://support.microsoft.com/en-us/office/restrictions-and-limitations-in-onedrive-and-sharepoint-64883a5d-228e-48f5-b3d2-eb39e07630db)

---

_Last updated: 2024-12-13_
