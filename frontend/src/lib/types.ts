export type Category =
  | "skills"
  | "harness"
  | "agents"
  | "orchestration"
  | "integration"
  | "prompting"
  | "infra"
  | "claude_code";

export type Status = "active" | "stable" | "deprecated" | "experimental";

export interface TechItem {
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
  deprecated_by_title: string | null;
  deprecated_reason: string | null;
  deprecated_at: string | null;
  /** 해당 기술 자체의 최초 출시일 (사이트 등록일과 별개) */
  tech_released_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ReviewQueueItem {
  id: string;
  tech_item: TechItem;
  reason: string;
  detected_at: string;
}

export interface CategoryCount {
  category: Category;
  count: number;
  active_count: number;
  deprecated_count: number;
}


export const CATEGORY_LABELS: Record<Category, string> = {
  skills: "스킬",
  harness: "하네스",
  agents: "에이전트",
  orchestration: "오케스트레이션",
  integration: "인테그레이션",
  prompting: "프롬프팅",
  infra: "인프라",
  claude_code: "Claude Code",
};

export const STATUS_LABELS: Record<Status, string> = {
  active: "활성",
  stable: "안정",
  deprecated: "지원 종료",
  experimental: "실험적",
};

export interface CategoryMeta {
  label: string;
  description: string;
  examples: string[];
}

export const CATEGORY_META: Record<Category, CategoryMeta> = {
  skills: {
    label: "스킬",
    description:
      "AI가 수행할 수 있는 능력 단위. 특정 작업을 처리하는 플러그인이나 도구 형태로, AI의 기능을 목적별로 확장한다.",
    examples: ["Code Review Skill", "PDF Skill", "PPTX Skill", "Web Search Skill"],
  },
  harness: {
    label: "하네스",
    description:
      "AI를 특정 워크플로에 실행하고 통제하는 프레임워크·실행환경. 에이전트가 동작하는 규칙과 컨텍스트를 정의한다.",
    examples: ["Claude Code Harness", "LangChain", "LlamaIndex"],
  },
  agents: {
    label: "에이전트",
    description:
      "자율적으로 태스크를 계획하고 실행하는 AI 시스템. 사람의 개입 없이 다단계 작업을 처리하며, 필요 시 도구를 호출한다.",
    examples: ["Claude Agent SDK", "AutoGPT", "CrewAI", "Devin"],
  },
  orchestration: {
    label: "오케스트레이션",
    description:
      "여러 AI 에이전트나 파이프라인을 조율하는 방법. 각 에이전트의 역할을 분담하고 결과를 통합한다.",
    examples: ["Multi-agent", "AutoGen", "Swarm", "CrewAI Flows"],
  },
  integration: {
    label: "인테그레이션",
    description:
      "AI와 외부 도구·서비스·데이터를 연결하는 방법. 표준 프로토콜 또는 커스텀 API로 AI의 접근 범위를 확장한다.",
    examples: ["MCP (Model Context Protocol)", "Tool Use", "RAG", "Function Calling"],
  },
  prompting: {
    label: "프롬프팅",
    description:
      "AI에서 더 나은 결과를 얻기 위한 입력 설계 기법. 모델 동작을 유도하는 패턴과 전략을 다룬다.",
    examples: ["Chain of Thought", "ReAct", "Few-shot", "Prompt Caching", "System Prompts"],
  },
  infra: {
    label: "인프라 / 운영",
    description:
      "AI 시스템의 배포·운영·비용·품질 관리. 프로덕션 환경에서 AI를 안정적으로 운영하기 위한 기반 기술.",
    examples: ["토큰 최적화", "비용 모니터링", "LLMOps", "관측성(Observability)"],
  },
  claude_code: {
    label: "Claude Code",
    description:
      "Anthropic의 Claude Code CLI 관련 공식 업데이트. 스킬·훅·MCP 서버 연동·설정·slash command 등 Claude Code를 더 잘 활용하기 위한 정보.",
    examples: ["새 스킬 릴리즈", "MCP 서버 업데이트", "hooks 설정", "settings.json 변경", "slash command 추가"],
  },
};
