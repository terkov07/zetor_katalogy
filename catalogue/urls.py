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
    path('part/<int:part_id>/pin/', views.pin_to_active_job, name='pin_to_active_job'),
]