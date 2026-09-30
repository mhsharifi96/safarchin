"""Pydantic schemas for every structured LLM output used by the planner agent.
Kept strict (extra fields forbidden) so malformed model output fails fast and
is caught by the bounded repair loop in apps.planner.repair.
"""
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class Assumption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    assumption: str
    reason: str


class PreferencesExtraction(BaseModel):
    """Output of the intake turn: which TripPreferences/Trip fields were
    updated from the latest user message, explicit assumptions made for
    fields the user left unclear, and what to say back / ask next."""

    model_config = ConfigDict(extra="forbid")

    origin: str | None = None
    destination: str | None = None
    start_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    end_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    adults_count: int | None = None
    children_count: int | None = None
    has_older_adults: bool | None = None
    arrival_time: str | None = Field(default=None, description="HH:MM 24h")
    departure_time: str | None = Field(default=None, description="HH:MM 24h")
    intercity_transport: Literal["flight", "train", "bus", "personal_car", "unknown"] | None = None
    local_transport: Literal["public_transit", "taxi", "rental_car", "walking", "mixed", "unknown"] | None = None
    interests: list[str] | None = None
    pace: Literal["relaxed", "balanced", "intense"] | None = None
    budget_amount: float | None = None
    budget_scope: Literal["per_person", "group"] | None = None
    accessibility_notes: str | None = None
    has_existing_accommodation: bool | None = None
    accommodation_notes: str | None = None
    room_count: int | None = None
    nightly_accommodation_budget: float | None = None

    assumptions: list[Assumption] = Field(default_factory=list)
    missing_essential_fields: list[str] = Field(default_factory=list)
    ready_for_summary: bool = Field(
        default=False, description="True once all essential fields are known or explicitly assumed"
    )
    assistant_reply_fa: str = Field(description="Persian, natural-language reply to show the user next")


class PlaceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    category: str = ""
    address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    source: Literal["tavily", "neshan", "model"] = "model"
    source_url: str = ""


class ItineraryItemPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_time: str | None = Field(default=None, description="HH:MM 24h, trip-local time")
    end_time: str | None = Field(default=None, description="HH:MM 24h, trip-local time")
    title: str
    description: str = ""
    category: Literal["sight", "food", "transport", "rest", "accommodation", "other"] = "other"
    place: PlaceRef | None = None


class ItineraryDayPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day_index: int
    date: str | None = Field(default=None, description="ISO date YYYY-MM-DD")
    city: str = ""
    notes: str = ""
    items: list[ItineraryItemPlan]


class AccommodationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    room_type: str = ""
    nightly_price: float | None = None
    place: PlaceRef | None = None
    recommended: bool = False


class ItineraryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary_fa: str
    days: list[ItineraryDayPlan]
    accommodation_options: list[AccommodationPlan] = Field(default_factory=list)
