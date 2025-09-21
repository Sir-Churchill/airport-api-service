from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("api/core/", include("airport.urls", namespace="airport")),
    path("api/user/", include("user.urls", namespace="user")),
    path('admin/', admin.site.urls),
]
