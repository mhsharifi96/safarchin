"use client";

import { useState } from "react";
import DatePicker from "react-multi-date-picker";

import { apiFetch } from "@/lib/api";
import type { Trip } from "@/types";
import Input from "@/components/ui/Input";
import { persian, persian_fa, isoToDateObject, jalaliDateObjectToIso } from "@/lib/jalali";

const PACE_OPTIONS = [
  { value: "relaxed", label: "آرام" },
  { value: "balanced", label: "متعادل" },
  { value: "intense", label: "فشرده" },
];
const INTERCITY_OPTIONS = [
  { value: "flight", label: "هواپیما" },
  { value: "train", label: "قطار" },
  { value: "bus", label: "اتوبوس" },
  { value: "personal_car", label: "خودروی شخصی" },
  { value: "unknown", label: "نامشخص" },
];
const LOCAL_OPTIONS = [
  { value: "public_transit", label: "حمل‌ونقل عمومی" },
  { value: "taxi", label: "تاکسی/اسنپ" },
  { value: "rental_car", label: "اجاره خودرو" },
  { value: "walking", label: "پیاده" },
  { value: "mixed", label: "ترکیبی" },
  { value: "unknown", label: "نامشخص" },
];
const BUDGET_SCOPE_OPTIONS = [
  { value: "per_person", label: "هرنفر" },
  { value: "group", label: "کل گروه" },
];

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-space-xs">
      <label className="font-label-lg text-label-lg font-semibold text-on-surface">{label}</label>
      <select
        className="h-12 rounded-full bg-surface-container-low px-space-md font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

const DATE_INPUT_CLASS =
  "w-full h-12 rounded-full bg-surface-container-low px-4 text-sm text-on-surface outline-none focus:bg-surface-container";

export default function PreferencesSummary({
  trip,
  onChange,
}: {
  trip: Trip;
  onChange: (trip: Trip) => void;
}) {
  const [saving, setSaving] = useState(false);
  const prefs = trip.preferences;

  async function patchTrip(body: Partial<Trip>) {
    setSaving(true);
    try {
      const updated = await apiFetch<Trip>(`/api/trips/${trip.id}/`, { method: "PATCH", body });
      onChange({ ...trip, ...updated });
    } finally {
      setSaving(false);
    }
  }

  async function patchPrefs(body: Partial<Trip["preferences"]>) {
    setSaving(true);
    try {
      const updated = await apiFetch<Trip["preferences"]>(`/api/trips/${trip.id}/preferences/`, {
        method: "PATCH",
        body,
      });
      onChange({ ...trip, preferences: updated });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-space-md">
      <div className="grid grid-cols-2 gap-space-sm">
        <Input
          key={`origin-${trip.origin}`}
          label="مبدا"
          icon="trip_origin"
          defaultValue={trip.origin}
          onBlur={(e) => patchTrip({ origin: e.target.value })}
        />
        <Input
          key={`destination-${trip.destination}`}
          label="مقصد"
          icon="flag"
          defaultValue={trip.destination}
          onBlur={(e) => patchTrip({ destination: e.target.value })}
        />
      </div>

      <div className="grid grid-cols-2 gap-space-sm">
        <div className="flex flex-col gap-space-xs">
          <label className="font-label-lg text-label-lg font-semibold text-on-surface">تاریخ شروع (شمسی)</label>
          <DatePicker
            calendar={persian}
            locale={persian_fa}
            value={isoToDateObject(trip.start_date)}
            onChange={(date) => {
              void patchTrip({ start_date: jalaliDateObjectToIso(date as never) });
            }}
            inputClass={DATE_INPUT_CLASS}
          />
        </div>
        <div className="flex flex-col gap-space-xs">
          <label className="font-label-lg text-label-lg font-semibold text-on-surface">تاریخ پایان (شمسی)</label>
          <DatePicker
            calendar={persian}
            locale={persian_fa}
            value={isoToDateObject(trip.end_date)}
            onChange={(date) => {
              void patchTrip({ end_date: jalaliDateObjectToIso(date as never) });
            }}
            inputClass={DATE_INPUT_CLASS}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-space-sm">
        <Input
          key={`adults-${prefs.adults_count}`}
          label="تعداد بزرگسال"
          icon="group"
          type="number"
          min={0}
          defaultValue={prefs.adults_count ?? ""}
          onBlur={(e) => patchPrefs({ adults_count: e.target.value ? Number(e.target.value) : null })}
        />
        <Input
          key={`children-${prefs.children_count}`}
          label="تعداد کودک"
          icon="child_care"
          type="number"
          min={0}
          defaultValue={prefs.children_count ?? ""}
          onBlur={(e) => patchPrefs({ children_count: e.target.value ? Number(e.target.value) : null })}
        />
      </div>

      <div className="grid grid-cols-2 gap-space-sm">
        <Select
          label="حمل‌ونقل بین‌شهری"
          value={prefs.intercity_transport}
          options={INTERCITY_OPTIONS}
          onChange={(v) => patchPrefs({ intercity_transport: v as Trip["preferences"]["intercity_transport"] })}
        />
        <Select
          label="حمل‌ونقل درون‌شهری"
          value={prefs.local_transport}
          options={LOCAL_OPTIONS}
          onChange={(v) => patchPrefs({ local_transport: v as Trip["preferences"]["local_transport"] })}
        />
      </div>

      <Select
        label="ریتم سفر"
        value={prefs.pace || ""}
        options={[{ value: "", label: "نامشخص" }, ...PACE_OPTIONS]}
        onChange={(v) => patchPrefs({ pace: (v || null) as Trip["preferences"]["pace"] })}
      />

      <div className="grid grid-cols-2 gap-space-sm">
        <Input
          key={`budget-${prefs.budget_amount}`}
          label="بودجه (تومان)"
          icon="payments"
          type="number"
          defaultValue={prefs.budget_amount ?? ""}
          onBlur={(e) => patchPrefs({ budget_amount: e.target.value ? Number(e.target.value) : null })}
        />
        <Select
          label="نوع بودجه"
          value={prefs.budget_scope || ""}
          options={[{ value: "", label: "نامشخص" }, ...BUDGET_SCOPE_OPTIONS]}
          onChange={(v) => patchPrefs({ budget_scope: (v || null) as Trip["preferences"]["budget_scope"] })}
        />
      </div>

      <Input
        key={`interests-${prefs.interests.join("، ")}`}
        label="علایق (با ویرگول جدا کنید)"
        icon="interests"
        defaultValue={prefs.interests.join("، ")}
        onBlur={(e) =>
          patchPrefs({
            interests: e.target.value
              .split(/[،,]/)
              .map((s) => s.trim())
              .filter(Boolean),
          })
        }
      />

      <Input
        key={`accessibility-${prefs.accessibility_notes}`}
        label="محدودیت پیاده‌روی یا دسترسی"
        icon="accessible"
        defaultValue={prefs.accessibility_notes}
        onBlur={(e) => patchPrefs({ accessibility_notes: e.target.value })}
      />

      {prefs.assumptions.length > 0 && (
        <div className="rounded-DEFAULT bg-tertiary-container/25 p-space-md font-body-sm text-body-sm text-on-tertiary-container">
          <p className="mb-space-xs flex items-center gap-1 font-label-lg text-label-lg font-semibold">
            <span className="material-symbols-outlined text-[16px]">lightbulb</span>
            فرض‌های سفرچین:
          </p>
          <ul className="list-inside list-disc space-y-1">
            {prefs.assumptions.map((a, i) => (
              <li key={i}>{a.assumption}</li>
            ))}
          </ul>
        </div>
      )}

      {saving && <p className="font-label-sm text-label-sm text-on-surface-variant">در حال ذخیره...</p>}
    </div>
  );
}
