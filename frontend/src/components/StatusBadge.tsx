import type { Status } from "@/lib/types";
import { STATUS_LABELS } from "@/lib/types";

interface StatusBadgeProps {
  status: Status;
  className?: string;
}

const STATUS_STYLES: Record<Status, string> = {
  active:
    "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  stable:
    "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  deprecated:
    "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  experimental:
    "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
};

export default function StatusBadge({ status, className = "" }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_STYLES[status]} ${className}`}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}
