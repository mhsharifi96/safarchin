import { HTMLAttributes } from "react";
import clsx from "clsx";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** "default" = 16px-radius bordered tile (list items, day cards). "prominent" = 32px-radius
   * elevated container used for the main content block of a screen (forms, workspace panels). */
  variant?: "default" | "prominent";
}

export default function Card({ variant = "default", className, children, ...rest }: CardProps) {
  return (
    <div
      className={clsx(
        "bg-surface-container-lowest shadow-sm",
        variant === "prominent"
          ? "rounded-lg p-space-lg"
          : "rounded-DEFAULT border border-surface-container-high p-space-md",
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
