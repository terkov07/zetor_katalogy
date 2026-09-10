import re

# Real Zetor order-number formats confirmed across two real catalogues:
#   "531 980 002 084"   — space-separated, 4 groups
#   "80.005.002"        — dot-separated, 3 groups
#   "99 2549"           — short 2-group form
#   "CSN 02 1176.25" / "PNZ 32 0203" — standard reference numbers
ORDER_NUMBER = re.compile(
    r"\b\d{2,3}[ ]\d{3}[ ]\d{3}[ ]\d{2,4}[xX]?\b"
    r"|\b\d{2,3}\.\d{3}\.\d{3}[xX]?\b"
    r"|\b\d{2}[ ]\d{3,4}\b"
    r"|\b(?:CSN|PNZ)\s?\d{2}\s?\d{3,4}(?:\.\d+)?\b"
)

# A standalone small number at the very start of a line — a plausible
# position number in either table layout.
LEADING_NUMBER = re.compile(r"^\s*[×xX+]?\s*(\d{1,3})\b")

# Lines that are just model codes (e.g. "Z 8011, Z 8045") aren't part
# names — skip them when searching backward for the real name text.
MODEL_CODE_LINE = re.compile(r"^[\sZz0-9,]+$")


def _looks_like_a_real_name(text):
    """
    Stricter check than MODEL_CODE_LINE / ORDER_NUMBER alone: rejects a
    candidate name line that's mostly digits/punctuation even when it
    doesn't exactly match the order-number pattern.

    Confirmed necessary: a real observed bug had a garbled, slightly
    OCR-mangled order number (a typo/misread digit) get accepted as a
    part's "name" because it didn't exactly match ORDER_NUMBER's strict
    pattern, but it also wasn't caught by the model-code check. A real
    Slovak/German/English part name is mostly letters; this requires
    at least a third of the characters to be alphabetic before trusting
    a line as a name.
    """
    if not text:
        return False
    letters = sum(1 for c in text if c.isalpha())
    return letters / len(text) >= 0.35


def parse_parts_from_text(text, page_number):
    """
    Scans a page's text (from either a real text layer or OCR output —
    the caller decides which) line by line for order-number patterns,
    and builds a best-effort {part_number, name, position_no, page} dict
    for each one found.

    Deliberately does NOT attempt to parse the per-model quantity columns
    — confirmed too unreliable to trust from OCR/flattened text alone.
    Order number and name are the high-confidence fields this extracts;
    position number is best-effort and should be treated as assistive,
    not authoritative — always one tap from the real page image to
    double-check.
    """
    lines = [l.strip() for l in text.splitlines()]
    parts = []

    for i, line in enumerate(lines):
        pos_match = LEADING_NUMBER.match(line)
        line_position_no = pos_match.group(1) if pos_match else ""
        remainder = line[pos_match.end():].strip(" -–—.") if pos_match else line

        matches = list(ORDER_NUMBER.finditer(remainder))
        if not matches:
            continue

        order_no = matches[0].group()
        same_line_name = remainder[matches[0].end():].strip(" -–—")
        position_no = line_position_no

        if same_line_name and _looks_like_a_real_name(same_line_name):
            name = same_line_name
        else:
            name = ""
            for j in range(i - 1, max(i - 5, -1), -1):
                candidate = lines[j]
                if not candidate or MODEL_CODE_LINE.match(candidate):
                    continue
                if ORDER_NUMBER.search(candidate):
                    continue
                candidate_name = LEADING_NUMBER.sub("", candidate).strip(" -–—.")
                if not _looks_like_a_real_name(candidate_name):
                    continue
                if not position_no:
                    cand_pos = LEADING_NUMBER.match(candidate)
                    if cand_pos:
                        position_no = cand_pos.group(1)
                name = candidate_name
                break

        parts.append({
            "part_number": order_no.strip(),
            "name": name,
            "position_no": position_no,
            "page": page_number,
        })

    return parts