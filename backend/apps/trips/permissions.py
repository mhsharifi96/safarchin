from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission


def has_trip_access(request, trip) -> bool:
    """Real ownership check: an authenticated user must own the trip, or an
    anonymous guest's current session key must match the trip's stored
    guest_session_key. The trip's UUID being hard to guess is not treated as
    sufficient authorization on its own."""
    if request.user.is_authenticated:
        return trip.owner_id == request.user.id
    session_key = request.session.session_key
    return bool(trip.guest_session_key) and trip.guest_session_key == session_key


class IsTripOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        trip = obj if obj.__class__.__name__ == "Trip" else obj.trip
        if not has_trip_access(request, trip):
            # 404 instead of 403 so guessing another user's trip id doesn't confirm it exists.
            raise NotFound("سفر مورد نظر یافت نشد.")
        return True
