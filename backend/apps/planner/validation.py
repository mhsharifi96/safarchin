"""Structural validation of a generated ItineraryPlan (step 8 of the
workflow). Returns a list of human-readable warning strings; callers decide
whether any warnings are severe enough to fail the job."""
from datetime import datetime

from .schemas import ItineraryPlan


def validate_plan(plan: ItineraryPlan, expected_day_count: int | None) -> list[str]:
    warnings: list[str] = []

    if not plan.days:
        warnings.append("هیچ روزی در برنامه تولید نشده است.")
        return warnings

    if expected_day_count and len(plan.days) != expected_day_count:
        warnings.append(
            f"تعداد روزهای برنامه ({len(plan.days)}) با مدت سفر ({expected_day_count} روز) مطابقت ندارد."
        )

    seen_indexes = set()
    for day in plan.days:
        if day.day_index in seen_indexes:
            warnings.append(f"روز {day.day_index} بیش از یک بار در برنامه تکرار شده است.")
        seen_indexes.add(day.day_index)

        if not day.items:
            warnings.append(f"روز {day.day_index} هیچ برنامه‌ای ندارد.")
            continue

        parsed_times: list[tuple[datetime, datetime, str]] = []
        for item in day.items:
            if not item.start_time or not item.end_time:
                continue
            try:
                start = datetime.strptime(item.start_time, "%H:%M")
                end = datetime.strptime(item.end_time, "%H:%M")
            except ValueError:
                warnings.append(f"روز {day.day_index}: زمان نامعتبر برای «{item.title}».")
                continue
            if end <= start:
                warnings.append(f"روز {day.day_index}: زمان پایان «{item.title}» قبل از زمان شروع آن است.")
                continue
            parsed_times.append((start, end, item.title))

        parsed_times.sort(key=lambda t: t[0])
        for (start_a, end_a, title_a), (start_b, _end_b, title_b) in zip(parsed_times, parsed_times[1:]):
            if start_b < end_a:
                warnings.append(f"روز {day.day_index}: تداخل زمانی بین «{title_a}» و «{title_b}».")

    return warnings
