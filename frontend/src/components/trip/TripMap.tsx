"use client";

import { useEffect, useRef, useState } from "react";
import type { Map as LeafletMap, LayerGroup } from "leaflet";

import type { PlaceRef } from "@/types";
import { EmptyState } from "@/components/ui/States";

const NESHAN_WEB_SDK_KEY = process.env.NEXT_PUBLIC_NESHAN_WEB_SDK_KEY;
const DEFAULT_CENTER: [number, number] = [35.6892, 51.389]; // Tehran, used when no place has coordinates yet

/** Itinerary items like "حرکت از تهران" (departure) carry the origin city itself as their
 * `place`, purely as a waypoint marker. Left in, they'd drag the view/center back toward
 * the origin instead of the actual destination -- so they're excluded when framing the
 * map, though still shown as pins. */
function isOriginWaypoint(place: PlaceRef, origin: string): boolean {
  const normalize = (s: string) => s.trim().toLowerCase();
  return normalize(place.name) === normalize(origin);
}

export default function TripMap({
  places,
  origin,
  route,
}: {
  places: PlaceRef[];
  origin?: string;
  /** A single day's stops, in visit order -- drawn as a connecting, numbered path so the
   * direction of travel for that day is visible on the map. */
  route?: PlaceRef[];
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markersRef = useRef<LayerGroup | null>(null);
  const routeLayerRef = useRef<LayerGroup | null>(null);
  const [ready, setReady] = useState(false);

  // Mount the Leaflet map exactly once for this component's lifetime. Re-creating a map on
  // a container that already has one throws "Map container is already initialized", which
  // happened here because `places` got a new array reference on nearly every re-render.
  useEffect(() => {
    if (!NESHAN_WEB_SDK_KEY || !containerRef.current) return;
    let cancelled = false;

    (async () => {
      const L = (await import("@neshan-maps-platform/leaflet")).default;
      if (cancelled || !containerRef.current || mapRef.current) return;

      const map = new L.Map(containerRef.current, {
        key: NESHAN_WEB_SDK_KEY,
        maptype: "dreamy",
        center: DEFAULT_CENTER,
        zoom: 11,
      });
      markersRef.current = L.layerGroup().addTo(map);
      routeLayerRef.current = L.layerGroup().addTo(map);
      mapRef.current = map;
      setReady(true);
    })();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
      markersRef.current = null;
      routeLayerRef.current = null;
    };
  }, []);

  // Redraw markers / reframe the view whenever the place list changes, without touching the
  // underlying map instance.
  useEffect(() => {
    const map = mapRef.current;
    const markers = markersRef.current;
    if (!ready || !map || !markers) return;

    let cancelled = false;

    (async () => {
      const L = (await import("@neshan-maps-platform/leaflet")).default;
      if (cancelled) return;

      markers.clearLayers();

      const withCoords = places.filter((p) => p.latitude !== null && p.longitude !== null);
      const destinationPoints = origin
        ? withCoords.filter((p) => !isOriginWaypoint(p, origin))
        : withCoords;
      // Fall back to all points (including origin) only if nothing else has coordinates yet.
      const focusPoints = destinationPoints.length ? destinationPoints : withCoords;

      withCoords.forEach((place) => {
        L.marker([place.latitude as number, place.longitude as number])
          .addTo(markers)
          .bindPopup(place.name);
      });

      const routeCoords = (route || [])
        .filter((p) => p.latitude !== null && p.longitude !== null)
        .map((p) => [p.latitude as number, p.longitude as number] as [number, number]);

      // A selected day's route takes over framing (it's what the user just asked to see);
      // otherwise fall back to the whole-trip overview.
      if (routeCoords.length) {
        const bounds = L.latLngBounds(routeCoords);
        map.fitBounds(bounds, { padding: [32, 32], maxZoom: 15 });
      } else if (focusPoints.length > 1) {
        const bounds = L.latLngBounds(
          focusPoints.map((p) => [p.latitude as number, p.longitude as number])
        );
        map.fitBounds(bounds, { padding: [24, 24], maxZoom: 15 });
      } else if (focusPoints.length === 1) {
        map.setView(
          [focusPoints[0].latitude as number, focusPoints[0].longitude as number],
          13
        );
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [places, origin, route, ready]);

  // Draw the selected day's route as a numbered, directional path -- kept in its own effect
  // (and layer) so it redraws independently of the whole-trip marker set above.
  useEffect(() => {
    const routeLayer = routeLayerRef.current;
    if (!ready || !routeLayer) return;

    let cancelled = false;

    (async () => {
      const L = (await import("@neshan-maps-platform/leaflet")).default;
      if (cancelled) return;

      routeLayer.clearLayers();

      const stops = (route || []).filter((p) => p.latitude !== null && p.longitude !== null);
      if (stops.length < 2) return;

      const latlngs = stops.map((p) => [p.latitude as number, p.longitude as number] as [number, number]);
      L.polyline(latlngs, {
        color: "#a33d23",
        weight: 4,
        opacity: 0.85,
        dashArray: "1 10",
        lineCap: "round",
      }).addTo(routeLayer);

      stops.forEach((place, index) => {
        L.marker([place.latitude as number, place.longitude as number], {
          icon: L.divIcon({
            className: "",
            html: `<div style="display:flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:9999px;background:#a33d23;color:#fff;font:bold 12px sans-serif;box-shadow:0 1px 4px rgba(0,0,0,0.3);">${index + 1}</div>`,
            iconSize: [22, 22],
            iconAnchor: [11, 11],
          }),
        })
          .addTo(routeLayer)
          .bindPopup(`${index + 1}. ${place.name}`);
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [route, ready]);

  if (!NESHAN_WEB_SDK_KEY) {
    return (
      <EmptyState
        title="نقشه در دسترس نیست"
        description="برای نمایش نقشه، کلید NEXT_PUBLIC_NESHAN_WEB_SDK_KEY را در تنظیمات فرانت‌اند وارد کنید."
      />
    );
  }

  return <div ref={containerRef} className="h-full min-h-[320px] w-full rounded-DEFAULT" />;
}
