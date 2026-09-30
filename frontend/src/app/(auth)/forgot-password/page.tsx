"use client";

import { FormEvent, useState } from "react";

import { apiFetch, ApiError } from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Card from "@/components/ui/Card";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await apiFetch<{ detail: string }>("/api/auth/forgot-password/", {
        method: "POST",
        body: { email },
      });
      setMessage(res.detail);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "خطای غیرمنتظره‌ای رخ داد.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-margin py-space-xl">
      <Card variant="prominent" className="flex flex-col">
        <div className="mb-space-lg flex flex-col">
          <div className="mb-space-xs flex items-center gap-space-xs">
            <span className="material-symbols-outlined text-[24px] text-primary">key</span>
            <h1 className="font-headline font-headline-lg-mobile text-headline-lg-mobile font-bold tracking-tight text-on-surface">
              بازیابی رمز عبور
            </h1>
          </div>
          <p className="font-body-md text-body-md text-on-surface-variant">
            ایمیل خود را وارد کنید تا لینک بازیابی رمز عبور برایتان ارسال شود.
          </p>
        </div>

        {message ? (
          <div className="flex items-center gap-space-xs rounded-DEFAULT bg-secondary-container/40 px-space-md py-space-sm font-body-sm text-body-sm font-medium text-on-secondary-container">
            <span className="material-symbols-outlined text-[20px] text-secondary">mark_email_read</span>
            <span>{message}</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-space-md">
            <Input
              label="ایمیل"
              type="email"
              icon="mail"
              ltr
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button type="submit" loading={loading} className="w-full">
              ارسال لینک بازیابی
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
}
