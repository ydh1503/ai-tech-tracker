import Link from "next/link";

interface DeprecatedBannerProps {
  deprecatedByTitle: string | null;
  deprecatedById: string | null;
  deprecatedReason: string | null;
}

export default function DeprecatedBanner({
  deprecatedByTitle,
  deprecatedById,
  deprecatedReason,
}: DeprecatedBannerProps) {
  return (
    <div className="rounded-xl border border-red-300 bg-red-50 dark:bg-red-950 dark:border-red-700 p-4 mb-6">
      <div className="flex items-start gap-3">
        {/* 경고 아이콘 */}
        <svg
          className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-500"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
          />
        </svg>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-red-700 dark:text-red-300">
            이 기술은 더 이상 권장되지 않습니다
          </p>

          {deprecatedByTitle && deprecatedById && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              대신 →{" "}
              <Link
                href={`/tech/${deprecatedById}`}
                className="font-semibold underline hover:text-red-800 dark:hover:text-red-200 transition-colors"
              >
                {deprecatedByTitle}
              </Link>{" "}
              사용을 권장합니다
            </p>
          )}

          {deprecatedReason && (
            <p className="mt-2 text-xs text-red-500 dark:text-red-400 leading-relaxed">
              {deprecatedReason}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
