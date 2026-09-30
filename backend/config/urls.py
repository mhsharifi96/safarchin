from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/trips/", include("apps.trips.urls")),
    path("api/planner/", include("apps.planner.urls")),
]
