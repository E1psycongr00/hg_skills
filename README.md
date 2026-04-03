# hg_skills

Codex용 스킬을 모아두는 저장소입니다. 이 저장소는 `skills/` 디렉터리를 기준으로 `npx skills`에서 바로 탐지할 수 있도록 구성되어 있습니다.

## 포함된 스킬

### `codex-skill-creator`

새 스킬을 만들고, 기존 스킬을 개선하고, 평가와 벤치마크를 돌리며 반복적으로 다듬을 때 쓰는 스킬입니다.

이 스킬은 Anthropic의 [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) 스킬에서 영향을 받아 만들어졌습니다.

다음과 같은 작업에 잘 맞습니다.

- 새 스킬의 `SKILL.md` 초안 작성
- 기존 스킬의 workflow 정리 및 리팩터링
- eval 케이스 작성과 결과 검토
- description 최적화로 트리거 정확도 개선

### `harness-loop`

목표 한 줄만 받아 Codex가 프로젝트를 온보딩하고, `.codex/harness-loop/project-slug/` 아래에 `memories/`와 `001-fix-login-flow/iteration-01/` 같은 goal/iteration 기록을 누적하면서 계획, 실행, 검증, 학습 루프를 자율적으로 운영하도록 돕는 스킬입니다.

다음과 같은 작업에 잘 맞습니다.

- "이 목표로 알아서 진행해"처럼 최소 입력만 주고 자율 실행시키기
- 프로젝트별 맥락과 반복 규칙을 외부 저장소에 축적하기
- 지난 실행의 `next.md`, `evaluations/`, memories를 읽고 이어서 개선하기
- 실행 후 다음 시도를 위한 피드백, 선호사항, 실패 패턴, 학습 내용을 남기기

### `codex-subagent-creator`

Codex의 `.codex/agents/*.toml` 커스텀 서브 에이전트를 반복해서 설계하고 작성할 때 쓰는 스킬입니다.

다음과 같은 작업에 잘 맞습니다.

- 특정 반복 업무에 맞는 reviewer, explorer, fixer, docs researcher agent 설계
- 하나의 작업을 여러 역할로 분해한 agent 세트 구성
- `name`, `description`, `developer_instructions`, `model`, `sandbox_mode` 등을 포함한 TOML 초안 작성
- `.codex/config.toml` 전역 설정이나 부모 프롬프트가 아니라 agent TOML 자체를 좁고 선명하게 설계

## 설치 방법

GitHub 저장소에서 바로 설치할 수 있습니다.

권장 방식:

```bash
npx skills add E1psycongr00/hg_skills -a codex
```

GitHub 주소를 그대로 써도 됩니다.

```bash
npx skills add https://github.com/E1psycongr00/hg_skills.git -a codex
```

설치 후에는 Codex를 다시 시작하면 스킬이 반영됩니다.

## 현재 포함된 스킬 요약

- `codex-skill-creator`: 새 스킬 작성, 기존 스킬 개선, eval 작성, 벤치마크, description 최적화를 돕는 스킬
- `harness-loop`: 프로젝트 온보딩, goal/iteration 기반 자율 실행, 평가 기록, 장기 기억 축적을 묶어서 운영하는 스킬
- `codex-subagent-creator`: Codex custom subagent TOML 설계, 역할 분해, 모델/샌드박스 선택을 agent 파일 중심으로 정리하는 스킬
