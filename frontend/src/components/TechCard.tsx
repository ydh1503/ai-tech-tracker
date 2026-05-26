import Link from "next/link";
import type { TechItem } from "@/lib/types";
import { CATEGORY_LABELS } from "@/lib/types";
import StatusBadge from "./StatusBadge";

interface TechCardProps {
  item: TechItem;
}

export default function TechCard({ item }: TechCardProps) {
  const isDeprecated = item.status === "deprecated";

  return (
    <Link href={`/tech/${item.id}`} className="block group">
      <div
        className={`relative rounded-xl border bg-white dark:bg-slate-800 shadow-sm transition-shadow hover:shadow-md overflow-hidden
          ${isDeprecated
            ? "border-red-300 dark:border-red-700 opacity-70"
            : "border-slate-200 dark:border-slate-700"
          }`}
      >
        {/* deprecated 상단 빨간 줄 */}
        {isDeprecated && (
          <div className="h-1 w-full bg-red-500" aria-hidden="true" />
        )}

        <div className="p-5">
          {/* 카테고리 + 상태 배지 */}
          <div className="flex items-center justify-between mb-3 gap-2 flex-wrap">
            <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/40 px-2 py-0.5 rounded-full">
              {CATEGORY_LABELS[item.category]}
            </span>
            <StatusBadge status={item.status} />
          </div>

          {/* 제목 */}
          <h3
            className={`text-base font-semibold text-slate-900 dark:text-slate-100 mb-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors
              ${isDeprecated ? "line-through decoration-red-500" : ""}`}
          >
            {item.title}
          </h3>

          {/* 요약 */}
          {item.summary && (
            <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">
              {item.summary}
            </p>
          )}

          {/* deprecated 대체 기술 안내 */}
          {isDeprecated && item.deprecated_by_title && (
            <p className="mt-2 text-xs text-red-600 dark:text-red-400 font-medium">
              대신 → {item.deprecated_by_title}
            </p>
          )}

          {/* 날짜 */}
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            {item.tech_released_at && (
              <span className="text-xs text-indigo-500 dark:text-indigo-400 font-medium">
                {new Date(item.tech_released_at).getFullYear()}년 출시
              </span>
            )}
            <span className="text-xs text-slate-400 dark:text-slate-500">
              {new Date(item.updated_at).toLocaleDateString("ko-KR")} 업데이트
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
