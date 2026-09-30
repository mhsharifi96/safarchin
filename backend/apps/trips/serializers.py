from rest_framework import serializers

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


class TripPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripPreferences
        fields = [
            "adults_count",
            "children_count",
            "has_older_adults",
            "arrival_time",
            "departure_time",
            "intercity_transport",
            "local_transport",
            "interests",
            "pace",
            "budget_amount",
            "budget_scope",
            "accessibility_notes",
            "has_existing_accommodation",
            "accommodation_notes",
            "room_count",
            "nightly_accommodation_budget",
            "assumptions",
            "updated_at",
        ]
        read_only_fields = ["assumptions", "updated_at"]


class TripSerializer(serializers.ModelSerializer):
    preferences = TripPreferencesSerializer(read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "title",
            "origin",
            "destination",
            "start_date",
            "end_date",
            "timezone",
            "status",
            "preferences",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class TripCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = ["title", "origin", "destination", "start_date", "end_date", "timezone"]


class ConversationMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class PlanningJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanningJob
        fields = ["id", "status", "error_message", "created_at", "updated_at"]


class PlaceCandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceCandidate
        fields = [
            "id",
            "name",
            "category",
            "address",
            "latitude",
            "longitude",
            "neshan_poi_id",
            "source",
            "source_url",
        ]


class AccommodationSerializer(serializers.ModelSerializer):
    place = PlaceCandidateSerializer(read_only=True)

    class Meta:
        model = Accommodation
        fields = ["id", "name", "room_type", "nightly_price", "is_selected", "source", "place"]


class ItineraryItemSerializer(serializers.ModelSerializer):
    place = PlaceCandidateSerializer(read_only=True)

    class Meta:
        model = ItineraryItem
        fields = ["id", "order", "start_time", "end_time", "title", "description", "category", "place"]


class ItineraryDaySerializer(serializers.ModelSerializer):
    items = ItineraryItemSerializer(many=True, read_only=True)

    class Meta:
        model = ItineraryDay
        fields = ["id", "day_index", "date", "city", "notes", "items"]


class ItinerarySerializer(serializers.ModelSerializer):
    days = ItineraryDaySerializer(many=True, read_only=True)

    class Meta:
        model = Itinerary
        fields = ["id", "version", "summary", "model_name", "generated_at", "days"]
