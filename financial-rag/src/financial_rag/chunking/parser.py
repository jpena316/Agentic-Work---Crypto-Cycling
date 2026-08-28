"""Parsers that turn raw 10-K HTML and transcript text into ordered sections."""

import re
import warnings
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Matches standalone "Item 1.", "Item 7A.", "ITEM 1A -" style headers on their own line.
_ITEM_HEADER_RE = re.compile(r"^item\s+\d+[a-z]?\.?\s*[-–—:]?\s*\S.*$", re.IGNORECASE)
_ITEM_HEADER_MAX_LEN = 150

# "Lynne M. Maxeiner: Good morning..." — speaker + speech on the same line.
_COLON_SPEAKER_RE = re.compile(
    r"^([A-Z][a-zA-Z.'-]*(?:\s[A-Z][a-zA-Z.'-]*){0,3})\s*:\s+(\S.*)$"
)
# "Jimmy Sexton -- Head of Investor Relations" — speaker + title, speech follows on later lines.
_DASH_SPEAKER_RE = re.compile(
    r"^([A-Z][a-zA-Z.'-]*(?:\s[A-Z][a-zA-Z.'-]*){0,3})\s+--\s+(\S.*)$"
)
_NAME_WORD_RE = re.compile(r"^[A-Z][a-z'-]*\.?$")


def _is_valid_speaker_name(name: str) -> bool:
    """Reject false positives like glossary terms ('OneCore:', 'CDU:') which
    aren't capitalized-word-per-token the way a person's name is."""
    words = name.split()
    if not (1 <= len(words) <= 4):
        return False
    return all(_NAME_WORD_RE.match(w) for w in words)


def parse_10k(path: str | Path) -> list[dict]:
    """Parse a 10-K HTML filing into a list of {section, text} dicts, one per Item."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    for tag in soup(["script", "style", "head"]):
        tag.decompose()

    raw_text = soup.get_text("\n")
    lines = [line.strip() for line in raw_text.splitlines()]
    lines = [line for line in lines if line]

    sections: list[dict] = []
    current_section = "Preamble"
    current_lines: list[str] = []

    for line in lines:
        is_header = len(line) <= _ITEM_HEADER_MAX_LEN and bool(_ITEM_HEADER_RE.match(line))
        if is_header:
            if current_lines:
                sections.append({"section": current_section, "text": "\n".join(current_lines)})
            current_section = line
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({"section": current_section, "text": "\n".join(current_lines)})

    return sections


def parse_transcript(path: str | Path) -> list[dict]:
    """Parse an earnings call transcript into a list of {section, text} dicts,
    one per speaker turn. Section is the speaker's name."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    sections: list[dict] = []
    current_speaker: str | None = None
    current_paragraphs: list[str] = []

    def flush() -> None:
        if current_speaker is None:
            return
        body = "\n\n".join(current_paragraphs).strip()
        if body:
            sections.append({"section": current_speaker, "text": body})

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        colon_match = _COLON_SPEAKER_RE.match(stripped)
        dash_match = _DASH_SPEAKER_RE.match(stripped)

        if colon_match and _is_valid_speaker_name(colon_match.group(1)):
            flush()
            current_speaker = colon_match.group(1)
            current_paragraphs = [colon_match.group(2)]
        elif dash_match and _is_valid_speaker_name(dash_match.group(1)):
            flush()
            current_speaker = dash_match.group(1)
            current_paragraphs = []
        elif current_speaker is not None:
            current_paragraphs.append(stripped)
        # else: preamble/nav noise before the first recognized speaker turn — skip.

    flush()
    return sections
