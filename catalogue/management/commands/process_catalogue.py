import os
import fitz  # PyMuPDF
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalogue.models import Catalogue, Section, Part
from catalogue.services.text_detection import has_text_layer
from catalogue.services.toc_parser import from_bookmarks, from_printed_toc
from catalogue.services.ocr import ocr_page
from catalogue.services.parts_parser import parse_parts_from_text
from catalogue.services.splitter import split_into_sections


class Command(BaseCommand):
    help = (
        "Process a Catalogue: detect its text layer, find its section "
        "structure (bookmarks, falling back to the printed table of "
        "contents), split it into per-section PDFs, and — for parts "
        "catalogues and modification catalogues — extract Part rows."
    )

    def add_arguments(self, parser):
        parser.add_argument("catalogue_id", type=int)

    def handle(self, *args, **options):
        try:
            catalogue = Catalogue.objects.get(id=options["catalogue_id"])
        except Catalogue.DoesNotExist:
            raise CommandError(f"No catalogue with id {options['catalogue_id']}")

        doc = fitz.open(catalogue.original_file.path)
        catalogue.page_count = len(doc)
        catalogue.rotation = doc[0].rotation if len(doc) else 0

        self.stdout.write("Checking for a text layer...")
        text_layer = has_text_layer(doc)
        catalogue.has_text_layer = text_layer
        catalogue.save()
        self.stdout.write(f"  has_text_layer = {text_layer}")

        self.stdout.write("Looking for section structure...")
        toc_entries = from_bookmarks(doc)
        source = "real bookmarks"
        if toc_entries is None:
            toc_entries = from_printed_toc(doc, has_text_layer=text_layer)
            source = "printed table of contents"
        self.stdout.write(f"  found {len(toc_entries)} entries via {source}")

        sections_data = self._entries_to_ranges(toc_entries, len(doc))

        self.stdout.write(f"Splitting into {len(sections_data)} section files...")
        output_dir = os.path.join(
            settings.MEDIA_ROOT, "catalogues", "sections", str(catalogue.id)
        )
        split_input = [
            {"title": s["title"], "start_page": s["start"], "end_page": s["end"]}
            for s in sections_data
        ]
        output_paths = split_into_sections(doc, split_input, output_dir)

        Section.objects.filter(catalogue=catalogue).delete()
        section_objs = []
        for i, (sdata, path) in enumerate(zip(sections_data, output_paths)):
            section = Section.objects.create(
                catalogue=catalogue,
                title=sdata["title"],
                start_page=sdata["start"],
                end_page=sdata["end"],
                order=i,
            )
            section.section_file.name = os.path.relpath(path, settings.MEDIA_ROOT)
            section.save()
            section_objs.append(section)

        if catalogue.type in ("parts_catalogue", "modification_catalogue"):
            self.stdout.write("Extracting parts (this is slow on scanned/OCR pages)...")
            Part.objects.filter(catalogue=catalogue).delete()
            total_parts = 0

            for page_num in range(len(doc)):
                page_text = doc[page_num].get_text() if text_layer else ocr_page(doc, page_num)
                parsed = parse_parts_from_text(page_text, page_number=page_num + 1)
                section_for_page = self._section_for_page(section_objs, page_num)

                for p in parsed:
                    Part.objects.create(
                        catalogue=catalogue,
                        section=section_for_page,
                        part_number=p["part_number"],
                        name_sk=p["name"],
                        page=p["page"],
                        position_no=p["position_no"],
                    )
                    total_parts += 1

                if page_num % 20 == 0:
                    self.stdout.write(f"  ...page {page_num + 1}/{len(doc)}")

            self.stdout.write(f"  extracted {total_parts} parts")

        self.stdout.write(self.style.SUCCESS(f"Done processing '{catalogue.title}'"))

    def _entries_to_ranges(self, entries, total_pages):
        entries = sorted(entries, key=lambda e: e["page"])
        ranges = []
        for i, e in enumerate(entries):
            start = e["page"] - 1
            end = (entries[i + 1]["page"] - 2) if i + 1 < len(entries) else total_pages - 1
            end = max(end, start)

            if not (0 <= start < total_pages) or not (0 <= end < total_pages):
                self.stdout.write(self.style.WARNING(
                    f"  skipping bad TOC entry '{e['title']}' (page {e['page']} out of range)"
                ))
                continue

            ranges.append({"title": e["title"], "start": start, "end": end})
        return ranges

    def _section_for_page(self, sections, page_num):
        for s in sections:
            if s.start_page <= page_num <= s.end_page:
                return s
        return None