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

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [formError, setFormError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setFormError("");
    setErrors({});
    try {
      await register(email, password, fullName);
      router.push("/verify-email?pending=1");
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.errors) setErrors(err.errors as Record<string, string[]>);
        else setFormError(err.message);
      } else {
        setFormError("خطای غیرمنتظره‌ای رخ داد.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-margin py-space-xl">
      <Card variant="prominent" className="flex flex-col">
        <div className="mb-space-lg flex flex-col">
          <div className="mb-space-xs flex items-center gap-space-xs">
            <span className="material-symbols-outlined text-[24px] text-primary">person_add</span>
            <h1 className="font-headline font-headline-lg-mobile text-headline-lg-mobile font-bold tracking-tight text-on-surface">
              ساخت حساب کاربری
            </h1>
          </div>
          <p className="font-body-md text-body-md text-on-surface-variant">
            چند قدم تا شروع اولین سفرت با سفرچین.
          </p>
        </div>

        {formError && (
          <div className="mb-space-md">
            <ErrorState message={formError} />
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-space-md">
          <Input
            label="نام و نام خانوادگی"
            icon="badge"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          <Input
            label="ایمیل"
            type="email"
            icon="mail"
            ltr
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={errors.email?.[0]}
          />
          <Input
            label="رمز عبور"
            type="password"
            icon="lock"
            hint="حداقل ۸ نویسه"
            ltr
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password?.[0]}
          />
          <Button type="submit" loading={loading} className="mt-space-sm w-full">
            ثبت‌نام
            <span className="material-symbols-outlined text-[20px]">arrow_back</span>
          </Button>
        </form>

        <div className="mt-space-md flex items-center justify-center gap-space-xs rounded-full bg-surface-container-lowest px-space-lg py-space-md text-center shadow-sm">
          <span className="font-body-md text-body-md text-on-surface-variant">حساب دارید؟</span>
          <Link href="/login" className="font-title-md text-title-md font-bold text-primary hover:underline">
            وارد شوید
          </Link>
        </div>
      </Card>
    </div>
  );
}
