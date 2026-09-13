"""Parsers that turn raw 10-K HTML and transcript text into ordered sections."""

import re
import warnings
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Matches standalone "Item 1. Business", "ITEM 7A - Quantitative..." style section
# headers, but not bare TOC entries like "Item 1A." with no title following — the
# mandatory \s+ before the title stops "A" (the sub-item letter) from being
# reinterpreted as the start of a (nonexistent) title via backtracking.
_ITEM_HEADER_RE = re.compile(r"^item\s+\d+[a-z]?\.?\s+[-–—:]?\s*[a-z]{2,}.*$", re.IGNORECASE)
_ITEM_HEADER_MAX_LEN = 150

# Running page headers/footers ("Table of Contents", "PART II.", bare page numbers)
# that EDGAR's HTML rendering repeats on every page — and, combined with the item
# number, also make each Item's table-of-contents row match _ITEM_HEADER_RE.
# Stripped before section-splitting so those TOC rows collapse to empty and get
# dropped, instead of shadowing the real section with the same title.
_NOISE_LINE_RE = re.compile(r"^(table of contents|part\s+[ivx]+\.?|\d+)$", re.IGNORECASE)

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


def _normalize_title(title: str) -> list[str]:
    return re.sub(r"[^\w\s]", "", title).lower().split()


def _dedupe_sections(sections: list[dict]) -> list[dict]:
    """Some filers' TOC rows repeat an Item's title verbatim with only casing/
    punctuation differences (e.g. "Item 5. Market..." vs "ITEM 5. MARKET...");
    with running headers/page-numbers already stripped, only real body text
    remains to tell them apart. Keep the ALL-CAPS variant — this filer's
    convention for real section headers — and fold any other same-titled
    section's text into Preamble instead of shadowing the real one."""
    groups: dict[tuple, list[int]] = {}
    for i, s in enumerate(sections):
        groups.setdefault(tuple(_normalize_title(s["section"])), []).append(i)

    drop: set[int] = set()
    preamble_extra: list[str] = []
    for indices in groups.values():
        if len(indices) < 2:
            continue
        all_caps = [i for i in indices if sections[i]["section"].isupper()]
        canonical = all_caps[0] if all_caps else max(indices, key=lambda i: len(sections[i]["text"]))
        for i in indices:
            if i != canonical:
                drop.add(i)
                preamble_extra.append(sections[i]["text"])

    result = [s for i, s in enumerate(sections) if i not in drop]
    if preamble_extra:
        for s in result:
            if s["section"] == "Preamble":
                s["text"] = "\n".join([s["text"], *preamble_extra])
                break
        else:
            result.insert(0, {"section": "Preamble", "text": "\n".join(preamble_extra)})
    return result


def parse_10k(path: str | Path) -> list[dict]:
    """Parse a 10-K HTML filing into a list of {section, text} dicts, one per Item."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    for tag in soup(["script", "style", "head", "ix:header"]):
        tag.decompose()

    raw_text = soup.get_text("\n")
    lines = [line.strip() for line in raw_text.splitlines()]
    lines = [line for line in lines if line and not _NOISE_LINE_RE.match(line)]

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

    # TOC rows repeat each Item's title verbatim, matching _ITEM_HEADER_RE just like
    # the real section header does; with running headers/page-numbers stripped above,
    # a TOC row's "body" is empty, so it can be dropped without touching real sections.
    sections = [s for s in sections if s["text"].strip()]
    return _dedupe_sections(sections)


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
