import Link from "next/link";
import type { Category, CategoryCount } from "@/lib/types";
import { CATEGORY_LABELS, CATEGORY_META } from "@/lib/types";
import { fetchCategories } from "@/lib/api";

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
        className={`flex-shrink-0 rounded-full px-4 py-1.5 text-sm font-medium transition-colors
          ${activeCategory === undefined
            ? "bg-indigo-600 text-white"
            : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-indigo-100 dark:hover:bg-indigo-900"
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
            className={`flex-shrink-0 flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-medium transition-colors
              ${isActive
                ? "bg-indigo-600 text-white"
                : "bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-indigo-100 dark:hover:bg-indigo-900"
              }`}
          >
            {CATEGORY_LABELS[cat]}
            {count !== undefined && (
              <span
                className={`inline-flex items-center justify-center rounded-full text-xs min-w-[1.25rem] h-5 px-1 font-semibold
                  ${isActive
                    ? "bg-white/20 text-white"
                    : "bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-200"
                  }`}
              >
                {count}
              </span>
            )}
            {deprecatedCount > 0 && (
              <span
                className={`inline-flex items-center justify-center rounded-full text-xs min-w-[1.25rem] h-5 px-1 font-semibold
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
