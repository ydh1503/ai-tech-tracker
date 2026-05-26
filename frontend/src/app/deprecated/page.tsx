import Link from "next/link";
import { fetchDeprecated } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { CATEGORY_LABELS } from "@/lib/types";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "지원 종료 기술",
  description: "더 이상 권장되지 않는 AI 기술과 대체 기술 목록입니다.",
};

export const revalidate = 60;

export default async function DeprecatedPage() {
  let items;
  try {
    items = await fetchDeprecated();
  } catch {
    items = null;
  }

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
      {/* 헤더 */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-red-100 dark:bg-red-900">
            <svg
              className="h-4 w-4 text-red-600 dark:text-red-300"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </span>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            지원 종료 기술
          </h1>
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          상위 호환 기술로 대체되었거나 더 이상 권장되지 않는 기술 목록입니다.
          기술 자체는 보존되며 역사적 맥락을 제공합니다.
        </p>
      </div>

      {/* 목록 */}
      {!items ? (
        <p className="text-sm text-slate-400 dark:text-slate-500 py-12 text-center">
          목록을 불러오지 못했습니다.
        </p>
      ) : items.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-slate-400 dark:text-slate-500 mb-2">
            현재 지원 종료된 기술이 없습니다.
          </p>
          <Link href="/" className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline">
            전체 목록 보기 →
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border border-red-200 dark:border-red-800 bg-white dark:bg-slate-800 overflow-hidden"
            >
              {/* 상단 빨간 줄 */}
              <div className="h-1 bg-red-500" aria-hidden="true" />

              <div className="p-5">
                {/* 카테고리 + 배지 */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                    {CATEGORY_LABELS[item.category]}
                  </span>
                  <StatusBadge status={item.status} />
                </div>

                {/* 제목 (취소선) */}
                <Link href={`/tech/${item.id}`}>
                  <h2 className="text-base font-semibold text-slate-700 dark:text-slate-300 line-through decoration-red-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                    {item.title}
                  </h2>
                </Link>

                {/* 요약 */}
                {item.summary && (
                  <p className="mt-1 text-sm text-slate-400 dark:text-slate-500 line-clamp-2">
                    {item.summary}
                  </p>
                )}

                {/* 대체 기술 */}
                {item.deprecated_by_title && item.deprecated_by && (
                  <div className="mt-3 flex items-center gap-2">
                    <span className="text-xs text-red-600 dark:text-red-400 font-medium">
                      대신 사용:
                    </span>
                    <Link
                      href={`/tech/${item.deprecated_by}`}
                      className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      {item.deprecated_by_title} →
                    </Link>
                  </div>
                )}

                {/* 대체 이유 */}
                {item.deprecated_reason && (
                  <div className="mt-3 rounded-lg bg-slate-50 dark:bg-slate-700/50 px-4 py-2.5">
                    <p className="text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                      지원 종료 이유
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                      {item.deprecated_reason}
                    </p>
                  </div>
                )}

                {/* 날짜 */}
                <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-400 dark:text-slate-500">
                  {item.deprecated_at && (
                    <span>
                      지원 종료: {new Date(item.deprecated_at).toLocaleDateString("ko-KR")}
                    </span>
                  )}
                  <span>
                    등록일: {new Date(item.created_at).toLocaleDateString("ko-KR")}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
