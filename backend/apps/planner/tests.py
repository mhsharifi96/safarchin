from django.test import SimpleTestCase, TestCase

from apps.trips.models import Trip, TripPreferences

from .intake_agent import _apply_extraction
from .route_optimize import optimize_day_order
from .schemas import ItineraryItemPlan, PlaceRef, PreferencesExtraction


def _item(title, category, lat=None, lng=None, start=None, end=None):
    place = PlaceRef(name=title, latitude=lat, longitude=lng) if lat is not None else None
    return ItineraryItemPlan(
        title=title, category=category, place=place, start_time=start, end_time=end
    )


class OptimizeDayOrderTests(SimpleTestCase):
    def test_reorders_flexible_stops_by_distance(self):
        # Hotel (anchor) at (0, 0); three sights placed so the naive (LLM) order
        # zig-zags (far, near, mid) but nearest-neighbor from the hotel should
        # visit near -> mid -> far instead.
        hotel = _item("هتل", "accommodation", 0.0, 0.0, "08:00", "08:30")
        far = _item("دور", "sight", 0.0, 0.30, "09:00", "10:00")
        near = _item("نزدیک", "sight", 0.0, 0.01, "10:00", "11:00")
        mid = _item("میانه", "sight", 0.0, 0.10, "11:00", "12:00")

        ordered = optimize_day_order([hotel, far, near, mid])

        self.assertEqual([i.title for i in ordered], ["هتل", "نزدیک", "میانه", "دور"])
        # Original time slots are preserved in sequence, just reassigned to the new occupants.
        self.assertEqual(
            [(i.start_time, i.end_time) for i in ordered],
            [("08:00", "08:30"), ("09:00", "10:00"), ("10:00", "11:00"), ("11:00", "12:00")],
        )

    def test_meals_and_accommodation_stay_pinned(self):
        hotel = _item("هتل", "accommodation", 0.0, 0.0)
        far = _item("دور", "sight", 0.0, 0.30)
        near = _item("نزدیک", "sight", 0.0, 0.01)
        mid = _item("میانه", "sight", 0.0, 0.10)
        lunch = _item("ناهار", "food", 0.0, 0.05)

        ordered = optimize_day_order([hotel, far, near, mid, lunch])

        # The three sights (between the hotel and lunch) get nearest-neighbor
        # reordered; `lunch` itself -- an anchor -- keeps its original slot
        # (still last), it doesn't get pulled earlier just because it's
        # geographically between some of the sights.
        self.assertEqual([i.title for i in ordered], ["هتل", "نزدیک", "میانه", "دور", "ناهار"])

    def test_items_without_coordinates_are_left_in_place(self):
        a = _item("بدون مکان", "sight")
        b = _item("با مکان", "sight", 0.0, 0.0)

        ordered = optimize_day_order([a, b])

        self.assertEqual([i.title for i in ordered], ["بدون مکان", "با مکان"])

    def test_empty_and_single_item_days(self):
        self.assertEqual(optimize_day_order([]), [])
        only = _item("تنها", "sight", 0.0, 0.0)
        self.assertEqual(optimize_day_order([only]), [only])


def _planned_trip(**overrides):
    defaults = dict(origin="تهران", destination="تبریز", status=Trip.Status.PLANNED)
    defaults.update(overrides)
    trip = Trip.objects.create(**defaults)
    TripPreferences.objects.create(trip=trip, budget_amount=5_000_000)
    return trip


def _extraction(**overrides):
    defaults = dict(ready_for_summary=False, assistant_reply_fa="باشه.")
    defaults.update(overrides)
    return PreferencesExtraction(**defaults)


class ApplyExtractionStatusTests(TestCase):
    """Chat changing a core field (destination/dates/budget) after a plan already
    exists must not leave the trip silently looking "planned" for the old plan."""

    def test_destination_change_on_planned_trip_without_ready_for_summary_falls_back(self):
        trip = _planned_trip()
        _apply_extraction(trip, _extraction(destination="اصفهان"))
        trip.refresh_from_db()
        self.assertEqual(trip.destination, "اصفهان")
        self.assertEqual(trip.status, Trip.Status.COLLECTING_INFO)

    def test_destination_change_on_planned_trip_with_ready_for_summary_goes_to_generation(self):
        trip = _planned_trip()
        _apply_extraction(trip, _extraction(destination="اصفهان", ready_for_summary=True))
        trip.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.READY_FOR_GENERATION)

    def test_budget_change_on_planned_trip_invalidates_it(self):
        trip = _planned_trip()
        _apply_extraction(trip, _extraction(budget_amount=9_000_000))
        trip.refresh_from_db()
        self.assertEqual(float(trip.preferences.budget_amount), 9_000_000)
        self.assertEqual(trip.status, Trip.Status.COLLECTING_INFO)

    def test_non_core_field_change_on_planned_trip_leaves_it_planned(self):
        trip = _planned_trip()
        _apply_extraction(trip, _extraction(pace="relaxed"))
        trip.refresh_from_db()
        self.assertEqual(trip.preferences.pace, "relaxed")
        self.assertEqual(trip.status, Trip.Status.PLANNED)

    def test_same_value_is_not_treated_as_a_change(self):
        trip = _planned_trip()
        _apply_extraction(trip, _extraction(destination="تبریز"))  # already the destination
        trip.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.PLANNED)

    def test_ready_for_summary_still_wins_when_not_previously_planned(self):
        trip = _planned_trip(status=Trip.Status.COLLECTING_INFO)
        _apply_extraction(trip, _extraction(destination="اصفهان", ready_for_summary=True))
        trip.refresh_from_db()
        self.assertEqual(trip.status, Trip.Status.READY_FOR_GENERATION)
