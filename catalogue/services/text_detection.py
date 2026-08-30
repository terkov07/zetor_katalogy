import fitz  # PyMuPDF


def has_text_layer(doc, sample_pages=5, min_chars=50):
    """
    Checks whether a PDF already has a real, extractable text layer
    (as opposed to being a raw scan with no text at all).

    Samples the first few pages rather than the whole document, since
    that's enough to tell the difference and is much faster on a
    400+ page catalogue.
    """
    pages_to_check = min(sample_pages, len(doc))
    sample_text = "".join(doc[i].get_text() for i in range(pages_to_check))
    return len(sample_text.strip()) > min_chars