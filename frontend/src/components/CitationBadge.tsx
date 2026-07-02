"use client";

export function CitationBadge({
  n,
  onClick,
  active,
}: {
  n: number;
  onClick: () => void;
  active: boolean;
}) {
  return (
    <button
      onClick={onClick}
      aria-label={`Zitat ${n} anzeigen`}
      className={`mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1
        align-text-top text-xs font-semibold transition-colors ${
          active
            ? "bg-indigo-600 text-white"
            : "bg-indigo-100 text-indigo-700 hover:bg-indigo-200"
        }`}
    >
      {n}
    </button>
  );
}
