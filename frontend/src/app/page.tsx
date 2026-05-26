import { Suspense } from "react";
import { fetchTechList } from "@/lib/api";
import TechCard from "@/components/TechCard";
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
    today.setUTCHours(0, 0, 0, 0);  // UTC 기준 자정 (배포 서버 타임존 무관)
    const createdAfter = today.toISOString();

    result = await fetchTechList({ size: 20, page: 1, created_after: createdAfter });

    if (result.items.length === 0) {
      // 오늘 업데이트가 없으면 전체 목록으로 fallback (페이지네이션 지원)
      isToday = false;
      result = await fetchTechList({ size: 20, page });
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

  return (
    <section>
      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        {isToday ? "오늘 업데이트" : "최근 업데이트"}
      </h2>
      {!isToday && (
        <p className="text-xs text-slate-400 dark:text-slate-500 mb-3">
          오늘 업데이트된 항목이 없어 최근 항목을 표시합니다.
        </p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {result.items.map((item) => (
          <TechCard key={item.id} item={item} />
        ))}
      </div>
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
      <div className="mb-8 text-center sm:text-left">
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
          AI 기술 트래커
        </h1>
        <p className="mt-2 text-slate-500 dark:text-slate-400">
          AI를 잘 활용하는 방법, 매일 업데이트
        </p>
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
            <div className="h-7 w-32 rounded bg-slate-100 dark:bg-slate-800 animate-pulse mb-4" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-40 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse"
                />
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
