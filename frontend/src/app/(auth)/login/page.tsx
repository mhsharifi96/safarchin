"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/api";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Card from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/States";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      router.push("/trips");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "خطای غیرمنتظره‌ای رخ داد.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-margin py-space-xl">
      <Card variant="prominent" className="flex flex-col">
        <div className="mb-space-lg flex flex-col">
          <div className="mb-space-xs flex items-center gap-space-xs">
            <span className="material-symbols-outlined text-[24px] text-primary">explore</span>
            <h1 className="font-headline font-headline-lg-mobile text-headline-lg-mobile font-bold tracking-tight text-on-surface">
              ورود به سفرچین
            </h1>
          </div>
          <p className="font-body-md text-body-md text-on-surface-variant">
            وارد شو و برنامه سفرت رو ادامه بده.
          </p>
        </div>

        {error && (
          <div className="mb-space-md">
            <ErrorState message={error} />
          </div>
        )}

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
          <Input
            label="رمز عبور"
            type="password"
            icon="lock"
            ltr
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <div className="flex justify-end pt-space-xs">
            <Link href="/forgot-password" className="font-label-md text-label-md font-medium text-primary hover:underline">
              رمز عبور را فراموش کرده‌اید؟
            </Link>
          </div>
          <Button type="submit" loading={loading} className="mt-space-sm w-full">
            ورود
            <span className="material-symbols-outlined text-[20px]">arrow_back</span>
          </Button>
        </form>

        <div className="mt-space-md flex items-center justify-center gap-space-xs rounded-full bg-surface-container-lowest px-space-lg py-space-md text-center shadow-sm">
          <span className="font-body-md text-body-md text-on-surface-variant">حساب کاربری ندارید؟</span>
          <Link href="/register" className="font-title-md text-title-md font-bold text-primary hover:underline">
            ثبت‌نام
          </Link>
        </div>
      </Card>
    </div>
  );
}
