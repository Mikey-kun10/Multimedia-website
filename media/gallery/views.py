from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import MediaItem
from .forms import MediaItemForm
from pathlib import Path
import mimetypes

def home(request):
    q = request.GET.get("q", "")
    items = MediaItem.objects.all()
    if q:
        items = items.filter(title__icontains=q)
    return render(request, "gallery/home.html", {"items": items, "q": q})

@require_http_methods(["GET", "POST"])
def upload(request):
    if request.method == "POST":
        form = MediaItemForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if request.user.is_authenticated:
                obj.owner = request.user
            obj.save()
            messages.success(request, "Uploaded successfully.")
            return redirect("gallery:detail", slug=obj.slug)
    else:
        form = MediaItemForm()
    return render(request, "gallery/upload.html", {"form": form})

def detail(request, slug):
    item = get_object_or_404(MediaItem, slug=slug)
    return render(request, "gallery/detail.html", {"item": item})

# --- simple HTTP Range support for audio/video ---
def stream_file(request, pk):
    item = get_object_or_404(MediaItem, pk=pk)
    if not item.file:
        return HttpResponseNotFound("File not found.")

    file_path = item.file.path
    file_size = Path(file_path).stat().st_size
    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or "application/octet-stream"

    range_header = request.headers.get("Range", "")
    if range_header:
        try:
            # Example: "Range: bytes=0-"
            _, range_spec = range_header.split("=")
            start_str, end_str = (range_spec.split("-") + [""])[:2]
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            resp = HttpResponse(status=206, content_type=content_type)
            resp["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            resp["Accept-Ranges"] = "bytes"
            resp["Content-Length"] = str(length)

            with open(file_path, "rb") as f:
                f.seek(start)
                resp.write(f.read(length))
            return resp
        except Exception:
            pass  

    return FileResponse(open(file_path, "rb"), content_type=content_type)

# def delete_item(request, pk):
#     item = get_object_or_404(MediaItem, pk=pk)
#     if request.method == "POST":
#         item.delete()
#         return redirect("gallery:home")
#     return redirect("gallery:detail", slug=item.slug)

def edit(request, pk):
    item = get_object_or_404(MediaItem, pk=pk)
    if request.method == "POST":
        form = MediaItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect("gallery:detail", slug=item.slug)
    else:
        form = MediaItemForm(instance=item)
    return render(request, "gallery/edit.html", {"form": form, "item": item})

from django.shortcuts import get_object_or_404, redirect
from .models import MediaItem

def delete(request, pk):
    item = get_object_or_404(MediaItem, pk=pk)
    item.delete()
    return redirect("gallery:home")
