"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api";
import type { Trip } from "@/types";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/States";

const EXAMPLE_PROMPT = "برای دو روز تبریز یه برنامه کامل بچین";

export default function HomePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) return;
    setLoading(true);
    setError("");
    try {
      const trip = await apiFetch<Trip>("/api/trips/", { method: "POST", body: { title: prompt.slice(0, 80) } });
      await apiFetch(`/api/trips/${trip.id}/messages/`, { method: "POST", body: { content: prompt } });
      router.push(`/trips/${trip.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطای غیرمنتظره‌ای رخ داد.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-margin py-space-xl text-center">
      <div className="mb-space-xs flex items-center justify-center gap-space-xs">
        <span className="material-symbols-outlined text-[28px] text-primary">explore</span>
        <span className="font-headline font-headline-sm text-headline-sm font-bold text-primary">سفرچین</span>
      </div>
      <h1 className="mb-space-sm font-headline font-headline-lg text-headline-lg font-bold text-on-surface">
        سفر بعدی‌تان را با سفرچین بچینید
      </h1>
      <p className="mb-space-xl font-body-lg text-body-lg text-on-surface-variant">
        فقط بگویید کجا می‌خواهید بروید، سفرچین بقیه‌اش را با شما پیش می‌برد: برنامه روزانه، مکان‌ها روی نقشه و
        پیشنهاد اقامت.
      </p>

      <Card variant="prominent" className="text-right">
        <form onSubmit={handleSubmit} className="flex flex-col gap-space-md">
          {error && <ErrorState message={error} />}
          <textarea
            className="min-h-28 rounded-DEFAULT bg-surface-container-low p-space-md font-body-md text-body-md text-on-surface outline-none placeholder:text-outline focus:bg-surface-container"
            placeholder={EXAMPLE_PROMPT}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <div className="flex justify-end">
            <Button type="submit" variant="primary" loading={loading} disabled={!prompt.trim()}>
              شروع برنامه‌ریزی
              <span className="material-symbols-outlined text-[20px]">arrow_back</span>
            </Button>
          </div>
        </form>

        <button
          type="button"
          className="mt-space-md font-label-md text-label-md text-primary hover:underline"
          onClick={() => setPrompt(EXAMPLE_PROMPT)}
        >
          نمونه: «{EXAMPLE_PROMPT}»
        </button>
      </Card>
    </div>
  );
}
