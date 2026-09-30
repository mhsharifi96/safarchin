"""The core orchestrated planning workflow (spec steps 3-9), implemented as a
single agent: one LLM bound to typed tools runs a bounded ReAct-style tool
loop (research -> resolve -> travel options -> schedule), then a final call
forces validated structured output (apps.planner.schemas.ItineraryPlan),
which is persisted to the DB.
"""
import json
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from apps.trips.models import Accommodation, Itinerary, ItineraryDay, ItineraryItem, PlaceCandidate, Trip

from .llm import get_chat_model
from .repair import run_with_structured_repair
from .schemas import ItineraryPlan, PlaceRef
from .tools.neshan import (
    neshan_geocode_tool,
    neshan_place_details_tool,
    neshan_place_search_tool,
    neshan_reverse_geocode_tool,
    neshan_route_tool,
)
from .tools.web_research import web_research_tool
from .validation import validate_plan

logger = logging.getLogger(__name__)

TOOLS = [
    web_research_tool,
    neshan_place_search_tool,
    neshan_place_details_tool,
    neshan_geocode_tool,
    neshan_reverse_geocode_tool,
    neshan_route_tool,
]
TOOL_MAP = {t.name: t for t in TOOLS}

MAX_TOOL_ITERATIONS = 6


def _trip_brief_fa(trip: Trip) -> str:
    prefs = trip.preferences
    duration = (trip.end_date - trip.start_date).days + 1 if trip.start_date and trip.end_date else None
    return (
        f"مبدا: {trip.origin}\nمقصد: {trip.destination}\n"
        f"تاریخ: {trip.start_date} تا {trip.end_date}"
        + (f" ({duration} روز)" if duration else "")
        + f"\nبزرگسال: {prefs.adults_count}, کودک: {prefs.children_count}\n"
        f"حمل‌ونقل بین‌شهری: {prefs.intercity_transport}, درون‌شهری: {prefs.local_transport}\n"
        f"علایق: {', '.join(prefs.interests or [])}\n"
        f"ریتم سفر: {prefs.pace}\n"
        f"بودجه: {prefs.budget_amount} ({prefs.budget_scope})\n"
        f"محدودیت پیاده‌روی/دسترسی: {prefs.accessibility_notes or 'ندارد'}\n"
        f"اقامت از قبل: {prefs.has_existing_accommodation}, یادداشت: {prefs.accommodation_notes}\n"
        f"فرض‌های صریح: {json.dumps(prefs.assumptions, ensure_ascii=False)}"
    )


def _run_tool_loop(trip: Trip) -> list:
    chat_model = get_chat_model(temperature=0.2)
    model_with_tools = chat_model.bind_tools(TOOLS)

    messages = [
        SystemMessage(
            content=(
                "تو یک عامل برنامه‌ریز سفر هستی که یک برنامه روزانه واقع‌بینانه برای سفرچین می‌سازد.\n"
                "مراحل کاری: ۱) با ابزار web_research مکان‌های کاندید (جاذبه، رستوران، فعالیت) را بر اساس "
                "علایق و مقصد پیدا کن. ۲) با neshan_place_search هر کاندید را به یک مکان واقعی و مختصات "
                "دقیق تبدیل کن (در صورت نیاز neshan_geocode یا neshan_reverse_geocode را هم به کار ببر). "
                "۳) در صورت نیاز neshan_place_details را برای ساعات کاری صدا بزن. "
                "۴) با neshan_route زمان جابجایی بین مکان‌های نزدیک به هم در یک روز را تخمین بزن تا برنامه "
                "زمانی واقع‌بینانه باشد (با توجه به ریتم سفر: آرام/متعادل/فشرده). "
                "وقتی اطلاعات کافی جمع شد، دیگر ابزاری صدا نزن و آماده اعلام پایان تحقیق باش.\n\n"
                f"اطلاعات سفر:\n{_trip_brief_fa(trip)}"
            )
        ),
        HumanMessage(content="تحقیق و جمع‌آوری اطلاعات لازم برای ساخت برنامه را شروع کن."),
    ]

    for _ in range(MAX_TOOL_ITERATIONS):
        ai_message: AIMessage = model_with_tools.invoke(messages)
        messages.append(ai_message)
        if not ai_message.tool_calls:
            break
        for call in ai_message.tool_calls:
            tool_fn = TOOL_MAP.get(call["name"])
            try:
                result = tool_fn.invoke(call["args"]) if tool_fn else {"error": f"unknown tool {call['name']}"}
            except Exception as exc:  # noqa: BLE001 - surface tool failure back to the model, don't crash the job
                logger.warning("Tool %s failed: %s", call["name"], exc)
                result = {"error": str(exc)}
            messages.append(
                ToolMessage(content=json.dumps(result, ensure_ascii=False, default=str), tool_call_id=call["id"])
            )

    return messages


def _persist_place(trip: Trip, place: PlaceRef | None, cache: dict) -> PlaceCandidate | None:
    if place is None:
        return None
    key = (place.name, place.latitude, place.longitude)
    if key in cache:
        return cache[key]
    obj = PlaceCandidate.objects.create(
        trip=trip,
        name=place.name,
        category=place.category,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        source=place.source,
        source_url=place.source_url,
    )
    cache[key] = obj
    return obj


def generate_itinerary(trip: Trip) -> Itinerary:
    duration = (trip.end_date - trip.start_date).days + 1 if trip.start_date and trip.end_date else None

    tool_messages = _run_tool_loop(trip)
    tool_messages.append(
        HumanMessage(
            content=(
                "حالا بر اساس تحقیقی که انجام دادی، خروجی نهایی برنامه سفر را دقیقاً مطابق اسکیمای "
                "ItineraryPlan به‌صورت JSON برگردان. برای هر آیتم در صورت امکان یک place با مختصات واقعی "
                "(از نتایج neshan_place_search) بگذار."
            )
        )
    )

    chat_model = get_chat_model(temperature=0.2)
    plan = run_with_structured_repair(chat_model, ItineraryPlan, tool_messages)

    warnings = validate_plan(plan, duration)
    if warnings:
        logger.warning("Itinerary for trip %s has validation warnings: %s", trip.id, warnings)

    place_cache: dict = {}

    Itinerary.objects.filter(trip=trip).delete()
    itinerary = Itinerary.objects.create(
        trip=trip,
        summary=plan.summary_fa + ("\n\nهشدارها:\n" + "\n".join(warnings) if warnings else ""),
        model_name=chat_model.model_name if hasattr(chat_model, "model_name") else "",
        raw_output=plan.model_dump(),
    )

    for day_plan in plan.days:
        day = ItineraryDay.objects.create(
            itinerary=itinerary,
            day_index=day_plan.day_index,
            date=day_plan.date or None,
            city=day_plan.city,
            notes=day_plan.notes,
        )
        for order, item_plan in enumerate(day_plan.items):
            place_obj = _persist_place(trip, item_plan.place, place_cache)
            ItineraryItem.objects.create(
                day=day,
                order=order,
                start_time=item_plan.start_time or None,
                end_time=item_plan.end_time or None,
                title=item_plan.title,
                description=item_plan.description,
                category=item_plan.category,
                place=place_obj,
            )

    Accommodation.objects.filter(trip=trip).delete()
    for accommodation_plan in plan.accommodation_options:
        place_obj = _persist_place(trip, accommodation_plan.place, place_cache)
        Accommodation.objects.create(
            trip=trip,
            place=place_obj,
            name=accommodation_plan.name,
            room_type=accommodation_plan.room_type,
            nightly_price=accommodation_plan.nightly_price,
            is_selected=False,
            source=accommodation_plan.place.source if accommodation_plan.place else "model",
        )

    return itinerary
