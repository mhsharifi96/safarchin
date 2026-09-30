export function LoadingState({ label = "در حال بارگذاری..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-space-sm py-16 text-on-surface-variant">
      <span className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      <p className="font-body-sm text-body-sm">{label}</p>
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-space-xs rounded-DEFAULT border border-dashed border-outline-variant py-16 text-center">
      <p className="font-title-md text-title-md text-on-surface">{title}</p>
      {description && (
        <p className="max-w-sm font-body-sm text-body-sm text-on-surface-variant">{description}</p>
      )}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-space-xs rounded-DEFAULT bg-error-container px-space-md py-space-sm font-body-sm text-body-sm font-medium text-on-error-container">
      <span className="material-symbols-outlined text-[20px] text-error">info</span>
      <span>{message}</span>
    </div>
  );
}
