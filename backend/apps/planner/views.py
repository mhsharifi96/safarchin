from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class PlannerHealthView(APIView):
    """Reports which external credentials are configured, without leaking
    their values, so the frontend/ops can tell what's mocked vs. live."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "openai_configured": bool(settings.OPENAI_API_KEY),
                "model_name": settings.OPENAI_MODEL_NAME,
                "langsmith_tracing_enabled": settings.LANGCHAIN_TRACING_V2,
                "tavily_configured": bool(settings.TAVILY_API_KEY),
                "neshan_configured": bool(settings.NESHAN_API_KEY),
            }
        )
