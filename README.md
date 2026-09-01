# Zetor Katalógy

A personal web app for browsing, searching, and organising ZETOR tractor parts catalogues, workshop manuals, and modification catalogues. Built for one sole-trader mechanic's own use — not a commercial product.

## Features

- Browse catalogues by tractor model (one catalogue can cover several models at once)
- Catalogues split into browsable sections instead of scrolling hundreds of pages
- Search by part number (dash/space-insensitive partial match) or by text
- View PDFs directly in the browser
- OCR fallback for scanned catalogues with no text layer (Slovak + English)
- "Jobs" — pin parts and notes to a specific work order/customer
- Django admin panel for adding tractor models and uploading catalogues

## Tech stack

- Python 3 / Django
- SQLite
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (via `pytesseract`), with the Slovak language pack
- Plain HTML/CSS/JS — no frontend framework, no build step
- The browser's own built-in PDF viewer (no vendored PDF.js, for now)

## Getting started

### Prerequisites

- Python 3.12+
- Tesseract OCR installed locally, with the **Slovak (`slk`)** language pack — on Windows, use the [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki) and tick Slovak during setup

### Setup

```bash
git clone https://github.com/terkov07/zetor_katalogy.git
cd zetor_katalogy
python -m venv venv
source venv/Scripts/activate   # venv/bin/activate on Mac/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` to add a tractor model and upload a catalogue PDF.

### Processing a catalogue

After uploading a catalogue through the admin panel, find its ID (visible in the admin page's URL) and run:

```bash
python manage.py process_catalogue <id>
```

This detects whether the PDF already has a text layer, finds its section structure (real PDF bookmarks, falling back to reading the catalogue's own printed table of contents), splits it into per-section files, and — for parts/modification catalogues — extracts part numbers into a searchable index.

Scanned catalogues with no text layer go through OCR page by page and can take several minutes on a large document.

## Project structure
- catalogue/
- models.py — TractorModel, Catalogue, Section, Part, Job, JobPin
- views.py — browsing, viewer, search, jobs
- services/ — the processing pipeline
- text_detection.py — checks for a real text layer
- ocr.py — OCR fallback (Tesseract, Slovak + English)
- toc_parser.py — finds sections via bookmarks or the printed TOC
- parts_parser.py — extracts part numbers/names from page text
- splitter.py — splits a catalogue into per-section PDFs
- management/commands/
- process_catalogue.py — runs the full pipeline on one catalogue
- templates/catalogue/
- static/
- css/app.css 

## Known limitations

- **Section detection on catalogues with a real (non-OCR) text layer** isn't fully reliable yet — page-number associations can come out wrong. Works well on scanned/OCR'd catalogues.
- **Part name matching** — part numbers extract reliably; matching the correct name to each number is inconsistent on some table layouts. Numbers and page links are always correct; names occasionally need manual correction via the admin panel.
- Both of the above are treated as assistive, not authoritative — always check the real page if a section or name looks wrong.

## Roadmap

- [ ] Offline downloads (per section)
- [ ] Installable PWA (manifest + service worker)
- [ ] Dark mode
- [ ] Slovak/English UI toggle
- [ ] Deployment to Railway
- [ ] Improve text-layer table-of-contents parsing
- [ ] Improve part name/position matching accuracy

## Status

Personal-use project, in active development. Core loop (browse → search → view → pin to job) is working end to end on real catalogue data.