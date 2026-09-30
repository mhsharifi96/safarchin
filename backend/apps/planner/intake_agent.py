"""Conversational trip-intake turn: parses the latest user message, updates
the single persisted TripPreferences row (never a separate ad-hoc state),
tracks explicit assumptions, and decides whether to ask another short
question or move to the editable summary. Steps 1-2 of the orchestrated
workflow in the spec ("parse intent and update preferences" / "determine
missing essential information")."""
from langchain_core.messages import HumanMessage, SystemMessage

from apps.trips.models import ConversationMessage, Trip

from .llm import LLMNotConfigured, get_chat_model
from .repair import RepairExhausted, run_with_structured_repair
from .schemas import PreferencesExtraction

ESSENTIAL_FIELDS = [
    "origin",
    "destination",
    "start_date",
    "end_date",
    "adults_count",
    "intercity_transport",
    "local_transport",
    "interests",
    "pace",
    "budget_amount",
]


def _known_state_fa(trip: Trip) -> str:
    prefs = trip.preferences
    lines = [
        f"مبدا: {trip.origin or 'نامشخص'}",
        f"مقصد: {trip.destination or 'نامشخص'}",
        f"تاریخ شروع: {trip.start_date or 'نامشخص'}",
        f"تاریخ پایان: {trip.end_date or 'نامشخص'}",
        f"تعداد بزرگسال: {prefs.adults_count if prefs.adults_count is not None else 'نامشخص'}",
        f"تعداد کودک: {prefs.children_count if prefs.children_count is not None else 'نامشخص'}",
        f"حمل‌ونقل بین‌شهری: {prefs.intercity_transport}",
        f"حمل‌ونقل درون‌شهری: {prefs.local_transport}",
        f"علایق: {', '.join(prefs.interests) if prefs.interests else 'نامشخص'}",
        f"ریتم سفر: {prefs.pace or 'نامشخص'}",
        f"بودجه: {prefs.budget_amount if prefs.budget_amount is not None else 'نامشخص'} ({prefs.budget_scope or '?'})",
        f"اقامت موجود: {prefs.has_existing_accommodation}",
    ]
    return "\n".join(lines)


def _build_messages(trip: Trip) -> list:
    system = SystemMessage(
        content=(
            "تو دستیار برنامه‌ریز سفر «سفرچین» هستی. فقط به فارسی و خودمانی اما محترمانه پاسخ بده.\n"
            "اطلاعات فعلی سفر که از قبل می‌دانی (هرگز دوباره درباره آن‌ها سوال نپرس مگر کاربر بخواهد تغییرش دهد):\n"
            f"{_known_state_fa(trip)}\n\n"
            "وظیفه‌ات: از آخرین پیام کاربر، فیلدهای مرتبط را استخراج کن، اگر چیزی نامشخص و ضروری است "
            "یک یا دو سوال کوتاه و مکالمه‌ای بپرس (نه یک فرم طولانی)، و اگر کاربر جزئیاتی را نگفت ولی "
            "می‌توان یک فرض منطقی گذاشت، آن را به‌صراحت در assumptions ثبت کن. "
            "وقتی همه فیلدهای ضروری مشخص یا با فرض صریح پر شدند، ready_for_summary=true بگذار و یک "
            "خلاصه کوتاه برای تایید کاربر در assistant_reply_fa بنویس."
        )
    )
    history = [
        HumanMessage(content=m.content) if m.role == ConversationMessage.Role.USER else SystemMessage(content=m.content)
        for m in trip.messages.order_by("created_at")
    ]
    return [system, *history]


def _apply_extraction(trip: Trip, extraction: PreferencesExtraction) -> None:
    # A plan already exists for the OLD values -- if the user changes a field that
    # actually shapes the itinerary (destination, dates, budget) mid-conversation,
    # that plan is now stale and must not keep silently claiming to be "planned".
    was_planned = trip.status == Trip.Status.PLANNED
    core_changed = False

    trip_fields = {}
    if extraction.origin:
        trip_fields["origin"] = extraction.origin
    if extraction.destination:
        trip_fields["destination"] = extraction.destination
    if extraction.start_date:
        trip_fields["start_date"] = extraction.start_date
    if extraction.end_date:
        trip_fields["end_date"] = extraction.end_date
    for key, value in trip_fields.items():
        old_value = getattr(trip, key)
        if str(old_value or "") != str(value):
            core_changed = True
        setattr(trip, key, value)

    prefs = trip.preferences
    pref_field_names = [
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
    ]
    for name in pref_field_names:
        value = getattr(extraction, name)
        if value is not None:
            # Of all the preference fields, only the budget actually invalidates an
            # existing plan the way destination/dates do -- pace, interests, transport,
            # etc. can be nudged without the itinerary itself being wrong.
            if name == "budget_amount":
                old_budget = getattr(prefs, name)
                if old_budget is None or float(old_budget) != value:
                    core_changed = True
            setattr(prefs, name, value)

    if extraction.assumptions:
        existing_fields = {a["field"] for a in prefs.assumptions}
        for assumption in extraction.assumptions:
            if assumption.field not in existing_fields:
                prefs.assumptions.append(assumption.model_dump())

    if extraction.ready_for_summary:
        trip.status = Trip.Status.READY_FOR_GENERATION
    elif was_planned and core_changed:
        # Still "planned" per the LLM's own judgement would be wrong here: the itinerary
        # on file no longer matches origin/destination/dates/budget. Send it back through
        # the summary/regenerate flow instead of leaving a mismatched plan looking current.
        trip.status = Trip.Status.COLLECTING_INFO

    trip.save()
    prefs.save()


def run_intake_turn(trip: Trip) -> str:
    try:
        chat_model = get_chat_model()
    except LLMNotConfigured as exc:
        return (
            "برای تولید پاسخ هوشمند به این پیام، سرویس مدل زبانی هنوز پیکربندی نشده است "
            f"({exc}). اطلاعات شما ذخیره شد و به‌محض تنظیم OPENAI_API_KEY، مکالمه ادامه می‌یابد."
        )

    messages = _build_messages(trip)
    try:
        extraction = run_with_structured_repair(chat_model, PreferencesExtraction, messages)
    except RepairExhausted as exc:
        return f"متاسفانه در پردازش پیام شما مشکلی پیش آمد، لطفاً دوباره امتحان کنید. ({exc})"

    _apply_extraction(trip, extraction)
    return extraction.assistant_reply_fa
