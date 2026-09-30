"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/context/AuthContext";
import Button from "@/components/ui/Button";

export default function Header() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="sticky top-0 z-50 bg-surface/85 shadow-[0_1px_8px_rgba(0,0,0,0.03)] backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-margin">
        <Link href="/" className="flex items-center gap-space-xs">
          <span className="material-symbols-outlined text-[24px] text-primary">explore</span>
          <span className="font-headline font-headline-sm text-headline-sm font-bold tracking-tight text-primary">
            سفرچین
          </span>
        </Link>
        <nav className="flex items-center gap-space-sm">
          <Link
            href="/trips"
            className="font-label-lg text-label-lg text-on-surface-variant transition-colors hover:text-primary"
          >
            سفرهای من
          </Link>
          {loading ? null : user ? (
            <>
              <Link
                href="/account"
                className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-container text-on-primary"
                title={user.full_name || user.email}
              >
                <span className="material-symbols-outlined text-[18px]">person</span>
              </Link>
              <Button
                variant="ghost"
                className="h-10 px-space-md"
                onClick={async () => {
                  await logout();
                  router.push("/");
                }}
              >
                خروج
              </Button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="font-label-lg text-label-lg text-on-surface-variant transition-colors hover:text-primary"
              >
                ورود
              </Link>
              <Link href="/register">
                <Button variant="primary" className="h-10 px-space-md">
                  ثبت‌نام
                </Button>
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
