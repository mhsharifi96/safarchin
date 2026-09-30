import { InputHTMLAttributes, forwardRef } from "react";
import clsx from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  /** Emails, passwords, phone-with-country-code, etc. must render LTR even inside the RTL page. */
  ltr?: boolean;
  /** Material Symbols icon name, pinned to the field's leading edge. */
  icon?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, ltr = false, icon, className, id, ...rest }, ref) => {
    const inputId = id || rest.name;
    return (
      <div className="flex flex-col gap-space-xs">
        {label && (
          <label
            htmlFor={inputId}
            className="flex items-center justify-between font-label-lg text-label-lg font-semibold text-on-surface"
          >
            <span>{label}</span>
            {hint && <span className="font-label-sm text-label-sm font-normal text-on-surface-variant">{hint}</span>}
          </label>
        )}
        <div className="relative flex items-center">
          <input
            ref={ref}
            id={inputId}
            dir={ltr ? "ltr" : undefined}
            className={clsx(
              "h-12 w-full rounded-full bg-surface-container-low px-space-md font-body-md text-body-md text-on-surface outline-none transition-colors placeholder:text-outline focus:bg-surface-container",
              icon && (ltr ? "pl-11" : "pr-11"),
              ltr && "ltr-field",
              error && "ring-2 ring-error",
              className
            )}
            {...rest}
          />
          {icon && (
            <span
              className={clsx(
                "material-symbols-outlined pointer-events-none absolute text-[20px] text-outline",
                ltr ? "left-4" : "right-4"
              )}
            >
              {icon}
            </span>
          )}
        </div>
        {error && <p className="font-body-sm text-body-sm text-error">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";

export default Input;
