from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.urls import reverse
import random
import string
from io import StringIO, BytesIO 
from PIL import Image as Img
from django.core.files.uploadedfile import InMemoryUploadedFile
from ckeditor_uploader.fields import RichTextUploadingField


def  random_string_generator(size=100, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
    
class Blog(models.Model):
    author = models.ForeignKey(User,on_delete=models.CASCADE)
    slug = models.SlugField(max_length=500,unique=True,blank=True)
    title =  models.CharField(max_length=200)
    category = models.CharField(max_length=255,default=None)
    thumbnail=models.ImageField(upload_to="postimages",default='main.png')
    content=RichTextUploadingField()
    featured=models.BooleanField(default=False)
    updated=models.DateTimeField(auto_now=True)
    created=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Post name{self.title}"


    
    def save(self,*args,**kwargs):
        if self.thumbnail:
            img = Img.open(BytesIO(self.thumbnail.read()))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.thumbnail((self.thumbnail.width/1.5,self.thumbnail.height/1.5),Img.ANTIALIAS)
            output=BytesIO()
            img.save(output,format='WebP',quality=70)
            output.seek(0)
            self.thumbnail=InMemoryUploadedFile(output,'ImageField',"%s.webp" %self.thumbnail.name.split('.')[0],'thumbnail/webp',len(output.getbuffer()),None)
        original_slug=slugify(self.title)
        queryset=Blog.objects.all().filter(slug__iexact=original_slug).count()
        count=1
        slug=original_slug
        while(queryset):
            slug=original_slug+'-'+str(count)
            count+=1
            queryset=Blog.objects.all().filter(slug__iexact=slug).count()
        self.slug=slug
        if self.featured:
            try:
                temp=Blog.objects.get(featured=True)
                if self!=temp:
                    temp.featured=False
                    temp.save()
            except Blog.DoesNotExist:
                pass
        super().save(*args,**kwargs)
    def get_absolute_url(self):
        return reverse('article-detail',kwargs={'slug':self.slug})
