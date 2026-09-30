class GuestSessionMiddleware:
    """Ensures anonymous visitors get a persisted, opaque Django session key
    before they hit trip-creation endpoints, so a guest trip can be tied to
    `request.session.session_key` without requiring an explicit sign-up step.
    The key itself is server-issued and unguessable; trip ownership checks
    still compare it against the trip's stored guest_session_key (see
    apps.trips.permissions) rather than trusting the trip id alone.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and request.path.startswith("/api/trips/") and not request.session.session_key:
            request.session.save()
        return self.get_response(request)
