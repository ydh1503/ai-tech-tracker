# -*- coding: utf-8 -*-
"""
각 항목의 상세 설명(description)과 출시일(tech_released_at)을 업데이트한다.
source_url로 항목을 찾아 ID를 조회한 뒤 PATCH한다.
"""
import json
import subprocess

TOKEN = "dev-admin-token-2026"
BASE = "http://localhost:8000"

# source_url -> (description, tech_released_at ISO)
UPDATES = {

# ── PROMPTING ──────────────────────────────────────────────────────────────────

"https://arxiv.org/abs/2210.03629": {
  "tech_released_at": "2022-10-07T00:00:00Z",
  "description": (
    "ReAct(Reason + Act)는 2022년 Google DeepMind 연구팀(Shunyu Yao 등)이 발표한 프롬프팅 기법으로, "
    "대형 언어 모델이 단순히 텍스트를 생성하는 것에서 벗어나 추론(Reasoning)과 행동(Acting)을 번갈아 수행하도록 유도하는 패턴입니다.\n\n"
    "핵심 동작 원리\n"
    "ReAct는 모델이 세 단계를 반복하도록 프롬프트를 구성합니다. "
    "먼저 Thought(추론) 단계에서 '이 질문에 답하려면 X를 먼저 찾아야 한다'와 같이 현재 상황을 분석합니다. "
    "이어서 Action(행동) 단계에서 웹 검색, 계산기 호출, API 조회 등 외부 도구를 실행하고, "
    "Observation(관찰) 단계에서 도구 실행 결과를 받아 다음 추론의 입력으로 사용합니다. "
    "이 사이클을 최종 답변이 나올 때까지 반복합니다.\n\n"
    "왜 중요한가\n"
    "기존 Chain-of-Thought는 내부 추론만 수행하고 외부 정보를 가져올 수 없었습니다. "
    "ReAct는 외부 세계와 상호작용하면서도 추론 과정을 투명하게 공개해 디버깅이 쉽고 신뢰할 수 있습니다. "
    "환각(hallucination)을 줄이는 데 효과적이며, 모델이 '모른다'는 것을 인식하고 실제로 검색해서 확인합니다. "
    "Wikipedia QA, HotpotQA, Fever 등 다양한 벤치마크에서 Chain-of-Thought 단독 대비 최대 10%p 성능 향상을 보였습니다.\n\n"
    "실제 적용\n"
    "LangChain의 create_react_agent, LangGraph의 기본 에이전트 루프, Anthropic의 Tool Use 패턴 모두 ReAct 철학을 기반으로 구현됩니다. "
    "프롬프트에 Thought:, Action:, Observation: 레이블을 명시하고 few-shot 예시를 포함시키면 "
    "GPT-4, Claude, Gemini 등 모든 주요 모델에서 동작합니다. "
    "도구 호출이 지원되는 API에서는 function calling이 ReAct의 Action 단계를 자연스럽게 대체합니다."
  )
},

"https://arxiv.org/abs/2005.14165": {
  "tech_released_at": "2020-05-28T00:00:00Z",
  "description": (
    "Few-shot Prompting은 OpenAI의 GPT-3 논문(Brown et al., 2020)에서 공식적으로 제시된 기법으로, "
    "모델에게 과제 수행 예시를 2~10개 제공함으로써 별도의 파인튜닝 없이 새로운 작업을 수행하게 합니다.\n\n"
    "핵심 원리\n"
    "Few-shot은 '맥락 내 학습(In-Context Learning)'의 한 형태입니다. "
    "Zero-shot은 예시 없이 지시만으로 수행하고, One-shot은 예시 1개, Few-shot은 2~10개를 제공합니다. "
    "예시의 형식, 내용, 순서가 모두 성능에 영향을 미치며, 좋은 예시 선택이 핵심입니다.\n\n"
    "효과적인 예시 구성법\n"
    "예시는 실제 데이터 분포를 대표해야 하며, 긍정/부정 사례를 균형 있게 포함해야 합니다. "
    "형식 일관성이 중요합니다. 입력과 출력의 구분자, 들여쓰기, 마무리 방식이 모든 예시에서 동일해야 합니다. "
    "모델이 패턴을 파악할 수 있을 만큼 다양한 예시를 넣되, 컨텍스트 창을 과도하게 차지하지 않도록 조절합니다.\n\n"
    "한계와 극복\n"
    "예시가 많아지면 비용과 지연이 증가합니다. 이를 해결하기 위해 동적 few-shot 선택(사용자 입력과 유사한 예시만 추출)을 사용합니다. "
    "매우 긴 예시가 필요한 경우 fine-tuning이 더 경제적입니다."
  )
},

"https://arxiv.org/abs/2203.11171": {
  "tech_released_at": "2022-03-21T00:00:00Z",
  "description": (
    "Self-Consistency는 2022년 Google Research(Wang et al.)가 발표한 기법으로, "
    "Chain-of-Thought 프롬프팅의 정확도를 높이기 위해 동일 질문에 대해 여러 추론 경로를 생성하고 "
    "다수결(majority voting)로 최종 답을 선택합니다.\n\n"
    "동작 방식\n"
    "같은 프롬프트를 temperature > 0으로 여러 번 실행(보통 10~40회)합니다. "
    "각 실행은 서로 다른 추론 경로를 거쳐 답에 도달합니다. "
    "최종적으로 가장 많이 등장한 답을 선택합니다. "
    "추론 과정이 달라도 결론이 같다면 그 답이 신뢰할 수 있다는 아이디어를 기반으로 합니다.\n\n"
    "성능\n"
    "GSM8K(수학 문제), SVAMP, AQuA 등 산술 추론 벤치마크에서 단일 Chain-of-Thought 대비 10~20%p 성능 향상을 보였습니다. "
    "CSQA, StrategyQA 같은 상식 추론에서도 유효합니다.\n\n"
    "비용 vs 정확도 트레이드오프\n"
    "샘플 수만큼 API 비용과 지연이 증가합니다. "
    "실시간 응답이 필요한 시스템보다는 고정밀이 요구되는 배치 처리나 의료/법률 판단에 적합합니다. "
    "샘플 수를 5~10개로 제한해도 대부분 이득을 얻을 수 있습니다."
  )
},

"https://openai.com/index/introducing-structured-outputs-in-the-api/": {
  "tech_released_at": "2024-08-06T00:00:00Z",
  "description": (
    "Structured Output(구조화 출력)은 LLM이 정확히 정의된 JSON Schema를 100% 준수하는 응답을 반환하도록 강제하는 기능입니다. "
    "OpenAI가 2024년 8월 gpt-4o-2024-08-06부터 정식 도입했습니다.\n\n"
    "기존 JSON 모드의 한계\n"
    "기존 JSON 모드(response_format: json_object)는 유효한 JSON을 반환하지만 스키마 준수는 보장하지 않았습니다. "
    "필드 누락, 타입 불일치, 예상 외 필드 추가 등이 발생해 파싱 오류나 버그로 이어졌습니다.\n\n"
    "Structured Output의 동작\n"
    "response_format에 json_schema와 schema 정의를 전달하면, 모델은 해당 스키마를 100% 준수하는 JSON만 생성합니다. "
    "필수 필드가 반드시 존재하고, 타입이 정확하며, additionalProperties: false가 지켜집니다. "
    "내부적으로 constrained decoding 기술을 사용해 스키마에 맞는 토큰만 샘플링합니다.\n\n"
    "실용적 활용\n"
    "데이터 추출 자동화(이메일/문서에서 구조화 데이터 추출), 함수 인자 생성, 단계별 워크플로우 파싱에 활용됩니다. "
    "Anthropic Claude도 tool_use 패턴으로 유사한 기능을 제공하며, Google Gemini도 JSON 스키마 모드를 지원합니다."
  )
},

"https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview": {
  "tech_released_at": "2023-03-01T00:00:00Z",
  "description": (
    "시스템 프롬프트 엔지니어링은 Chat 형태 LLM API에서 system 역할로 전달되는 지시문을 최적화하는 기술입니다. "
    "사용자 메시지와 분리된 이 영역은 모델의 기본 동작, 페르소나, 규칙, 맥락을 정의합니다.\n\n"
    "시스템 프롬프트가 중요한 이유\n"
    "잘 설계된 시스템 프롬프트는 모델 성능을 크게 향상시킵니다. "
    "OpenAI, Anthropic, Google의 연구에 따르면 명확한 역할 부여('당신은 X 전문가입니다')가 "
    "응답 품질을 10~30% 향상시킵니다. "
    "또한 유해 콘텐츠 필터, 응답 형식 고정, 지식 범위 제한 등 안전 장치 역할도 합니다.\n\n"
    "효과적인 시스템 프롬프트 구성 요소\n"
    "역할 정의(페르소나), 맥락(배경 정보), 제약 조건(하면 안 되는 것), 출력 형식, 응답 언어/톤을 포함합니다. "
    "Anthropic Claude의 경우 XML 태그를 사용한 구조화를 권장합니다. "
    "구체적일수록 좋으며, 금지 사항보다 허용 사항을 명시하는 것이 더 효과적입니다.\n\n"
    "실제 적용 팁\n"
    "긴 시스템 프롬프트는 Prompt Caching으로 비용을 절감합니다. "
    "프롬프트 버저닝으로 변경 이력을 관리하고, A/B 테스트로 성능 차이를 측정합니다. "
    "사용자 입력과 명확히 구분되는 구분자를 사용해 프롬프트 인젝션 공격을 방어합니다."
  )
},

"https://arxiv.org/abs/2201.11903": {
  "tech_released_at": "2022-01-28T00:00:00Z",
  "description": (
    "Chain-of-Thought(CoT) 프롬프팅은 2022년 Google Research(Wei et al.)가 발표한 기법으로, "
    "모델이 최종 답변 전에 단계별 추론 과정을 명시적으로 서술하도록 유도합니다.\n\n"
    "핵심 아이디어\n"
    "'답은 X입니다' 대신 '1단계: ... 2단계: ... 따라서 답은 X입니다'처럼 사고 과정을 보여주면 "
    "모델이 더 정확한 답을 냅니다. 이는 복잡한 추론을 작은 단계로 분해해 각 단계에서 오류를 잡을 수 있기 때문입니다.\n\n"
    "두 가지 CoT 방식\n"
    "Few-shot CoT는 추론 단계가 포함된 예시를 제공하는 방식입니다. "
    "Zero-shot CoT는 프롬프트 끝에 '단계적으로 생각해봅시다(Let's think step by step)'를 추가하는 것만으로도 동작합니다. "
    "이 간단한 문구 추가만으로 GSM8K 수학 벤치마크에서 정확도가 대폭 향상됩니다.\n\n"
    "활용 영역과 한계\n"
    "수학 문제, 코드 디버깅, 논리 퍼즐, 멀티스텝 계획에서 특히 효과적입니다. "
    "단순 사실 조회나 분류 태스크에서는 오히려 불필요한 토큰 소비만 늘릴 수 있습니다. "
    "추론 토큰에 추가 비용이 발생하므로, 실시간 응답이 필요한 단순 태스크에는 부적합합니다."
  )
},

"https://arxiv.org/abs/2305.10601": {
  "tech_released_at": "2023-05-17T00:00:00Z",
  "description": (
    "Tree of Thoughts(ToT)는 2023년 Princeton과 Google 연구팀(Yao et al.)이 발표한 추론 프레임워크로, "
    "Chain-of-Thought의 선형 추론을 넘어 여러 추론 경로를 트리 구조로 탐색합니다.\n\n"
    "Chain-of-Thought의 한계 극복\n"
    "CoT는 한 번 잘못된 방향으로 추론하면 되돌아올 수 없습니다. "
    "ToT는 BFS(너비 우선 탐색)나 DFS(깊이 우선 탐색)로 여러 사고 경로를 동시에 탐색하고, "
    "각 노드를 평가해 유망하지 않은 경로를 가지치기(pruning)합니다.\n\n"
    "동작 방식\n"
    "LLM이 현재 상태에서 여러 '다음 생각'을 생성합니다. "
    "생성된 각 생각을 같은 LLM(또는 별도 평가자)이 '좋음/나쁨/불확실'로 평가합니다. "
    "좋은 경로만 계속 탐색하고 나머지는 폐기합니다. 이 과정을 최종 답에 도달할 때까지 반복합니다.\n\n"
    "성능과 비용\n"
    "Game of 24(수 퍼즐)에서 CoT 4% 대비 ToT 74%의 성공률을 보였습니다. "
    "단, 여러 번의 LLM 호출이 필요해 비용이 10~100배 증가합니다. "
    "따라서 창의적 글쓰기, 복잡한 계획 수립, 수학 증명처럼 고품질이 중요한 배치 작업에 적합합니다."
  )
},

# ── SKILLS ─────────────────────────────────────────────────────────────────────

"https://arxiv.org/abs/2005.11401": {
  "tech_released_at": "2020-05-22T00:00:00Z",
  "description": (
    "RAG(Retrieval-Augmented Generation, 검색 증강 생성)는 2020년 Meta AI(Lewis et al.)가 발표한 아키텍처로, "
    "LLM의 파라미터 기반 지식에 외부 검색 결과를 결합해 더 정확하고 최신의 응답을 생성합니다.\n\n"
    "RAG가 필요한 이유\n"
    "LLM은 훈련 데이터 마감 이후의 최신 정보를 모르고, 특정 도메인(내부 문서, 사내 규정)의 지식이 없으며, "
    "사실을 기억하면서 환각(hallucination)을 일으킵니다. "
    "RAG는 이 세 가지 문제를 모두 해결합니다.\n\n"
    "동작 파이프라인\n"
    "문서를 청크로 분할하고 임베딩 모델로 벡터화해 벡터 데이터베이스에 저장합니다. "
    "사용자 질문도 동일한 임베딩 모델로 벡터화해 유사 청크를 검색합니다. "
    "검색된 청크를 컨텍스트로 삽입해 LLM이 이를 참조해 답변하도록 합니다.\n\n"
    "RAG 품질 향상 기법\n"
    "청크 크기 최적화(일반적으로 256~512 토큰), 메타데이터 필터링, 하이브리드 검색(벡터 + BM25 키워드), "
    "재순위(reranking) 모델 적용, HyDE(가상 문서 임베딩) 등을 활용합니다. "
    "RAGAS 프레임워크로 Context Precision, Context Recall, Faithfulness, Answer Relevancy를 측정합니다."
  )
},

"https://arxiv.org/abs/1301.3666": {
  "tech_released_at": "2013-01-15T00:00:00Z",
  "description": (
    "임베딩(Embedding)은 텍스트·이미지·오디오 등을 의미를 보존하는 고차원 숫자 벡터로 변환하는 기술입니다. "
    "Word2Vec(2013, Google)에서 시작해 BERT, OpenAI Ada, text-embedding-3-large까지 진화했습니다.\n\n"
    "임베딩의 핵심 특성\n"
    "의미적으로 유사한 텍스트는 벡터 공간에서 가깝게 위치합니다. "
    "'왕' - '남자' + '여자' = '여왕'처럼 벡터 산술이 의미를 반영합니다. "
    "코사인 유사도나 내적으로 두 텍스트의 유사도를 수치화할 수 있습니다.\n\n"
    "주요 임베딩 모델 비교\n"
    "OpenAI text-embedding-3-large는 3072차원으로 다국어를 지원하며 MTEB 벤치마크 최상위권입니다. "
    "Cohere embed-v3는 검색 최적화 모델로 100개 언어를 지원합니다. "
    "로컬 실행이 필요하면 BAAI/bge-m3 또는 intfloat/multilingual-e5-large를 사용합니다. "
    "한국어에는 jhgan/ko-sroberta-multitask가 좋은 성능을 보입니다.\n\n"
    "벡터 데이터베이스 생태계\n"
    "Pinecone(완전 관리형), Weaviate(멀티모달), Qdrant(성능 최적화), Chroma(로컬 개발), "
    "pgvector(PostgreSQL 확장), Milvus(대규모 분산) 등 20개 이상이 있습니다. "
    "소규모 프로젝트는 FAISS(Facebook AI)를 메모리에서 직접 사용하는 방법도 있습니다."
  )
},

"https://arxiv.org/abs/2106.09685": {
  "tech_released_at": "2021-06-17T00:00:00Z",
  "description": (
    "파인튜닝(Fine-tuning)은 사전 학습된 기반 모델(Base Model)을 특정 도메인이나 태스크에 최적화된 추가 학습 데이터로 재훈련하는 기법입니다. "
    "OpenAI의 GPT-3 파인튜닝 API가 2021년 상용화되며 실용적 접근이 가능해졌습니다.\n\n"
    "언제 파인튜닝이 필요한가\n"
    "Few-shot 프롬프팅으로 원하는 품질이 나오지 않을 때, 응답 스타일을 일관되게 고정해야 할 때, "
    "특정 도메인 용어가 많아 프롬프트에 모두 설명하기 어려울 때, 비용 절감을 위해 작은 모델을 전문화할 때 고려합니다.\n\n"
    "LoRA와 QLoRA\n"
    "전체 파인튜닝은 수십~수백 GB GPU 메모리가 필요합니다. "
    "LoRA(Low-Rank Adaptation)는 원본 파라미터를 동결하고 작은 어댑터 행렬만 훈련해 메모리를 1/10로 줄입니다. "
    "QLoRA는 LoRA에 4비트 양자화를 결합해 7B 모델을 16GB GPU에서 파인튜닝 가능하게 합니다. "
    "Hugging Face PEFT, Axolotl, LLaMA-Factory 등이 대표적인 파인튜닝 도구입니다.\n\n"
    "데이터 요구사항\n"
    "OpenAI 파인튜닝은 최소 10~50개 예시로 시작 가능하지만 수백~수천 개가 더 좋습니다. "
    "데이터 품질이 양보다 중요합니다. 잘못된 예시가 섞이면 오히려 성능이 저하됩니다."
  )
},

"https://www.anthropic.com/news/prompt-caching": {
  "tech_released_at": "2024-08-15T00:00:00Z",
  "description": (
    "Prompt Caching은 Anthropic이 2024년 8월 발표한 기능으로, 반복되는 긴 프롬프트 접두사(시스템 프롬프트, 문서, 예시 등)를 "
    "서버 측에 캐싱해 입력 비용을 최대 90%, 지연을 최대 85% 줄입니다.\n\n"
    "동작 원리\n"
    "프롬프트에 cache_control 파라미터를 추가해 캐싱할 위치를 지정합니다. "
    "처음 호출 시 KV 캐시가 생성되며 Write 비용(일반 입력의 1.25배)이 발생합니다. "
    "이후 5분 이내 동일 프롬프트 접두사로 호출하면 Read 비용(일반 입력의 10%)만 청구됩니다. "
    "1024 토큰 이상의 접두사만 캐싱 가능합니다.\n\n"
    "비용 절감 시나리오\n"
    "100,000 토큰짜리 법률 문서를 RAG 컨텍스트로 매번 전송하는 경우, "
    "Prompt Caching 적용 후 입력 비용이 90% 감소합니다. "
    "긴 시스템 프롬프트를 사용하는 챗봇, 멀티턴 대화에서 전체 히스토리 재전송, "
    "동일 문서 기반 QA 반복 작업 모두 큰 절감 효과가 있습니다.\n\n"
    "OpenAI의 유사 기능\n"
    "OpenAI도 gpt-4o 기준 1024 토큰 이상 프롬프트를 자동으로 캐싱하며 입력 비용 50%를 절감합니다. "
    "Anthropic과 달리 명시적 지정 없이 자동으로 동작합니다."
  )
},

# ── AGENTS ─────────────────────────────────────────────────────────────────────

"https://github.com/langchain-ai/langgraph": {
  "tech_released_at": "2024-01-17T00:00:00Z",
  "description": (
    "LangGraph는 LangChain 팀이 2024년 1월 발표한 에이전트 및 멀티에이전트 워크플로우 오케스트레이션 라이브러리입니다. "
    "기존 체인(선형 실행) 한계를 넘어 순환, 조건 분기, 병렬 처리가 가능한 상태 기반 그래프를 구성합니다.\n\n"
    "핵심 개념\n"
    "State는 그래프 전체에 공유되는 TypedDict 형태의 데이터 컨테이너입니다. "
    "Node는 State를 받아 수정하고 반환하는 Python 함수입니다. "
    "Edge는 노드 간 연결이며, 조건부 엣지로 런타임에 다음 노드를 동적으로 결정합니다.\n\n"
    "LangGraph가 해결하는 문제\n"
    "복잡한 에이전트 루프 구현, 에이전트 실행 상태 영속화(중단 후 재개), "
    "Human-in-the-loop(중간 인간 검토), 병렬 서브그래프 실행, 스트리밍 응답을 지원합니다. "
    "Checkpointing으로 에이전트 실행 상태를 저장해 긴 작업을 중단하고 재개할 수 있습니다.\n\n"
    "배포와 생태계\n"
    "LangGraph Platform(Cloud/Self-hosted)으로 프로덕션 배포를 지원합니다. "
    "LangSmith와 통합해 에이전트 실행 추적 및 디버깅이 가능합니다. "
    "다른 에이전트 프레임워크(AutoGen, CrewAI)와 달리 상태 관리와 지속성에 강점이 있습니다."
  )
},

"https://github.com/microsoft/autogen": {
  "tech_released_at": "2023-09-01T00:00:00Z",
  "description": (
    "AutoGen은 Microsoft Research가 2023년 9월 발표한 대화 기반 멀티에이전트 프레임워크입니다. "
    "여러 에이전트가 서로 메시지를 주고받으며 복잡한 태스크를 협력적으로 해결합니다.\n\n"
    "핵심 에이전트 유형\n"
    "AssistantAgent는 LLM을 백엔드로 사용하는 AI 에이전트입니다. "
    "UserProxyAgent는 사람 대신 코드를 실행하거나 피드백을 전달합니다. "
    "GroupChat은 여러 에이전트를 하나의 채팅방에 모아 라운드로빈이나 선택적 발화로 협력시킵니다.\n\n"
    "코드 실행과 안전성\n"
    "AutoGen의 가장 강력한 기능은 에이전트가 Python 코드를 직접 작성하고 실행한 결과를 다시 논의에 반영하는 것입니다. "
    "Docker 컨테이너 내에서 코드를 실행해 로컬 시스템을 보호합니다. "
    "코드 오류가 발생하면 에이전트가 오류 메시지를 받아 자동으로 수정을 시도합니다.\n\n"
    "AutoGen v0.4 변경사항\n"
    "2024년 말 배포된 v0.4는 비동기(async) 지원, 이벤트 드리븐 아키텍처로 완전히 재설계되었습니다. "
    "더 유연한 에이전트 계층 구조와 외부 서비스 통합이 개선되었습니다."
  )
},

"https://github.com/crewAIInc/crewAI": {
  "tech_released_at": "2024-01-10T00:00:00Z",
  "description": (
    "CrewAI는 2024년 1월 출시된 역할 기반 멀티에이전트 협업 프레임워크입니다. "
    "실제 팀처럼 역할(Role), 목표(Goal), 배경(Backstory)을 가진 AI 에이전트들이 "
    "태스크를 분담하고 결과물을 조합해 최종 산출물을 만듭니다.\n\n"
    "핵심 구성 요소\n"
    "Agent는 역할, 목표, 도구 세트, LLM을 갖습니다. "
    "Task는 에이전트에게 할당된 구체적인 작업과 기대 출력물을 정의합니다. "
    "Crew는 여러 Agent와 Task를 묶어 실행 순서(순차/병렬)를 관리합니다. "
    "Process는 Sequential(순서대로), Hierarchical(매니저가 할당), Consensual(합의 기반) 방식을 지원합니다.\n\n"
    "AutoGen과의 차이\n"
    "AutoGen이 대화 기반이라면 CrewAI는 역할 기반입니다. "
    "CrewAI는 각 에이전트의 전문성을 명확히 정의해 팀워크 시뮬레이션에 가깝습니다. "
    "콘텐츠 제작, 리서치, 비즈니스 자동화에 많이 활용됩니다.\n\n"
    "LLM 지원\n"
    "OpenAI, Anthropic, Azure, Google, HuggingFace, Ollama(로컬) 등 모든 주요 LLM을 지원합니다."
  )
},

"https://openai.com/blog/new-models-and-developer-products-announced-at-devday": {
  "tech_released_at": "2023-11-06T00:00:00Z",
  "description": (
    "OpenAI Assistants API는 2023년 11월 OpenAI DevDay에서 발표한 상태 관리 에이전트 플랫폼입니다. "
    "Thread(대화 세션), Message(메시지), Run(실행), Assistant(설정)의 4개 리소스로 구성됩니다.\n\n"
    "핵심 구성 요소\n"
    "Assistant는 모델, 지시문, 도구 세트, 파일을 가진 영구적인 설정 객체입니다. "
    "Thread는 사용자 대화 히스토리를 저장하며 무한 길이의 대화를 자동으로 요약 처리합니다. "
    "Run은 Thread에서 Assistant를 실행하는 단일 작업 단위이며 비동기로 처리됩니다.\n\n"
    "내장 도구\n"
    "File Search(벡터 검색 기반 문서 QA), Code Interpreter(Python 실행 및 파일 생성), "
    "Function Calling(사용자 정의 도구 호출)을 기본 제공합니다. "
    "File Search는 업로드한 PDF, Word, CSV 등에서 자동으로 벡터 인덱스를 생성합니다.\n\n"
    "비용과 한계\n"
    "Thread는 기본 60일 후 자동 삭제됩니다. "
    "File Search는 벡터 스토어 사용 요금이 별도 발생합니다. "
    "복잡한 커스텀 에이전트 로직은 LangGraph 등 오픈소스 프레임워크가 더 유연합니다."
  )
},

"https://github.com/anthropics/sdk-v1": {
  "tech_released_at": "2024-11-01T00:00:00Z",
  "description": (
    "Anthropic Agent SDK(Claude Agent SDK)는 2024년 11월 공개된 Python 라이브러리로, "
    "Claude 모델 기반의 에이전트를 구조화된 방식으로 구축할 수 있게 합니다.\n\n"
    "anthropic Python SDK와의 관계\n"
    "기존 anthropic Python 패키지가 기반이며, 에이전트 패턴을 표준화하는 상위 레이어입니다. "
    "Tool Use(Function Calling), 멀티턴 대화, 스트리밍을 네이티브로 지원합니다.\n\n"
    "주요 기능\n"
    "도구 정의를 Python 함수에서 자동으로 JSON Schema로 변환합니다. "
    "에이전트 루프(도구 결과를 다시 Claude에 전달하는 사이클)를 간단하게 구현합니다. "
    "computer_use, bash, text_editor 등 내장 도구 타입을 지원합니다.\n\n"
    "Claude의 도구 사용 특성\n"
    "Claude는 tool_use 메시지 타입으로 도구를 호출하고, tool_result로 결과를 받습니다. "
    "병렬 도구 호출을 지원해 여러 API를 동시에 요청합니다. "
    "토큰 예산 설정으로 확장 사고(extended thinking) 비용을 제어합니다."
  )
},

# ── HARNESS ────────────────────────────────────────────────────────────────────

"https://github.com/langchain-ai/langchain": {
  "tech_released_at": "2022-10-25T00:00:00Z",
  "description": (
    "LangChain은 2022년 10월 Harrison Chase가 공개한 오픈소스 LLM 애플리케이션 프레임워크입니다. "
    "프롬프트 관리, 모델 연결, 출력 파싱, 도구 통합을 표준화된 인터페이스로 제공합니다.\n\n"
    "핵심 추상화\n"
    "LLM/ChatModel은 40개 이상 모델을 동일 인터페이스로 호출합니다. "
    "Chain은 여러 컴포넌트를 파이프라인으로 연결합니다. "
    "Memory는 대화 히스토리를 관리합니다. "
    "Document Loader, Text Splitter, VectorStore, Retriever로 RAG 파이프라인을 구성합니다.\n\n"
    "LCEL(LangChain Expression Language)\n"
    "파이프(|) 연산자로 컴포넌트를 체이닝합니다. "
    "prompt | llm | parser 형태로 선언적 파이프라인을 구성합니다. "
    "스트리밍, 비동기, 배치 처리를 통일된 인터페이스로 지원합니다.\n\n"
    "LangChain vs LangGraph\n"
    "LangChain은 선형 파이프라인에 적합하고, "
    "LangGraph는 순환과 조건 분기가 필요한 에이전트에 적합합니다. "
    "현재 LangChain 팀은 복잡한 에이전트에는 LangGraph를 권장합니다."
  )
},

"https://github.com/run-llama/llama_index": {
  "tech_released_at": "2022-11-01T00:00:00Z",
  "description": (
    "LlamaIndex(구 GPT Index)는 2022년 11월 Jerry Liu가 창립한 데이터 중심 LLM 프레임워크입니다. "
    "다양한 데이터 소스를 LLM이 쿼리할 수 있는 인덱스로 변환하는 데 특화되어 있습니다.\n\n"
    "LangChain과의 차이\n"
    "LangChain이 범용 LLM 파이프라인에 초점을 맞춘다면, LlamaIndex는 데이터 인덱싱과 검색에 특화됩니다. "
    "RAG 파이프라인 구성 요소가 더 세분화되어 있고, 인덱스 타입이 다양합니다.\n\n"
    "핵심 기능\n"
    "SimpleDirectoryReader로 PDF, Word, Excel, CSV, 웹페이지 등 100개 이상 형식을 로드합니다. "
    "VectorStoreIndex(벡터 검색), SummaryIndex(요약 기반), KnowledgeGraphIndex(그래프 기반)를 지원합니다. "
    "SubQuestionQueryEngine으로 복잡한 질문을 서브 질문으로 분해해 각각 검색 후 통합합니다. "
    "RouterQueryEngine으로 질문 유형에 따라 다른 인덱스로 라우팅합니다.\n\n"
    "고급 RAG 기법\n"
    "Sentence Window Retrieval(문장 단위 검색 후 주변 문맥 확장), "
    "Auto-Merging Retrieval(계층적 청크 구조), HyDE(가상 문서 임베딩)를 내장 지원합니다. "
    "RAGAS 평가 지표와 통합해 RAG 품질을 자동 측정합니다."
  )
},

"https://github.com/microsoft/semantic-kernel": {
  "tech_released_at": "2023-03-17T00:00:00Z",
  "description": (
    "Semantic Kernel은 Microsoft가 2023년 3월 오픈소스로 공개한 엔터프라이즈 AI 오케스트레이션 SDK입니다. "
    "C#, Python, Java를 지원하며 기존 .NET/Azure 생태계와 자연스럽게 통합됩니다.\n\n"
    "핵심 개념\n"
    "Kernel은 중앙 오케스트레이터로 플러그인, 메모리, AI 서비스를 조율합니다. "
    "Plugin(구 Skill)은 함수 모음으로 Native Functions(언어 메서드)와 Semantic Functions(프롬프트 함수)로 구분됩니다. "
    "Planner는 목표를 달성하기 위한 함수 실행 계획을 자동으로 수립합니다. "
    "Memory는 텍스트 임베딩 기반 의미 검색과 대화 히스토리를 관리합니다.\n\n"
    "엔터프라이즈 특화 기능\n"
    "Azure OpenAI Service, Azure Cognitive Search와 네이티브 통합됩니다. "
    "Process Framework로 기업 비즈니스 프로세스를 LLM으로 자동화합니다. "
    "OpenTelemetry 통합으로 프로덕션 모니터링을 지원합니다. "
    "이미 Copilot Studio, Bing, Microsoft 365 Copilot 내부에서 사용됩니다.\n\n"
    "LangChain과 비교\n"
    "Python/JS 중심의 LangChain과 달리 C# 생태계가 우선입니다. "
    "마이크로서비스/Azure 기반 엔터프라이즈 환경에 적합합니다."
  )
},

"https://github.com/deepset-ai/haystack": {
  "tech_released_at": "2020-11-01T00:00:00Z",
  "description": (
    "Haystack은 독일 AI 스타트업 deepset이 2020년 개발한 프로덕션급 LLM 애플리케이션 프레임워크입니다. "
    "파이프라인 기반 아키텍처로 유연한 LLM 애플리케이션 구성을 지원합니다.\n\n"
    "파이프라인 아키텍처\n"
    "모든 것이 컴포넌트(Component)로 구성됩니다. "
    "DocumentStore(문서 저장), Retriever(문서 검색), Ranker(재순위), Reader/Generator(답변 생성)를 "
    "파이프라인으로 연결합니다. YAML 파일로 파이프라인을 선언적으로 정의하고 버전 관리합니다.\n\n"
    "지원 문서 스토어\n"
    "Elasticsearch, OpenSearch, Weaviate, Qdrant, Chroma, Pinecone, pgvector, Milvus, "
    "인메모리 스토어 등 다양한 벡터/키워드 DB를 지원합니다.\n\n"
    "Haystack 2.x 변화\n"
    "2024년 초 출시된 2.x는 컴포넌트 인터페이스를 완전히 재설계했습니다. "
    "타입 힌팅 기반의 강력한 파이프라인 유효성 검사, 비동기 실행, 더 유연한 데이터 흐름을 지원합니다.\n\n"
    "deepset Cloud\n"
    "deepset Cloud에서 Haystack 파이프라인을 SaaS로 제공합니다. "
    "Elasticsearch에서 마이그레이션하거나 복잡한 검색 파이프라인이 필요한 기업에 적합합니다."
  )
},

"https://docs.smith.langchain.com/": {
  "tech_released_at": "2023-07-01T00:00:00Z",
  "description": (
    "LangSmith는 LangChain이 2023년 7월 출시한 LLM 애플리케이션 옵저버빌리티(Observability) 및 평가 플랫폼입니다. "
    "LLM 앱의 실행 추적, 디버깅, 테스트, 모니터링을 통합 제공합니다.\n\n"
    "핵심 기능\n"
    "Tracing은 LLM 호출, 체인 실행, 도구 호출의 전체 트리를 시각화합니다. "
    "각 단계의 입력/출력, 토큰 사용량, 비용, 지연 시간을 상세히 기록합니다. "
    "Datasets는 실제 운영 트레이스를 기반으로 테스트 셋을 구성합니다. "
    "Evaluators로 자동화된 품질 평가(정확도, 일관성, 관련성)를 설정합니다.\n\n"
    "프롬프트 허브\n"
    "팀 간 프롬프트를 버전 관리하고 공유합니다. "
    "프롬프트를 변경하고 즉시 Playground에서 테스트해 성능 변화를 추적합니다.\n\n"
    "비용과 요금제\n"
    "월 5,000 트레이스까지 무료입니다. "
    "Plus 플랜은 월 $39부터이며 더 많은 트레이스와 평가 실행을 제공합니다. "
    "Langfuse, Phoenix(Arize) 등이 오픈소스 대안입니다."
  )
},

# ── ORCHESTRATION ──────────────────────────────────────────────────────────────

"https://github.com/langgenius/dify": {
  "tech_released_at": "2023-04-12T00:00:00Z",
  "description": (
    "Dify는 2023년 4월 LangGenius가 출시한 오픈소스 LLM 애플리케이션 개발 플랫폼입니다. "
    "코드 없이 RAG 파이프라인, 에이전트, 워크플로우를 구성하는 시각적 스튜디오를 제공합니다.\n\n"
    "주요 기능\n"
    "Prompt IDE에서 프롬프트를 작성하고 A/B 테스트 및 성능 비교가 가능합니다. "
    "RAG Pipeline은 파일 업로드, 청크 분할, 임베딩, 벡터 저장 과정을 자동화합니다. "
    "Workflow는 조건 분기, 루프, 병렬 처리를 지원하는 시각적 그래프 편집기입니다. "
    "Agent는 ReAct 패턴 기반으로 도구를 사용하는 AI 에이전트를 노코드로 구성합니다.\n\n"
    "자체 호스팅과 SaaS\n"
    "Docker Compose로 완전 자체 호스팅이 가능해 데이터가 외부로 나가지 않습니다. "
    "dify.ai 클라우드에서 SaaS로도 이용 가능하며 팀 협업 기능을 제공합니다. "
    "GitHub 스타 85,000개를 넘은 가장 인기 있는 LLM 앱 플랫폼 중 하나입니다.\n\n"
    "지원 모델\n"
    "OpenAI, Anthropic, Azure, Google, Mistral, Llama, 로컬 Ollama 모델까지 200개 이상 지원합니다."
  )
},

"https://github.com/FlowiseAI/Flowise": {
  "tech_released_at": "2023-04-01T00:00:00Z",
  "description": (
    "Flowise는 2023년 4월 출시된 LangChain & LlamaIndex 시각화 도구로, "
    "드래그 앤 드롭으로 LLM 파이프라인을 구성합니다.\n\n"
    "핵심 가치\n"
    "LangChain의 복잡한 코드를 시각적 노드로 표현합니다. "
    "ChatOpenAI, PromptTemplate, PineconeVectorStore 같은 컴포넌트를 캔버스에 드래그해 연결합니다. "
    "만든 플로우는 REST API로 즉시 배포되어 외부 앱에서 호출할 수 있습니다.\n\n"
    "자체 호스팅\n"
    "Docker로 완전한 자체 호스팅이 가능합니다. "
    "npm install -g flowise && flowise start로 로컬에서 즉시 실행됩니다. "
    "FlowiseAI 클라우드에서 관리형 서비스도 제공합니다.\n\n"
    "Dify와 비교\n"
    "Flowise는 LangChain 컴포넌트에 집중하고 개발자 친화적입니다. "
    "Dify는 더 완성된 올인원 플랫폼으로 비개발자도 쓸 수 있는 UI를 제공합니다. "
    "GitHub 스타 43,000개 이상을 보유합니다."
  )
},

"https://docs.n8n.io/advanced-ai/": {
  "tech_released_at": "2023-09-01T00:00:00Z",
  "description": (
    "n8n AI Agent Nodes는 2023년 하반기 n8n에 추가된 AI 에이전트 자동화 기능입니다. "
    "기존 400개 이상의 서비스 통합(GitHub, Slack, Google Sheets, Jira 등)에 AI 에이전트 기능을 결합합니다.\n\n"
    "n8n이란\n"
    "n8n은 Zapier, Make.com과 유사한 워크플로우 자동화 도구이지만, "
    "오픈소스이고 자체 호스팅이 가능하며 JavaScript/Python 커스텀 코드를 직접 작성할 수 있습니다.\n\n"
    "AI Agent Node 기능\n"
    "LangChain 기반으로 동작하며 Vector Store, Embeddings, Text Splitter 등 AI 노드를 제공합니다. "
    "에이전트가 대화 히스토리를 기억하며 여러 도구(서비스 통합)를 자율적으로 선택해 태스크를 수행합니다. "
    "SQL 쿼리, 웹 검색, 파일 처리, 외부 API 호출을 에이전트가 직접 실행합니다.\n\n"
    "n8n과 Make.com/Zapier 비교\n"
    "Zapier/Make.com은 단순 트리거-액션 자동화에 강하지만 AI 에이전트 기능이 제한적입니다. "
    "n8n은 복잡한 AI 로직과 기존 비즈니스 프로세스 통합에 강점이 있습니다."
  )
},

"https://blog.langchain.dev/langgraph-platform/": {
  "tech_released_at": "2024-06-01T00:00:00Z",
  "description": (
    "LangGraph Platform은 LangGraph 에이전트를 프로덕션 환경에 배포·관리하기 위한 인프라 플랫폼입니다. "
    "2024년 하반기부터 GA(정식 출시)되었으며, LangChain Cloud에서 서비스됩니다.\n\n"
    "핵심 기능\n"
    "하나의 LangGraph 에이전트를 수천 개의 동시 실행으로 자동 스케일합니다. "
    "Checkpointing이 내장되어 긴 실행 에이전트의 상태를 영속화하고 실패 시 재개합니다. "
    "Streaming API로 에이전트 중간 결과를 실시간으로 클라이언트에 전달합니다. "
    "LangSmith와 통합해 모든 에이전트 실행을 자동 추적합니다.\n\n"
    "배포 옵션\n"
    "LangGraph Cloud(완전 관리형), Self-Hosted Enterprise(AWS, GCP, Azure 직접 배포), "
    "Self-Hosted Lite(무료, 기능 제한)의 세 가지 옵션이 있습니다.\n\n"
    "대안 비교\n"
    "AgentOps, Langfuse는 모니터링에 특화되어 있고, "
    "Modal/Fly.io는 범용 컨테이너 배포를 지원하며, "
    "LangGraph Platform은 LangGraph 에이전트에 특화된 풀스택 솔루션입니다."
  )
},

# ── INTEGRATION ────────────────────────────────────────────────────────────────

"https://www.anthropic.com/api": {
  "tech_released_at": "2023-03-14T00:00:00Z",
  "description": (
    "Anthropic Claude API는 Claude 모델군(Claude 3.5 Sonnet, Haiku, Opus 등)을 호출하는 공식 REST API입니다. "
    "2023년 3월 Claude 1.0 출시와 함께 API 접근이 시작되었습니다.\n\n"
    "주요 API 구조\n"
    "POST /v1/messages가 핵심 엔드포인트입니다. "
    "system(시스템 프롬프트), messages(대화 히스토리), model(모델 이름), max_tokens를 전달합니다. "
    "stream: true로 Server-Sent Events 스트리밍을 활성화합니다.\n\n"
    "Claude 고유 기능\n"
    "Extended Thinking은 모델이 답변 전에 긴 내부 추론을 수행하며, 토큰 예산(budget_tokens)으로 제어합니다. "
    "Tool Use는 도구 정의, 도구 호출, 결과 반환의 표준 사이클을 지원합니다. "
    "Prompt Caching으로 반복 프롬프트 접두사를 캐싱해 비용을 최대 90% 절감합니다. "
    "Vision으로 이미지, PDF, 문서를 직접 분석합니다.\n\n"
    "요금 안내(Claude 3.5 Sonnet 기준)\n"
    "입력 $3/M 토큰, 출력 $15/M 토큰. 캐시 적용 시 입력 $0.30/M 토큰. "
    "Python SDK: pip install anthropic, JS SDK: npm install @anthropic-ai/sdk."
  )
},

"https://platform.openai.com/docs/api-reference": {
  "tech_released_at": "2020-06-11T00:00:00Z",
  "description": (
    "OpenAI API는 GPT-4o, o1, Whisper, DALL-E, Embeddings 등 OpenAI의 모든 모델을 REST API로 제공합니다. "
    "2020년 6월 GPT-3 API 공개와 함께 상용 AI API 시대를 열었습니다.\n\n"
    "핵심 엔드포인트\n"
    "Chat Completions(/v1/chat/completions)는 GPT-4o, o1 등을 호출합니다. "
    "Embeddings(/v1/embeddings)는 텍스트를 벡터로 변환합니다. "
    "Responses API(2025년 신규)는 Assistants API의 후속으로 더 단순한 상태 관리를 제공합니다.\n\n"
    "Function Calling / Tool Use\n"
    "tools 파라미터에 함수 정의를 전달하면 모델이 적절한 함수와 인자를 선택합니다. "
    "Parallel Tool Calling으로 여러 함수를 동시에 호출합니다. "
    "Structured Outputs(strict: true)로 JSON 스키마 100% 준수를 보장합니다.\n\n"
    "호환성\n"
    "vLLM, Ollama, LiteLLM 등 오픈소스 프레임워크들이 OpenAI API 형식을 그대로 지원하므로 "
    "base_url만 변경하면 로컬 모델로 전환됩니다."
  )
},

"https://platform.openai.com/docs/guides/function-calling": {
  "tech_released_at": "2023-06-13T00:00:00Z",
  "description": (
    "GPT-4o Function Calling(현재 Tool Use)은 2023년 6월 OpenAI가 도입한 기능으로, "
    "LLM이 구조화된 함수 호출을 통해 외부 시스템과 상호작용합니다.\n\n"
    "동작 방식\n"
    "tools 파라미터에 함수 이름, 설명, JSON Schema 형태의 파라미터를 정의합니다. "
    "모델이 사용자 요청에서 함수 호출이 필요하다고 판단하면 tool_calls 응답을 반환합니다. "
    "애플리케이션이 실제 함수를 실행하고 결과를 tool 역할 메시지로 다시 전달합니다. "
    "모델은 함수 결과를 참조해 최종 자연어 응답을 생성합니다.\n\n"
    "Parallel Function Calling\n"
    "2023년 11월부터 한 번에 여러 함수를 병렬로 호출합니다. "
    "예를 들어 '서울과 도쿄 날씨를 알려줘' 요청에 날씨 API를 두 번 동시에 호출합니다.\n\n"
    "활용 패턴\n"
    "데이터베이스 조회, 외부 API 호출, 계산 실행, 파일 시스템 접근, 이메일 전송 등 "
    "LLM이 직접 할 수 없는 모든 작업을 도구로 정의합니다. "
    "Anthropic의 Tool Use, Google의 Function Declarations도 동일한 패턴을 따릅니다."
  )
},

"https://github.com/ollama/ollama": {
  "tech_released_at": "2023-07-01T00:00:00Z",
  "description": (
    "Ollama는 2023년 7월 출시된 로컬 LLM 실행 도구입니다. "
    "복잡한 CUDA 설정 없이 터미널 명령어 하나로 Llama, Mistral, Phi, Gemma 등을 실행합니다.\n\n"
    "주요 기능\n"
    "ollama pull llama3.2로 모델을 다운로드하고 ollama run llama3.2로 대화를 시작합니다. "
    "OpenAI 호환 API(localhost:11434/v1/chat/completions)를 제공해 기존 앱에 바로 연결됩니다. "
    "Modelfile로 시스템 프롬프트, 파라미터(temperature, top_p)를 정의한 커스텀 모델을 만들 수 있습니다.\n\n"
    "하드웨어 요구사항 가이드\n"
    "7B 모델 4비트 양자화(Q4): 최소 8GB RAM(CPU 추론) 또는 6GB VRAM(GPU). "
    "13B 모델: 16GB RAM 또는 10GB VRAM. "
    "70B 모델: 64GB RAM 또는 48GB VRAM 권장. "
    "Apple Silicon Mac은 Metal GPU 가속이 자동 적용됩니다.\n\n"
    "활용 사례\n"
    "개인 정보 보호(데이터가 로컬에만 있음), 오프라인 환경, "
    "API 비용 절감, 파인튜닝된 특수 모델 실행에 적합합니다."
  )
},

"https://github.com/huggingface/transformers": {
  "tech_released_at": "2019-10-09T00:00:00Z",
  "description": (
    "Hugging Face Transformers는 2019년 10월 출시된 오픈소스 LLM 라이브러리로, "
    "PyTorch, TensorFlow, JAX 기반의 수만 개 모델을 통일된 API로 제공합니다.\n\n"
    "핵심 API\n"
    "AutoModel, AutoTokenizer로 모델 타입에 상관없이 동일한 코드로 로드합니다. "
    "pipeline()은 가장 간단한 고수준 API로 텍스트 분류, 생성, 요약, 번역을 한 줄로 실행합니다. "
    "Trainer API로 커스텀 데이터셋 파인튜닝을 체계적으로 관리합니다.\n\n"
    "Hugging Face Hub\n"
    "150만 개 이상의 모델, 25만 개 이상의 데이터셋, 수십만 개의 Space(데모 앱)가 있습니다. "
    "from_pretrained('모델명')으로 Hub에서 직접 모델을 다운로드해 실행합니다. "
    "GGUF, GPTQ, AWQ 등 양자화 모델도 Hub에서 바로 사용 가능합니다.\n\n"
    "생태계 패키지\n"
    "datasets(데이터 로딩), evaluate(메트릭), peft(파라미터 효율적 파인튜닝), "
    "accelerate(분산 훈련), trl(RLHF), optimum(ONNX/TensorRT 최적화)이 함께 제공됩니다."
  )
},

"https://github.com/vercel/ai": {
  "tech_released_at": "2023-05-23T00:00:00Z",
  "description": (
    "Vercel AI SDK(ai 패키지)는 2023년 5월 출시된 TypeScript/JavaScript LLM 통합 라이브러리입니다. "
    "Next.js, React, Svelte, Node.js에서 스트리밍 AI UI를 손쉽게 구현합니다.\n\n"
    "세 가지 핵심 레이어\n"
    "AI Core는 generateText, streamText, generateObject, streamObject 함수로 "
    "텍스트 생성과 구조화 출력을 처리합니다. "
    "AI UI는 useChat, useCompletion, useObject 훅으로 React 상태 관리와 스트리밍을 자동화합니다. "
    "AI RSC는 React Server Components와 통합해 서버에서 UI를 스트리밍합니다.\n\n"
    "멀티 프로바이더 지원\n"
    "OpenAI, Anthropic, Google, Mistral, Cohere, Groq, Azure, Amazon Bedrock을 "
    "동일한 인터페이스로 교체 사용합니다.\n\n"
    "Structured Generation\n"
    "zod 스키마를 전달하면 generateObject가 타입 안전한 JSON 객체를 반환합니다. "
    "모델 Provider에 상관없이 Structured Output을 일관되게 사용할 수 있습니다.\n\n"
    "ChatGPT 클론 빠른 구현\n"
    "useChat 훅과 서버 액션만으로 스트리밍 채팅 UI를 손쉽게 만들 수 있습니다."
  )
},

# ── INFRA ──────────────────────────────────────────────────────────────────────

"https://github.com/vllm-project/vllm": {
  "tech_released_at": "2023-06-20T00:00:00Z",
  "description": (
    "vLLM은 UC Berkeley가 2023년 6월 발표한 고처리량 LLM 추론 엔진입니다. "
    "PagedAttention 기술로 기존 대비 최대 24배의 처리량을 달성합니다.\n\n"
    "PagedAttention이란\n"
    "GPU KV 캐시를 OS의 가상 메모리처럼 관리합니다. "
    "기존 방식은 최대 시퀀스 길이만큼 연속된 GPU 메모리를 미리 예약해 낭비가 심했습니다. "
    "PagedAttention은 KV 캐시를 작은 페이지 단위로 동적 할당해 메모리 낭비를 5% 미만으로 줄입니다. "
    "이 덕분에 더 많은 요청을 동시에 처리(continuous batching)할 수 있습니다.\n\n"
    "OpenAI 호환 API\n"
    "vllm serve meta-llama/Llama-3.1-70B-Instruct 명령 하나로 OpenAI 형식 API 서버가 시작됩니다. "
    "기존 OpenAI SDK 코드에서 base_url만 변경하면 됩니다.\n\n"
    "성능 비교(A100 80GB, Llama 3 70B 기준)\n"
    "일반 HuggingFace Transformers 대비 처리량 약 25배 향상. "
    "Tensor Parallelism으로 다중 GPU 배포, Quantization(AWQ, GPTQ, FP8)으로 메모리 절감을 지원합니다."
  )
},

"https://github.com/ggml-org/llama.cpp": {
  "tech_released_at": "2023-03-10T00:00:00Z",
  "description": (
    "llama.cpp는 2023년 3월 Georgi Gerganov가 만든 순수 C/C++ LLM 추론 엔진입니다. "
    "CUDA 없이 CPU만으로 LLM을 실행 가능하게 하며, Apple Silicon GPU 가속을 지원합니다.\n\n"
    "GGUF 포맷\n"
    "GGUF(GGML Unified Format)는 llama.cpp가 사용하는 모델 파일 형식입니다. "
    "단일 파일에 모든 모델 정보(가중치, 양자화, 메타데이터)를 저장합니다. "
    "양자화 레벨: Q4_K_M(권장, 성능과 품질 균형), Q8_0(고품질), Q2_K(극소형), F16(전체 정밀도). "
    "HuggingFace Hub에서 직접 GGUF 파일을 다운로드해 사용합니다.\n\n"
    "지원 모델\n"
    "Llama 3/2/1, Mistral, Phi-3/4, Gemma 2, Qwen 2.5, DeepSeek-R1, Command-R 등 대부분 오픈소스 모델 지원. "
    "커뮤니티에서 매주 새 모델의 GGUF 변환본을 제공합니다.\n\n"
    "활용 사례\n"
    "Ollama, LM Studio, Jan이 내부적으로 llama.cpp를 사용합니다. "
    "Raspberry Pi, MacBook Air 같은 저사양 기기에서도 7B 모델 실행이 가능합니다."
  )
},

"https://developer.nvidia.com/blog/nvidia-nim-offers-optimized-inference-microservices-for-deploying-ai-models-at-scale/": {
  "tech_released_at": "2024-03-18T00:00:00Z",
  "description": (
    "NVIDIA NIM(NVIDIA Inference Microservices)은 NVIDIA가 2024년 3월 GTC에서 발표한 "
    "최적화 LLM 추론 마이크로서비스입니다. "
    "엔터프라이즈 환경에서 AI 모델을 빠르고 안정적으로 배포하는 컨테이너화된 솔루션입니다.\n\n"
    "NIM의 핵심 가치\n"
    "복잡한 TensorRT-LLM 최적화, 모델 로딩, API 서버 설정을 모두 하나의 Docker 컨테이너로 제공합니다. "
    "docker run으로 시작하면 OpenAI 호환 API 서버가 즉시 동작합니다.\n\n"
    "지원 모델과 최적화\n"
    "Llama 3.1/3.2, Mistral, Phi-3, Gemma, Stable Diffusion 등 100개 이상 모델을 지원합니다. "
    "TensorRT-LLM 자동 적용으로 vLLM 대비 추가 20~40% 성능 향상. "
    "Multi-GPU Tensor Parallelism 자동 설정으로 A100/H100 클러스터 배포가 간단합니다.\n\n"
    "라이선스와 비용\n"
    "NVIDIA AI Enterprise 구독이 필요합니다(개발 테스트는 무료). "
    "NVIDIA GPU가 없는 클라우드 환경에서 NIM API(api.nvidia.com)를 통해 테스트 가능합니다."
  )
},

"https://lmstudio.ai/": {
  "tech_released_at": "2023-10-01T00:00:00Z",
  "description": (
    "LM Studio는 2023년 10월 출시된 로컬 LLM 실행 데스크톱 애플리케이션입니다. "
    "코드 없이 GUI로 HuggingFace의 GGUF 모델을 검색하고 다운로드해 실행합니다.\n\n"
    "주요 기능\n"
    "내장 모델 브라우저에서 Llama, Mistral, Phi, Qwen 등 수천 개 GGUF 모델을 검색·다운로드합니다. "
    "ChatGPT 스타일 채팅 UI에서 다운받은 모델과 즉시 대화합니다. "
    "로컬 OpenAI 호환 서버(localhost:1234)를 켜면 외부 앱(Cursor, Obsidian, VS Code)에서 연결 가능합니다. "
    "멀티 모달 모델 지원으로 이미지 첨부 대화가 가능합니다.\n\n"
    "Ollama와 비교\n"
    "Ollama는 CLI 기반으로 개발자 친화적입니다. "
    "LM Studio는 GUI 기반으로 비개발자도 쉽게 사용할 수 있습니다. "
    "LM Studio는 모델 성능 모니터링(CPU, GPU, 메모리 사용량, 토큰/s)을 시각적으로 제공합니다.\n\n"
    "지원 플랫폼\n"
    "Windows(NVIDIA CUDA, AMD ROCm), macOS(Apple Silicon Metal, Intel), Linux를 지원합니다."
  )
},

}  # UPDATES dict end


def patch(item_id: str, payload: dict) -> dict:
    """PATCH /api/admin/tech/{id}"""
    cmd = [
        "curl", "-s", "-X", "PATCH",
        f"{BASE}/api/admin/tech/{item_id}",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-d", json.dumps(payload, ensure_ascii=False),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(result.stdout)


def get_all_items() -> list:
    cmd = [
        "curl", "-s",
        f"{BASE}/api/tech?size=100",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    data = json.loads(result.stdout)
    return data.get("items", [])


def main():
    print("Fetching all items...")
    items = get_all_items()
    print(f"Found {len(items)} items")

    # source_url -> id map
    url_to_id = {item["source_url"]: item["id"] for item in items}

    success = 0
    failed = 0
    not_found = 0

    for source_url, update in UPDATES.items():
        item_id = url_to_id.get(source_url)
        if not item_id:
            print(f"[NOT FOUND] {source_url}")
            not_found += 1
            continue

        payload = {}
        if "description" in update:
            payload["description"] = update["description"]
        if "tech_released_at" in update:
            payload["tech_released_at"] = update["tech_released_at"]

        result = patch(item_id, payload)

        if "id" in result:
            print(f"[OK] {result.get('title', source_url)}")
            success += 1
        else:
            print(f"[FAIL] {source_url}: {result}")
            failed += 1

    print(f"\nDone: {success} updated, {failed} failed, {not_found} not found")


if __name__ == "__main__":
    main()
