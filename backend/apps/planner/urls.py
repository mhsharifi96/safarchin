from django.urls import path

from .views import PlannerHealthView

urlpatterns = [
    path("health/", PlannerHealthView.as_view(), name="planner-health"),
]
