import uuid

from django.conf import settings
from django.db import models


class Trip(models.Model):
    """Core identity of a trip. Owned either by an authenticated User or, for
    guests, tied to an opaque Django session key (see apps.accounts.middleware
    and apps.trips.permissions.has_trip_access -- the UUID pk alone is never
    treated as sufficient authorization)."""

    class Status(models.TextChoices):
        COLLECTING_INFO = "collecting_info", "در حال تکمیل اطلاعات"
        READY_FOR_GENERATION = "ready_for_generation", "آماده تولید برنامه"
        GENERATING = "generating", "در حال تولید برنامه"
        PLANNED = "planned", "برنامه‌ریزی شده"
        ARCHIVED = "archived", "بایگانی‌شده"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="trips"
    )
    guest_session_key = models.CharField(max_length=40, blank=True, db_index=True)

    title = models.CharField(max_length=200, blank=True)
    origin = models.CharField(max_length=150, blank=True)
    destination = models.CharField(max_length=150, blank=True)
    # Date-only travel dates (no time-of-day) -- distinct from timestamps below.
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    # Trip-local timezone used to interpret itinerary wall-clock times (e.g. Asia/Tehran).
    timezone = models.CharField(max_length=64, default="Asia/Tehran")

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.COLLECTING_INFO)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["owner"]), models.Index(fields=["guest_session_key"])]
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title or f"Trip {self.id}"


class TripPreferences(models.Model):
    class Pace(models.TextChoices):
        RELAXED = "relaxed", "آرام"
        BALANCED = "balanced", "متعادل"
        INTENSE = "intense", "فشرده"

    class BudgetScope(models.TextChoices):
        PER_PERSON = "per_person", "هرنفر"
        GROUP = "group", "کل گروه"

    class IntercityTransport(models.TextChoices):
        FLIGHT = "flight", "هواپیما"
        TRAIN = "train", "قطار"
        BUS = "bus", "اتوبوس"
        PERSONAL_CAR = "personal_car", "خودروی شخصی"
        UNKNOWN = "unknown", "نامشخص"

    class LocalTransport(models.TextChoices):
        PUBLIC_TRANSIT = "public_transit", "حمل‌ونقل عمومی"
        TAXI = "taxi", "تاکسی/اسنپ"
        RENTAL_CAR = "rental_car", "اجاره خودرو"
        WALKING = "walking", "پیاده"
        MIXED = "mixed", "ترکیبی"
        UNKNOWN = "unknown", "نامشخص"

    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="preferences")

    adults_count = models.PositiveSmallIntegerField(null=True, blank=True)
    children_count = models.PositiveSmallIntegerField(null=True, blank=True)
    has_older_adults = models.BooleanField(null=True, blank=True)

    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)

    intercity_transport = models.CharField(
        max_length=20, choices=IntercityTransport.choices, default=IntercityTransport.UNKNOWN
    )
    local_transport = models.CharField(
        max_length=20, choices=LocalTransport.choices, default=LocalTransport.UNKNOWN
    )

    interests = models.JSONField(default=list, blank=True)
    pace = models.CharField(max_length=10, choices=Pace.choices, null=True, blank=True)

    budget_amount = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    budget_scope = models.CharField(max_length=10, choices=BudgetScope.choices, null=True, blank=True)

    accessibility_notes = models.TextField(blank=True)

    has_existing_accommodation = models.BooleanField(null=True, blank=True)
    accommodation_notes = models.TextField(blank=True)
    room_count = models.PositiveSmallIntegerField(null=True, blank=True)
    nightly_accommodation_budget = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)

    # Explicit assumptions the agent made for unanswered fields: [{"field": "...", "assumption": "...", "reason": "..."}]
    assumptions = models.JSONField(default=list, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Preferences for {self.trip_id}"


class ConversationMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class PlanningJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در صف"
        RUNNING = "running", "در حال اجرا"
        SUCCEEDED = "succeeded", "موفق"
        FAILED = "failed", "ناموفق"

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="planning_jobs")
    celery_task_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class PlaceCandidate(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="place_candidates")
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=300, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    neshan_poi_id = models.CharField(max_length=200, blank=True)
    source = models.CharField(max_length=20, default="model")  # tavily | neshan | model
    # Default URLField max_length (200) is too short for real-world URLs -- a Tavily web
    # research result with a URL-encoded Persian slug hit 230 chars and crashed itinerary
    # generation outright (DataError, whole job failed). 500 comfortably covers this.
    source_url = models.URLField(blank=True, max_length=500)
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Accommodation(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="accommodations")
    place = models.ForeignKey(PlaceCandidate, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    room_type = models.CharField(max_length=100, blank=True)
    nightly_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    is_selected = models.BooleanField(default=False)
    source = models.CharField(max_length=20, default="model")
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Itinerary(models.Model):
    trip = models.OneToOneField(Trip, on_delete=models.CASCADE, related_name="itinerary")
    version = models.PositiveIntegerField(default=1)
    summary = models.TextField(blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    raw_output = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now=True)


class ItineraryDay(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="days")
    day_index = models.PositiveSmallIntegerField()
    date = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["day_index"]


class ItineraryItem(models.Model):
    class Category(models.TextChoices):
        SIGHT = "sight", "بازدید"
        FOOD = "food", "غذا"
        TRANSPORT = "transport", "جابجایی"
        REST = "rest", "استراحت"
        ACCOMMODATION = "accommodation", "اقامت"
        OTHER = "other", "سایر"

    day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE, related_name="items")
    order = models.PositiveSmallIntegerField(default=0)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    place = models.ForeignKey(PlaceCandidate, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["order"]
