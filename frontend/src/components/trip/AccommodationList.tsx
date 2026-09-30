"use client";

import { useState } from "react";

import { apiFetch } from "@/lib/api";
import type { Accommodation } from "@/types";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import { formatToman } from "@/lib/persian";

export default function AccommodationList({
  tripId,
  accommodations,
  onSelected,
}: {
  tripId: string;
  accommodations: Accommodation[];
  onSelected: () => void;
}) {
  const [selectingId, setSelectingId] = useState<number | null>(null);

  async function handleSelect(id: number) {
    setSelectingId(id);
    try {
      await apiFetch(`/api/trips/${tripId}/accommodations/${id}/select/`, { method: "POST" });
      onSelected();
    } finally {
      setSelectingId(null);
    }
  }

  if (accommodations.length === 0) {
    return <p className="font-body-sm text-body-sm text-on-surface-variant">پیشنهاد اقامتی هنوز موجود نیست.</p>;
  }

  return (
    <div className="grid gap-space-sm sm:grid-cols-2">
      {accommodations.map((acc) => (
        <Card
          key={acc.id}
          variant="prominent"
          className={acc.is_selected ? "ring-2 ring-primary-container" : undefined}
        >
          <div className="mb-space-xs flex items-start gap-space-xs">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tertiary-container/40 text-tertiary">
              <span className="material-symbols-outlined text-[18px]">hotel</span>
            </div>
            <div className="min-w-0">
              <p className="truncate font-title-md text-title-md font-medium text-on-surface">{acc.name}</p>
              {acc.room_type && (
                <p className="font-body-sm text-body-sm text-on-surface-variant">{acc.room_type}</p>
              )}
            </div>
          </div>
          {acc.place?.address && (
            <p className="font-body-sm text-body-sm text-on-surface-variant">{acc.place.address}</p>
          )}
          <p className="mt-space-xs font-title-md text-title-md font-semibold text-primary">
            {formatToman(acc.nightly_price)} / شب
          </p>
          <div className="mt-space-sm">
            {acc.is_selected ? (
              <span className="flex items-center gap-1 font-label-md text-label-md font-medium text-secondary">
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                انتخاب شده
              </span>
            ) : (
              <Button
                variant="secondary"
                loading={selectingId === acc.id}
                onClick={() => handleSelect(acc.id)}
                className="h-10 px-space-md"
              >
                انتخاب این اقامتگاه
              </Button>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}
