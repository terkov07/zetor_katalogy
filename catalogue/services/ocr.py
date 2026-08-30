import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# Only needed if `tesseract --version` doesn't work in your terminal —
# tells pytesseract exactly where the Tesseract program is installed.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def ocr_page(doc, page_number, lang="slk+eng", dpi=300):
    """
    Runs OCR on a single page of a scanned (no-text-layer) PDF and
    returns the extracted text as a plain string.

    lang="slk+eng" runs Slovak and English recognition together, since
    the real catalogues mix Slovak part names with numeric/Latin
    order codes — this combination reads both accurately.

    dpi=300 matches the resolution the sharper real sample was actually
    scanned at (see master spec 4.5) — rendering higher than the source
    doesn't add real accuracy, just processing time.
    """
    page = doc[page_number]
    pix = page.get_pixmap(dpi=dpi)
    image = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(image, lang=lang)