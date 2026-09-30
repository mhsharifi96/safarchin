from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Accommodation, ConversationMessage, PlanningJob, Trip, TripPreferences
from .permissions import has_trip_access
from .serializers import (
    AccommodationSerializer,
    ConversationMessageSerializer,
    ItinerarySerializer,
    PlanningJobSerializer,
    TripCreateSerializer,
    TripPreferencesSerializer,
    TripSerializer,
)


def _owned_trips_queryset(request):
    if request.user.is_authenticated:
        return Trip.objects.filter(owner=request.user)
    session_key = request.session.session_key
    if not session_key:
        return Trip.objects.none()
    return Trip.objects.filter(owner__isnull=True, guest_session_key=session_key)


def _get_owned_trip_or_404(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    if not has_trip_access(request, trip):
        from rest_framework.exceptions import NotFound

        raise NotFound("سفر مورد نظر یافت نشد.")
    return trip


class TripListCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "planner"

    def get(self, request):
        trips = _owned_trips_queryset(request)
        return Response(TripSerializer(trips, many=True).data)

    def post(self, request):
        serializer = TripCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.is_authenticated and not request.session.session_key:
            request.session.save()

        trip = serializer.save(
            owner=request.user if request.user.is_authenticated else None,
            guest_session_key="" if request.user.is_authenticated else request.session.session_key,
        )
        TripPreferences.objects.create(trip=trip)
        return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)


class TripDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, trip_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        return Response(TripSerializer(trip).data)

    def patch(self, request, trip_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        serializer = TripCreateSerializer(trip, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TripSerializer(trip).data)

    def delete(self, request, trip_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        trip.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TripPreferencesView(APIView):
    """Partial updates keep the form UI and conversational intake in sync
    with a single persisted TripPreferences row per trip."""

    permission_classes = [AllowAny]

    def patch(self, request, trip_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        preferences, _ = TripPreferences.objects.get_or_create(trip=trip)
        serializer = TripPreferencesSerializer(preferences, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TripMessagesView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "planner"

    def get(self, request, trip_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        messages = trip.messages.all()
        return Response(ConversationMessageSerializer(messages, many=True).data)

    def post(self, request, trip_id):
        """Appends the user's message and runs one turn of the intake agent
        (parse intent -> update TripPreferences -> ask next question or
        propose the editable summary). See apps.planner.intake_agent."""
        trip = _get_owned_trip_or_404(request, trip_id)
        content = (request.data.get("content") or "").strip()
        if not content:
            return Response({"detail": "متن پیام نمی‌تواند خالی باشد."}, status=status.HTTP_400_BAD_REQUEST)

        ConversationMessage.objects.create(trip=trip, role=ConversationMessage.Role.USER, content=content)

        from apps.planner.intake_agent import run_intake_turn

        assistant_reply = run_intake_turn(trip)
        ConversationMessage.objects.create(
            trip=trip, role=ConversationMessage.Role.ASSISTANT, content=assistant_reply
        )
        trip.refresh_from_db()
        return Response(
            {
                "reply": assistant_reply,
                "trip": TripSerializer(trip).data,
            }
        )


class TripGeneratePlanView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "planner"

    def post(self, request, trip_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        trip.status = Trip.Status.GENERATING
        trip.save(update_fields=["status"])
        job = PlanningJob.objects.create(trip=trip)

        from apps.planner.tasks import generate_itinerary_task

        async_result = generate_itinerary_task.delay(str(trip.id), job.id)
        job.celery_task_id = async_result.id
        job.save(update_fields=["celery_task_id"])
        return Response(PlanningJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class TripPlanningJobStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, trip_id, job_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        job = get_object_or_404(PlanningJob, pk=job_id, trip=trip)
        return Response(PlanningJobSerializer(job).data)


class TripAccommodationsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, trip_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        return Response(AccommodationSerializer(trip.accommodations.all(), many=True).data)


class TripAccommodationSelectView(APIView):
    """Selecting a stay records it on TripPreferences (so the next
    generation call has it as real context for the agent's schedule/travel-
    time tools) and flips the trip back to ready-for-generation so the
    itinerary -- including routes to/from this accommodation -- can be
    regenerated around it."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "planner"

    def post(self, request, trip_id, accommodation_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        accommodation = get_object_or_404(Accommodation, pk=accommodation_id, trip=trip)

        trip.accommodations.exclude(pk=accommodation.pk).update(is_selected=False)
        accommodation.is_selected = True
        accommodation.save(update_fields=["is_selected"])

        preferences, _ = TripPreferences.objects.get_or_create(trip=trip)
        preferences.has_existing_accommodation = True
        address = accommodation.place.address if accommodation.place else ""
        preferences.accommodation_notes = f"اقامتگاه انتخاب‌شده: {accommodation.name} ({address})".strip()
        preferences.save(update_fields=["has_existing_accommodation", "accommodation_notes"])

        trip.status = Trip.Status.READY_FOR_GENERATION
        trip.save(update_fields=["status"])

        return Response(AccommodationSerializer(accommodation).data)


class TripItineraryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, trip_id):
        trip = _get_owned_trip_or_404(request, trip_id)
        if not hasattr(trip, "itinerary"):
            return Response({"detail": "هنوز برنامه‌ای تولید نشده است."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ItinerarySerializer(trip.itinerary).data)
