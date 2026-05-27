import Link from "next/link";
import { STATUS_LABELS } from "@/lib/types";

interface FilterBarProps {
  basePath: string;
  currentStatus?: string;
  currentRange?: string;
  searchParams?: Record<string, string>;
}

const DATE_RANGE_OPTIONS = [
  { value: "all", label: "전체 기간" },
  { value: "today", label: "오늘" },
  { value: "week", label: "이번 주" },
  { value: "month", label: "이번 달" },
];

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "all", label: "모든 상태" },
  { value: "active", label: STATUS_LABELS.active },
  { value: "stable", label: STATUS_LABELS.stable },
  { value: "experimental", label: STATUS_LABELS.experimental },
  { value: "deprecated", label: STATUS_LABELS.deprecated },
];

function buildUrl(
  basePath: string,
  overrides: Record<string, string>,
  base: Record<string, string> = {},
): string {
  const merged = { ...base, ...overrides };
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(merged)) {
    if (v && v !== "all") qs.set(k, v);
  }
  const str = qs.toString();
  return str ? `${basePath}?${str}` : basePath;
}

export default function FilterBar({
  basePath,
  currentStatus = "all",
  currentRange = "all",
  searchParams = {},
}: FilterBarProps) {
  const hasFilter = (currentStatus && currentStatus !== "all") || (currentRange && currentRange !== "all");
  const baseParams = Object.fromEntries(
    Object.entries(searchParams).filter(([k]) => k !== "status" && k !== "range" && k !== "page"),
  );

  return (
    <div className="flex flex-wrap items-center gap-2 mb-6">
      {/* 상태 필터 */}
      <div className="flex items-center gap-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-1 py-1">
        {STATUS_OPTIONS.map((opt) => {
          const isActive = currentStatus === opt.value || (opt.value === "all" && !currentStatus);
          return (
            <Link
              key={opt.value}
              href={buildUrl(basePath, { status: opt.value }, baseParams)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
              }`}
            >
              {opt.label}
            </Link>
          );
        })}
      </div>

      {/* 날짜 범위 필터 */}
      <div className="flex items-center gap-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-1 py-1">
        {DATE_RANGE_OPTIONS.map((opt) => {
          const isActive = currentRange === opt.value || (opt.value === "all" && !currentRange);
          return (
            <Link
              key={opt.value}
              href={buildUrl(basePath, { range: opt.value }, baseParams)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
              }`}
            >
              {opt.label}
            </Link>
          );
        })}
      </div>

      {/* 필터 초기화 */}
      {hasFilter && (
        <Link
          href={buildUrl(basePath, {}, baseParams)}
          className="text-xs text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400 transition-colors px-1"
        >
          × 필터 초기화
        </Link>
      )}
    </div>
  );
}
