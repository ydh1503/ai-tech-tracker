import { notFound } from "next/navigation";
import Link from "next/link";
import { fetchTechById } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { CATEGORY_LABELS } from "@/lib/types";
import type { Metadata } from "next";
import type { TechItem, Status } from "@/lib/types";

export const revalidate = 60;

interface ComparePageProps {
  searchParams: Promise<{ a?: string; b?: string }>;
}

export async function generateMetadata({ searchParams }: ComparePageProps): Promise<Metadata> {
  const { a, b } = await searchParams;
  if (!a || !b) return { title: "기술 비교" };
  try {
    const [itemA, itemB] = await Promise.all([fetchTechById(a), fetchTechById(b)]);
    return { title: `${itemA.title} vs ${itemB.title}` };
  } catch {
    return { title: "기술 비교" };
  }
}

export default async function ComparePage({ searchParams }: ComparePageProps) {
  const { a, b } = await searchParams;

  if (!a || !b) {
    return (
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-16 text-center">
        <p className="text-slate-500 dark:text-slate-400">
          비교할 두 항목의 ID를 URL 파라미터 <code>?a=ID1&b=ID2</code>로 전달하세요.
        </p>
        <Link href="/" className="mt-4 inline-block text-indigo-600 dark:text-indigo-400 hover:underline">
          목록으로 →
        </Link>
      </div>
    );
  }

  let itemA!: TechItem;
  let itemB!: TechItem;
  try {
    [itemA, itemB] = await Promise.all([fetchTechById(a), fetchTechById(b)]);
  } catch {
    notFound();
  }

  // 비교 행 정의
  type FieldKey = keyof TechItem;
  const compareFields: { label: string; key: FieldKey; format?: (v: unknown) => string }[] = [
    { label: "카테고리", key: "category", format: (v) => CATEGORY_LABELS[v as keyof typeof CATEGORY_LABELS] ?? String(v) },
    { label: "상태", key: "status" },
    { label: "출시일", key: "tech_released_at", format: (v) => v ? new Date(v as string).toLocaleDateString("ko-KR", { year: "numeric", month: "long" }) : "—" },
    { label: "사이트 등록일", key: "created_at", format: (v) => new Date(v as string).toLocaleDateString("ko-KR") },
    { label: "최종 수정일", key: "updated_at", format: (v) => new Date(v as string).toLocaleDateString("ko-KR") },
    { label: "한 줄 요약", key: "summary", format: (v) => (v as string | null) ?? "—" },
  ];

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
      {/* 뒤로가기 */}
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-6"
      >
        ← 목록으로
      </Link>

      <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-8">기술 비교</h1>

      {/* 헤더: 제목 나란히 */}
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 mb-6">
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <Link href={`/tech/${itemA.id}`} className="font-semibold text-slate-900 dark:text-slate-100 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors line-clamp-2">
            {itemA.title}
          </Link>
          <div className="mt-2">
            <StatusBadge status={itemA.status} />
          </div>
        </div>
        <span className="text-slate-400 dark:text-slate-500 font-bold text-lg">vs</span>
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
          <Link href={`/tech/${itemB.id}`} className="font-semibold text-slate-900 dark:text-slate-100 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors line-clamp-2">
            {itemB.title}
          </Link>
          <div className="mt-2">
            <StatusBadge status={itemB.status} />
          </div>
        </div>
      </div>

      {/* 비교 테이블 */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
        <table className="w-full text-sm">
          <colgroup>
            <col className="w-1/4" />
            <col className="w-[37.5%]" />
            <col className="w-[37.5%]" />
          </colgroup>
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">항목</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-indigo-600 dark:text-indigo-400">{itemA.title}</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-indigo-600 dark:text-indigo-400">{itemB.title}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {compareFields.map(({ label, key, format }) => {
              const valA = itemA[key];
              const valB = itemB[key];
              const displayA = format ? format(valA) : String(valA ?? "—");
              const displayB = format ? format(valB) : String(valB ?? "—");
              const isDifferent = displayA !== displayB;
              return (
                <tr key={key} className={isDifferent ? "bg-amber-50/50 dark:bg-amber-900/10" : ""}>
                  <td className="px-4 py-3 font-medium text-slate-600 dark:text-slate-400 text-xs">{label}</td>
                  <td className={`px-4 py-3 text-slate-800 dark:text-slate-200 ${isDifferent ? "font-medium" : ""}`}>
                    {key === "status" ? <StatusBadge status={valA as Status} /> : displayA}
                  </td>
                  <td className={`px-4 py-3 text-slate-800 dark:text-slate-200 ${isDifferent ? "font-medium" : ""}`}>
                    {key === "status" ? <StatusBadge status={valB as Status} /> : displayB}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 상세 설명 비교 */}
      {(itemA.description || itemB.description) && (
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">{itemA.title} — 상세 설명</h3>
            <div className="rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-4 py-3 text-sm text-slate-700 dark:text-slate-300 whitespace-pre-line min-h-[80px]">
              {itemA.description ?? "—"}
            </div>
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">{itemB.title} — 상세 설명</h3>
            <div className="rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-4 py-3 text-sm text-slate-700 dark:text-slate-300 whitespace-pre-line min-h-[80px]">
              {itemB.description ?? "—"}
            </div>
          </div>
        </div>
      )}

      {/* 원본 링크 */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
        <a href={itemA.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 text-xs text-indigo-600 dark:text-indigo-400 hover:underline">
          {itemA.title} 원본 출처 →
        </a>
        <a href={itemB.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 text-xs text-indigo-600 dark:text-indigo-400 hover:underline">
          {itemB.title} 원본 출처 →
        </a>
      </div>
    </div>
  );
}
