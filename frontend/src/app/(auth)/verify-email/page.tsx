"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

import { apiFetch, ApiError } from "@/lib/api";
import Card from "@/components/ui/Card";
import { LoadingState } from "@/components/ui/States";

function VerifyEmailContent() {
  const params = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  const pending = params.get("pending");

  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const isVerifying = Boolean(uid && token) && status === "idle";

  useEffect(() => {
    if (!uid || !token) return;
    apiFetch<{ detail: string }>("/api/auth/verify-email/", { method: "POST", body: { uid, token } })
      .then((res) => {
        setStatus("success");
        setMessage(res.detail);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err instanceof ApiError ? err.message : "خطای غیرمنتظره‌ای رخ داد.");
      });
  }, [uid, token]);

  if (pending && !uid) {
    return (
      <Card variant="prominent" className="flex flex-col">
        <div className="mb-space-xs flex items-center gap-space-xs">
          <span className="material-symbols-outlined text-[24px] text-primary">mark_email_unread</span>
          <h1 className="font-headline font-headline-lg-mobile text-headline-lg-mobile font-bold tracking-tight text-on-surface">
            ایمیل خود را بررسی کنید
          </h1>
        </div>
        <p className="font-body-md text-body-md text-on-surface-variant">
          یک لینک تایید به ایمیل شما ارسال شد. برای فعال‌سازی کامل حساب، روی آن کلیک کنید.
          (در محیط توسعه، ایمیل به‌جای ارسال واقعی در لاگ سرور بک‌اند چاپ می‌شود.)
        </p>
      </Card>
    );
  }

  if (!uid || !token) {
    return (
      <Card variant="prominent">
        <p className="font-body-md text-body-md text-on-surface-variant">لینک تایید نامعتبر است.</p>
      </Card>
    );
  }

  return (
    <Card variant="prominent" className="flex flex-col">
      <div className="mb-space-md flex items-center gap-space-xs">
        <span className="material-symbols-outlined text-[24px] text-primary">verified</span>
        <h1 className="font-headline font-headline-lg-mobile text-headline-lg-mobile font-bold tracking-tight text-on-surface">
          تایید ایمیل
        </h1>
      </div>
      {isVerifying && <LoadingState label="در حال تایید ایمیل..." />}
      {status === "success" && (
        <p className="font-body-md text-body-md font-medium text-secondary">{message}</p>
      )}
      {status === "error" && (
        <p className="font-body-md text-body-md font-medium text-error">{message}</p>
      )}
      <p className="mt-space-md font-body-sm text-body-sm text-on-surface-variant">
        <Link href="/login" className="font-medium text-primary hover:underline">
          بازگشت به ورود
        </Link>
      </p>
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="mx-auto max-w-md px-margin py-space-xl">
      <Suspense fallback={<LoadingState />}>
        <VerifyEmailContent />
      </Suspense>
    </div>
  );
}
