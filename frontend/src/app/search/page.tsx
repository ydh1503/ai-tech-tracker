import { searchTech } from "@/lib/api";
import TechCard from "@/components/TechCard";
import SearchBar from "@/components/SearchBar";
import Pagination from "@/components/Pagination";
import type { Metadata } from "next";

export const revalidate = 0;

interface SearchPageProps {
  searchParams: Promise<{ q?: string; page?: string }>;
}

export async function generateMetadata(
  { searchParams }: SearchPageProps,
): Promise<Metadata> {
  const { q } = await searchParams;
  if (!q) return { title: "검색" };
  return {
    title: `"${q}" 검색 결과`,
    description: `AI 기술 트래커에서 "${q}"를 검색한 결과입니다.`,
  };
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q, page: pageParam } = await searchParams;
  const query = q?.trim() ?? "";
  const page = Number(pageParam ?? 1);

  let result = null;
  let error = false;

  if (query) {
    try {
      result = await searchTech(query, page);
    } catch {
      error = true;
    }
  }

  const totalPages = result?.pages ?? 1;
  const currentPage = result?.page ?? page;

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-8">
      {/* 검색 헤더 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4">
          {query ? `"${query}" 검색 결과` : "기술 검색"}
        </h1>
        <SearchBar defaultValue={query} />
      </div>

      {/* 결과 */}
      {!query && (
        <p className="text-sm text-slate-400 dark:text-slate-500 text-center py-12">
          검색어를 입력하세요.
        </p>
      )}

      {error && (
        <p className="text-sm text-slate-400 dark:text-slate-500 text-center py-12">
          검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.
        </p>
      )}

      {result !== null && !error && (
        <>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
            {result.total > 0
              ? `총 ${result.total}개의 결과를 찾았습니다.`
              : `"${query}"에 해당하는 기술이 없습니다.`}
          </p>

          {result.items.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {result.items.map((item) => (
                <TechCard key={item.id} item={item} />
              ))}
            </div>
          )}

          {/* 페이지네이션 */}
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            basePath="/search"
            searchParams={query ? { q: query } : undefined}
          />
        </>
      )}
    </div>
  );
}
