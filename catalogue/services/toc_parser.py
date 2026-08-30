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


# Matches a TOC entry's start-of-line: an optional × or + marker (seen on
# real samples marking optional/variant parts), then a group/position code
# (digits, optionally with a trailing letter like "261" or "306A"), then
# the title text, then — somewhere later on the same line — the page
# number, usually preceded by a run of OCR-mangled dot-leaders.
ENTRY_START = re.compile(r"^[×xX+]?\s*(\d{2,4}[A-Za-z]?)\s+(.+?)\s+(\d{1,4})\s*$")


def from_printed_toc(doc, has_text_layer, max_pages=10, dpi=300):
    """
    Parses the catalogue's own printed table of contents (confirmed present
    on real samples even when there are no real PDF bookmarks) into the
    same {"title", "page"} shape as from_bookmarks, so callers don't need
    to care which source was used.

    Reads real embedded text if available; otherwise OCRs each of the
    first `max_pages` pages using PSM 4 (single variable-width column),
    which — confirmed by testing against a real sample — preserves the
    trailing page-number column noticeably better than default OCR
    settings do on this dot-leader table layout.
    """
    entries = []
    pages_to_check = min(max_pages, len(doc))

    for i in range(pages_to_check):
        if has_text_layer:
            text = doc[i].get_text()
        else:
            pix = doc[i].get_pixmap(dpi=dpi)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(image, lang="slk+eng", config="--psm 4")

        for line in text.splitlines():
            match = ENTRY_START.match(line.strip())
            if match:
                code, title, page_num = match.groups()
                entries.append({
                    "title": f"{code} {title}".strip(),
                    "page": int(page_num),
                })

    return entries