from django.db import models
import uuid
import os
from django.template.defaultfilters import slugify
import random
import string
from django.utils.crypto import get_random_string


# Create your models here.
def random_gen(size=25):
    return ''.join(get_random_string(size))


def video_upload_location(instance, filename):
    video_description = random_gen()
    random_video_name = get_random_string(22)
    video_name = filename.lower().replace(" ", random_video_name)
    return os.path.join(str(uuid.uuid4()), video_description, video_name)


def video_thumbnail_upload_location(instance, filename):
    rand_chars = get_random_string(10)
    image_file_area = rand_chars
    random_image_name = get_random_string(25)
    image_name = filename.lower().replace("-", random_image_name)
    return os.path.join(str(uuid.uuid4()), image_file_area, image_name)


def random_string_generator(size=30, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class VideoFileDetails(models.Model):
    name = models.CharField(max_length=255, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    upadate = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"file name {self.name}"

    class Meta:
        verbose_name = 'Video File Detail'
        verbose_name_plural = 'Video file Details'

def generate_video_id(length=50):
    characters = string.ascii_letters + string.digits + '-_'
    return ''.join(random.choice(characters) for _ in range(length))

class VideoUpload(models.Model):
    vid = models.CharField(max_length=1000, default=generate_video_id, blank=True,null=True )
    video_title = models.CharField(max_length=255, default=None, blank=True, null=True)
    video_description = models.TextField(max_length=600, default=None, blank=True, null=True)
    video_thumbnail = models.ImageField(upload_to=video_thumbnail_upload_location, null=True, blank=True, default=None)
    slug = models.SlugField(max_length=1000, unique=True, blank=True)
    file = models.FileField(upload_to=video_upload_location, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    upadate = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"name of files uploaded are {self.file}"

    def save(self, *args, **kwargs):
        original_slug = slugify(random_string_generator())
        queryset = VideoUpload.objects.all().filter(slug__iexact=original_slug).count()
        count = 1
        slug = original_slug
        while (queryset):
            slug = original_slug + '-' + str(count) + "-".join(random_string_generator())
            count += 1
            queryset = VideoUpload.objects.all().filter(slug__iexact=slug).count()
        self.slug = slug
        super().save(*args, **kwargs)
