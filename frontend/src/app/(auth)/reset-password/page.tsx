"use client";

import { FormEvent, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";

import { apiFetch, ApiError } from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Card from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/States";

function ResetPasswordForm() {
  const params = useSearchParams();
  const router = useRouter();
  const uid = params.get("uid") || "";
  const token = params.get("token") || "";

  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await apiFetch("/api/auth/reset-password/", {
        method: "POST",
        body: { uid, token, new_password: newPassword },
      });
      setDone(true);
      setTimeout(() => router.push("/login"), 2000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطای غیرمنتظره‌ای رخ داد.");
    } finally {
      setLoading(false);
    }
  }

  if (!uid || !token) {
    return (
      <Card variant="prominent">
        <ErrorState message="لینک بازیابی نامعتبر است." />
      </Card>
    );
  }

  return (
    <Card variant="prominent" className="flex flex-col">
      <div className="mb-space-lg flex flex-col">
        <div className="mb-space-xs flex items-center gap-space-xs">
          <span className="material-symbols-outlined text-[24px] text-primary">lock_reset</span>
          <h1 className="font-headline font-headline-lg-mobile text-headline-lg-mobile font-bold tracking-tight text-on-surface">
            تنظیم رمز عبور جدید
          </h1>
        </div>
      </div>

      {done ? (
        <div className="flex items-center gap-space-xs rounded-DEFAULT bg-secondary-container/40 px-space-md py-space-sm font-body-sm text-body-sm font-medium text-on-secondary-container">
          <span className="material-symbols-outlined text-[20px] text-secondary">check_circle</span>
          <span>رمز عبور شما تغییر کرد. در حال انتقال به صفحه ورود...</span>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-space-md">
          {error && <ErrorState message={error} />}
          <Input
            label="رمز عبور جدید"
            type="password"
            icon="lock"
            ltr
            required
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <Button type="submit" loading={loading} className="w-full">
            تغییر رمز عبور
          </Button>
        </form>
      )}
      <p className="mt-space-md text-center font-body-sm text-body-sm text-on-surface-variant">
        <Link href="/login" className="font-medium text-primary hover:underline">
          بازگشت به ورود
        </Link>
      </p>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="mx-auto max-w-md px-margin py-space-xl">
      <Suspense fallback={null}>
        <ResetPasswordForm />
      </Suspense>
    </div>
  );
}
