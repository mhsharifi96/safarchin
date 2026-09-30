from django.urls import path

from . import views

urlpatterns = [
    path("", views.TripListCreateView.as_view(), name="trip-list-create"),
    path("<uuid:trip_id>/", views.TripDetailView.as_view(), name="trip-detail"),
    path("<uuid:trip_id>/preferences/", views.TripPreferencesView.as_view(), name="trip-preferences"),
    path("<uuid:trip_id>/messages/", views.TripMessagesView.as_view(), name="trip-messages"),
    path("<uuid:trip_id>/generate/", views.TripGeneratePlanView.as_view(), name="trip-generate"),
    path(
        "<uuid:trip_id>/generate/<int:job_id>/",
        views.TripPlanningJobStatusView.as_view(),
        name="trip-generate-status",
    ),
    path("<uuid:trip_id>/itinerary/", views.TripItineraryView.as_view(), name="trip-itinerary"),
    path("<uuid:trip_id>/accommodations/", views.TripAccommodationsView.as_view(), name="trip-accommodations"),
    path(
        "<uuid:trip_id>/accommodations/<int:accommodation_id>/select/",
        views.TripAccommodationSelectView.as_view(),
        name="trip-accommodation-select",
    ),
]
