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
