"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api";
import type { Accommodation, Itinerary, PlanningJob, Trip } from "@/types";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/States";
import ChatPanel from "@/components/trip/ChatPanel";
import PreferencesSummary from "@/components/trip/PreferencesSummary";
import ItineraryView from "@/components/trip/ItineraryView";
import AccommodationList from "@/components/trip/AccommodationList";
import TripMap from "@/components/trip/TripMap";

const STATUS_LABEL_FA: Record<Trip["status"], string> = {
  collecting_info: "در حال تکمیل اطلاعات",
  ready_for_generation: "آماده تولید برنامه",
  generating: "در حال تولید برنامه...",
  planned: "برنامه‌ریزی‌شده",
  archived: "بایگانی‌شده",
};

export default function TripDetailPage() {
  const params = useParams<{ id: string }>();
  const tripId = params.id;

  const [trip, setTrip] = useState<Trip | null>(null);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [accommodations, setAccommodations] = useState<Accommodation[]>([]);
  const [job, setJob] = useState<PlanningJob | null>(null);
  const [loadError, setLoadError] = useState("");
  const [generateError, setGenerateError] = useState("");
  const [selectedDayId, setSelectedDayId] = useState<number | null>(null);
  // Adjusted during render (React's recommended pattern for resetting state when an
  // upstream value changes) rather than in an effect, to avoid an extra commit/re-render.
  const [lastItineraryId, setLastItineraryId] = useState<number | undefined>(undefined);
  if (itinerary?.id !== lastItineraryId) {
    setLastItineraryId(itinerary?.id);
    setSelectedDayId(null);
  }

  const loadTrip = useCallback(() => {
    apiFetch<Trip>(`/api/trips/${tripId}/`)
      .then(setTrip)
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "خطا در بارگذاری سفر."));
  }, [tripId]);

  const loadItinerary = useCallback(() => {
    apiFetch<Itinerary>(`/api/trips/${tripId}/itinerary/`)
      .then(setItinerary)
      .catch(() => setItinerary(null));
    apiFetch<Accommodation[]>(`/api/trips/${tripId}/accommodations/`)
      .then(setAccommodations)
      .catch(() => setAccommodations([]));
  }, [tripId]);

  useEffect(() => {
    loadTrip();
    loadItinerary();
  }, [loadTrip, loadItinerary]);

  // Poll job status while a plan is being generated.
  useEffect(() => {
    if (!job || job.status === "succeeded" || job.status === "failed") return;
    const interval = setInterval(async () => {
      const updated = await apiFetch<PlanningJob>(`/api/trips/${tripId}/generate/${job.id}/`);
      setJob(updated);
      if (updated.status === "succeeded") {
        loadTrip();
        loadItinerary();
      }
    }, 2500);
    return () => clearInterval(interval);
  }, [job, tripId, loadTrip, loadItinerary]);

  async function handleGenerate() {
    setGenerateError("");
    try {
      const newJob = await apiFetch<PlanningJob>(`/api/trips/${tripId}/generate/`, { method: "POST" });
      setJob(newJob);
      loadTrip();
    } catch (err) {
      setGenerateError(err instanceof ApiError ? err.message : "شروع تولید برنامه ممکن نشد.");
    }
  }

  // Memoized so the array reference is stable across re-renders that don't change the
  // underlying data (e.g. the 2.5s job-status poll) -- TripMap re-inits its Leaflet map
  // whenever this reference changes, and a churning reference caused rapid re-init races.
  const places = useMemo(
    () =>
      [
        ...(itinerary?.days.flatMap((d) => d.items.map((i) => i.place).filter(Boolean)) || []),
        ...accommodations.map((a) => a.place).filter(Boolean),
      ] as Array<NonNullable<Accommodation["place"]>>,
    [itinerary, accommodations]
  );

  // The selected day's stops, in visit order, for TripMap to draw as a route.
  const selectedDayRoute = useMemo(() => {
    const day = itinerary?.days.find((d) => d.id === selectedDayId);
    return (day?.items.map((i) => i.place).filter(Boolean) || []) as Array<
      NonNullable<Accommodation["place"]>
    >;
  }, [itinerary, selectedDayId]);

  if (loadError) return <ErrorState message={loadError} />;
  if (!trip) return <LoadingState />;

  return (
    <div className="mx-auto max-w-6xl px-margin py-space-lg">
      <div className="sticky top-16 z-40 -mx-margin mb-space-lg flex flex-wrap items-center justify-between gap-space-sm bg-surface/90 px-margin py-space-sm shadow-[0_1px_8px_rgba(0,0,0,0.05)] backdrop-blur-xl">
        <div>
          <h1 className="font-headline font-headline-md text-headline-md font-bold text-on-surface">
            {trip.title || `${trip.origin} به ${trip.destination}`}
          </h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant">{STATUS_LABEL_FA[trip.status]}</p>
        </div>
        {(trip.status === "ready_for_generation" || trip.status === "planned") && (
          <Button
            variant="primary"
            onClick={handleGenerate}
            loading={job?.status === "pending" || job?.status === "running"}
          >
            <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
            {trip.status === "planned" ? "تولید دوباره برنامه" : "تولید برنامه سفر"}
          </Button>
        )}
      </div>

      {generateError && (
        <div className="mb-space-md">
          <ErrorState message={generateError} />
        </div>
      )}
      {job?.status === "failed" && (
        <div className="mb-space-md">
          <ErrorState message={`تولید برنامه ناموفق بود: ${job.error_message}`} />
        </div>
      )}

      <div className="grid gap-space-lg lg:grid-cols-2">
        <div className="flex flex-col gap-space-lg">
          <Card className="h-[420px] overflow-hidden p-0">
            <ChatPanel tripId={tripId} onTripUpdate={setTrip} />
          </Card>
          <Card variant="prominent">
            <h2 className="mb-space-md flex items-center gap-space-xs font-headline-sm text-headline-sm font-semibold text-on-surface">
              <span className="material-symbols-outlined text-[20px] text-primary">tune</span>
              خلاصه قابل ویرایش سفر
            </h2>
            <PreferencesSummary trip={trip} onChange={setTrip} />
          </Card>
        </div>

        <div className="flex flex-col gap-space-lg">
          <Card className="h-[320px] overflow-hidden p-1">
            <TripMap places={places} origin={trip.origin} route={selectedDayRoute} />
          </Card>

          {itinerary ? (
            <ItineraryView
              itinerary={itinerary}
              selectedDayId={selectedDayId}
              onSelectDay={setSelectedDayId}
            />
          ) : (
            <Card variant="prominent">
              <p className="font-body-md text-body-md text-on-surface-variant">
                {job?.status === "running" || job?.status === "pending"
                  ? "سفرچین در حال ساخت برنامه سفر شماست..."
                  : "هنوز برنامه‌ای تولید نشده است. پس از تکمیل اطلاعات، روی «تولید برنامه سفر» بزنید."}
              </p>
            </Card>
          )}

          {accommodations.length > 0 && (
            <div>
              <h2 className="mb-space-sm flex items-center gap-space-xs font-headline-sm text-headline-sm font-semibold text-on-surface">
                <span className="material-symbols-outlined text-[20px] text-primary">hotel</span>
                پیشنهاد اقامت
              </h2>
              <AccommodationList tripId={tripId} accommodations={accommodations} onSelected={loadItinerary} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
