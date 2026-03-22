# Description Eval

이 문서는 스킬 `description`의 trigger 품질을 최적화하는 방법이 담겨 있다. 검증은 이 최적화 단계 안에 포함된다.

가장 중요한 점은 두 가지다.

- per-skill `description-evals.md`가 항상 사람이 읽는 source-of-truth다
- per-skill `evals/trigger-eval.json`에는 `{ "query": "...", "should_trigger": true|false }` 사례를 모아 둔다

이 문서는 특정 스크립트의 사용법 문서가 아니다. 자동화 도구가 있으면 활용할 수 있지만, 나중에 삭제되더라도 아래 로직과 기록 방식만 유지되면 description eval 시스템은 그대로 재현 가능해야 한다.

---

## 최적화 목적

- description trigger 경계를 설계하거나 수정할 때
- `evals/trigger-eval.json`을 만들거나 고칠 때
- train/test split을 확정할 때
- candidate description을 추가할 때
- iteration 결과를 기록하고 최종 description을 고를 때

---

## 핵심 산출물

- `description-evals.md`
  - 목표, 경계, split, candidate, decision log를 기록한다
- `evals/trigger-eval.json`
  - 실행 가능한 trigger eval 입력이다
  - 각 사례는 기본적으로 `query`와 `should_trigger`만 있으면 된다
- 결과 JSON 또는 표
  - iteration별 case 결과와 요약 점수를 남긴다
- 선택 사항: HTML 리포트
  - 사람이 비교하기 쉽게 도와주는 보조 산출물이다

---

## Description 최적화하기

### 좋은 Description 최적화란

description을 최적화에 중요한 것은 검증 기반 의도된 방식으로 스킬이 trigger 되는지 검증하고, 사용자에게 개선 방안을 이야기하면 지속적으로 검증/개선해서 의도된대로 skill이 trigger 되도록 하는 것이다.

### 좋은 테스트 케이스 작성 가이드

- positive와 negative를 둘 다 넣는다
- 기본 8개 테스트 케이스를 사용하며, 특별한 이유가 없으면 positive 5개, negative 3개로 맞춘다
- easy negative보다 인접한 negative를 우선 넣는다
- 실제 사용자가 할 법한 요청 문장으로 쓴다
- 한 번의 사용자 요청처럼 자연스럽게 쓴다
- 같은 실패 유형만 반복하지 말고 경계 사례를 넓게 섞는다
- 스킬 트리거 테스트인 만큼 프롬프트는 최대한 간략하게 작성한다.

### 평가의 핵심 로직

이 평가에서 보는 것은 "응답 품질"이 아니라 "이 description이 이 query에서 스킬을 떠올리게 하는가"다.

각 case는 아래 절차로 평가한다.

1. 실제 skill body는 유지한다
2. frontmatter의 `description`만 candidate 값으로 바꾼다(첫 검증에선 candidate가 없으므로 건너띔)
3. `codex exec`에 query를 넣고 실행한다
4. 그 실행에서 benchmark 대상 skill이 실제로 활성화됐는지 판정한다
5. 그 결과를 `triggered` 또는 `not triggered`로 기록한다

### Description 최적화 실행 절차

#### 1단계: 입력 파일(eval 스펙) 작성하기

입력 파일: `evals/trigger-eval.json`

새 파일은 항상 `query`를 필드로 사용한다. `prompt`는 legacy alias로만 취급한다.

```json
[
  {
    "query": "이 저장소에서 머지된 브랜치 정리용 Codex 스킬 하나 만들어줘.",
    "should_trigger": true
  },
  {
    "query": "파이썬 리스트 컴프리헨션 문법만 간단히 설명해줘.",
    "should_trigger": false
  }
]
```

이미 `evals/trigger-eval.json`이 준비되어 있고, 개선 작업에서 해당 문서를 개선해야 한다면 개선하나, 그렇지 않으면 건너뛰어도 된다.

#### 2단계: 워크 스페이스(테스트 환경) 생성/관리:

`<skill-name>-description-workspace`를 만든다. 이 안에서 `iteration-N/` 으로 관리한다. 각 iteration에는 오직 두 파일만 스냅샷한다.

- `SKILL.md` - 현재 description 또는 candidate description이 들어 있는 스냅샷
- `evals/trigger-eval.json` - 그 iteration에서 고정할 trigger test set

원본 skill 디렉토리의 다른 파일은 스냅샷하지 않는다. description trigger 평가는 응답 품질이 아니라 "이 description이 query에서 skill을 떠올리게 하는가"를 보는 것이므로, 이 두 파일만 있으면 된다.

#### 3단계 테스트 케이스 실행:

평가할 description 또는 candidate description 하나당, snapshot된 `SKILL.md` + `evals/trigger-eval.json` 쌍으로 같은 query set을 반복 실행한다.

기본 실행 설정:

- description 테스트를 위한 `codex exec` 호출 모델은 `GPT-5.3-Codex-Spark`를 사용한다
- reasoning effort 기본값은 `low`다
- query set 기본 크기는 `8`이다
- `Runs Per Query` 기본값은 `3`이다

각 run에서 반드시 지켜야 할 기준:

- skill body는 바꾸지 않는다
- description만 바꾼다. (candidate description을 스냅샷한 경우)
- 같은 query set을 쓴다
- 탐색 iteration끼리는 같은 codex exec model, reasoning effort, threshold를 쓴다
- trigger 판정 기준을 iteration 사이에서 바꾸지 않는다

##### case-level 결과 저장

각 case마다 최소 아래 항목을 남긴다.

```json
{
  "case_id": 1,
  "query": "이 저장소에서 머지된 브랜치 정리용 Codex 스킬 하나 만들어줘.",
  "should_trigger": true,
  "triggers": 2,
  "runs": 3,
  "trigger_rate": 0.67,
  "pass": true
}
```

#### 4단계: 점수 계산

점수 계산은 실행이 끝난 뒤 case별 `triggers`, `runs`, `trigger_rate`를 바탕으로 판정하는 단계다. 실행 설정 자체는 아래 `실행 절차` 섹션에서 정하고, 여기서는 pass/fail 계산 규칙만 다룬다.

case 단위 판정:

- positive case: `trigger_rate >= threshold`면 pass
- negative case: `trigger_rate < threshold`면 pass
- `trigger_rate = triggers / runs`

iteration 단위 요약:

- `passed`: 통과한 case 수
- `failed`: 실패한 case 수
- `total`: 전체 case 수
- `score`: 보통 `passed / total`

예를 들어 `should_trigger: true`인 case가 3회 중 2회 trigger되면 `2/3 = 0.67`이므로 pass다. `should_trigger: false`인 case가 3회 중 1회 trigger되면 `1/3 = 0.33`이므로 threshold 0.5 기준에서는 pass다.

#### 5단계: iteration 요약 문서 작성

iteration마다 최소 아래를 남긴다.

- 검증한 스냅샷 메타데이터와 description
- test summary
- 대표적인 false negative
- 대표적인 false positive
- 다음 iteration에서 무엇을 바꿀지에 대한 가설 (검증 데이터 또는 description 수정)

##### 출력 문서

문서는 description 검증 워크 스페이스에서 테스트 작업을 방금 완료한 iteration 안에 둔다.
문서 이름: `description-evals.md`

~~~

## Snapshot Metadata

- Skill Name: [skill-name]
- Iteration: [iteration-N]
- Baseline: [original | current-best | candidate]
- Skill Snapshot: [path/to/iteration-N/SKILL.md]
- Trigger Eval Snapshot: [path/to/iteration-N/evals/trigger-eval.json]
- Description Hash: [optional sha256]
- Eval Set Hash: [optional sha256]
- Threshold: [0.5]
- Runs Per Query: [3]
- Model: [GPT-5.3-Codex-Spark]

## Description Snapshot

```text
{{스냅샷한 description 본문}}
```

## Test Summary

- Total Queries: [N]
- Positive: [N]
- Negative: [N]
- Passed: [N]
- Failed: [N]
- Overall Score: [passed / total]
- Notable Pattern: [짧은 해석]

## False Positives / False Negatives

| Case ID | Query | Expected | Actual | Notes |
| --- | --- | --- | --- | --- |
| 001 | ... | should trigger | did not trigger | false negative |
| 002 | ... | should not trigger | triggered | false positive |
| 없음 |  |  |  |  |

## Next_Iteration

- Description change: [what to change]
- Eval change: [what to add/remove/split]
- Reason: [why this is the best next move]
- Confidence / Risk: [optional]
~~~


#### 6단계: 사용자 피드백

이전 단계 요약 문서를 바탕으로 사용자와 대화 또는 반영할 개선점을 피드백 받고 어떤 식으로 개선할 지에 대해 논의하고 사용자가 허락하면 다음 iteration 단계에서 candidate description과 개선할 eval 테스트 케이스 포인트를 반영한다.

이 다섯 가지가 비어 있으면 점수만 남아 있어도 decision quality를 검증하기 어렵다.

### 리포트와 시각화

- HTML 리포트는 보조 도구다
- JSON 스키마는 `references/schemas.md`를 참고한다

---
