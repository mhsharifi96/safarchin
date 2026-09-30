"""LangChain model adapter, configured entirely from environment/settings.

The requested model label "5.6-luna" maps to the real, currently-public
OpenAI model id "gpt-5.6-luna" (verified against provider docs, not assumed).
OPENAI_MODEL_NAME is still fully configurable via env -- this module never
silently swaps in a different model than what's configured; if the model
can't be resolved we raise rather than falling back to another id.
"""
from django.conf import settings
from langchain_openai import ChatOpenAI


class LLMNotConfigured(RuntimeError):
    pass


def get_chat_model(*, temperature: float = 0.3) -> ChatOpenAI:
    if not settings.OPENAI_API_KEY:
        raise LLMNotConfigured(
            "OPENAI_API_KEY is not set. Configure it in backend/.env to enable the planning agent."
        )
    kwargs = {
        "model": settings.OPENAI_MODEL_NAME,
        "api_key": settings.OPENAI_API_KEY,
        "temperature": temperature,
    }
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)
