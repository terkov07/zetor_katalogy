from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages

from .models import TractorModel, Catalogue, Section, Part, Job, JobPin


def library(request):
    """Home page: every tractor model, with its catalogue count."""
    models = TractorModel.objects.prefetch_related("catalogues").all()
    return render(request, "catalogue/library.html", {"models": models})


def model_detail(request, pk):
    """A tractor model's catalogues, grouped by type."""
    model = get_object_or_404(TractorModel, pk=pk)
    catalogues = model.catalogues.all()

    grouped = {"parts_catalogue": [], "modification_catalogue": [], "workshop_manual": []}
    for cat in catalogues:
        grouped.setdefault(cat.type, []).append(cat)

    return render(request, "catalogue/model_detail.html", {
        "model": model,
        "grouped": grouped,
    })


def catalogue_detail(request, pk):
    """A catalogue's list of sections, with a link to its modification
    catalogue if one exists (via the amends relationship)."""
    catalogue = get_object_or_404(Catalogue, pk=pk)
    sections = catalogue.sections.all()
    modifications = catalogue.modifications.all()  # reverse of `amends`

    return render(request, "catalogue/catalogue_detail.html", {
        "catalogue": catalogue,
        "sections": sections,
        "modifications": modifications,
    })


def viewer(request, pk):
    """
    Shows a PDF using the browser's own built-in viewer (Chrome/Firefox/
    Edge all handle zoom, page nav, and in-document search natively) —
    deliberately not vendoring PDF.js for this first version, since the
    native viewer needs zero extra setup and covers the same core needs.

    Pass ?section=<id> to view one split-out section instead of the
    whole original file, and/or ?page=<n> to open at a specific page.
    """
    catalogue = get_object_or_404(Catalogue, pk=pk)
    section = None

    section_id = request.GET.get("section")
    if section_id:
        section = get_object_or_404(Section, pk=section_id, catalogue=catalogue)
        file_url = section.section_file.url
    else:
        file_url = catalogue.original_file.url

    page = request.GET.get("page")
    if page:
        file_url = f"{file_url}#page={page}"

    return render(request, "catalogue/viewer.html", {
        "catalogue": catalogue,
        "section": section,
        "file_url": file_url,
    })


def search(request):
    """
    Searches by part number (dash/space-insensitive partial match) or
    by name text. mode is 'num', 'txt', or 'all' (default).
    """
    q = request.GET.get("q", "").strip()
    mode = request.GET.get("mode", "all")
    results = []

    if q:
        q_norm = q.replace("-", "").replace(" ", "").lower()
        num_match = Q(part_number_normalised__startswith=q_norm)
        text_match = Q(name_sk__icontains=q) | Q(name_en__icontains=q)

        if mode == "num":
            lookup = num_match
        elif mode == "txt":
            lookup = text_match
        else:
            lookup = num_match | text_match

        results = (
            Part.objects.filter(lookup)
            .select_related("section", "catalogue")[:30]
        )

    return render(request, "catalogue/search.html", {
        "q": q,
        "mode": mode,
        "results": results,
        "active_job": Job.objects.filter(is_active=True).first(),
    })


def job_list(request):
    """Lists every job, newest first, and handles creating a new one."""
    if request.method == "POST":
        model_id = request.POST.get("model")
        customer = request.POST.get("customer", "").strip()
        job = Job.objects.create(
            model_id=model_id or None,
            customer=customer,
        )
        return redirect("job_detail", pk=job.pk)

    jobs = Job.objects.select_related("model").all()
    models = TractorModel.objects.all()
    return render(request, "catalogue/job_list.html", {"jobs": jobs, "models": models})


def job_detail(request, pk):
    """
    Shows a job's pinned parts and notes. Also handles, via different
    POST actions on the same URL:
    - "activate": makes this the one active job (unsets any other)
    - "add_note": overwrites the note text
    - "pin": pins a part by typing its exact part number
    - "unpin": removes one pinned part
    """
    job = get_object_or_404(Job, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "activate":
            Job.objects.update(is_active=False)
            job.is_active = True
            job.save()

        elif action == "add_note":
            job.note = request.POST.get("note", "")
            job.save()

        elif action == "pin":
            typed = request.POST.get("part_number", "").strip()
            normalised = typed.replace("-", "").replace(" ", "").lower()
            part = Part.objects.filter(part_number_normalised=normalised).first()
            if part:
                JobPin.objects.get_or_create(job=job, part=part)
                messages.success(request, f"Pripnuté: {part.part_number}")
            else:
                messages.error(request, f"Diel „{typed}“ sa nenašiel. Skontrolujte číslo alebo ho vyhľadajte cez Hľadať.")

        elif action == "unpin":
            pin_id = request.POST.get("pin_id")
            JobPin.objects.filter(id=pin_id, job=job).delete()

        return redirect("job_detail", pk=job.pk)

    pins = job.pins.select_related("part", "part__catalogue", "part__section")
    return render(request, "catalogue/job_detail.html", {"job": job, "pins": pins})


def job_export(request, pk):
    """Plain-text summary of a job — good enough to copy/paste or print."""
    job = get_object_or_404(Job, pk=pk)
    pins = job.pins.select_related("part", "part__catalogue")

    lines = [
        f"Zákazka: {job.customer or '(bez mena zákazníka)'}",
        f"Model: {job.model or '-'}",
        f"Dátum: {job.created_at:%d.%m.%Y}",
        "",
        "Poznámky:",
        job.note or "(žiadne)",
        "",
        "Pripnuté diely:",
    ]
    for pin in pins:
        lines.append(f"  {pin.part.part_number} — {pin.part.name_sk} ({pin.part.catalogue.title}, strana {pin.part.page})")

    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def pin_to_active_job(request, part_id):
    """Pins a part to whichever job is currently active — used by the
    "Pripnúť" button on search results, so pinning doesn't require
    leaving the search page."""
    if request.method == "POST":
        job = Job.objects.filter(is_active=True).first()
        part = get_object_or_404(Part, pk=part_id)
        if job:
            JobPin.objects.get_or_create(job=job, part=part)
    return redirect(request.META.get("HTTP_REFERER", "search"))