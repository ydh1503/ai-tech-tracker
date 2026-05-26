import type { TechItem } from "@/lib/types";
import { CATEGORY_LABELS } from "@/lib/types";
import StatusBadge from "./StatusBadge";
import Link from "next/link";

interface TimelineProps {
  items: TechItem[];
}

function groupByDate(items: TechItem[]): Map<string, TechItem[]> {
  const map = new Map<string, TechItem[]>();
  for (const item of items) {
    const date = new Date(item.updated_at).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    const existing = map.get(date);
    if (existing) {
      existing.push(item);
    } else {
      map.set(date, [item]);
    }
  }
  return map;
}

export default function Timeline({ items }: TimelineProps) {
  const grouped = groupByDate(items);

  if (items.length === 0) {
    return (
      <p className="text-sm text-slate-400 dark:text-slate-500 py-8 text-center">
        업데이트 이력이 없습니다.
      </p>
    );
  }

  return (
    <div className="relative">
      {/* 세로 선 */}
      <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-slate-200 dark:bg-slate-700" aria-hidden="true" />

      <ol className="space-y-8">
        {Array.from(grouped.entries()).map(([date, dateItems]) => (
          <li key={date} className="relative pl-10">
            {/* 타임라인 점 */}
            <div className="absolute left-0 top-1 flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600 text-white text-xs font-bold">
              {dateItems.length}
            </div>

            {/* 날짜 헤더 */}
            <p className="mb-3 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              {date}
            </p>

            <ul className="space-y-2">
              {dateItems.map((item) => (
                <li key={item.id}>
                  <Link
                    href={`/tech/${item.id}`}
                    className="flex items-center justify-between gap-3 rounded-lg border border-slate-100 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-2.5 hover:border-indigo-300 dark:hover:border-indigo-600 transition-colors group"
                  >
                    <div className="min-w-0">
                      <span className="block text-sm font-medium text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 truncate">
                        {item.title}
                      </span>
                      <span className="text-xs text-slate-400 dark:text-slate-500">
                        {CATEGORY_LABELS[item.category]}
                      </span>
                    </div>
                    <StatusBadge status={item.status} className="flex-shrink-0" />
                  </Link>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </div>
  );
}
