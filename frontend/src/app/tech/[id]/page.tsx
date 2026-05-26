import { notFound } from "next/navigation";
import Link from "next/link";
import { fetchTechById } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import DeprecatedBanner from "@/components/DeprecatedBanner";
import type { Metadata } from "next";
import { CATEGORY_LABELS } from "@/lib/types";

export const revalidate = 60;

interface TechDetailPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata(
  { params }: TechDetailPageProps,
): Promise<Metadata> {
  const { id } = await params;
  try {
    const item = await fetchTechById(id);
    return {
      title: item.title,
      description: item.summary ?? item.description ?? undefined,
    };
  } catch {
    return { title: "기술을 찾을 수 없습니다" };
  }
}

export default async function TechDetailPage({ params }: TechDetailPageProps) {
  const { id } = await params;

  let item;
  try {
    item = await fetchTechById(id);
  } catch {
    notFound();
  }

  // notFound()는 never를 반환하므로 catch에서 항상 탈출하지만, 방어적 체크 추가
  if (!item) notFound();

  const isDeprecated = item.status === "deprecated";

  return (
    <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-8">
      {/* 뒤로가기 */}
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-6"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
        </svg>
        목록으로
      </Link>

      {/* Deprecated 배너 */}
      {isDeprecated && (
        <DeprecatedBanner
          deprecatedByTitle={item.deprecated_by_title}
          deprecatedById={item.deprecated_by}
          deprecatedReason={item.deprecated_reason}
        />
      )}

      {/* 기사 헤더 */}
      <article>
        <header className="mb-6">
          {/* 카테고리 + 상태 */}
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <Link
              href={`/category/${item.category}`}
              className="text-xs font-medium text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/40 px-2.5 py-1 rounded-full hover:bg-indigo-100 dark:hover:bg-indigo-900 transition-colors"
            >
              {CATEGORY_LABELS[item.category]}
            </Link>
            <StatusBadge status={item.status} />
          </div>

          {/* 제목 */}
          <h1
            className={`text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100 leading-snug
              ${isDeprecated ? "line-through decoration-red-500 opacity-75" : ""}`}
          >
            {item.title}
          </h1>

          {/* 날짜 */}
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400 dark:text-slate-500">
            {item.tech_released_at && (
              <span className="font-medium text-indigo-500 dark:text-indigo-400">
                🗓 출시일: {new Date(item.tech_released_at).toLocaleDateString("ko-KR", { year: "numeric", month: "long" })}
              </span>
            )}
            <span>
              사이트 등록: {new Date(item.created_at).toLocaleDateString("ko-KR")}
            </span>
            <span>
              최종 수정: {new Date(item.updated_at).toLocaleDateString("ko-KR")}
            </span>
            {item.deprecated_at && (
              <span>
                지원 종료일: {new Date(item.deprecated_at).toLocaleDateString("ko-KR")}
              </span>
            )}
          </div>
        </header>

        {/* 요약 */}
        {item.summary && (
          <div className="mb-6 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800 px-5 py-4">
            <p className="text-sm font-semibold text-indigo-700 dark:text-indigo-300 mb-1">
              한 줄 요약
            </p>
            <p className="text-base text-slate-800 dark:text-slate-200 leading-relaxed">
              {item.summary}
            </p>
          </div>
        )}

        {/* 상세 설명 */}
        {item.description && (
          <div className="mb-6 prose prose-sm dark:prose-invert max-w-none text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
            {item.description}
          </div>
        )}

        {/* 링크 버튼 */}
        <div className="flex flex-wrap gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
          {item.official_url && (
            <a
              href={item.official_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={2}
                stroke="currentColor"
                aria-hidden="true"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
              공식 문서
            </a>
          )}
          <a
            href={item.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 dark:border-slate-600 hover:border-slate-400 text-slate-700 dark:text-slate-300 px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-500"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
            </svg>
            원본 출처
          </a>
        </div>
      </article>
    </div>
  );
}
