import type { Itinerary } from "@/types";
import Card from "@/components/ui/Card";
import { toPersianDigits } from "@/lib/persian";
import { isoToJalaliDisplay } from "@/lib/jalali";

const CATEGORY_LABEL_FA: Record<string, string> = {
  sight: "بازدید",
  food: "غذا",
  transport: "جابجایی",
  rest: "استراحت",
  accommodation: "اقامت",
  other: "سایر",
};

const CATEGORY_ICON: Record<string, string> = {
  sight: "photo_camera",
  food: "restaurant",
  transport: "directions_car",
  rest: "self_improvement",
  accommodation: "hotel",
  other: "place",
};

function formatTime(time: string | null): string {
  if (!time) return "";
  return toPersianDigits(time.slice(0, 5));
}

export default function ItineraryView({
  itinerary,
  selectedDayId,
  onSelectDay,
}: {
  itinerary: Itinerary;
  /** The day whose route is currently drawn on the map, if any. */
  selectedDayId?: number | null;
  onSelectDay?: (dayId: number | null) => void;
}) {
  return (
    <div className="flex flex-col gap-space-lg">
      {itinerary.summary && (
        <p className="whitespace-pre-line font-body-sm text-body-sm text-on-surface-variant">{itinerary.summary}</p>
      )}
      {itinerary.days.map((day) => {
        const isSelected = selectedDayId === day.id;
        return (
        <Card key={day.id} variant="prominent" className={isSelected ? "ring-2 ring-primary-container" : undefined}>
          <div className="mb-space-md flex items-center justify-between gap-space-sm">
            <h3 className="flex items-center gap-space-xs font-headline-sm text-headline-sm font-semibold text-on-surface">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-container font-label-sm text-label-sm font-bold text-on-primary">
                {toPersianDigits(day.day_index)}
              </span>
              <span>
                روز {toPersianDigits(day.day_index)}
                {day.date && ` · ${isoToJalaliDisplay(day.date)}`}
                {day.city && ` · ${day.city}`}
              </span>
            </h3>
            {onSelectDay && (
              <button
                type="button"
                onClick={() => onSelectDay(isSelected ? null : day.id)}
                className={
                  isSelected
                    ? "flex shrink-0 items-center gap-1 rounded-full bg-primary-container px-space-sm py-1 font-label-sm text-label-sm font-semibold text-on-primary"
                    : "flex shrink-0 items-center gap-1 rounded-full bg-surface-container-low px-space-sm py-1 font-label-sm text-label-sm font-semibold text-on-surface-variant hover:bg-secondary-fixed/30"
                }
              >
                <span className="material-symbols-outlined text-[14px]">route</span>
                {isSelected ? "پنهان کردن مسیر" : "نمایش مسیر روی نقشه"}
              </button>
            )}
          </div>
          <ol className="flex flex-col gap-space-md">
            {day.items.map((item) => (
              <li key={item.id} className="flex gap-space-sm border-r-2 border-primary-fixed pr-space-sm">
                <div className="w-16 shrink-0 font-label-sm text-label-sm text-on-surface-variant">
                  {formatTime(item.start_time)}
                  {item.end_time && ` - ${formatTime(item.end_time)}`}
                </div>
                <div className="flex-1">
                  <p className="flex items-center gap-1 font-title-md text-title-md font-medium text-on-surface">
                    <span className="material-symbols-outlined text-[16px] text-secondary">
                      {CATEGORY_ICON[item.category] ?? "place"}
                    </span>
                    {item.title}
                    <span className="font-label-sm text-label-sm font-normal text-on-surface-variant">
                      ({CATEGORY_LABEL_FA[item.category]})
                    </span>
                  </p>
                  {item.description && (
                    <p className="font-body-sm text-body-sm text-on-surface-variant">{item.description}</p>
                  )}
                  {item.place?.address && (
                    <p className="font-body-sm text-body-sm text-on-surface-variant">{item.place.address}</p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </Card>
        );
      })}
    </div>
  );
}
