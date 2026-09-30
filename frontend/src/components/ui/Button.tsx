import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "accent" | "ghost";
  loading?: boolean;
}

const VARIANT_CLASSES: Record<string, string> = {
  primary:
    "bg-primary-container text-on-primary shadow-md shadow-primary-container/20 hover:bg-primary",
  accent:
    "bg-primary-container text-on-primary shadow-md shadow-primary-container/20 hover:bg-primary",
  secondary:
    "bg-surface-container-low text-secondary hover:bg-secondary-fixed/30",
  ghost: "bg-transparent text-on-surface border border-outline-variant hover:bg-surface-container-low",
};

export default function Button({
  variant = "primary",
  loading = false,
  disabled,
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={clsx(
        "inline-flex h-12 items-center justify-center gap-space-xs rounded-full px-space-lg font-label-lg text-label-lg font-semibold transition-all duration-150 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-60",
        VARIANT_CLASSES[variant],
        className
      )}
      {...rest}
    >
      {loading && (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  );
}
