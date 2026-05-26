import Link from "next/link";
import type { Category, CategoryCount } from "@/lib/types";
import { CATEGORY_LABELS, CATEGORY_META } from "@/lib/types";
import { fetchCategories } from "@/lib/api";

const CATEGORY_ACTIVE_COLORS: Record<Category, string> = {
  skills:        "bg-emerald-600 text-white border-emerald-600",
  harness:       "bg-violet-600 text-white border-violet-600",
  agents:        "bg-blue-600 text-white border-blue-600",
  orchestration: "bg-amber-600 text-white border-amber-600",
  integration:   "bg-cyan-600 text-white border-cyan-600",
  prompting:     "bg-rose-600 text-white border-rose-600",
  infra:         "bg-slate-600 text-white border-slate-600",
  claude_code:   "bg-orange-600 text-white border-orange-600",
};

const CATEGORY_DOT_COLORS: Record<Category, string> = {
  skills:        "bg-emerald-500",
  harness:       "bg-violet-500",
  agents:        "bg-blue-500",
  orchestration: "bg-amber-500",
  integration:   "bg-cyan-500",
  prompting:     "bg-rose-500",
  infra:         "bg-slate-500",
  claude_code:   "bg-orange-500",
};

interface CategoryNavProps {
  activeCategory?: Category;
}

export default async function CategoryNav({ activeCategory }: CategoryNavProps) {
  let categoryCounts: CategoryCount[] = [];

  try {
    categoryCounts = await fetchCategories();
  } catch {
    // API 장애 시 카테고리 수 없이 렌더링
  }

  const countMap = new Map(categoryCounts.map((c) => [c.category, c.count]));
  const deprecatedMap = new Map(categoryCounts.map((c) => [c.category, c.deprecated_count]));

  const allCategories: Category[] = [
    "skills",
    "harness",
    "agents",
    "orchestration",
    "integration",
    "prompting",
    "infra",
    "claude_code",
  ];

  return (
    <nav
      aria-label="카테고리 탐색"
      className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide"
    >
      {/* 전체 탭 */}
      <Link
        href="/"
        className={`flex-shrink-0 rounded-full px-4 py-1.5 text-sm font-medium transition-all border
          ${activeCategory === undefined
            ? "bg-indigo-600 text-white border-indigo-600"
            : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-600"
          }`}
      >
        전체
      </Link>

      {allCategories.map((cat) => {
        const count = countMap.get(cat);
        const deprecatedCount = deprecatedMap.get(cat) ?? 0;
        const isActive = activeCategory === cat;
        return (
          <Link
            key={cat}
            href={`/category/${cat}`}
            title={CATEGORY_META[cat].description}
            className={`flex-shrink-0 flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-all border
              ${isActive
                ? CATEGORY_ACTIVE_COLORS[cat]
                : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:border-slate-300 dark:hover:border-slate-600"
              }`}
          >
            {/* 카테고리 color dot */}
            {!isActive && <span className={`w-2 h-2 rounded-full flex-shrink-0 ${CATEGORY_DOT_COLORS[cat]}`} />}
            {CATEGORY_LABELS[cat]}
            {count !== undefined && (
              <span
                className={`inline-flex items-center justify-center rounded-full text-xs min-w-[1.25rem] h-4 px-1 font-semibold
                  ${isActive
                    ? "bg-white/20 text-white"
                    : "bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400"
                  }`}
              >
                {count}
              </span>
            )}
            {deprecatedCount > 0 && (
              <span
                className={`inline-flex items-center justify-center rounded-full text-xs min-w-[1.25rem] h-4 px-1 font-semibold
                  ${isActive
                    ? "bg-red-400/30 text-white"
                    : "bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400"
                  }`}
              >
                -{deprecatedCount}
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
