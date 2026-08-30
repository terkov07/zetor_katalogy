import re
import fitz
import pytesseract
from PIL import Image
import io


def from_bookmarks(doc, min_useful_ratio=0.5):
    toc = doc.get_toc()
    if not toc:
        return None

    filename_like = sum(1 for _, title, _ in toc if re.fullmatch(r"\d+(\.pdf)?", title.strip(), re.IGNORECASE))
    one_per_page_ish = len(toc) >= len(doc) * min_useful_ratio

    if filename_like / len(toc) > 0.5 and one_per_page_ish:
        return None

    return [{"title": title.strip(), "page": page} for _, title, page in toc]


ENTRY_ONE_LINE = re.compile(r"^[×xX+]?\s*(\d{2,4}[A-Za-z]?)\s+(.+?)\s+(\d{1,4})\s*$")
CODE_ONLY_LINE = re.compile(r"^[×xX+]?\s*(\d{2,4}[A-Za-z]?)\s*$")
NUMBER_ONLY_LINE = re.compile(r"^(\d{1,4})\s*$")


def from_printed_toc(doc, has_text_layer, max_pages=10, dpi=300):
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
                code_only = CODE_ONLY_LINE.match(line)
                if code_only:
                    pending_code = code_only.group(1)
                continue

            if pending_title is None:
                pending_title = line
                continue

            number_only = NUMBER_ONLY_LINE.match(line)
            if number_only:
                entries.append({
                    "title": f"{pending_code} {pending_title}".strip(),
                    "page": int(number_only.group(1)),
                })
                pending_code = pending_title = None

    return _filter_plausible_entries(entries)


def _filter_plausible_entries(entries):
    plausible = []
    for e in entries:
        letters = sum(1 for c in e["title"] if c.isalpha())
        if letters < 3:
            continue
        plausible.append(e)
    return plausible