import re
import fitz
import pytesseract
from PIL import Image
import io


def from_bookmarks(doc, min_useful_ratio=0.5):
    """
    Returns a list of {"title": str, "page": int} from the PDF's own
    embedded bookmarks — or None if there are no bookmarks, or if they
    look like scanning-software junk rather than a real table of contents.

    Confirmed real case: one sample catalogue has 417 "bookmarks" for its
    416 pages, each one just named after the original scanned page's
    filename (e.g. "1.pdf", "2.pdf"...) — not real section titles. A
    document with (roughly) one bookmark per page, mostly matching an
    "N.pdf" pattern, is treated as having no usable bookmarks at all.
    """
    toc = doc.get_toc()
    if not toc:
        return None

    filename_like = sum(1 for _, title, _ in toc if re.fullmatch(r"\d+(\.pdf)?", title.strip(), re.IGNORECASE))
    one_per_page_ish = len(toc) >= len(doc) * min_useful_ratio

    if filename_like / len(toc) > 0.5 and one_per_page_ish:
        return None  # junk — one bookmark per page named after scan files

    return [{"title": title.strip(), "page": page} for _, title, page in toc]


# Matches an entry that's entirely on one line — confirmed this is how
# OCR output (PSM 4) lays a TOC entry out: code, title, and the trailing
# page number all together, e.g. "255 Pedály . i 195".
ENTRY_ONE_LINE = re.compile(r"^[×xX+]?\s*(\d{2,4}[A-Za-z]?)\s+(.+?)\s+(\d{1,4})\s*$")

# A line that's ONLY a group code — confirmed this is how a real embedded
# text layer lays a TOC entry out instead: the code, title, multilingual
# description, and page number each land on their own separate line
# (get_text() inserts a line break per positioned text span, not per
# visual table row, so the two extraction sources produce genuinely
# different line structures for the same printed table).
CODE_ONLY_LINE = re.compile(r"^[×xX+]?\s*(\d{2,4}[A-Za-z]?)\s*$")
NUMBER_ONLY_LINE = re.compile(r"^(\d{1,4})\s*$")


def _fix_ocr_digits(s):
    """
    Corrects common OCR letter/digit confusions — only ever applied when
    trying to interpret something AS a number (a group code or page
    number), never to real title/description text. Confirmed necessary
    on a real lower-quality scan where '0' was consistently misread as
    the letter 'O' (e.g. "O15" instead of "015"). Doesn't catch every
    case — '99' misread as 'gg' on the same real page is a more severe
    failure this can't recover, and that's a disclosed known limitation
    on badly degraded scans, not something silently hidden.
    """
    subs = {"O": "0", "o": "0", "l": "1", "I": "1", "L": "1", "S": "5", "B": "8"}
    return "".join(subs.get(c, c) for c in s)


def _match_with_fallback(pattern, line):
    """Tries a line against `pattern` as-is first, then again with OCR
    digit-correction applied, and returns whichever matches (or None)."""
    return pattern.match(line) or pattern.match(_fix_ocr_digits(line))


def from_printed_toc(doc, has_text_layer, max_pages=10, dpi=300):
    """
    Parses the catalogue's own printed table of contents (confirmed
    present on real samples even when there are no real PDF bookmarks)
    into {"title", "page"} dicts.

    Handles two genuinely different real line structures, since testing
    showed the source matters, not just the printed layout: OCR output
    tends to keep a whole entry (code + title + page number) on one line;
    a real embedded text layer instead splits each field onto its own
    line. Both are tried per line, in a small state machine, so this
    works regardless of which source produced the text.
    """
    entries = []
    pages_to_check = min(max_pages, len(doc))
    pending_code = None
    pending_title = None

    for i in range(pages_to_check):
        if has_text_layer:
            text = doc[i].get_text()
        else:
            pix = doc[i].get_pixmap(dpi=dpi)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(image, lang="slk+eng", config="--psm 4")

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            one_line = ENTRY_ONE_LINE.match(line)
            if one_line:
                code, title, page_num = one_line.groups()
                entries.append({"title": f"{code} {title}".strip(), "page": int(page_num)})
                pending_code = pending_title = None
                continue

            if pending_code is None:
                code_only = _match_with_fallback(CODE_ONLY_LINE, line)
                if code_only:
                    pending_code = code_only.group(1)
                continue

            if pending_title is None:
                pending_title = line
                continue

            number_only = _match_with_fallback(NUMBER_ONLY_LINE, line)
            if number_only:
                entries.append({
                    "title": f"{pending_code} {pending_title}".strip(),
                    "page": int(number_only.group(1)),
                })
                pending_code = pending_title = None
            # otherwise: a multilingual description line — ignored, still
            # waiting for the trailing page-number line to close the entry

    return _filter_plausible_entries(entries)


def _filter_plausible_entries(entries):
    """
    Defensive filter, not a fix for the root parsing problem: drops
    entries that are clearly broken (a title that's basically just
    digits, or absurdly short) rather than silently writing garbage
    Section rows to the database.
    """
    plausible = []
    for e in entries:
        title = e["title"]
        letters = sum(1 for c in title if c.isalpha())
        if letters < 3:
            continue
        plausible.append(e)
    return plausible