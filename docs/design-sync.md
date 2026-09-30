# Design sync: Stitch ↔ implementation

## Status: synced from the real Stitch project

Connected to the `stitch` MCP server and pulled the actual project: **SafarChin Travel Planner**
(`projects/13952509925073167296`, 22 screens, design system "SafarChin Persian Travel" — Neo-Terracotta &
Biophilic Mint). One full screen export (`ورود به سفرچین` / login) was downloaded and inspected to confirm the
exact conventions (Tailwind arbitrary config, Material Symbols Outlined icons, pill geometry, RTL layout), then
the whole frontend was reskinned to match.

## Design tokens (implemented in [`frontend/src/app/globals.css`](../frontend/src/app/globals.css))

All values are the Stitch project's own generated Tailwind theme (`namedColors` / `designTheme` from the
Stitch API), not approximations:

| Token group | Source |
|---|---|
| Colors | Material-3-style role tokens: `primary`/`on-primary`/`primary-container`, `secondary*`, `tertiary*`, `surface`/`surface-container-*` (5 tiers), `outline`/`outline-variant`, `error*`. Primary = terracotta `#a33d23`/`#e76f51`, secondary = teal `#006a60`, tertiary = deep teal `#216964`, base surface = warm ivory `#fbf9f5`. |
| Radius | `DEFAULT` 1rem, `lg` 2rem, `xl` 3rem, `full` 9999px (pill), plus `xs`/`sm` for small chip/tail corners. |
| Spacing | `space-xs/sm/md/lg/xl`, `gutter`, `margin`, `margin-tablet`, `margin-desktop` — exact values from the Stitch spacing scale. |
| Typography | Full type scale (`display-lg`, `headline-lg`, `headline-lg-mobile`, `headline-md`, `headline-sm`, `title-md`, `body-lg/md/sm`, `label-lg/md/sm`) as paired `--text-*`/`--text-*--line-height`/`--text-*--font-weight` Tailwind v4 tokens, matching Stitch's `fontSize` config exactly. |
| Fonts | Headlines: `Bricolage Grotesque` → falls back per-glyph to `Vazirmatn` (no Latin-only font has Persian glyphs, so the stack is `'Bricolage Grotesque', Vazirmatn, sans-serif`, same as Stitch's own screens). Body/labels: `Work Sans` → `Vazirmatn` fallback. Loaded via `next/font/google` (Vazirmatn, Bricolage Grotesque) plus a `<link>` for the `Material Symbols Outlined` icon font (used via `<span className="material-symbols-outlined">`), exactly as Stitch's screens do. |

## Screen → route/component mapping

| Stitch screen | Route / component |
|---|---|
| ورود به سفرچین (Login) | [`app/(auth)/login/page.tsx`](../frontend/src/app/(auth)/login/page.tsx) — restyled 1:1 from the downloaded HTML export: icon+headline card, pill inputs with leading icons, primary pill CTA, footer signup pill. |
| ساخت حساب کاربری (Register) | [`app/(auth)/register/page.tsx`](../frontend/src/app/(auth)/register/page.tsx) |
| بازیابی رمز عبور / تنظیم رمز جدید | [`forgot-password`](../frontend/src/app/(auth)/forgot-password/page.tsx), [`reset-password`](../frontend/src/app/(auth)/reset-password/page.tsx) |
| تأیید ایمیل | [`verify-email`](../frontend/src/app/(auth)/verify-email/page.tsx) |
| حساب کاربری + سفرهای ذخیره‌شده | [`app/account/page.tsx`](../frontend/src/app/account/page.tsx) |
| سفرهای من (list) | [`app/trips/page.tsx`](../frontend/src/app/trips/page.tsx) — status pill badges per trip. |
| دستیار سفرچین (assistant chat) | [`ChatPanel`](../frontend/src/components/trip/ChatPanel.tsx) — rounded chat bubbles, pill composer with round send FAB. |
| برنامه سفر / روز‌ها (itinerary) | [`ItineraryView`](../frontend/src/components/trip/ItineraryView.tsx) — numbered day badge, category icons, terracotta timeline rail. |
| اقامت مناسب سفر (accommodation) | [`AccommodationList`](../frontend/src/components/trip/AccommodationList.tsx) |
| جزئیات و سلیقه سفر (preferences) | [`PreferencesSummary`](../frontend/src/components/trip/PreferencesSummary.tsx) — pill inputs/selects, "فرض‌های سفرچین" assumptions banner in tertiary tint. |
| نقشه تعاملی سفر | [`TripMap`](../frontend/src/components/trip/TripMap.tsx) (unchanged Neshan integration, restyled container radius). |
| میز کار برنامه و نقشه سفر (desktop workspace) | [`app/trips/[id]/page.tsx`](../frontend/src/app/trips/[id]/page.tsx) — two-column grid combining the above. |

Shared primitives, all rebuilt to the Stitch component spec: [`Button`](../frontend/src/components/ui/Button.tsx)
(pill, terracotta primary / sage-tint secondary / outline ghost), [`Input`](../frontend/src/components/ui/Input.tsx)
(pill, `surface-container-low` fill, optional leading Material icon), [`Card`](../frontend/src/components/ui/Card.tsx)
(`default` = 16px hairline-bordered tile, `prominent` = 32px elevated container), [`States`](../frontend/src/components/ui/States.tsx),
[`Header`](../frontend/src/components/layout/Header.tsx) (fixed, blurred, logo lockup + pill actions).

## Known deviations / not carried over

- Stitch's screens include a bottom-of-screen "guest login" affordance and a floating pill bottom-navigation
  bar (دستیار / سفر من / نقشه). Neither maps to existing backend functionality or app routing structure, so
  they were **not** added — only the visual language (colors, shapes, spacing, icons, type) was ported onto the
  app's real, existing pages and flows. Revisit if guest mode or a tab-based navigation shell is scoped later.
- No dark mode (Stitch project is light-mode only; `colorMode: LIGHT`).
- RTL, Persian-digit formatting (`lib/persian.ts`) and Jalali calendar (`lib/jalali.ts`) were already correct
  and unchanged.
