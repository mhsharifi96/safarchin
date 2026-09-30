"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { apiFetch, ApiError } from "@/lib/api";
import type { ConversationMessage, Trip } from "@/types";
import { ErrorState } from "@/components/ui/States";

export default function ChatPanel({
  tripId,
  onTripUpdate,
}: {
  tripId: string;
  onTripUpdate: (trip: Trip) => void;
}) {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiFetch<ConversationMessage[]>(`/api/trips/${tripId}/messages/`).then(setMessages);
  }, [tripId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const content = input.trim();
    if (!content) return;
    setInput("");
    setError("");
    setMessages((prev) => [
      ...prev,
      { id: Date.now(), role: "user", content, created_at: new Date().toISOString() },
    ]);
    setSending(true);
    try {
      const res = await apiFetch<{ reply: string; trip: Trip }>(`/api/trips/${tripId}/messages/`, {
        method: "POST",
        body: { content },
      });
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: "assistant", content: res.reply, created_at: new Date().toISOString() },
      ]);
      onTripUpdate(res.trip);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "پیام ارسال نشد.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex h-full flex-col bg-surface-container-lowest">
      <div className="flex items-center gap-space-xs border-b border-surface-container-high px-space-md py-space-sm">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
          <span className="material-symbols-outlined text-[18px]">smart_toy</span>
        </div>
        <span className="font-title-md text-title-md font-semibold text-on-surface">دستیار سفرچین</span>
      </div>

      <div className="flex-1 space-y-space-sm overflow-y-auto p-space-md">
        {messages.length === 0 && (
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            بگویید چه سفری در ذهن دارید تا سفرچین سوالات لازم را از شما بپرسد.
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={
                m.role === "user"
                  ? "max-w-[80%] rounded-DEFAULT rounded-br-xs bg-primary-container px-space-md py-space-sm font-body-md text-body-md text-on-primary"
                  : "max-w-[80%] rounded-DEFAULT rounded-bl-xs bg-surface-container-low px-space-md py-space-sm font-body-md text-body-md text-on-surface"
              }
            >
              {m.content}
            </div>
          </div>
        ))}
        {sending && (
          <p className="font-label-sm text-label-sm text-on-surface-variant">سفرچین در حال نوشتن پاسخ است...</p>
        )}
        <div ref={bottomRef} />
      </div>
      {error && (
        <div className="px-space-md pb-space-sm">
          <ErrorState message={error} />
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex gap-space-xs border-t border-surface-container-high p-space-sm">
        <input
          className="h-11 flex-1 rounded-full bg-surface-container-low px-space-md font-body-md text-body-md text-on-surface outline-none placeholder:text-outline focus:bg-surface-container"
          placeholder="پیام خود را بنویسید..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          type="submit"
          disabled={!input.trim() || sending}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary-container text-on-primary transition-all active:translate-y-px disabled:cursor-not-allowed disabled:opacity-60"
        >
          <span className="material-symbols-outlined text-[20px]">send</span>
        </button>
      </form>
    </div>
  );
}
