"use client";

import { useState, useCallback, useRef } from "react";
import type { ReviewQueueItem, Category, Status } from "@/lib/types";
import { CATEGORY_LABELS, STATUS_LABELS } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import {
  fetchAdminQueue,
  fetchTechById,
  approveDeprecated,
  rejectDeprecated,
  addTechItem,
  updateTechItem,
  fetchCrawlLogs,
  type AddTechItemBody,
  type UpdateTechItemBody,
  type CrawlLogItem,
} from "@/lib/api";

// ─── 검토 큐 카드 ──────────────────────────────────────────────────────────────

interface QueueItemCardProps {
  item: ReviewQueueItem;
  onApprove: (id: string, reason: string, deprecatedById?: string) => void;
  onReject: (id: string) => void;
  loading: boolean;
}

function QueueItemCard({ item, onApprove, onReject, loading }: QueueItemCardProps) {
  const [reason, setReason] = useState(item.reason);
  const [deprecatedById, setDeprecatedById] = useState("");
  const [replacementQuery, setReplacementQuery] = useState("");
  const [replacementResults, setReplacementResults] = useState<{ id: string; title: string }[]>([]);
  const [replacementLabel, setReplacementLabel] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleReplacementSearch = (q: string) => {
    setReplacementQuery(q);
    setReplacementLabel(q);
    setDeprecatedById("");
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (!q.trim()) { setReplacementResults([]); setShowDropdown(false); return; }
    searchTimeout.current = setTimeout(async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/tech/search?q=${encodeURIComponent(q)}&size=5`);
        const data = await res.json();
        setReplacementResults(data.items ?? []);
        setShowDropdown(true);
      } catch { setReplacementResults([]); }
    }, 300);
  };

  return (
    <div className="rounded-xl border border-yellow-200 dark:border-yellow-800 bg-white dark:bg-slate-800 p-5">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="min-w-0">
          <p className="text-xs text-slate-400 dark:text-slate-500 mb-1">
            {CATEGORY_LABELS[item.tech_item.category]}
          </p>
          <h3 className="font-semibold text-slate-900 dark:text-slate-100">
            {item.tech_item.title}
          </h3>
          {item.tech_item.summary && (
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400 line-clamp-2">
              {item.tech_item.summary}
            </p>
          )}
        </div>
        <StatusBadge status={item.tech_item.status} className="flex-shrink-0" />
      </div>

      {/* 감지 이유 (수정 가능) */}
      <div className="mb-4">
        <label className="block text-xs font-semibold text-yellow-700 dark:text-yellow-300 mb-1">
          Deprecated 확정 사유 (필수)
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={2}
          className="w-full rounded-lg border border-yellow-200 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20 px-3 py-2 text-xs text-yellow-900 dark:text-yellow-200 focus:outline-none focus:ring-2 focus:ring-yellow-400 resize-none"
        />
      </div>

      {/* 대체 기술 검색 */}
      <div className="mb-4 relative">
        <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
          대체 기술 검색 (선택)
        </label>
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={replacementLabel}
            onChange={(e) => handleReplacementSearch(e.target.value)}
            onFocus={() => replacementResults.length > 0 && setShowDropdown(true)}
            className="flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-3 py-2 text-xs text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            placeholder="기술명으로 검색..."
          />
          {deprecatedById && (
            <button
              type="button"
              onClick={() => { setDeprecatedById(""); setReplacementLabel(""); setReplacementResults([]); }}
              className="text-xs text-slate-400 hover:text-red-500 transition-colors"
            >
              ×
            </button>
          )}
        </div>
        {showDropdown && replacementResults.length > 0 && (
          <ul className="absolute z-10 mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-lg max-h-48 overflow-auto">
            {replacementResults.map((r) => (
              <li key={r.id}>
                <button
                  type="button"
                  onClick={() => { setDeprecatedById(r.id); setReplacementLabel(r.title); setShowDropdown(false); }}
                  className="w-full text-left px-3 py-2 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 truncate"
                >
                  {r.title}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex items-center justify-between gap-3">
        <span className="text-xs text-slate-400 dark:text-slate-500">
          감지 일시: {new Date(item.detected_at).toLocaleString("ko-KR")}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => onReject(item.id)}
            disabled={loading}
            className="rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:border-slate-400 transition-colors disabled:opacity-50"
          >
            거부
          </button>
          <button
            onClick={() => onApprove(item.id, reason.trim(), deprecatedById.trim() || undefined)}
            disabled={loading || !reason.trim()}
            className="rounded-lg bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
          >
            Deprecated 확정
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── 항목 추가 폼 ──────────────────────────────────────────────────────────────

interface AddItemFormProps {
  token: string;
  onSuccess: () => void;
}

const CATEGORIES: Category[] = [
  "skills", "harness", "agents", "orchestration", "integration", "prompting", "infra", "claude_code",
];
const STATUSES: Status[] = ["active", "stable", "deprecated", "experimental"];

function AddItemForm({ token, onSuccess }: AddItemFormProps) {
  const [form, setForm] = useState<AddTechItemBody>({
    title: "",
    description: "",
    summary: "",
    category: "skills",
    status: "active",
    official_url: "",
    source_url: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
    setSuccess(false);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!form.title || !form.source_url) {
      setError("제목과 원본 출처 URL은 필수입니다.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await addTechItem(token, form);
      setSuccess(true);
      setForm({
        title: "",
        description: "",
        summary: "",
        category: "skills",
        status: "active",
        official_url: "",
        source_url: "",
      });
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "추가 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 제목 */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            제목 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="title"
            value={form.title}
            onChange={handleChange}
            className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Claude Skill SDK"
          />
        </div>

        {/* 카테고리 */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            카테고리
          </label>
          <select
            name="category"
            value={form.category}
            onChange={handleChange}
            className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {CATEGORY_LABELS[cat]}
              </option>
            ))}
          </select>
        </div>

        {/* 상태 */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            상태
          </label>
          <select
            name="status"
            value={form.status}
            onChange={handleChange}
            className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </div>

        {/* 공식 URL */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            공식 URL
          </label>
          <input
            type="url"
            name="official_url"
            value={form.official_url}
            onChange={handleChange}
            className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="https://docs.anthropic.com/..."
          />
        </div>
      </div>

      {/* 원본 출처 URL */}
      <div>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
          원본 출처 URL <span className="text-red-500">*</span>
        </label>
        <input
          type="url"
          name="source_url"
          value={form.source_url}
          onChange={handleChange}
          className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="https://..."
        />
      </div>

      {/* 한 줄 요약 */}
      <div>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
          한 줄 요약
        </label>
        <input
          type="text"
          name="summary"
          value={form.summary}
          onChange={handleChange}
          maxLength={500}
          className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="한 줄로 요약 (최대 500자)"
        />
      </div>

      {/* 상세 설명 */}
      <div>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
          상세 설명
        </label>
        <textarea
          name="description"
          value={form.description}
          onChange={handleChange}
          rows={4}
          className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
          placeholder="상세 설명을 입력하세요..."
        />
      </div>

      {/* 오류 / 성공 메시지 */}
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
      )}
      {success && (
        <p className="text-xs text-green-600 dark:text-green-400">항목이 성공적으로 추가되었습니다.</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white py-2 text-sm font-medium transition-colors disabled:opacity-50"
      >
        {loading ? "추가 중..." : "항목 추가"}
      </button>
    </form>
  );
}

// ─── 항목 수정 폼 ──────────────────────────────────────────────────────────────

interface EditItemFormProps {
  token: string;
}

function EditItemForm({ token }: EditItemFormProps) {
  const [itemId, setItemId] = useState("");
  const [form, setForm] = useState<UpdateTechItemBody>({
    title: "",
    description: "",
    summary: "",
    category: "skills",
    status: "active",
    official_url: "",
    deprecated_reason: "",
  });
  const [loadingItem, setLoadingItem] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [itemLoaded, setItemLoaded] = useState(false);

  function handleFormChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setSaveError(null);
    setSaveSuccess(false);
  }

  async function handleLoad() {
    const id = itemId.trim();
    if (!id) return;
    setLoadingItem(true);
    setLoadError(null);
    setItemLoaded(false);
    setSaveSuccess(false);
    setSaveError(null);
    try {
      const item = await fetchTechById(id);
      setForm({
        title: item.title,
        description: item.description ?? "",
        summary: item.summary ?? "",
        category: item.category,
        status: item.status,
        official_url: item.official_url ?? "",
        deprecated_reason: item.deprecated_reason ?? "",
      });
      setItemLoaded(true);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "항목 불러오기 실패");
    } finally {
      setLoadingItem(false);
    }
  }

  async function handleSave(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const id = itemId.trim();
    if (!id) {
      setSaveError("항목 ID를 입력하세요.");
      return;
    }
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      // 빈 문자열 필드는 전송하되 undefined는 제외
      const payload: UpdateTechItemBody = {};
      if (form.title !== undefined) payload.title = form.title;
      if (form.description !== undefined) payload.description = form.description;
      if (form.summary !== undefined) payload.summary = form.summary;
      if (form.category !== undefined) payload.category = form.category;
      if (form.status !== undefined) payload.status = form.status;
      if (form.official_url !== undefined) payload.official_url = form.official_url;
      if (form.deprecated_reason !== undefined) payload.deprecated_reason = form.deprecated_reason;
      await updateTechItem(id, token, payload);
      setSaveSuccess(true);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "수정 실패");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* ID 불러오기 */}
      <div>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
          항목 ID <span className="text-red-500">*</span>
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={itemId}
            onChange={(e) => {
              setItemId(e.target.value);
              setItemLoaded(false);
              setLoadError(null);
            }}
            className="flex-1 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="수정할 항목의 UUID를 입력하세요"
          />
          <button
            type="button"
            onClick={handleLoad}
            disabled={loadingItem || !itemId.trim()}
            className="rounded-lg bg-slate-600 hover:bg-slate-700 text-white px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
          >
            {loadingItem ? "불러오는 중..." : "불러오기"}
          </button>
        </div>
        {loadError && (
          <p className="mt-1 text-xs text-red-600 dark:text-red-400">{loadError}</p>
        )}
        {itemLoaded && (
          <p className="mt-1 text-xs text-green-600 dark:text-green-400">항목을 불러왔습니다. 아래에서 수정 후 저장하세요.</p>
        )}
      </div>

      {/* 수정 폼 */}
      <form onSubmit={handleSave} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* 제목 */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              제목
            </label>
            <input
              type="text"
              name="title"
              value={form.title ?? ""}
              onChange={handleFormChange}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Claude Skill SDK"
            />
          </div>

          {/* 카테고리 */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              카테고리
            </label>
            <select
              name="category"
              value={form.category ?? "skills"}
              onChange={handleFormChange}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {CATEGORY_LABELS[cat]}
                </option>
              ))}
            </select>
          </div>

          {/* 상태 */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              상태
            </label>
            <select
              name="status"
              value={form.status ?? "active"}
              onChange={handleFormChange}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </div>

          {/* 공식 URL */}
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              공식 URL
            </label>
            <input
              type="url"
              name="official_url"
              value={form.official_url ?? ""}
              onChange={handleFormChange}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="https://docs.anthropic.com/..."
            />
          </div>
        </div>

        {/* 한 줄 요약 */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            한 줄 요약
          </label>
          <input
            type="text"
            name="summary"
            value={form.summary ?? ""}
            onChange={handleFormChange}
            maxLength={500}
            className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="한 줄로 요약 (최대 500자)"
          />
        </div>

        {/* 상세 설명 */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            상세 설명
          </label>
          <textarea
            name="description"
            value={form.description ?? ""}
            onChange={handleFormChange}
            rows={4}
            className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y"
            placeholder="상세 설명을 입력하세요..."
          />
        </div>

        {/* Deprecated 사유 */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
            Deprecated 사유
          </label>
          <input
            type="text"
            name="deprecated_reason"
            value={form.deprecated_reason ?? ""}
            onChange={handleFormChange}
            className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="더 이상 사용되지 않는 이유 (선택)"
          />
        </div>

        {/* 오류 / 성공 메시지 */}
        {saveError && (
          <p className="text-xs text-red-600 dark:text-red-400">{saveError}</p>
        )}
        {saveSuccess && (
          <p className="text-xs text-green-600 dark:text-green-400">항목이 성공적으로 수정되었습니다.</p>
        )}

        <button
          type="submit"
          disabled={saving || !itemId.trim()}
          className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white py-2 text-sm font-medium transition-colors disabled:opacity-50"
        >
          {saving ? "저장 중..." : "수정 저장"}
        </button>
      </form>
    </div>
  );
}

// ─── 메인 관리자 페이지 ────────────────────────────────────────────────────────

export default function AdminPage() {
  const [token, setToken] = useState("");
  const [submittedToken, setSubmittedToken] = useState("");
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [loadingQueue, setLoadingQueue] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [queueError, setQueueError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"queue" | "add" | "edit" | "logs">("queue");
  const [crawlLoading, setCrawlLoading] = useState(false);
  const [crawlResult, setCrawlResult] = useState<string | null>(null);
  const [crawlLogs, setCrawlLogs] = useState<CrawlLogItem[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [reprocessLoading, setReprocessLoading] = useState(false);
  const [reprocessResult, setReprocessResult] = useState<string | null>(null);

  const loadQueue = useCallback(async (t: string) => {
    if (!t) return;
    setLoadingQueue(true);
    setQueueError(null);
    try {
      const items = await fetchAdminQueue(t);
      setQueue(items);
    } catch (err) {
      setQueueError(err instanceof Error ? err.message : "큐 로드 실패");
    } finally {
      setLoadingQueue(false);
    }
  }, []);

  const loadCrawlLogs = useCallback(async (t: string) => {
    if (!t) return;
    setLogsLoading(true);
    try {
      const res = await fetchCrawlLogs(t, 1);
      setCrawlLogs(res.items);
    } catch {
      setCrawlLogs([]);
    } finally {
      setLogsLoading(false);
    }
  }, []);

  function handleTokenSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const t = token.trim();
    if (!t) return;
    setSubmittedToken(t);
    loadQueue(t);
    loadCrawlLogs(t);
  }

  async function handleReprocessDescriptions() {
    setReprocessLoading(true);
    setReprocessResult(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/admin/tech/reprocess-descriptions?limit=50`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${submittedToken}`,
          },
        },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail ?? `HTTP ${res.status}`);
      }
      const data = await res.json();
      setReprocessResult(data.message ?? "재처리 완료");
    } catch (err) {
      setReprocessResult(err instanceof Error ? err.message : "재처리 실패");
    } finally {
      setReprocessLoading(false);
    }
  }

  async function handleTriggerCrawl() {
    setCrawlLoading(true);
    setCrawlResult(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/admin/crawl/trigger`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${submittedToken}`,
          },
        },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail ?? `HTTP ${res.status}`);
      }
      setCrawlResult("크롤링이 시작되었습니다.");
    } catch (err) {
      setCrawlResult(err instanceof Error ? err.message : "크롤 트리거 실패");
    } finally {
      setCrawlLoading(false);
    }
  }

  async function handleApprove(id: string, reason: string, deprecatedById?: string) {
    setActionLoading(true);
    try {
      await approveDeprecated(id, submittedToken, { reason, deprecated_by_id: deprecatedById });
    } catch (err) {
      alert(err instanceof Error ? err.message : "승인 실패");
      setActionLoading(false);
      return;
    }
    // 승인 성공 → 큐 새로고침 (실패해도 승인 자체는 완료됨)
    try {
      await loadQueue(submittedToken);
    } catch {
      alert("승인은 완료됐지만 목록 새로고침에 실패했습니다. 페이지를 새로고침 해주세요.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleReject(id: string) {
    setActionLoading(true);
    try {
      await rejectDeprecated(id, submittedToken);
    } catch (err) {
      alert(err instanceof Error ? err.message : "거부 실패");
      setActionLoading(false);
      return;
    }
    // 거부 성공 → 큐 새로고침
    try {
      await loadQueue(submittedToken);
    } catch {
      alert("거부는 완료됐지만 목록 새로고침에 실패했습니다. 페이지를 새로고침 해주세요.");
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
      {/* 헤더 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          관리자 페이지
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Deprecated 검토 큐 관리 및 수동 항목 추가
        </p>
      </div>

      {/* 토큰 입력 */}
      <form onSubmit={handleTokenSubmit} className="mb-8">
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-5">
          <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
            관리자 토큰
          </label>
          <div className="flex gap-2">
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="flex-1 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="관리자 토큰을 입력하세요"
            />
            <button
              type="submit"
              className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 text-sm font-medium transition-colors"
            >
              인증
            </button>
          </div>
          {submittedToken && (
            <p className="mt-2 text-xs text-green-600 dark:text-green-400">
              토큰이 설정되었습니다. 검토 큐를 로드했습니다.
            </p>
          )}
        </div>
      </form>

      {submittedToken && (
        <>
          {/* 탭 */}
          <div className="flex gap-1 mb-6 rounded-xl bg-slate-100 dark:bg-slate-800 p-1">
            <button
              onClick={() => setActiveTab("queue")}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors
                ${activeTab === "queue"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
            >
              검토 큐 {queue.length > 0 && `(${queue.length})`}
            </button>
            <button
              onClick={() => setActiveTab("add")}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors
                ${activeTab === "add"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
            >
              항목 추가
            </button>
            <button
              onClick={() => setActiveTab("edit")}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors
                ${activeTab === "edit"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
            >
              항목 수정
            </button>
            <button
              onClick={() => { setActiveTab("logs"); loadCrawlLogs(submittedToken); }}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors
                ${activeTab === "logs"
                  ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                }`}
            >
              크롤 로그
            </button>
          </div>

          {/* 검토 큐 탭 */}
          {activeTab === "queue" && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-slate-700 dark:text-slate-300">
                  검토 큐 {queue.length > 0 && `(${queue.length}건)`}
                </h2>
                <div className="flex items-center gap-3 flex-wrap">
                  {crawlResult && (
                    <span className="text-xs text-green-600 dark:text-green-400">{crawlResult}</span>
                  )}
                  {reprocessResult && (
                    <span className="text-xs text-indigo-600 dark:text-indigo-400">{reprocessResult}</span>
                  )}
                  <button
                    onClick={handleReprocessDescriptions}
                    disabled={reprocessLoading}
                    className="rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
                  >
                    {reprocessLoading ? "생성 중..." : "Description 일괄 생성"}
                  </button>
                  <button
                    onClick={handleTriggerCrawl}
                    disabled={crawlLoading}
                    className="rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50"
                  >
                    {crawlLoading ? "크롤 중..." : "크롤 실행"}
                  </button>
                  <button
                    onClick={() => loadQueue(submittedToken)}
                    disabled={loadingQueue}
                    className="rounded-lg border border-slate-300 dark:border-slate-600 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:border-slate-400 transition-colors disabled:opacity-50"
                  >
                    새로고침
                  </button>
                </div>
              </div>

              {loadingQueue && (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-40 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse" />
                  ))}
                </div>
              )}

              {queueError && (
                <div className="rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950 p-4">
                  <p className="text-sm text-red-600 dark:text-red-400">{queueError}</p>
                  <button
                    onClick={() => loadQueue(submittedToken)}
                    className="mt-2 text-xs text-red-600 dark:text-red-400 underline"
                  >
                    다시 시도
                  </button>
                </div>
              )}

              {!loadingQueue && !queueError && queue.length === 0 && (
                <div className="text-center py-16">
                  <p className="text-slate-400 dark:text-slate-500">
                    검토 대기 중인 항목이 없습니다.
                  </p>
                </div>
              )}

              {!loadingQueue && queue.length > 0 && (
                <div className="space-y-4">
                  {queue.map((item) => (
                    <QueueItemCard
                      key={item.id}
                      item={item}
                      onApprove={handleApprove}
                      onReject={handleReject}
                      loading={actionLoading}
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 항목 추가 탭 */}
          {activeTab === "add" && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-5">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-4">
                수동 항목 추가
              </h2>
              <AddItemForm
                token={submittedToken}
                onSuccess={() => loadQueue(submittedToken)}
              />
            </div>
          )}

          {/* 항목 수정 탭 */}
          {activeTab === "edit" && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-5">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 mb-4">
                항목 수정
              </h2>
              <EditItemForm token={submittedToken} />
            </div>
          )}

          {/* 크롤 로그 탭 */}
          {activeTab === "logs" && (
            <section>
              <h2 className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-4">크롤링 로그</h2>
              {logsLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-16 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse" />
                  ))}
                </div>
              ) : crawlLogs.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-8">크롤 로그가 없습니다.</p>
              ) : (
                <div className="space-y-2">
                  {crawlLogs.map((log) => (
                    <div
                      key={log.id}
                      className={`rounded-xl border px-4 py-3 text-sm flex items-start justify-between gap-3 ${
                        log.error
                          ? "border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20"
                          : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800"
                      }`}
                    >
                      <div className="min-w-0">
                        <p className="font-medium text-slate-800 dark:text-slate-200 truncate">{log.source}</p>
                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
                          {new Date(log.crawled_at).toLocaleString("ko-KR")}
                        </p>
                        {log.error && (
                          <p className="text-xs text-red-600 dark:text-red-400 mt-1 line-clamp-2">{log.error}</p>
                        )}
                      </div>
                      <div className="flex-shrink-0 text-right">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                          log.error
                            ? "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300"
                            : "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300"
                        }`}>
                          {log.error ? "오류" : `+${log.items_added}건`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
