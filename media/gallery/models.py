from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
from pathlib import Path
from PIL import Image
import mimetypes

def upload_path(instance, filename):
    return f"uploads/{instance.owner_id or 'anon'}/{filename}"

def thumb_path(instance, filename):
    stem = Path(filename).stem
    return f"uploads/{instance.owner_id or 'anon'}/thumbs/{stem}.jpg"

class MediaItem(models.Model):
    MEDIA_TYPES = [
        ("image", "Image"),
        ("audio", "Audio"),
        ("video", "Video"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to=upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=["jpg","jpeg","png","gif","webp","mp3","wav","ogg","mp4","webm","mov","mkv"]
        )]
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default="other")
    thumbnail = models.ImageField(upload_to=thumb_path, blank=True, null=True)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # detect media type by mimetype
        mt, _ = mimetypes.guess_type(self.file.name)
        if mt:
            if mt.startswith("image/"):
                self.media_type = "image"
            elif mt.startswith("audio/"):
                self.media_type = "audio"
            elif mt.startswith("video/"):
                self.media_type = "video"
            else:
                self.media_type = "other"

        # create slug on first save
        if not self.slug:
            base = slugify(self.title) or "media"
            candidate = base
            i = 1
            while MediaItem.objects.filter(slug=candidate).exists():
                i += 1
                candidate = f"{base}-{i}"
            self.slug = candidate

        super().save(*args, **kwargs)

        # generate thumbnail for images only (simple Pillow resize)
        if self.media_type == "image" and self.file:
            try:
                from io import BytesIO
                from django.core.files.base import ContentFile

                self.file.open("rb")
                img = Image.open(self.file)
                img.thumbnail((480, 480))
                buf = BytesIO()
                img.convert("RGB").save(buf, format="JPEG", quality=80)
                thumb_file = ContentFile(buf.getvalue())
                self.thumbnail.save(f"{Path(self.file.name).name}.jpg", thumb_file, save=False)
                super().save(update_fields=["thumbnail"])
            except Exception:
                # thumbnail generation best-effort
                pass

    def __str__(self):
        return f"{self.title} ({self.media_type})"

