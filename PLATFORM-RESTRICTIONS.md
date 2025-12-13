# Platform Filename Restrictions

This document lists all filename restrictions that NameDrop tests for and corrects across different operating systems and file systems. Use this as a reference to understand what characters and patterns are disallowed or problematic on each platform.

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

## Windows OS

### Excluded Characters
The following characters are **not allowed** in Windows filenames:

<span class="char-box">&lt;</span> <span class="char-box">&gt;</span> <span class="char-box">:</span> <span class="char-box">"</span> <span class="char-box">|</span> <span class="char-box">?</span> <span class="char-box">*</span> <span class="char-box">\</span> <span class="char-box">/</span>

(and control characters)

### Reserved Names
Windows reserves these names (case-insensitive) and they cannot be used as filenames, even with extensions:
- `CON`, `PRN`, `AUX`, `NUL`
- `COM1`, `COM2`, `COM3`, `COM4`, `COM5`, `COM6`, `COM7`, `COM8`, `COM9`
- `LPT1`, `LPT2`, `LPT3`, `LPT4`, `LPT5`, `LPT6`, `LPT7`, `LPT8`, `LPT9`
- `.` and `..` (reserved directory names)

### Position Restrictions
- **Trailing space**: Not allowed - Windows automatically strips trailing spaces
- **Trailing period**: Not allowed - Windows automatically strips trailing periods (the period before the file extension is preserved)

### Length Restrictions
- **Maximum filename length**: 255 characters
- **Maximum path length**: 260 characters (MAX_PATH default)

### Additional Restrictions
- Filenames cannot end with a space or period followed by an extension
- Filenames cannot consist solely of spaces

---

## macOS

### Excluded Characters
The following characters are **not allowed** in macOS filenames:

<span class="char-box">:</span> <span class="char-box">/</span>

(colon is used as path separator in Classic Mac OS; forward slash is reserved for path separators)

### Reserved Names
None

### Position Restrictions
None

### Length Restrictions
- **Maximum filename length**: 255 characters
- **Maximum path length**: 255 characters

### Additional Restrictions
None

---

## Linux

### Excluded Characters
The following characters are **not allowed** in Linux filenames:

<span class="char-box">/</span>

(forward slash is reserved for path separators)

### Reserved Names
None

### Position Restrictions
None

### Length Restrictions
- **Maximum filename length**: 255 bytes (UTF-8 encoded)
- **Maximum path length**: 255 bytes (UTF-8 encoded)

### Additional Restrictions
None

---

## Cloud Drives

Cloud platforms (OneDrive, Dropbox, Google Drive, etc.) typically follow Windows restrictions for compatibility.

### Excluded Characters
The following characters are **not allowed**:

<span class="char-box">&lt;</span> <span class="char-box">&gt;</span> <span class="char-box">:</span> <span class="char-box">"</span> <span class="char-box">|</span> <span class="char-box">?</span> <span class="char-box">*</span> <span class="char-box">\</span> <span class="char-box">/</span>

(and control characters)

### Problematic Characters
The following characters are **problematic** and may cause issues:

<span class="char-box">!</span> <span class="char-box">@</span> <span class="char-box">#</span> <span class="char-box">$</span> <span class="char-box">%</span> <span class="char-box">^</span> <span class="char-box">&</span> <span class="char-box">(</span> <span class="char-box">)</span> <span class="char-box">[</span> <span class="char-box">]</span> <span class="char-box">{</span> <span class="char-box">}</span> <span class="char-box">;</span> <span class="char-box">,</span> <span class="char-box">=</span> <span class="char-box">+</span>

### Reserved Names
Same as Windows (case-insensitive):
- `CON`, `PRN`, `AUX`, `NUL`
- `COM1` through `COM9`
- `LPT1` through `LPT9`
- `.` and `..` (reserved directory names)

### Position Restrictions
- **Trailing space**: Not allowed
- **Trailing period**: Not allowed

### Length Restrictions
- **Maximum filename length**: 255 characters
- **Maximum path length**: 260 characters

### Additional Restrictions
- Filenames cannot end with a space or period followed by an extension
- Filenames cannot consist solely of spaces

---

## FAT32

FAT32 is a file system commonly used on USB drives and older storage devices. It supports Long File Names (LFN) up to 255 characters, but also maintains compatibility with the older 8.3 format (8 characters for name + 3 for extension = 11 characters total).

**Windows behavior on FAT32**: Windows will reject names that end with a space or period (e.g., "MyFolder " or "file.").

### Excluded Characters
The following characters are **not allowed**:

<span class="char-box">&lt;</span> <span class="char-box">&gt;</span> <span class="char-box">:</span> <span class="char-box">"</span> <span class="char-box">|</span> <span class="char-box">?</span> <span class="char-box">*</span> <span class="char-box">\</span> <span class="char-box">/</span>

(same as Windows)

### Reserved Names
Same as Windows (case-insensitive):
- `CON`, `PRN`, `AUX`, `NUL`
- `COM1` through `COM9`
- `LPT1` through `LPT9`
- `.` and `..` (reserved directory names)

### Position Restrictions
- **Trailing space**: Not allowed - Windows rejects names ending with a space (e.g., "MyFolder ")
- **Trailing period**: Not allowed - Windows rejects names ending with a period (e.g., "file.")

### Length Restrictions
- **Maximum filename length**: 255 characters (LFN limit)
- **Note**: For maximum compatibility with older systems, consider the 8.3 format (11 characters total: 8 for name + 3 for extension)

### Additional Restrictions
- Filenames cannot end with a space or period followed by an extension
- Filenames cannot consist solely of spaces

---

## Everything (All Platforms Combined)

When selecting "Everything", NameDrop applies the most restrictive combination of all platforms to ensure maximum compatibility.

### Excluded Characters

<span class="char-box">&lt;</span> <span class="char-box">&gt;</span> <span class="char-box">:</span> <span class="char-box">"</span> <span class="char-box">|</span> <span class="char-box">?</span> <span class="char-box">*</span> <span class="char-box">\</span> <span class="char-box">/</span>

(and control characters)

### Problematic Characters

<span class="char-box">!</span> <span class="char-box">@</span> <span class="char-box">#</span> <span class="char-box">$</span> <span class="char-box">%</span> <span class="char-box">^</span> <span class="char-box">&</span> <span class="char-box">(</span> <span class="char-box">)</span> <span class="char-box">[</span> <span class="char-box">]</span> <span class="char-box">{</span> <span class="char-box">}</span> <span class="char-box">;</span> <span class="char-box">,</span> <span class="char-box">=</span> <span class="char-box">+</span>

### Position Restrictions
- **Trailing space**: Not allowed
- **Trailing period**: Not allowed
- **Leading space**: Not allowed (can cause cross-platform issues)

### Length Restrictions
- **Maximum filename length**: 255 characters (conservative limit for all platforms)
- **Maximum path length**: 260 characters (Windows default)

### Additional Restrictions
- Filenames cannot end with a space or period followed by an extension
- Filenames cannot consist solely of spaces

---

## Recommended Portable Filename Charset

If you want near-zero surprises across Windows/macOS/Linux/tools and cloud platforms:

### ✅ Use These Characters
- **Letters**: `A-Z`, `a-z`
- **Numbers**: `0-9`
- **Special characters**: `.` (period), `_` (underscore), `-` (hyphen)
- **Spaces**: Spaces are fine, **just not at the end**

### ❌ Avoid These
- All other punctuation marks
- Non-ASCII characters (accented letters, symbols, etc.)
- Leading or trailing spaces
- Leading or trailing periods (except for hidden files like `.gitignore`)

### Examples
✅ **Good filenames:**
- `My Document.txt`
- `project_file-2024.pdf`
- `README.md`
- `.gitignore`

❌ **Problematic filenames:**
- `My Document .txt` (trailing space)
- `file..txt` (trailing period before extension)
- `résumé.pdf` (non-ASCII characters)
- `file@name.txt` (problematic character)

---

## Notes

- **Spaces**: Spaces are generally allowed in filenames on all platforms, but leading and trailing spaces can cause issues and are restricted on some platforms.
- **Periods**: Leading periods are allowed (used for hidden files like `.gitignore`). Trailing periods are restricted on Windows and FAT32.
- **Case sensitivity**: Windows and macOS are case-insensitive (but case-preserving), while Linux is case-sensitive.
- **Unicode**: Most modern file systems support Unicode characters, but for maximum compatibility, it's recommended to use standard ASCII characters.

For more detailed technical information, see [local/filename-restrictions.md](local/filename-restrictions.md).
