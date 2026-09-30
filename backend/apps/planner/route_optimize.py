"""Greedy nearest-neighbor reordering of a day's flexible stops (sights, rests,
transport legs, etc.) by straight-line distance, so the day backtracks as little
as possible. Meals and accommodation check-in/out are left in their original slot
-- their *timing* (breakfast in the morning, dinner in the evening) matters more
than geographic optimality, so they act as fixed anchors that flexible stops are
chained between.
"""
from math import asin, cos, radians, sin, sqrt

from .schemas import ItineraryItemPlan

ANCHOR_CATEGORIES = {"food", "accommodation"}


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(a))


def _has_coords(item: ItineraryItemPlan) -> bool:
    return bool(item.place and item.place.latitude is not None and item.place.longitude is not None)


def _nearest_neighbor(
    segment: list[ItineraryItemPlan], start: tuple[float, float] | None
) -> list[ItineraryItemPlan]:
    """Greedily visit the closest remaining stop next, then reassign the segment's
    own (already time-ordered) start/end times to the new sequence -- only *which*
    stop fills each time slot changes, so the day's time flow stays intact."""
    if len(segment) <= 1:
        return segment

    original_times = [(it.start_time, it.end_time) for it in segment]
    remaining = list(segment)
    ordered: list[ItineraryItemPlan] = []
    current = start
    while remaining:
        if current is None:
            nxt = remaining.pop(0)
        else:
            nxt = min(
                remaining,
                key=lambda it: _haversine_km(
                    current[0], current[1], it.place.latitude, it.place.longitude
                ),
            )
            remaining.remove(nxt)
        ordered.append(nxt)
        current = (nxt.place.latitude, nxt.place.longitude)

    for item, (start_time, end_time) in zip(ordered, original_times):
        item.start_time = start_time
        item.end_time = end_time
    return ordered


def optimize_day_order(items: list[ItineraryItemPlan]) -> list[ItineraryItemPlan]:
    """Reorder a day's geocoded, non-anchor stops for the shortest total travel
    distance. Anchors (meals, accommodation) and items with no coordinates keep
    their original position; runs of flexible stops between anchors are
    nearest-neighbor-ordered, chained onward from the last known anchor
    coordinate (or the trip's first stop, if the day opens with flexible stops)."""
    result: list[ItineraryItemPlan] = []
    segment: list[ItineraryItemPlan] = []
    anchor_coord: tuple[float, float] | None = None

    def flush() -> None:
        nonlocal segment
        if segment:
            result.extend(_nearest_neighbor(segment, anchor_coord))
            segment = []

    for item in items:
        is_anchor = item.category in ANCHOR_CATEGORIES or not _has_coords(item)
        if is_anchor:
            flush()
            result.append(item)
            if _has_coords(item):
                anchor_coord = (item.place.latitude, item.place.longitude)
        else:
            segment.append(item)
    flush()
    return result
