const PERSIAN_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

/** Converts any ASCII digits found in a string/number to Persian digits for display. */
export function toPersianDigits(value: string | number): string {
  return String(value).replace(/[0-9]/g, (digit) => PERSIAN_DIGITS[Number(digit)]);
}

export function formatPersianNumber(value: number): string {
  return toPersianDigits(new Intl.NumberFormat("en-US").format(value));
}

/** Formats an amount of Tomans with Persian digits and a "تومان" suffix. */
export function formatToman(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return "نامشخص";
  return `${formatPersianNumber(amount)} تومان`;
}
