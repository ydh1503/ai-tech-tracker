import { notFound } from "next/navigation";
import { Suspense } from "react";
import { fetchTechGrouped } from "@/lib/api";
import TechGroupCard from "@/components/TechGroupCard";
import CategoryNav from "@/components/CategoryNav";
import Pagination from "@/components/Pagination";
import type { Category } from "@/lib/types";
import { CATEGORY_LABELS, CATEGORY_META } from "@/lib/types";
import type { Metadata } from "next";

export const revalidate = 60;

const VALID_CATEGORIES: Category[] = [
  "skills",
  "harness",
  "agents",
  "orchestration",
  "integration",
  "prompting",
  "infra",
  "claude_code",
];

interface CategoryPageProps {
  params: Promise<{ slug: string }>;
  searchParams?: Promise<{ page?: string }>;
}

export async function generateMetadata(
  { params }: CategoryPageProps,
): Promise<Metadata> {
  const { slug } = await params;
  if (!VALID_CATEGORIES.includes(slug as Category)) {
    return { title: "카테고리를 찾을 수 없습니다" };
  }
  const label = CATEGORY_LABELS[slug as Category];
  return {
    title: `${label} — 카테고리`,
    description: `AI 기술 트래커에서 ${label} 카테고리의 기술 목록을 확인하세요.`,
  };
}

export default async function CategoryPage({ params, searchParams }: CategoryPageProps) {
  const { slug } = await params;
  const resolvedSearch = await searchParams;
  const page = Number(resolvedSearch?.page ?? 1);

  if (!VALID_CATEGORIES.includes(slug as Category)) {
    notFound();
  }

  const category = slug as Category;

  let result;
  try {
    result = await fetchTechGrouped({ category, size: 20, page });
  } catch {
    result = null;
  }

  const totalPages = result?.pages ?? 1;
  const currentPage = result?.page ?? page;

  return (
    <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8">
      {/* 카테고리 네비게이션 */}
      <div className="mb-8">
        <Suspense fallback={null}>
          <CategoryNav activeCategory={category} />
        </Suspense>
      </div>

      {/* 카테고리 설명 헤더 */}
      <div className="mb-8 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          {CATEGORY_META[category].label}
        </h1>
        <p className="mt-2 text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
          {CATEGORY_META[category].description}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {CATEGORY_META[category].examples.map((example) => (
            <span
              key={example}
              className="inline-flex items-center rounded-full bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 px-3 py-1 text-xs font-medium text-slate-600 dark:text-slate-300"
            >
              {example}
            </span>
          ))}
        </div>
        {result && (
          <p className="mt-4 text-xs text-slate-400 dark:text-slate-500">
            총 {result.total}개 그룹 (패치 버전 그룹화 포함)
          </p>
        )}
      </div>

      {/* 기술 카드 목록 */}
      {!result ? (
        <p className="text-sm text-slate-400 dark:text-slate-500 py-12 text-center">
          목록을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
        </p>
      ) : result.items.length === 0 ? (
        <p className="text-sm text-slate-400 dark:text-slate-500 py-12 text-center">
          이 카테고리에 등록된 기술이 없습니다.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {result.items.map((group) => (
            <TechGroupCard key={group.group_key} group={group} />
          ))}
        </div>
      )}

      {/* 페이지네이션 */}
      {result && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          basePath={`/category/${slug}`}
        />
      )}
    </div>
  );
}
