"""
Robust Text Sanitization and Normalization for Document Parsers.
Handles NUL bytes, broken control characters, encoding artifacts, and letter-spaced headings
while strictly PRESERVING legitimate Unicode (accents, international names, technical symbols).
"""

import re
import unicodedata


def sanitize_text(text: str) -> str:
    """
    Cleans extracted document text for safe database storage and LLM ingestion.
    
    1. Removes NUL bytes (\x00) to prevent PostgreSQL 22P05 errors.
    2. Strips genuinely invalid control characters (ASCII < 32 except \t, \n, \r, and DEL/C1).
    3. Normalizes replacement characters (\ufffd) into bullets or apostrophes based on context.
    4. Preserves all valid Unicode (e.g., é, è, ü, ñ, ç, Dutch/French/German characters).
    5. Normalizes excessive whitespace and blank lines.
    """
    if not text:
        return ""

    # 1. Remove NUL characters (\x00)
    cleaned = text.replace("\x00", "")

    # 2. Context-aware replacement of \ufffd (Unicode replacement character)
    # Between letters (e.g., lIndustrie -> l'Industrie, cdric -> cédric)
    cleaned = re.sub(r"(?<=[a-zA-Z])\ufffd(?=[a-zA-Z])", "'", cleaned)
    # At start of string, start of line, or bullet item
    cleaned = re.sub(r"(?:^|(?<=[\n\r]))\s*\ufffd\s*", "• ", cleaned)
    cleaned = re.sub(r"\s+\ufffd\s+", " • ", cleaned)
    # Any remaining replacement character
    cleaned = cleaned.replace("\ufffd", " ")

    # 3. Strip genuinely invalid control characters while preserving \t, \n, \r
    # Legitimate Unicode characters (including Latin-1 Supplement, Latin Extended, etc.) are kept intact.
    chars = []
    for ch in cleaned:
        code = ord(ch)
        if code in (9, 10, 13):  # \t, \n, \r
            chars.append(ch)
        elif code < 32 or (127 <= code <= 159):  # ASCII control codes and C1 control characters
            chars.append(" ")
        else:
            chars.append(ch)
    cleaned = "".join(chars)

    # 4. Normalize common Unicode quotes and dashes to clean standard representations
    cleaned = cleaned.replace("\u2018", "'").replace("\u2019", "'")
    cleaned = cleaned.replace("\u201c", '"').replace("\u201d", '"')
    cleaned = cleaned.replace("\u2013", "-").replace("\u2014", "-")
    cleaned = cleaned.replace("\u00a0", " ")  # Non-breaking space

    # 5. Normalize excessive whitespace while preserving paragraph structure
    # Replace sequences of 3+ newlines with 2 newlines
    cleaned = re.sub(r"\r\n", "\n", cleaned)
    cleaned = re.sub(r"\r", "\n", cleaned)
    # Clean trailing whitespace per line
    lines = [re.sub(r"[ \t]+$", "", line) for line in cleaned.split("\n")]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def reconstruct_spaced_headings(text: str) -> str:
    """
    Detects and reconstructs spaced-out headings commonly found in designer PDF resumes.
    Example: 'W O R K   E X P E R I E N C E' -> 'WORK EXPERIENCE'
    Example: 'J E R E M Y   S C H E P P E R S' -> 'JEREMY SCHEPPERS'
    """
    if not text:
        return ""

    lines = text.split("\n")
    reconstructed_lines = []

    for line in lines:
        stripped = line.strip()
        # Check if line contains a sequence of single letters separated by spaces
        # e.g., 'W O R K   E X P E R I E N C E' or 'S K I L L S & C O M P E T E N C I E S'
        tokens = stripped.split()
        single_chars = [t for t in tokens if len(t) == 1 and t.isalnum()]
        if len(tokens) >= 4 and len(single_chars) / len(tokens) >= 0.70:
            # First preserve double-or-more space boundaries
            protected = re.sub(r" {2,}", " __WORD_BOUNDARY__ ", stripped)
            # Collapse single spaces between single letters
            collapsed = re.sub(r"(?<=\b[A-Za-z]) (?=[A-Za-z]\b)", "", protected)
            collapsed = collapsed.replace("__WORD_BOUNDARY__", " ")
            reconstructed_lines.append(re.sub(r"\s+", " ", collapsed).strip())
        else:
            reconstructed_lines.append(line)

    return "\n".join(reconstructed_lines)
