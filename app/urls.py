from django.urls import path
from .views import index, blogdetail, galleryview, contactview, aboutview, watchview, watch_all, searchview


app_name = 'app'
urlpatterns = [
    path("", index, name="indexpage"),
    path("<slug:slug>.html", blogdetail, name="article-detail"),
    path("artgallery", galleryview, name="gallery"),
    path("contact", contactview, name="contact"),
    path("about", aboutview, name="about"),
    path("allvideos", watch_all, name="allvideos"),
    path("watch/<slug:slug>", watchview, name="videos"),
    path("searching/", searchview, name="searching"),
    path("search/", searchview, name="search")
]
