import Link from "next/link";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  basePath: string;
  searchParams?: Record<string, string>;
}

function buildHref(
  page: number,
  basePath: string,
  searchParams?: Record<string, string>,
): string {
  const params = new URLSearchParams(searchParams);
  if (page > 1) {
    params.set("page", String(page));
  }
  const query = params.toString();
  return query ? `${basePath}?${query}` : basePath;
}

/**
 * 표시할 페이지 번호 목록을 계산한다.
 * 항상 첫 페이지(1)와 마지막 페이지(totalPages)를 포함하고,
 * 현재 페이지 ±2 범위를 포함한다. 생략 구간은 "..."(문자열)로 표시한다.
 */
function getPageItems(
  currentPage: number,
  totalPages: number,
): (number | "...")[] {
  const pages = new Set<number>();
  pages.add(1);
  pages.add(totalPages);
  for (let p = currentPage - 2; p <= currentPage + 2; p++) {
    if (p >= 1 && p <= totalPages) {
      pages.add(p);
    }
  }

  const sorted = Array.from(pages).sort((a, b) => a - b);

  const items: (number | "...")[] = [];
  let prev = 0;
  for (const p of sorted) {
    if (prev && p - prev > 1) {
      items.push("...");
    }
    items.push(p);
    prev = p;
  }
  return items;
}

export default function Pagination({
  currentPage,
  totalPages,
  basePath,
  searchParams,
}: PaginationProps) {
  if (totalPages <= 1) return null;

  const items = getPageItems(currentPage, totalPages);
  const hasPrev = currentPage > 1;
  const hasNext = currentPage < totalPages;

  const baseBtn = "px-3 py-1.5 text-sm font-medium transition-colors rounded-lg";

  return (
    <nav className="flex items-center justify-center gap-1 mt-8" aria-label="페이지네이션">
      {/* 이전 */}
      {hasPrev ? (
        <Link
          href={buildHref(currentPage - 1, basePath, searchParams)}
          className={`${baseBtn} border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:border-indigo-400`}
        >
          ← 이전
        </Link>
      ) : (
        <span
          aria-disabled="true"
          className={`${baseBtn} border border-slate-200 dark:border-slate-700 text-slate-300 dark:text-slate-600 cursor-not-allowed`}
        >
          ← 이전
        </span>
      )}

      {/* 페이지 번호 */}
      {items.map((item, idx) =>
        item === "..." ? (
          <span
            key={`ellipsis-${idx}`}
            className="text-slate-400 dark:text-slate-500 px-2"
          >
            ...
          </span>
        ) : item === currentPage ? (
          <span
            key={item}
            aria-current="page"
            className={`${baseBtn} bg-indigo-600 text-white`}
          >
            {item}
          </span>
        ) : (
          <Link
            key={item}
            href={buildHref(item, basePath, searchParams)}
            className={`${baseBtn} bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-indigo-100 dark:hover:bg-indigo-900`}
          >
            {item}
          </Link>
        ),
      )}

      {/* 다음 */}
      {hasNext ? (
        <Link
          href={buildHref(currentPage + 1, basePath, searchParams)}
          className={`${baseBtn} border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:border-indigo-400`}
        >
          다음 →
        </Link>
      ) : (
        <span
          aria-disabled="true"
          className={`${baseBtn} border border-slate-200 dark:border-slate-700 text-slate-300 dark:text-slate-600 cursor-not-allowed`}
        >
          다음 →
        </span>
      )}
    </nav>
  );
}
