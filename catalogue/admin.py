from django.contrib import admin
from .models import TractorModel, Catalogue, Section, Part, Job, JobPin

admin.site.register(TractorModel)
admin.site.register(Catalogue)
admin.site.register(Section)
admin.site.register(Part)
admin.site.register(Job)
admin.site.register(JobPin)