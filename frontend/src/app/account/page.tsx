"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";
import type { Trip, User } from "@/types";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/States";
import { toPersianDigits } from "@/lib/persian";

function ProfileForm({ user, onSaved }: { user: User; onSaved: () => Promise<void> }) {
  const [fullName, setFullName] = useState(user.full_name);
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      await apiFetch("/api/auth/me/", { method: "PATCH", body: { full_name: fullName } });
      await onSaved();
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card variant="prominent" className="mb-space-lg flex flex-col gap-space-md">
      <Input label="ایمیل" icon="mail" value={user.email} disabled ltr />
      <Input label="نام و نام خانوادگی" icon="badge" value={fullName} onChange={(e) => setFullName(e.target.value)} />
      {!user.is_email_verified && (
        <div className="flex items-center gap-space-xs font-body-sm text-body-sm text-primary">
          <span className="material-symbols-outlined text-[16px]">warning</span>
          ایمیل شما هنوز تایید نشده است.
        </div>
      )}
      <div>
        <Button onClick={handleSave} loading={saving}>
          ذخیره تغییرات
        </Button>
      </div>
    </Card>
  );
}

export default function AccountPage() {
  const { user, loading, refresh } = useAuth();
  const [trips, setTrips] = useState<Trip[]>([]);

  useEffect(() => {
    if (user) apiFetch<Trip[]>("/api/trips/").then(setTrips).catch(() => setTrips([]));
  }, [user]);

  if (loading) return <LoadingState />;

  if (!user) {
    return (
      <div className="mx-auto max-w-md px-margin py-space-xl">
        <Card variant="prominent">
          <p className="font-body-md text-body-md text-on-surface-variant">
            برای مشاهده این صفحه باید{" "}
            <Link href="/login" className="font-medium text-primary hover:underline">
              وارد شوید
            </Link>
            .
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-margin py-space-xl">
      <div className="mb-space-lg flex items-center gap-space-xs">
        <span className="material-symbols-outlined text-[24px] text-primary">account_circle</span>
        <h1 className="font-headline font-headline-lg-mobile text-headline-lg-mobile font-bold text-on-surface">
          حساب کاربری
        </h1>
      </div>
      <ProfileForm key={user.id} user={user} onSaved={refresh} />

      <h2 className="mb-space-sm font-headline-sm text-headline-sm font-semibold text-on-surface">
        سفرهای ذخیره‌شده ({toPersianDigits(trips.length)})
      </h2>
      <div className="flex flex-col gap-space-sm">
        {trips.map((trip) => (
          <Link key={trip.id} href={`/trips/${trip.id}`}>
            <Card className="transition-colors hover:border-primary-container">
              <p className="font-title-md text-title-md font-medium text-on-surface">
                {trip.title || `${trip.origin} به ${trip.destination}`}
              </p>
              <p className="font-body-sm text-body-sm text-on-surface-variant">{trip.destination}</p>
            </Card>
          </Link>
        ))}
        {trips.length === 0 && (
          <p className="font-body-sm text-body-sm text-on-surface-variant">هنوز سفری ثبت نکرده‌اید.</p>
        )}
      </div>
    </div>
  );
}
