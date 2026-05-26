import { Suspense } from "react";
import { fetchTechGrouped } from "@/lib/api";
import TechGroupCard from "@/components/TechGroupCard";
import CategoryNav from "@/components/CategoryNav";
import Pagination from "@/components/Pagination";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI 기술 트래커",
  description: "AI 스킬, 에이전트, 하네스 등 AI 활용 기술을 매일 업데이트합니다.",
};

export const revalidate = 60;

async function LatestTechList({ page = 1 }: { page?: number }) {
  let result;
  let isToday = true;

  try {
    const today = new Date();
    today.setUTCHours(0, 0, 0, 0);
    const createdAfter = today.toISOString();

    result = await fetchTechGrouped({ size: 20, page: 1, created_after: createdAfter });

    if (result.items.length === 0) {
      isToday = false;
      result = await fetchTechGrouped({ size: 20, page });
    }
  } catch {
    return (
      <p className="text-sm text-slate-400 dark:text-slate-500 py-12 text-center">
        기술 목록을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
      </p>
    );
  }

  if (result.items.length === 0) {
    return (
      <p className="text-sm text-slate-400 dark:text-slate-500 py-12 text-center">
        등록된 기술이 없습니다.
      </p>
    );
  }

  const [featured, ...rest] = result.items;

  return (
    <section>
      {/* 섹션 헤더 */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            {isToday ? "오늘 업데이트" : "최근 업데이트"}
          </h2>
          {isToday && (
            <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              {result.items.length}건
            </span>
          )}
        </div>
        {!isToday && (
          <p className="text-xs text-slate-400 dark:text-slate-500">
            오늘 업데이트 없음 — 최근 항목 표시
          </p>
        )}
      </div>

      {/* Featured 카드 (첫 번째 항목) */}
      <div className="mb-4">
        <TechGroupCard group={featured} featured />
      </div>

      {/* 나머지 카드 그리드 */}
      {rest.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {rest.map((group) => (
            <TechGroupCard key={group.group_key} group={group} />
          ))}
        </div>
      )}

      {!isToday && result.pages > 1 && (
        <div className="mt-8">
          <Pagination
            currentPage={result.page}
            totalPages={result.pages}
            basePath="/"
          />
        </div>
      )}
    </section>
  );
}

interface HomePageProps {
  searchParams?: Promise<{ page?: string }>;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearch = await (searchParams ?? Promise.resolve<{ page?: string }>({}));
  const page = Number(resolvedSearch.page ?? 1);

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8">
      {/* 히어로 */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              AI 기술 트래커
            </h1>
            <p className="mt-1.5 text-slate-500 dark:text-slate-400 text-sm">
              AI를 잘 활용하는 방법, 매일 업데이트 — 스킬·에이전트·프롬프팅·인프라
            </p>
          </div>
        </div>
      </div>

      {/* 카테고리 네비게이션 */}
      <div className="mb-8">
        <Suspense fallback={<div className="h-9 animate-pulse rounded-full bg-slate-100 dark:bg-slate-800 w-64" />}>
          <CategoryNav />
        </Suspense>
      </div>

      {/* 기술 카드 목록 */}
      <Suspense
        fallback={
          <section>
            <div className="h-7 w-32 rounded bg-slate-100 dark:bg-slate-800 animate-pulse mb-5" />
            <div className="h-36 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse mb-4" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-32 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse" />
              ))}
            </div>
          </section>
        }
      >
        <LatestTechList page={page} />
      </Suspense>
    </div>
  );
}
