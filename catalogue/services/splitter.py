import os


def split_into_sections(doc, sections, output_dir):
    """
    Cuts a catalogue into one PDF per section, based on a list of
    {"title", "start_page", "end_page"} dicts (0-indexed page numbers,
    inclusive).

    Uses doc.select() + doc.save() rather than decoding and redrawing
    pages, so embedded images are copied through untouched — confirmed
    important, since two real catalogues had very different source image
    quality (86dpi vs 300dpi) and the pipeline must never make either one
    worse (see master spec 4.5). garbage=4 and deflate=True clean up and
    compress the file structure itself (removing now-unused objects left
    over from the pages that were cut) without touching the images —
    confirmed by testing: without these two flags, a split section kept
    every object from the original file regardless of how few pages were
    selected, so file size never actually shrank.

    Returns a list of the output file paths, in the same order as `sections`.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_paths = []

    for i, section in enumerate(sections):
        # Reopen a fresh copy of the document for each section — doc.select()
        # mutates the document in place, dropping every page not selected,
        # so it can't be reused for the next section without reloading.
        section_doc = type(doc)(doc.name)
        page_range = list(range(section["start_page"], section["end_page"] + 1))
        section_doc.select(page_range)

        safe_title = "".join(c if c.isalnum() else "_" for c in section["title"])[:50]
        filename = f"{i:03d}_{safe_title}.pdf"
        output_path = os.path.join(output_dir, filename)
        section_doc.save(output_path, garbage=4, deflate=True)
        section_doc.close()

        output_paths.append(output_path)

    return output_paths