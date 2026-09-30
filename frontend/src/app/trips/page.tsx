"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { apiFetch } from "@/lib/api";
import type { Trip } from "@/types";
import Card from "@/components/ui/Card";
import { EmptyState, LoadingState } from "@/components/ui/States";
import { isoToJalaliDisplay } from "@/lib/jalali";

const STATUS_LABEL_FA: Record<Trip["status"], string> = {
  collecting_info: "در حال تکمیل اطلاعات",
  ready_for_generation: "آماده تولید برنامه",
  generating: "در حال تولید برنامه",
  planned: "برنامه‌ریزی‌شده",
  archived: "بایگانی‌شده",
};

const STATUS_BADGE_CLASS: Record<Trip["status"], string> = {
  collecting_info: "bg-surface-container-high text-on-surface-variant",
  ready_for_generation: "bg-tertiary-container/50 text-on-tertiary-container",
  generating: "bg-primary-fixed text-on-primary-fixed-variant",
  planned: "bg-secondary-container/60 text-on-secondary-container",
  archived: "bg-surface-container text-on-surface-variant",
};

export default function TripsPage() {
  const [trips, setTrips] = useState<Trip[] | null>(null);

  useEffect(() => {
    apiFetch<Trip[]>("/api/trips/")
      .then(setTrips)
      .catch(() => setTrips([]));
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-margin py-space-xl">
      <div className="mb-space-lg flex items-center justify-between">
        <div className="flex items-center gap-space-xs">
          <span className="material-symbols-outlined text-[24px] text-primary">luggage</span>
          <h1 className="font-headline font-headline-lg-mobile text-headline-lg-mobile font-bold text-on-surface">
            سفرهای من
          </h1>
        </div>
        <Link
          href="/"
          className="flex items-center gap-1 font-label-lg text-label-lg font-semibold text-primary hover:underline"
        >
          <span className="material-symbols-outlined text-[18px]">add_circle</span>
          سفر جدید
        </Link>
      </div>

      {trips === null && <LoadingState />}
      {trips && trips.length === 0 && (
        <EmptyState title="هنوز سفری نساخته‌اید" description="از صفحه اصلی یک سفر جدید شروع کنید." />
      )}
      <div className="flex flex-col gap-space-sm">
        {trips?.map((trip) => (
          <Link key={trip.id} href={`/trips/${trip.id}`}>
            <Card className="transition-colors hover:border-primary-container">
              <div className="flex items-center justify-between gap-space-sm">
                <div className="min-w-0">
                  <p className="truncate font-title-md text-title-md font-medium text-on-surface">
                    {trip.title || `${trip.origin} به ${trip.destination}`}
                  </p>
                  <p className="truncate font-body-sm text-body-sm text-on-surface-variant">
                    {trip.origin} به {trip.destination}
                    {trip.start_date && ` · ${isoToJalaliDisplay(trip.start_date)}`}
                  </p>
                </div>
                <span
                  className={`shrink-0 rounded-full px-space-sm py-1 font-label-sm text-label-sm ${STATUS_BADGE_CLASS[trip.status]}`}
                >
                  {STATUS_LABEL_FA[trip.status]}
                </span>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
