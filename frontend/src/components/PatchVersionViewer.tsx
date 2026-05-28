"use client";

import { useState } from "react";
import type { PatchVersionSummary } from "@/lib/types";

interface PatchVersionViewerProps {
  siblings: PatchVersionSummary[];
  currentId: string;
}

export default function PatchVersionViewer({ siblings, currentId }: PatchVersionViewerProps) {
  const [selectedId, setSelectedId] = useState(currentId);

  if (siblings.length <= 1) return null;

  const selected = siblings.find((s) => s.id === selectedId) ?? siblings[0];
  const isCurrentVersion = selected.id === currentId;

  return (
    <div className="mb-8 rounded-xl border border-indigo-100 dark:border-indigo-900 bg-indigo-50/50 dark:bg-indigo-950/20 p-5">
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-4">
        <svg className="h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z" />
        </svg>
        <span className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">
          버전 히스토리 ({siblings.length}개)
        </span>
      </div>

      {/* 버전 선택 버튼들 */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {siblings.map((s) => (
          <button
            key={s.id}
            onClick={() => setSelectedId(s.id)}
            className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium transition-all
              ${selectedId === s.id
                ? "bg-indigo-600 text-white shadow-sm scale-105"
                : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-600 hover:text-indigo-700 dark:hover:text-indigo-300"
              }`}
          >
            v{s.version_str}
          </button>
        ))}
      </div>

      {/* 선택된 버전 내용 */}
      <div className="rounded-lg bg-white dark:bg-slate-800/80 border border-indigo-100 dark:border-indigo-800 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="font-mono text-sm font-semibold text-slate-900 dark:text-slate-100">
            v{selected.version_str}
            {isCurrentVersion && (
              <span className="ml-2 text-xs font-sans font-normal text-indigo-600 dark:text-indigo-400 bg-indigo-100 dark:bg-indigo-900/40 rounded-full px-2 py-0.5">
                현재 버전
              </span>
            )}
          </span>
          <span className="text-xs text-slate-400 dark:text-slate-500">
            {new Date(selected.updated_at).toLocaleDateString("ko-KR")}
          </span>
        </div>

        {selected.summary && (
          <p className="text-sm font-medium text-slate-800 dark:text-slate-200 mb-3">
            {selected.summary}
          </p>
        )}

        {selected.description ? (
          <div className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-line leading-relaxed max-h-60 overflow-y-auto scrollbar-hide">
            {selected.description}
          </div>
        ) : (
          <p className="text-xs text-slate-400 dark:text-slate-500 italic">상세 내용 없음</p>
        )}

        {!isCurrentVersion && (
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700">
            <a
              href={`/tech/${selected.id}`}
              className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
            >
              이 버전 전체 보기 →
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
