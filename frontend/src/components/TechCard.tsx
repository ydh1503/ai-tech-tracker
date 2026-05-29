import Link from "next/link";
import type { TechItem } from "@/lib/types";
import { CATEGORY_LABELS, CATEGORY_COLORS } from "@/lib/types";
import StatusBadge from "./StatusBadge";

interface TechCardProps {
  item: TechItem;
  featured?: boolean;
}

export default function TechCard({ item, featured = false }: TechCardProps) {
  const isDeprecated = item.status === "deprecated";
  const colors = CATEGORY_COLORS[item.category];

  return (
    <Link href={`/tech/${item.id}`} className="block group">
      <div className={`
        relative flex overflow-hidden rounded-xl border transition-all duration-200
        hover:-translate-y-0.5 hover:shadow-lg
        ${isDeprecated ? "opacity-60 border-red-300 dark:border-red-800 bg-white dark:bg-slate-800" : `${colors.border} ${colors.bg}`}
      `}>
        {/* 왼쪽 카테고리 컬러 바 */}
        <div className={`w-1 flex-shrink-0 ${isDeprecated ? "bg-red-400" : colors.accent}`} />

        <div className={`flex-1 ${featured ? "p-5" : "p-4"}`}>
          {/* 카테고리 배지 + 상태 */}
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${isDeprecated ? "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300" : colors.badge}`}>
              {CATEGORY_LABELS[item.category]}
            </span>
            <StatusBadge status={item.status} />
          </div>

          {/* 제목 */}
          <h3 className={`font-semibold leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors
            ${featured ? "text-lg mb-2" : "text-sm mb-1.5"}
            ${isDeprecated ? "line-through decoration-red-500 text-slate-500 dark:text-slate-500" : "text-slate-900 dark:text-slate-100"}
          `}>
            {item.title}
          </h3>

          {/* 요약 */}
          {item.summary && (
            <p className={`text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed
              ${featured ? "text-sm" : "text-xs"}`}>
              {item.summary}
            </p>
          )}

          {/* deprecated 대체 기술 */}
          {isDeprecated && item.deprecated_by_title && (
            <p className="mt-1.5 text-xs text-red-600 dark:text-red-400 font-medium">
              → {item.deprecated_by_title}
            </p>
          )}

          {/* 하단: 날짜 */}
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            {item.tech_released_at && (
              <span className="text-xs font-medium text-slate-400 dark:text-slate-500">
                {new Date(item.tech_released_at).getFullYear()}년
              </span>
            )}
            <span className="text-xs text-slate-400 dark:text-slate-500">
              {new Date(item.updated_at).toLocaleDateString("ko-KR", { month: "short", day: "numeric" })}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
