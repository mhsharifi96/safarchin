import DateObject from "react-date-object";
import persian from "react-date-object/calendars/persian";
import persian_fa from "react-date-object/locales/persian_fa";
import gregorian from "react-date-object/calendars/gregorian";
import gregorian_en from "react-date-object/locales/gregorian_en";

import { toPersianDigits } from "./persian";

/** Backend stores/accepts Gregorian ISO dates (YYYY-MM-DD); the UI always
 * displays/collects Jalali. These helpers are the only place that convert
 * between the two so the boundary stays obvious. */

export function isoToJalaliDisplay(iso: string | null | undefined): string {
  if (!iso) return "نامشخص";
  const date = new DateObject({ date: iso, calendar: gregorian, locale: gregorian_en }).convert(
    persian,
    persian_fa
  );
  return toPersianDigits(date.format("YYYY/MM/DD"));
}

export function jalaliDateObjectToIso(dateObject: DateObject | null): string | null {
  if (!dateObject) return null;
  const gregorianDate = dateObject.convert(gregorian, gregorian_en);
  return gregorianDate.format("YYYY-MM-DD");
}

export function isoToDateObject(iso: string | null | undefined): DateObject | null {
  if (!iso) return null;
  return new DateObject({ date: iso, calendar: gregorian, locale: gregorian_en }).convert(persian, persian_fa);
}

export { persian, persian_fa };
