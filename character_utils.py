"""
Character utilities for detecting and fixing non-standard ASCII characters in file names
"""

import unicodedata


class CharacterUtils:
    """Utilities for character detection and normalization"""
    
    # Accented character mapping to unaccented equivalents
    ACCENT_MAP = {
        'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
        'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
        'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
        'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o', 'ø': 'o',
        'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
        'ý': 'y', 'ÿ': 'y',
        'ñ': 'n', 'ç': 'c',
        'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A',
        'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
        'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O', 'Ø': 'O',
        'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
        'Ý': 'Y', 'Ÿ': 'Y',
        'Ñ': 'N', 'Ç': 'C',
        'æ': 'ae', 'œ': 'oe', 'ß': 'ss',
        'Æ': 'AE', 'Œ': 'OE',
        'ð': 'd', 'Ð': 'D', 'þ': 'th', 'Þ': 'TH',
        'ł': 'l', 'Ł': 'L', 'đ': 'd', 'Đ': 'D',
        'č': 'c', 'Č': 'C', 'ć': 'c', 'Ć': 'C',
        'ř': 'r', 'Ř': 'R', 'ž': 'z', 'Ž': 'Z',
        'š': 's', 'Š': 'S', 'ť': 't', 'Ť': 'T',
        'ď': 'd', 'Ď': 'D', 'ň': 'n', 'Ň': 'N',
        'ą': 'a', 'Ą': 'A', 'ę': 'e', 'Ę': 'E',
        'ė': 'e', 'Ė': 'E', 'į': 'i', 'Į': 'I',
        'ų': 'u', 'Ų': 'U', 'ū': 'u', 'Ū': 'U',
        'ą': 'a', 'Ą': 'A', 'ć': 'c', 'Ć': 'C',
        'ę': 'e', 'Ę': 'E', 'ł': 'l', 'Ł': 'L',
        'ń': 'n', 'Ń': 'N', 'ó': 'o', 'Ó': 'O',
        'ś': 's', 'Ś': 'S', 'ź': 'z', 'Ź': 'Z',
        'ż': 'z', 'Ż': 'Z',
        'ğ': 'g', 'Ğ': 'G', 'ş': 's', 'Ş': 'S',
        'ı': 'i', 'İ': 'I',
        'ă': 'a', 'Ă': 'A', 'â': 'a', 'Â': 'A',
        'î': 'i', 'Î': 'I', 'ș': 's', 'Ș': 'S',
        'ț': 't', 'Ț': 'T',
    }
    
    def __init__(self):
        pass
    
    def get_common_allowed_chars(self):
        """Get string of common special characters allowed in file names across OSes"""
        # Characters safe for Windows, macOS, Linux, and cloud services
        # Includes: space, period, hyphen, underscore, plus some brackets and punctuation
        # Note: Windows doesn't allow: < > : " | ? * \
        # macOS doesn't allow: :
        # Most cloud services are more restrictive
        return " -_.()[]{}!@#$%^&+=,;'`"
    
    def is_standard_ascii(self, char: str, ignore_chars: set = None) -> bool:
        """
        Check if character is standard ASCII (printable ASCII 32-126)
        Excluding characters in ignore_chars set
        """
        if ignore_chars and char in ignore_chars:
            return True
            
        # Standard ASCII printable range is 32-126
        return 32 <= ord(char) <= 126
    
    def find_non_standard_ascii(self, text: str, ignore_chars: set = None) -> set:
        """
        Find all non-standard ASCII characters in text
        Returns set of characters that are not standard ASCII
        """
        bad_chars = set()
        for char in text:
            if not self.is_standard_ascii(char, ignore_chars):
                bad_chars.add(char)
        return bad_chars
    
    def replace_accented_chars(self, text: str, ignore_chars: set = None) -> str:
        """
        Replace accented characters with unaccented equivalents
        Only handles accented characters, leaves other non-ASCII alone if not in ignore_chars
        """
        result = []
        for char in text:
            if char in ignore_chars:
                result.append(char)
            elif char in self.ACCENT_MAP:
                result.append(self.ACCENT_MAP[char])
            elif self.is_standard_ascii(char, ignore_chars):
                result.append(char)
            else:
                # Non-accented non-ASCII character - keep it
                result.append(char)
        return ''.join(result)
    
    def remove_bad_chars(self, text: str, ignore_chars: set = None) -> str:
        """
        Remove all non-standard ASCII characters
        """
        result = []
        for char in text:
            if self.is_standard_ascii(char, ignore_chars):
                result.append(char)
        return ''.join(result)
    
    def auto_fix_name(self, text: str, ignore_chars: set = None) -> str:
        """
        Auto-fix: replace accented chars with equivalents, remove other non-ASCII
        """
        # First replace accented characters
        text = self.replace_accented_chars(text, ignore_chars)
        # Then remove any remaining non-standard ASCII
        text = self.remove_bad_chars(text, ignore_chars)
        return text
    
    def normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode characters using NFD decomposition
        Useful for some edge cases
        """
        return unicodedata.normalize('NFD', text)

