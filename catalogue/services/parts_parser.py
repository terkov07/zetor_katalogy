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


def parse_parts_from_text(text, page_number):
    """
    Scans a page's text (from either a real text layer or OCR output —
    the caller decides which) line by line for order-number patterns,
    and builds a best-effort {part_number, name, position_no, page} dict
    for each one found.

    KNOWN LIMITATION (confirmed by testing against real catalogues):
    order-number extraction is reliable; name/position association is
    NOT yet reliable on the stacked layout, where OCR line-wrapping
    breaks the simple "look at nearby lines" heuristic more often than
    expected. Ship as-is for now — every extracted Part should stay
    linked back to its real page image (see master spec risk register:
    treat as assistive, not authoritative) — and revisit this once
    Step 7 lets it run against full real catalogues, where the actual
    failure patterns will be easier to see and fix than from single
    isolated pages.
    """
    lines = [l.strip() for l in text.splitlines()]
    parts = []

    for i, line in enumerate(lines):
        # Peel off a leading position number FIRST, before searching for
        # the order number in the rest of the line. Tested finding: doing
        # this the other way round let the order-number regex accidentally
        # swallow the position number as its own first digit-group on
        # real grid-layout rows, corrupting the match (e.g. matching
        # "17 531 980 002" instead of the real "531 980 002 034").
        pos_match = LEADING_NUMBER.match(line)
        line_position_no = pos_match.group(1) if pos_match else ""
        remainder = line[pos_match.end():].strip(" -–—.") if pos_match else line

        matches = list(ORDER_NUMBER.finditer(remainder))
        if not matches:
            continue

        order_no = matches[0].group()
        same_line_name = remainder[matches[0].end():].strip(" -–—")
        position_no = line_position_no

        if same_line_name and not MODEL_CODE_LINE.match(same_line_name):
            name = same_line_name
        else:
            name = ""
            for j in range(i - 1, max(i - 5, -1), -1):
                candidate = lines[j]
                if not candidate or MODEL_CODE_LINE.match(candidate):
                    continue
                if ORDER_NUMBER.search(candidate):
                    continue
                if not position_no:
                    cand_pos = LEADING_NUMBER.match(candidate)
                    if cand_pos:
                        position_no = cand_pos.group(1)
                name = LEADING_NUMBER.sub("", candidate).strip(" -–—.")
                break

        parts.append({
            "part_number": order_no.strip(),
            "name": name,
            "position_no": position_no,
            "page": page_number,
        })

    return parts