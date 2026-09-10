from django.urls import path
from . import views

urlpatterns = [
    path('', views.library, name='library'),
    path('model/<int:pk>/', views.model_detail, name='model_detail'),
    path('catalogue/<int:pk>/', views.catalogue_detail, name='catalogue_detail'),
    path('catalogue/<int:pk>/view/', views.viewer, name='viewer'),
    path('search/', views.search, name='search'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/export/', views.job_export, name='job_export'),
    path('part/<int:part_id>/pin/<int:job_id>/', views.pin_to_job, name='pin_to_job'),
    path('lang/<str:lang_code>/', views.set_language, name='set_language'),
    path('offline/', views.offline, name='offline'),
    path('section/<int:pk>/download/', views.download_section, name='download_section'),
]