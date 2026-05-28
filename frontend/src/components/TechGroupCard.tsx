import Link from "next/link";
import type { TechGroupedItem } from "@/lib/types";
import { CATEGORY_LABELS } from "@/lib/types";
import StatusBadge from "./StatusBadge";
import type { Category } from "@/lib/types";

const CATEGORY_COLORS: Record<Category, { bg: string; border: string; accent: string; badge: string }> = {
  skills:        { bg: "bg-emerald-50 dark:bg-emerald-950/30",  border: "border-emerald-200 dark:border-emerald-800",  accent: "bg-emerald-500",  badge: "bg-emerald-100 dark:bg-emerald-900/60 text-emerald-700 dark:text-emerald-300" },
  harness:       { bg: "bg-violet-50 dark:bg-violet-950/30",    border: "border-violet-200 dark:border-violet-800",    accent: "bg-violet-500",   badge: "bg-violet-100 dark:bg-violet-900/60 text-violet-700 dark:text-violet-300" },
  agents:        { bg: "bg-blue-50 dark:bg-blue-950/30",        border: "border-blue-200 dark:border-blue-800",        accent: "bg-blue-500",     badge: "bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300" },
  orchestration: { bg: "bg-amber-50 dark:bg-amber-950/30",      border: "border-amber-200 dark:border-amber-800",      accent: "bg-amber-500",    badge: "bg-amber-100 dark:bg-amber-900/60 text-amber-700 dark:text-amber-300" },
  integration:   { bg: "bg-cyan-50 dark:bg-cyan-950/30",        border: "border-cyan-200 dark:border-cyan-800",        accent: "bg-cyan-500",     badge: "bg-cyan-100 dark:bg-cyan-900/60 text-cyan-700 dark:text-cyan-300" },
  prompting:     { bg: "bg-rose-50 dark:bg-rose-950/30",        border: "border-rose-200 dark:border-rose-800",        accent: "bg-rose-500",     badge: "bg-rose-100 dark:bg-rose-900/60 text-rose-700 dark:text-rose-300" },
  infra:         { bg: "bg-slate-100 dark:bg-slate-800/50",     border: "border-slate-300 dark:border-slate-600",      accent: "bg-slate-500",    badge: "bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300" },
  claude_code:   { bg: "bg-orange-50 dark:bg-orange-950/30",    border: "border-orange-200 dark:border-orange-800",    accent: "bg-orange-500",   badge: "bg-orange-100 dark:bg-orange-900/60 text-orange-700 dark:text-orange-300" },
};

interface TechGroupCardProps {
  group: TechGroupedItem;
  featured?: boolean;
}

export default function TechGroupCard({ group, featured = false }: TechGroupCardProps) {
  const { latest, patches, base_title, version_prefix, patch_count } = group;
  const isGroup = patch_count > 1;
  const isDeprecated = latest.status === "deprecated";
  const colors = CATEGORY_COLORS[latest.category];

  return (
    <Link href={`/tech/${latest.id}`} className="block group">
      <div
        className={`relative flex overflow-hidden rounded-xl border transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg
          ${isDeprecated
            ? "opacity-60 border-red-300 dark:border-red-800 bg-white dark:bg-slate-800"
            : `${colors.border} ${colors.bg}`
          }`}
      >
        {/* 왼쪽 카테고리 컬러 바 */}
        <div className={`w-1 flex-shrink-0 ${isDeprecated ? "bg-red-400" : colors.accent}`} />

        <div className={`flex-1 ${featured ? "p-5" : "p-4"}`}>
          {/* 카테고리 배지 + 그룹 배지 + 상태 */}
          <div className="flex items-center justify-between gap-2 mb-2 flex-wrap">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold
                  ${isDeprecated ? "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300" : colors.badge}`}
              >
                {CATEGORY_LABELS[latest.category]}
              </span>
              {isGroup && (
                <span className="inline-flex items-center gap-1 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 text-xs font-semibold">
                  {version_prefix && <span className="font-mono">{version_prefix}</span>}
                  {version_prefix && <span className="opacity-60">·</span>}
                  {patch_count}개 버전
                </span>
              )}
            </div>
            <StatusBadge status={latest.status} />
          </div>

          {/* 제목 */}
          <h3
            className={`font-semibold leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors
              ${featured ? "text-lg mb-2" : "text-sm mb-1.5"}
              ${isDeprecated
                ? "line-through decoration-red-500 text-slate-500 dark:text-slate-500"
                : "text-slate-900 dark:text-slate-100"
              }`}
          >
            {isGroup ? base_title : latest.title}
          </h3>

          {/* 요약 */}
          {latest.summary && (
            <p className={`text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed ${featured ? "text-sm" : "text-xs"}`}>
              {latest.summary}
            </p>
          )}

          {/* 버전 칩 (그룹만 표시) */}
          {isGroup && (
            <div className="mt-2 flex items-center gap-1 flex-wrap">
              {patches.slice(0, 5).map((p) => (
                <span
                  key={p.id}
                  className="text-xs font-mono bg-white/70 dark:bg-slate-700/70 text-slate-600 dark:text-slate-300 rounded px-1.5 py-0.5 border border-slate-200 dark:border-slate-600"
                >
                  v{p.version_str}
                </span>
              ))}
              {patches.length > 5 && (
                <span className="text-xs text-slate-400 dark:text-slate-500 font-medium">
                  +{patches.length - 5}
                </span>
              )}
            </div>
          )}

          {/* 날짜 */}
          <div className="mt-3 text-xs text-slate-400 dark:text-slate-500">
            {new Date(latest.updated_at).toLocaleDateString("ko-KR", { month: "short", day: "numeric" })}
            {isGroup && (
              <span className="ml-2 text-slate-300 dark:text-slate-600">최신: v{patches[0]?.version_str}</span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
