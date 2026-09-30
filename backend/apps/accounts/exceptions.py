from rest_framework.views import exception_handler as drf_exception_handler


def safarchin_exception_handler(exc, context):
    """Normalizes DRF error responses to a consistent {"detail": str, "errors": dict|None} shape
    so the frontend doesn't need per-endpoint error parsing."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        response.data = {"detail": data["detail"], "errors": None}
    elif isinstance(data, dict):
        detail = data.get("detail") or "درخواست نامعتبر است."
        response.data = {"detail": detail, "errors": data}
    elif isinstance(data, list):
        response.data = {"detail": "درخواست نامعتبر است.", "errors": {"non_field_errors": data}}
    return response
