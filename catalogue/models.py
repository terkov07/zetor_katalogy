from django.db import models


class TractorModel(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Catalogue(models.Model):
    TYPE_CHOICES = [
        ("parts_catalogue", "Parts catalogue"),
        ("modification_catalogue", "Modification catalogue"),
        ("workshop_manual", "Workshop manual"),
    ]

    title = models.CharField(max_length=200)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    # Set only on a modification_catalogue — points at the parts_catalogue it amends.
    amends = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="modifications",
    )
    language = models.CharField(max_length=10, default="sk")
    original_file = models.FileField(upload_to="catalogues/originals/")
    page_count = models.IntegerField(default=0)
    has_text_layer = models.BooleanField(default=False)
    # Approximate source resolution detected during processing — informs
    # zoom-quality expectations (see master spec 4.5).
    image_dpi = models.IntegerField(null=True, blank=True)
    rotation = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    models_covered = models.ManyToManyField(TractorModel, related_name="catalogues", blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Section(models.Model):
    catalogue = models.ForeignKey(Catalogue, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=200)
    start_page = models.IntegerField()
    end_page = models.IntegerField()
    section_file = models.FileField(upload_to="catalogues/sections/", blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.catalogue.title} — {self.title}"


class Part(models.Model):
    catalogue = models.ForeignKey(Catalogue, on_delete=models.CASCADE, related_name="parts")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, related_name="parts")
    part_number = models.CharField(max_length=50)
    # Dashes/spaces stripped, lowercased — lets search do a fast indexed
    # startswith lookup instead of string-processing every row per query.
    part_number_normalised = models.CharField(max_length=50, db_index=True, blank=True)
    name_sk = models.CharField(max_length=300, blank=True)
    name_en = models.CharField(max_length=300, blank=True)
    page = models.IntegerField(default=0)
    figure_ref = models.CharField(max_length=20, blank=True)
    position_no = models.CharField(max_length=10, blank=True)

    def save(self, *args, **kwargs):
        self.part_number_normalised = (
            self.part_number.replace("-", "").replace(" ", "").lower()
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.part_number} — {self.name_sk or self.name_en}"


class Job(models.Model):
    model = models.ForeignKey(TractorModel, null=True, blank=True, on_delete=models.SET_NULL)
    customer = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        label = self.customer or "Job"
        return f"{label} ({self.model})" if self.model else label


class JobPin(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="pins")
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    pinned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pinned_at"]

    def __str__(self):
        return f"{self.job} — {self.part.part_number}"