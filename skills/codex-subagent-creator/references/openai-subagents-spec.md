# OpenAI Codex Custom Agent File Notes

공식 문서를 바탕으로 Codex custom agent TOML 파일을 설계할 때 바로 참고할 핵심만 정리했다.

## 출처

- Subagents: https://developers.openai.com/codex/subagents
- Subagent concepts: https://developers.openai.com/codex/concepts/subagents
- Codex Prompting Guide: https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide

확인 기준일: 2026-04-03

## 이 문서의 범위

- 이 문서는 `.codex/agents/*.toml` 같은 custom agent 파일 스키마와 작성 원칙만 다룬다.
- `.codex/config.toml`의 `[agents]`, `max_threads`, `max_depth`, `job_max_runtime_seconds` 같은 프로젝트 전역 런타임 설정은 다루지 않는다.

## 파일 위치

- 개인 범위: `~/.codex/agents/`
- 프로젝트 범위: `.codex/agents/`

각 TOML 파일은 하나의 custom agent를 정의한다.

## 이 스킬의 로컬 규칙

공식 문서상 `name`이 source of truth이지만, 이 저장소의 `codex-subagent-creator`는 더 엄격한 규칙을 쓴다.

- `.codex/agents/<basename>.toml`의 `<basename>`과 TOML 내부 `name`은 완전히 같아야 한다.
- 하이픈과 언더스코어 차이도 불일치로 본다.
- 파일명과 `name`의 정합성은 설명으로 예외 처리하지 않는다.

## 필수 필드

모든 standalone custom agent 파일에는 다음 필드가 필요하다.

- `name`
- `description`
- `developer_instructions`

공식 문서의 설명:

- `name`: Codex가 이 agent를 스폰하거나 참조할 때 쓰는 식별자
- `description`: 사람이 읽는 호출 가이드. Codex가 언제 이 agent를 써야 하는지 설명
- `developer_instructions`: 실제 동작을 정의하는 핵심 운영 지침

## 자주 쓰는 선택 필드

- `nickname_candidates`
- `model`
- `model_reasoning_effort`
- `sandbox_mode`
- `mcp_servers`
- `skills.config`

이 값을 생략하면 부모 세션의 설정을 상속한다.

## 설계 원칙

공식 문서가 강조하는 핵심:

- 좋은 custom agent는 narrow and opinionated 하다.
- 각 agent에는 clear job, matching tool surface, anti-drift instructions가 있어야 한다.
- 읽기 중심 병렬화가 먼저이고, 쓰기 중심 병렬화는 충돌 비용을 신중히 본다.

실무 해석:

- 탐색과 수정은 분리하는 편이 안전하다.
- 리뷰와 구현을 한 agent에 섞으면 경계가 흐려진다.
- 큰 작업은 "누가 무엇을 소유하는가"가 보이도록 쪼갠다.

## 모델 선택 메모

Subagent concepts 문서 기준:

- `gpt-5.4`: 대부분의 agent에 대한 기본값. 코디네이션, 애매한 판단, 복합 작업에 적합
- `gpt-5.4-mini`: 빠르고 가벼운 읽기 중심 스캔, 대량 탐색, 보조 조사
- `gpt-5.3-codex-spark`: 텍스트 중심의 초저지연 반복 작업이 중요할 때

`model_reasoning_effort` 가이드:

- `high`: 복잡한 로직 추적, 리뷰, 보안, 엣지 케이스 점검
- `medium`: 대부분의 일반 작업 기본값
- `low`: 단순하고 빠른 작업

## 샌드박스와 도구 경계 메모

- 탐색, 리뷰, 문서 검증은 기본적으로 `read-only`
- 코드 수정이나 파일 생성이 실제 목표일 때만 `workspace-write`
- 도구 권한이 커질수록 역할 범위를 더 좁게 적는다
- 브라우저나 MCP가 핵심 의존성이면 필요한 이유가 agent 설명과 지침에 보여야 한다

## TOML 기본 골격

```toml
name = "agent_name"
description = "Human-facing guidance for when Codex should use this agent."
model = "gpt-5.4"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
developer_instructions = """
State the mission.
State the priorities.
State the evidence or tool expectations.
State the boundaries and handoff format.
"""
```

## 예시 패턴

### 읽기 전용 탐색

```toml
name = "code_mapper"
description = "Read-only codebase explorer for locating the relevant code path."
model = "gpt-5.4-mini"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
developer_instructions = """
Map the code that owns the reported behavior.
Identify entry points, state transitions, and likely files before any edits begin.
Do not propose or apply fixes unless the parent agent explicitly asks.
Return concise evidence with file references.
"""
```

### 구현 전용 수정자

```toml
name = "ui_fixer"
description = "Implementation-focused agent for small, targeted fixes after the issue is understood."
model = "gpt-5.4"
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"
developer_instructions = """
Own the fix once the failure mode is clear.
Make the smallest defensible change.
Do not revert unrelated edits.
Validate only the behavior you changed and report what remains uncertain.
"""
```
