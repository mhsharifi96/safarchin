from django.contrib import admin

from .models import (
    Accommodation,
    ConversationMessage,
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    PlaceCandidate,
    PlanningJob,
    Trip,
    TripPreferences,
)

admin.site.register(Trip)
admin.site.register(TripPreferences)
admin.site.register(ConversationMessage)
admin.site.register(PlanningJob)
admin.site.register(PlaceCandidate)
admin.site.register(Accommodation)
admin.site.register(Itinerary)
admin.site.register(ItineraryDay)
admin.site.register(ItineraryItem)
