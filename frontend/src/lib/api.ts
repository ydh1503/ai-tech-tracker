import type {
  TechItem,
  PaginatedResponse,
  ReviewQueueItem,
  CategoryCount,
  Category,
  Status,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    next: { revalidate: 60 },  // 기본값: 60초 캐시 (options의 next로 덮어쓸 수 있음)
    ...options,
    headers,  // headers는 항상 마지막에 (항상 override)
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API 오류 ${res.status}: ${text}`);
  }

  return res.json() as Promise<T>;
}

// ─── 백엔드 응답 타입 (내부용) ──────────────────────────────────────────────────

/**
 * GET /api/tech/{id} 응답 — TechItemResponse (전체 필드 포함)
 * description, deprecated_by_item, deprecated_at 포함
 */
interface BackendTechItem {
  id: string;
  title: string;
  description: string | null;
  raw_content: string | null;
  summary: string | null;
  category: Category;
  status: Status;
  official_url: string | null;
  source_url: string;
  deprecated_by: string | null;
  deprecated_by_item: { id: string; title: string; source_url: string; status: Status } | null;
  deprecated_reason: string | null;
  deprecated_at: string | null;
  tech_released_at: string | null;
  created_at: string;
  updated_at: string;
}

/** 상세 응답 정규화 (deprecated_by_item → deprecated_by_title 변환) */
function normalizeTechItem(item: BackendTechItem): TechItem {
  return {
    ...item,
    raw_content: item.raw_content,
    deprecated_by_title: item.deprecated_by_item?.title ?? null,
  };
}


/**
 * GET /api/tech, GET /api/tech/search 응답 — TechItemList (요약 필드만)
 * description, deprecated_by_item, deprecated_at 없음
 */
interface BackendTechListItem {
  id: string;
  title: string;
  summary: string | null;
  category: Category;
  status: Status;
  official_url: string | null;
  source_url: string;
  deprecated_by: string | null;
  deprecated_reason: string | null;
  tech_released_at: string | null;
  created_at: string;
  updated_at: string;
}

/** 목록 응답 정규화 — 없는 필드는 null로 채움 */
function normalizeTechListItem(item: BackendTechListItem): TechItem {
  return {
    id: item.id,
    title: item.title,
    description: null,          // TechItemList에 없음 (상세 페이지에서만 표시)
    raw_content: null,          // TechItemList에 없음 (상세 페이지에서만 표시)
    summary: item.summary,
    category: item.category,
    status: item.status,
    official_url: item.official_url,
    source_url: item.source_url,
    deprecated_by: item.deprecated_by,
    deprecated_by_title: null,  // TechItemList에 deprecated_by_item 없음
    deprecated_reason: item.deprecated_reason,
    deprecated_at: null,        // TechItemList에 없음
    tech_released_at: item.tech_released_at,
    created_at: item.created_at,
    updated_at: item.updated_at,
  };
}

interface BackendPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface BackendReviewQueueItem {
  id: string;
  tech_item: BackendTechListItem;  // ReviewQueueItem은 TechItemList 사용
  reason: string;
  detected_at: string;
  reviewed: boolean;
  reviewed_at: string | null;
  approved: boolean | null;
}

interface BackendCategoryCount {
  category: Category;
  count: number;
  active_count: number;
  deprecated_count: number;
}

interface BackendTimelineItem {
  id: string;
  title: string;
  summary: string | null;
  category: Category;
  status: Status;
  source_url: string;
  tech_released_at: string | null;
  updated_at: string;
  created_at: string;
}

// ─── 공개 API ──────────────────────────────────────────────────────────────────

export interface FetchTechListParams {
  page?: number;
  size?: number;
  category?: Category;
  status?: Status;
  q?: string;
  created_after?: string;
}

export async function fetchTechList(
  params: FetchTechListParams = {},
): Promise<PaginatedResponse<TechItem>> {
  const qs = new URLSearchParams();
  if (params.page !== undefined) qs.set("page", String(params.page));
  if (params.size !== undefined) qs.set("size", String(params.size));
  if (params.category) qs.set("category", params.category);
  if (params.status) qs.set("status", params.status);
  if (params.q) qs.set("q", params.q);
  if (params.created_after) qs.set("created_after", params.created_after);
  const query = qs.toString() ? `?${qs.toString()}` : "";
  const raw = await apiFetch<BackendPaginatedResponse<BackendTechListItem>>(`/api/tech${query}`);
  return {
    ...raw,
    items: raw.items.map(normalizeTechListItem),
  };
}

export async function fetchTechById(id: string): Promise<TechItem> {
  const raw = await apiFetch<BackendTechItem>(`/api/tech/${id}`);
  return normalizeTechItem(raw);
}

export async function fetchDeprecated(): Promise<TechItem[]> {
  const raw = await apiFetch<BackendPaginatedResponse<BackendTechItem>>(
    `/api/tech/deprecated?size=100`,
  );
  return raw.items.map(normalizeTechItem);
}

export async function searchTech(
  q: string,
  page?: number,
): Promise<PaginatedResponse<TechItem>> {
  const qs = new URLSearchParams({ q });
  if (page !== undefined) qs.set("page", String(page));
  const raw = await apiFetch<BackendPaginatedResponse<BackendTechListItem>>(
    `/api/tech/search?${qs.toString()}`,
  );
  return {
    ...raw,
    items: raw.items.map(normalizeTechListItem),
  };
}

export async function fetchCategories(): Promise<CategoryCount[]> {
  const raw = await apiFetch<BackendCategoryCount[]>(`/api/categories`);
  return raw.map((c) => ({
    category: c.category,
    count: c.count,
    active_count: c.active_count,
    deprecated_count: c.deprecated_count,
  }));
}

export async function fetchTimeline(): Promise<TechItem[]> {
  const raw = await apiFetch<BackendTimelineItem[]>(`/api/feed/timeline`);
  return raw.map((item) => ({
    id: item.id,
    title: item.title,
    description: null,
    raw_content: null,
    summary: item.summary,
    category: item.category,
    status: item.status,
    official_url: null,
    source_url: item.source_url,
    deprecated_by: null,
    deprecated_by_title: null,
    deprecated_reason: null,
    deprecated_at: null,
    tech_released_at: item.tech_released_at,
    created_at: item.created_at,
    updated_at: item.updated_at,
  }));
}

// ─── 관리자 API ────────────────────────────────────────────────────────────────

export async function fetchAdminQueue(
  token: string,
): Promise<ReviewQueueItem[]> {
  const raw = await apiFetch<BackendPaginatedResponse<BackendReviewQueueItem>>(
    `/api/admin/queue?reviewed=false&size=100`,
    undefined,
    token,
  );
  return raw.items.map((item) => ({
    id: item.id,
    tech_item: normalizeTechListItem(item.tech_item),
    reason: item.reason,
    detected_at: item.detected_at,
  }));
}

export interface ApproveDeprecatedBody {
  deprecated_by_id?: string;
  reason: string;
}

export async function approveDeprecated(
  id: string,
  token: string,
  body: ApproveDeprecatedBody,
): Promise<void> {
  await apiFetch<unknown>(
    `/api/admin/queue/${id}/approve`,
    {
      method: "POST",
      body: JSON.stringify(body),
      next: { revalidate: 0 },
    },
    token,
  );
}

export async function rejectDeprecated(
  id: string,
  token: string,
  reason?: string,
): Promise<void> {
  await apiFetch<unknown>(
    `/api/admin/queue/${id}/reject`,
    {
      method: "POST",
      body: JSON.stringify({ reason: reason ?? null }),
      next: { revalidate: 0 },
    },
    token,
  );
}

export interface AddTechItemBody {
  title: string;
  description?: string;
  summary?: string;
  category: Category;
  status: Status;
  official_url?: string;
  source_url: string;
}

export async function addTechItem(
  token: string,
  data: AddTechItemBody,
): Promise<TechItem> {
  const raw = await apiFetch<BackendTechItem>(
    `/api/admin/tech`,
    {
      method: "POST",
      body: JSON.stringify(data),
      next: { revalidate: 0 },
    },
    token,
  );
  return normalizeTechItem(raw);
}

export interface UpdateTechItemBody {
  title?: string;
  description?: string;
  summary?: string;
  category?: Category;
  status?: Status;
  official_url?: string;
  deprecated_reason?: string;
}

export async function updateTechItem(
  id: string,
  token: string,
  data: UpdateTechItemBody,
): Promise<TechItem> {
  const raw = await apiFetch<BackendTechItem>(
    `/api/admin/tech/${id}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
      next: { revalidate: 0 },
    },
    token,
  );
  return normalizeTechItem(raw);
}
