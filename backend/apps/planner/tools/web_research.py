"""Web research tool backed by Tavily (https://tavily.com), used by the
planner agent to gather candidate places / current visit information with
sources before they're resolved to real geographic places via Neshan."""
from django.conf import settings
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from tavily import TavilyClient


class WebResearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: float = 0.0


class WebResearchInput(BaseModel):
    query: str = Field(description="Search query, e.g. 'بهترین جاذبه‌های گردشگری تبریز'")
    max_results: int = Field(default=5, ge=1, le=10)


def web_research(query: str, max_results: int = 5) -> list[WebResearchResult]:
    if not settings.TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not set. Configure it in backend/.env to enable web research.")
    client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    response = client.search(query=query, max_results=max_results, search_depth="advanced")
    return [
        WebResearchResult(
            title=item.get("title", ""),
            url=item.get("url", ""),
            content=item.get("content", ""),
            score=item.get("score", 0.0),
        )
        for item in response.get("results", [])
    ]


@tool("web_research", args_schema=WebResearchInput)
def web_research_tool(query: str, max_results: int = 5) -> list[dict]:
    """Search the live web (via Tavily) for candidate places, events, or
    current visit information relevant to the trip, returning titles, URLs
    and snippets so results can be cited."""
    return [r.model_dump() for r in web_research(query, max_results)]
