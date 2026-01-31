"""Vietnamese text processing utilities."""

import re
import unicodedata
from typing import Optional


class VietnameseTextProcessor:
    """Utility class for processing Vietnamese text."""

    # Vietnamese diacritics mapping
    VIETNAMESE_DIACRITICS = {
        "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
        "ă": "a", "ằ": "a", "ắ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a",
        "â": "a", "ầ": "a", "ấ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
        "đ": "d",
        "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
        "ê": "e", "ề": "e", "ế": "e", "ể": "e", "ễ": "e", "ệ": "e",
        "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
        "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
        "ô": "o", "ồ": "o", "ố": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
        "ơ": "o", "ờ": "o", "ớ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
        "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
        "ư": "u", "ừ": "u", "ứ": "u", "ử": "u", "ữ": "u", "ự": "u",
        "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
        # Uppercase
        "À": "A", "Á": "A", "Ả": "A", "Ã": "A", "Ạ": "A",
        "Ă": "A", "Ằ": "A", "Ắ": "A", "Ẳ": "A", "Ẵ": "A", "Ặ": "A",
        "Â": "A", "Ầ": "A", "Ấ": "A", "Ẩ": "A", "Ẫ": "A", "Ậ": "A",
        "Đ": "D",
        "È": "E", "É": "E", "Ẻ": "E", "Ẽ": "E", "Ẹ": "E",
        "Ê": "E", "Ề": "E", "Ế": "E", "Ể": "E", "Ễ": "E", "Ệ": "E",
        "Ì": "I", "Í": "I", "Ỉ": "I", "Ĩ": "I", "Ị": "I",
        "Ò": "O", "Ó": "O", "Ỏ": "O", "Õ": "O", "Ọ": "O",
        "Ô": "O", "Ồ": "O", "Ố": "O", "Ổ": "O", "Ỗ": "O", "Ộ": "O",
        "Ơ": "O", "Ờ": "O", "Ớ": "O", "Ở": "O", "Ỡ": "O", "Ợ": "O",
        "Ù": "U", "Ú": "U", "Ủ": "U", "Ũ": "U", "Ụ": "U",
        "Ư": "U", "Ừ": "U", "Ứ": "U", "Ử": "U", "Ữ": "U", "Ự": "U",
        "Ỳ": "Y", "Ý": "Y", "Ỷ": "Y", "Ỹ": "Y", "Ỵ": "Y",
    }

    # Common Vietnamese military academy name variations
    SCHOOL_ALIASES = {
        "hvktqs": "học viện kỹ thuật quân sự",
        "hvqs": "học viện quân sự",
        "hvqy": "học viện quân y",
        "hvbc": "học viện biên chống",
        "hvpkkq": "học viện phòng không không quân",
        "ktqs": "kỹ thuật quân sự",
        "truong sq": "trường sĩ quan",
        "sq": "sĩ quan",
        "cb": "công binh",
        "tt": "thông tin",
        "pkkq": "phòng không không quân",
        "hq": "hải quân",
        "bca": "bộ công an",
        "ca": "công an",
        "qđ": "quân đội",
        "qs": "quân sự",
    }

    @classmethod
    def remove_diacritics(cls, text: str) -> str:
        """Remove Vietnamese diacritics from text.

        Args:
            text: Vietnamese text with diacritics.

        Returns:
            Text without diacritics.
        """
        result = []
        for char in text:
            if char in cls.VIETNAMESE_DIACRITICS:
                result.append(cls.VIETNAMESE_DIACRITICS[char])
            else:
                result.append(char)
        return "".join(result)

    @classmethod
    def normalize_text(cls, text: str, lowercase: bool = True) -> str:
        """Normalize Vietnamese text for search/comparison.

        Args:
            text: Input text.
            lowercase: Convert to lowercase.

        Returns:
            Normalized text.
        """
        # Unicode normalization
        text = unicodedata.normalize("NFC", text)

        # Remove diacritics
        text = cls.remove_diacritics(text)

        # Lowercase
        if lowercase:
            text = text.lower()

        # Normalize whitespace
        text = " ".join(text.split())

        return text

    @classmethod
    def expand_abbreviations(cls, text: str) -> str:
        """Expand common Vietnamese abbreviations.

        Args:
            text: Text with abbreviations.

        Returns:
            Text with expanded abbreviations.
        """
        text_lower = text.lower()

        for abbrev, full in cls.SCHOOL_ALIASES.items():
            # Word boundary matching
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            text_lower = re.sub(pattern, full, text_lower)

        return text_lower

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Clean and normalize text for processing.

        Args:
            text: Raw input text.

        Returns:
            Cleaned text.
        """
        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove special characters but keep Vietnamese
        text = re.sub(r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]", " ", text)

        # Normalize whitespace again
        text = " ".join(text.split())

        return text.strip()

    @classmethod
    def extract_numbers(cls, text: str) -> list[float]:
        """Extract all numbers from text.

        Args:
            text: Input text.

        Returns:
            List of extracted numbers.
        """
        # Match integers and decimals
        pattern = r"\d+(?:[.,]\d+)?"
        matches = re.findall(pattern, text)

        numbers = []
        for match in matches:
            # Convert to float (handle Vietnamese decimal separator)
            match = match.replace(",", ".")
            try:
                numbers.append(float(match))
            except ValueError:
                continue

        return numbers

    @classmethod
    def extract_year(cls, text: str) -> Optional[int]:
        """Extract year from text.

        Args:
            text: Input text containing year.

        Returns:
            Extracted year or None.
        """
        # Match 4-digit years (2000-2099)
        pattern = r"\b(20[0-9]{2})\b"
        match = re.search(pattern, text)

        if match:
            return int(match.group(1))

        # Also check for short form (năm 24 = 2024)
        short_pattern = r"\b(?:năm|nam)\s*(\d{2})\b"
        match = re.search(short_pattern, text.lower())
        if match:
            year = int(match.group(1))
            if year < 50:
                return 2000 + year
            else:
                return 1900 + year

        return None

    @classmethod
    def extract_score(cls, text: str) -> Optional[float]:
        """Extract admission score from text.

        Args:
            text: Input text containing score.

        Returns:
            Extracted score or None.
        """
        # Common patterns for scores
        patterns = [
            r"(\d{1,2}(?:[.,]\d+)?)\s*điểm",
            r"điểm\s*(?:là|:)?\s*(\d{1,2}(?:[.,]\d+)?)",
            r"(\d{1,2}(?:[.,]\d+)?)\s*(?:khối|block)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                score_str = match.group(1).replace(",", ".")
                try:
                    score = float(score_str)
                    # Validate score range (0-30 for Vietnam)
                    if 0 <= score <= 30:
                        return score
                except ValueError:
                    continue

        # Fallback: look for standalone numbers that could be scores
        numbers = cls.extract_numbers(text)
        for num in numbers:
            if 15 <= num <= 30:  # Reasonable score range
                return num

        return None

    @classmethod
    def extract_khoi_thi(cls, text: str) -> Optional[str]:
        """Extract exam subject group (khối thi) from text.

        Args:
            text: Input text.

        Returns:
            Khoi thi code (A00, A01, B00, etc.) or None.
        """
        # Pattern for khoi thi codes
        pattern = r"\b([ABCD]\d{2})\b"
        match = re.search(pattern, text.upper())

        if match:
            return match.group(1)

        # Also check for text descriptions
        khoi_mapping = {
            "khối a": "A00",
            "khoi a": "A00",
            "a": "A00",
            "khối b": "B00",
            "khoi b": "B00",
            "b": "B00",
            "khối c": "C00",
            "khoi c": "C00",
            "c": "C00",
            "khối d": "D01",
            "khoi d": "D01",
            "d": "D01",
        }

        text_lower = cls.normalize_text(text)
        for key, value in khoi_mapping.items():
            if key in text_lower:
                return value

        return None

    @classmethod
    def is_question(cls, text: str) -> bool:
        """Check if text is a question.

        Args:
            text: Input text.

        Returns:
            True if text appears to be a question.
        """
        text_lower = text.lower().strip()

        # Question marks
        if "?" in text:
            return True

        # Vietnamese question words
        question_words = [
            "bao nhiêu", "bao nhieu",
            "như thế nào", "nhu the nao",
            "thế nào", "the nao",
            "làm sao", "lam sao",
            "tại sao", "tai sao",
            "vì sao", "vi sao",
            "ở đâu", "o dau",
            "khi nào", "khi nao",
            "ai",
            "gì", "gi",
            "nào", "nao",
            "có thể", "co the",
            "có phải", "co phai",
            "có không", "co khong",
            "được không", "duoc khong",
            "cho hỏi", "cho hoi",
            "xin hỏi",
        ]

        for qword in question_words:
            if qword in text_lower:
                return True

        return False


# Singleton instance for convenience
processor = VietnameseTextProcessor()
