"""Typed tools wrapping the Neshan platform REST APIs
(https://platform.neshan.org/api/), verified against the current official
docs (Sept 2026):

  Search            GET https://api.neshan.org/v3/search?q={json}      header Api-Key
  Geocoding         GET https://api.neshan.org/geocoding/v1?json={..}  header Api-Key
  Reverse geocoding GET https://api.neshan.org/v5/reverse?lat=&lng=     header Api-Key
  POI details       GET https://api.neshan.org/v1/point?hash={poiHash} header Api-Key
  Routing/direction GET https://api.neshan.org/v4/direction?...        header Api-Key

All calls raise RuntimeError with a clear message if NESHAN_API_KEY is unset,
rather than silently returning fake data.
"""
import json

import httpx
from django.conf import settings
from langchain_core.tools import tool
from pydantic import BaseModel, Field

NESHAN_BASE_URL = "https://api.neshan.org"


def _require_api_key() -> str:
    if not settings.NESHAN_API_KEY:
        raise RuntimeError("NESHAN_API_KEY is not set. Configure it in backend/.env to enable Neshan integrations.")
    return settings.NESHAN_API_KEY


def _client() -> httpx.Client:
    return httpx.Client(headers={"Api-Key": _require_api_key()}, timeout=10.0)


class PlaceSearchInput(BaseModel):
    term: str = Field(description="Search text, e.g. 'رستوران سنتی تبریز'")
    center_lat: float = Field(description="Latitude to search around")
    center_lng: float = Field(description="Longitude to search around")


def search_places(term: str, center_lat: float, center_lng: float) -> list[dict]:
    query = json.dumps({"term": term, "center": {"latitude": center_lat, "longitude": center_lng}})
    with _client() as client:
        response = client.get(f"{NESHAN_BASE_URL}/v3/search", params={"q": query})
        response.raise_for_status()
        data = response.json()
    return [
        {
            "title": item.get("title", ""),
            "address": item.get("address", ""),
            "category": item.get("category", ""),
            "type": item.get("type", ""),
            "latitude": item.get("location", {}).get("y"),
            "longitude": item.get("location", {}).get("x"),
            "poi_hash": item.get("poiHash", ""),
        }
        for item in data.get("items", [])
    ]


@tool("neshan_place_search", args_schema=PlaceSearchInput)
def neshan_place_search_tool(term: str, center_lat: float, center_lng: float) -> list[dict]:
    """Search for real places (POIs) near a coordinate using Neshan's Search
    API. Use this to resolve web-research candidates to real, mappable
    places before adding them to an itinerary."""
    return search_places(term, center_lat, center_lng)


class PlaceDetailsInput(BaseModel):
    poi_hash: str = Field(description="poiHash returned by neshan_place_search")


def get_place_details(poi_hash: str) -> dict:
    with _client() as client:
        response = client.get(f"{NESHAN_BASE_URL}/v1/point", params={"hash": poi_hash})
        response.raise_for_status()
        return response.json()


@tool("neshan_place_details", args_schema=PlaceDetailsInput)
def neshan_place_details_tool(poi_hash: str) -> dict:
    """Fetch detailed info (address, work hours, phone) for a place found via
    neshan_place_search, when available."""
    return get_place_details(poi_hash)


class GeocodeInput(BaseModel):
    address: str
    city: str = ""
    province: str = ""


def geocode_address(address: str, city: str = "", province: str = "") -> list[dict]:
    payload = {"address": address}
    if city:
        payload["city"] = city
    if province:
        payload["province"] = province
    with _client() as client:
        response = client.get(f"{NESHAN_BASE_URL}/geocoding/v1", params={"json": json.dumps(payload)})
        response.raise_for_status()
        data = response.json()
    return [
        {
            "latitude": item.get("location", {}).get("latitude"),
            "longitude": item.get("location", {}).get("longitude"),
            "city": item.get("city", ""),
            "province": item.get("province", ""),
        }
        for item in data.get("items", [])
    ]


@tool("neshan_geocode", args_schema=GeocodeInput)
def neshan_geocode_tool(address: str, city: str = "", province: str = "") -> list[dict]:
    """Convert a free-text address into coordinates using Neshan Geocoding."""
    return geocode_address(address, city, province)


class ReverseGeocodeInput(BaseModel):
    lat: float
    lng: float


def reverse_geocode(lat: float, lng: float) -> dict:
    with _client() as client:
        response = client.get(f"{NESHAN_BASE_URL}/v5/reverse", params={"lat": lat, "lng": lng})
        response.raise_for_status()
        return response.json()


@tool("neshan_reverse_geocode", args_schema=ReverseGeocodeInput)
def neshan_reverse_geocode_tool(lat: float, lng: float) -> dict:
    """Convert coordinates into a formatted address using Neshan Reverse Geocoding."""
    return reverse_geocode(lat, lng)


class RoutingInput(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float
    vehicle_type: str = Field(default="car", description="'car' or 'motorcycle'")


def get_route(
    origin_lat: float, origin_lng: float, destination_lat: float, destination_lng: float, vehicle_type: str = "car"
) -> dict:
    with _client() as client:
        response = client.get(
            f"{NESHAN_BASE_URL}/v4/direction",
            params={
                "type": vehicle_type,
                "origin": f"{origin_lat},{origin_lng}",
                "destination": f"{destination_lat},{destination_lng}",
            },
        )
        response.raise_for_status()
        data = response.json()
    routes = data.get("routes", [])
    if not routes:
        return {"distance_meters": None, "duration_seconds": None}
    leg = routes[0]["legs"][0]
    return {
        "distance_meters": leg.get("distance", {}).get("value"),
        "duration_seconds": leg.get("duration", {}).get("value"),
        "summary": leg.get("summary", ""),
    }


@tool("neshan_route", args_schema=RoutingInput)
def neshan_route_tool(
    origin_lat: float, origin_lng: float, destination_lat: float, destination_lng: float, vehicle_type: str = "car"
) -> dict:
    """Calculate driving/motorcycle travel time and distance between two
    coordinates using Neshan's routing (direction) API."""
    return get_route(origin_lat, origin_lng, destination_lat, destination_lng, vehicle_type)
