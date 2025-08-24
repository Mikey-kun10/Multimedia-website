from django.contrib import admin
from django.urls import path
from . import views

app_name = "gallery"

urlpatterns = [
    path("", views.home, name="home"),
    path("upload/", views.upload, name="upload"),
    path("media/<slug:slug>/", views.detail, name="detail"),
    path("stream/<int:pk>/", views.stream_file, name="stream"), 
    path("edit/<int:pk>/", views.edit, name="edit"),   
    path("delete/<int:pk>/", views.delete, name="delete")

]