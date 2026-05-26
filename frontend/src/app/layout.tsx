import type { Metadata } from "next";
import "@/styles/globals.css";
import Link from "next/link";
import SearchBar from "@/components/SearchBar";

export const metadata: Metadata = {
  title: {
    default: "AI 기술 트래커",
    template: "%s | AI 기술 트래커",
  },
  description: "AI를 잘 활용하는 방법, 매일 업데이트. AI 스킬, 에이전트, 하네스, 프롬프팅 기법을 한눈에.",
  openGraph: {
    title: "AI 기술 트래커",
    description: "AI를 잘 활용하는 방법, 매일 업데이트",
    type: "website",
    locale: "ko_KR",
  },
  alternates: {
    types: {
      "application/atom+xml": "/feed.xml",
    },
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body>
        <div className="min-h-screen flex flex-col">
          {/* 헤더 */}
          <header className="sticky top-0 z-40 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
            <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
              <div className="flex h-14 items-center justify-between gap-4">
                {/* 로고 */}
                <Link
                  href="/"
                  className="flex items-center gap-2 text-lg font-bold text-indigo-600 dark:text-indigo-400 whitespace-nowrap"
                >
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23-.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
                    />
                  </svg>
                  AI 기술 트래커
                </Link>

                {/* 검색 (중간 크기 이상) */}
                <div className="hidden sm:flex flex-1 max-w-sm">
                  <SearchBar />
                </div>

                {/* 네비게이션 링크 */}
                <nav className="flex items-center gap-3 text-sm font-medium text-slate-600 dark:text-slate-300">
                  <Link
                    href="/deprecated"
                    className="hidden md:block hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                  >
                    지원 종료
                  </Link>
                  <Link
                    href="/admin"
                    className="rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-1 text-xs hover:border-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                  >
                    관리자
                  </Link>
                </nav>
              </div>
            </div>
          </header>

          {/* 메인 */}
          <main className="flex-1">
            {children}
          </main>

          {/* 푸터 */}
          <footer className="border-t border-slate-200 dark:border-slate-800 py-8 text-center text-xs text-slate-400 dark:text-slate-500">
            <div className="mx-auto max-w-6xl px-4">
              <p>AI 기술 트래커 — AI를 더 잘 활용하는 방법을 매일 업데이트합니다</p>
              <p className="mt-1">
                백엔드:{" "}
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-slate-600 dark:hover:text-slate-300"
                >
                  API 문서
                </a>
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
