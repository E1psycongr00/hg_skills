---
name: codex-skill-creator
description: 새 스킬을 만들고, 기존 스킬을 수정하고 개선하며, 스킬 성능을 측정합니다. 사용자가 스킬을 처음부터 만들고 싶어 하거나, 기존 스킬을 편집 또는 최적화하려 하거나, eval을 실행해 스킬을 테스트하려 하거나, 분산 분석이 포함된 벤치마크를 돌리거나, 더 정확하게 트리거되도록 스킬 설명을 최적화하려 할 때 사용하세요.
---

새 스킬을 만들고, 테스트하고, 반복적으로 개선할 수 있는 스킬이어야 한다.

## 큰 흐름

- 스킬의 목표, 기대 결과, 성공 기준을 정한다.
- SKILL.md 초안을 만들고, description과 본문의 책임을 분리한다.
- 현실적인 테스트 프롬프트와 eval 데이터를 준비한다.
- benchmark와 사람 리뷰를 통해 결과를 평가한다.
- 사용자 피드백과 실행 기록을 바탕으로 스킬을 개선한다.
- 만족할 때까지 반복한 뒤 description 최적화와 패키징으로 마무리한다.

---

## 좋은 스킬 철학

- 단순 지식 저장소가 아니라 재사용 가능한 절차 지식 패키지여야 한다.
- 넓은 만능형보다, 특정 작업을 더 빠르고 일관되게 수행하는 좁고 깊은 스킬이 좋다.
- 적은 설명으로도 목표에 맞는 절차를 재현할 수 있어야 한다.
- 필요할 때만 깊게 읽는 구조를 선호한다. 본문은 짧고, 참조 파일과 스크립트는 선택적으로 불러오게 한다.
- trigger 경계는 description에서 정하고, 본문은 이미 선택된 뒤의 실행 절차에 집중한다. 자세한 기준은 아래 `description과 본문 경계` 섹션을 따른다.

---

## 사용자와 소통

작업을 시작하기 전에 사용자 요구사항으로부터 스킬 작성 또는 재작성에 필요한 맥락을 명확히 얻어야 한다. 좋은 스킬을 만들기 위한 맥락 수집을 분명히 하고, 사용자의 요구사항을 비판적으로 읽어 아쉬운 점이나 위험한 점도 함께 짚어라.

소통할 때는 전문 용어를 늘어놓기보다, 사용자가 지금 결정을 내리는 데 필요한 정보만 정확하게 전달하는 것이 중요하다. 확신이 없다면 용어를 짧게 풀어서 설명하고, 이해할지 애매하면 간단한 정의를 덧붙여도 좋다.

---

## 스킬 생성하기

### 의도 파악

현재 대화 자체에 이미 스킬로 만들고 싶은 워크플로가 담겨 있을 수도 있다. 사용자가 "이걸 스킬로 만들어줘"라고 말하면, 먼저 대화 기록에서 다음 정보를 최대한 추출해라.

- 어떤 도구를 썼는지
- 어떤 단계 순서로 진행했는지
- 사용자가 어떤 수정을 요구했는지
- 어떤 입력/출력 형식이 관찰됐는지

비어 있는 부분만 사용자에게 물으면 된다. 특히 다음 두 가지는 초기에 분명히 해 둬라.

1. 이 요구가 좋은 스킬 후보인지, 불필요하거나 위험한 부분은 없는지
2. 스킬이 제대로 동작하는지 확인할 테스트 케이스를 만들지

### 인터뷰와 리서치

엣지 케이스, 입력/출력 형식, 예시 파일, 성공 기준, 의존성을 먼저 적극적으로 질문하세요. 이 부분이 정리되기 전에는 테스트 프롬프트를 쓰지 마세요.

기존 스킬 초안이나 유사 스킬이 있다면 먼저 읽고, 필요한 경우 관련 스크립트와 참조 문서도 확인해라. 이미 환경에서 확인할 수 있는 정보는 다시 사용자에게 묻지 않는 편이 좋다.

### SKILL.md 작성하기

사용자 인터뷰 내용을 바탕으로 다음 요소를 채우세요.

- **name**: 스킬 식별자
- **description**: 언제 트리거되는지, 무엇을 하는지. 이 필드가 스킬을 떠올리게 하는 가장 중요한 단서다.
- **compatibility**: 필요한 도구나 의존성(선택 사항이며, 실제로는 드물게만 필요하다)
- **나머지 스킬 본문**: 스킬이 이미 선택된 뒤 따라야 하는 실행 지침

#### description과 본문 경계

- `description`의 책임: 언제 이 스킬을 써야 하는지, 언제 쓰지 말아야 하는지, 어떤 경계 사례에서 이 스킬이 맞는지 요약한다.
- `SKILL.md` 본문의 책임: 스킬이 이미 선택된 뒤 무엇을 해야 하는지 설명한다. 작업 순서, 입력/출력 형식, 체크리스트, 참조 파일/스크립트 사용 조건, 방향성등 같은 스킬 운영에 필요한 내용만 둔다.
- 본문에는 `언제 사용`, `사용 범위`, `트리거 조건`, `should trigger`, `when to use`, `do not use` 같은 섹션이나 문장을 만들지 마라. 이런 내용은 description으로 옮겨라.
- 본문 최종 점검 때는 "이 문장이 스킬을 고르는 기준인가, 고른 뒤 실행하는 기준인가?"를 확인해라. 고르는 기준이면 description으로 이동한다.

### 스킬 작성 가이드

#### 스킬의 구성

```text
skill-name/
├── SKILL.md (필수)
│   ├── YAML frontmatter (name, description 필수)
│   └── Markdown 지침
└── Bundled Resources (선택)
    ├── scripts/    - 결정적이거나 반복적인 작업을 처리하는 실행 코드
    ├── references/ - 필요할 때만 읽어들이는 문서
    └── assets/     - 출력에 사용하는 파일(템플릿, 아이콘, 글꼴 등)
```

#### 점진적 공개

스킬은 3단계 로딩 구조를 사용한다.

1. **메타데이터** (name + description) - 항상 컨텍스트에 들어간다
2. **SKILL.md 본문** - 스킬이 트리거되면 컨텍스트에 들어간다
3. **번들 리소스** - 필요할 때만 사용한다

실무 기준으로는 다음을 권장한다.

- SKILL.md는 가능하면 500줄 이하로 유지한다.
- 참조 파일은 언제 읽어야 하는지까지 포함해서 분명하게 가리킨다.
- 큰 참조 파일(300줄 이상)에는 목차를 둔다.

하나의 스킬이 여러 도메인이나 프레임워크를 지원한다면, 변형별로 나누어 정리하는 편이 좋다.

```text
cloud-deploy/
├── SKILL.md (워크플로 + 선택 기준)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

#### 놀라움이 없어야 한다는 원칙

스킬에는 악성코드나 익스플로잇 코드, 또는 시스템 보안을 해칠 수 있는 내용이 들어가면 안 된다. 스킬 내용은 설명된 사용자 의도 기준으로 봤을 때 놀랍거나 숨겨진 동작을 해서는 안 된다. 사용자를 오도하는 스킬, 무단 접근이나 데이터 유출 등 악의적 목적을 돕는 요청에는 동조하지 마라.

#### 작성 패턴

지침은 가급적 명령형으로 쓰세요.

**출력 형식 정의**는 이런 식으로 할 수 있습니다.

```markdown
## 보고서 구조
항상 정확히 이 템플릿을 사용하세요:
# [제목]
## 요약
## 핵심 발견
## 권장 사항
```

**예시 패턴**도 유용하다.

```markdown
## 커밋 메시지 형식
**예시 1:**
입력: JWT 토큰 기반 사용자 인증 추가
출력: feat(auth): implement JWT-based authentication
```

### 글쓰기 스타일

무조건 따라야 하는 규칙을 늘어놓기보다는, 왜 중요한지 모델이 이해하도록 설명해라. 스킬을 특정 예시에 과적합시키지 말고 일반적으로 유용하도록 만들고, 초안을 쓴 뒤에는 한 걸음 물러나 새 눈으로 다시 보고 개선해라.

### 테스트 케이스

스킬 초안을 쓴 뒤에는 실제 사용자가 정말 이렇게 말할 법한 2~3개의 현실적인 테스트 프롬프트를 만든다. 사용자에게 먼저 보여 주고 방향을 확인한 뒤 실행해라.

테스트 케이스는 `evals/evals.json`에 저장해라. 아직 assertion은 쓰지 말고 프롬프트만 먼저 넣는다. assertion은 다음 단계에서 실행이 진행되는 동안 작성하면 된다.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "사용자 작업 프롬프트",
      "expected_output": "기대 결과 설명",
      "files": [
        {
          "source": "evals/files/example/package.json",
          "target": "package.json"
        }
      ]
    }
  ]
}
```

전체 스키마(나중에 추가할 `assertions` 필드 포함)는 `references/schemas.md`를 참고하세요.

## 테스트 케이스 실행과 평가

이 섹션은 하나의 연속된 흐름이다. 중간에서 멈추지 마라. `/skill-test`나 다른 테스트용 스킬은 사용하면 안 된다.

### 0단계: setup으로 iteration scaffold 만들기

결과는 가능한 한 benchmark 전용 clean root(예: `~/.codex/isolated-runs/skill-bench/<skill-name>/`) 아래에 저장한다. 워크스페이스 안에서는 `iteration-N/`으로 정리하고, 각 테스트 케이스는 `eval-N/` 디렉터리를 쓴다. 사람이 읽는 설명적인 이름은 `eval_metadata.json`의 `eval_name`에 넣고, 특별한 이유가 있을 때만 `--workspace-root`로 위치를 바꾼다.

벤치마크용 디렉터리 scaffold, `eval_metadata.json`, `run_prompt.md`, 입력 파일 staging, `with_skill`용 `.agents/skills/` 복사본 준비는 수동으로 하지 말고 `scripts/setup_benchmark.py`를 기본 진입점으로 사용하세요.

```bash
python -m scripts.setup_benchmark <path/to/skill-folder>
```

기존 스킬 개선처럼 baseline이 `old_skill`인 경우에는 스냅샷된 이전 스킬 경로를 함께 넘긴다.

```bash
python -m scripts.setup_benchmark <path/to/skill-folder> \
  --baseline old_skill \
  --old-skill-path <path/to/old-skill-snapshot>
```

setup이 끝난 뒤에는 각 eval 아래에 최소한 다음 정보가 준비되어 있어야 한다.

- `eval_metadata.json`
- `with_skill/run-1/` 또는 baseline run 디렉터리
- `run_prompt.md`, `outputs/`, `container/workspace/`, `container/workspace_contract.json`

`eval_metadata.json`은 setup 스크립트가 생성한다. 이 파일에는 적어도 `eval_id`, `eval_name`, `prompt`, `files`, `assertions`가 들어 있어야 한다.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "사용자의 작업 프롬프트",
  "files": [],
  "assertions": []
}
```

### 1단계: benchmark runner 실행하기

실행의 최소 단위는 `eval × config × run`이다. run 하나는 `codex exec` 프로세스 1회에 대응한다. benchmark 실행도 수동으로 queue를 운영하지 말고 `scripts/run_benchmark.py`를 기본 진입점으로 사용하세요.

```bash
python -m scripts.run_benchmark <workspace>/iteration-N
python -m scripts.run_benchmark <workspace>/iteration-N --resume
```

실행 규칙은 다음을 따른다.

- config 이름은 기본적으로 `with_skill`과 `without_skill`를 사용한다. 기존 스킬 개선의 baseline config는 `old_skill`을 사용한다.
- 기본 실행 정책은 config당 `run-1`만이다. 사용자가 반복 실행을 명시적으로 요청한 경우에만 최대 `run-3`까지 확장한다.
- 같은 eval의 `with_skill/run-K`와 baseline `run-K`는 항상 같은 배치로 시작한다.
- 동시에 살아 있는 `codex exec` 프로세스 총합은 6을 넘기지 않는다.
- 기본 benchmark runner는 pair 단위 rolling queue를 적용한다. 슬롯이 비면 다음 eval pair를 자동으로 넣는다.

격리 규칙은 이 섹션의 canonical 기준이다.

- 각 run의 실제 cwd는 보통 `<run>/container/`로 잡고, 프로젝트 파일은 그 아래 `workspace/`에 둔다.
- `with_skill` 실행에는 benchmark 대상 스킬을 `container/.agents/skills/` 아래에 보이게 준비하되 `evals/` 디렉터리는 복사하지 않는다.
- baseline(`without_skill`)에는 benchmark 대상 스킬을 `container/.agents/skills/`에 두지 않고, prompt에도 benchmark 대상 스킬의 이름, description, path, 참조 파일 경로를 직접 넣지 않는다.
- `old_skill` baseline은 스냅샷된 이전 스킬만 `container/.agents/skills/` 아래에 두고, 현재 편집 중인 스킬 경로는 넘기지 않는다.
- `run_prompt.md`는 가능하면 `container/` 기준 상대경로를 쓰고, 프롬프트 안에서는 `workspace/`를 사용자의 프로젝트 루트처럼 취급하게 한다.
- run prompt에는 읽기/수정 범위가 `workspace/` 아래로 제한된다는 점과, 최종 결과물 및 transcript 출력 위치를 분명히 적는다.

실행 환경 기본값도 이 섹션을 기준으로 삼는다.

- benchmark나 eval 목적으로 실행하는 `codex exec` 호출 모델은 항상 `gpt-5.4-mini`로 고정한다.
- 기본 runner는 내부적으로 `--json`, `--ephemeral`, `--skip-git-repo-check`, `workspace-write` sandbox를 사용한다.
- `js_repl`은 명시적으로 enable 하고, 프롬프트에서는 필요 시 파일 입출력에 사용할 수 있다고 알려 주는 편이 좋다.
- 실행 로그는 `codex-events.jsonl`, `codex-stderr.log`, `run_provenance.json`에 남긴다.

### 2단계: 실행 중 assertion 초안 만들기

queue가 비거나 현재 실행 중인 eval들이 끝나기만 기다리지 마세요. benchmark가 돌아가는 동안 각 테스트 케이스의 정량 assertion을 초안으로 만들고, 이미 끝난 eval 중 assertion이 정리된 것은 바로 grading 준비 단계로 넘겨라.

좋은 assertion은 객관적으로 검증 가능하고, 이름만 읽어도 무엇을 본다는 게 드러나야 한다. 문체나 디자인처럼 사람이 판단해야 하는 부분에 assertion을 억지로 만들지 마라.

초안을 다 만들었다면 `eval_metadata.json`과 `evals/evals.json` 둘 다 업데이트해라. 보통은 **assertion 작성 -> 막 끝난 eval의 grading 준비 -> 다음 eval pair 투입** 순서로 움직이면 된다.

### 3단계: timing 데이터 저장하기

기본 benchmark runner는 각 `codex exec` 실행 직전에 시각을 기록하고(`executor_start`), 프로세스가 끝나는 즉시 종료 시각을 기록한다(`executor_end`). 이 둘의 차이로 `duration_ms`, `total_duration_seconds`, `executor_duration_seconds`를 계산해 해당 `run-*` 디렉터리의 `timing.json`에 저장한다. `codex exec --json` 이벤트 로그에서 `total_tokens`를 얻을 수 있다면 함께 저장하고, 얻지 못했다면 `0` 또는 미기록으로 두어도 된다.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3,
  "executor_start": "2026-01-15T10:30:00Z",
  "executor_end": "2026-01-15T10:30:23Z",
  "executor_duration_seconds": 23.3
}
```

가능하면 `codex-events.jsonl`과 `codex-stderr.log`도 함께 남겨라. grading runner가 뒤에서 timing 파일에 정보를 추가하더라도 executor timing 필드는 그대로 보존해야 한다.

### 3.5단계: 격리 상태 점검하기

벤치마크가 끝난 뒤에는 "with/without이 정말 분리됐는가?"를 따로 확인하세요. pass rate가 비슷하게 나왔을 때 특히 중요하다.

- `with_skill` transcript에는 스킬을 읽었거나 스킬 path를 사용했다는 흔적이 있는가?
- `without_skill` 쪽 `run_prompt.md`, transcript, report, user notes에는 benchmark 대상 스킬의 이름/path/description이 직접 새어 들어가지 않았는가?
- `run_provenance.json`이 있다면 `executor`, `configuration`, `skill_path_requested`, `baseline_type`, `prompt_path`, `command` 같은 메타데이터를 확인한다.

가능하면 이 점검 결과를 `isolation_report.md` 같은 메모 파일로 남겨라. baseline 오염 가능성이나 skill 적용 증거 부족이 보이면, 그 iteration의 benchmark 결과는 강한 결론의 근거로 쓰지 않는 편이 좋다.

### 4단계: 채점, 집계, 리뷰어

개별 eval의 grading은 전체 iteration 종료 전에도 앞당겨 시작할 수 있다. 다만 최종 `benchmark.json` 집계와 리뷰어 생성은 모든 실행과 grading이 끝난 뒤에 진행해라.

1. **채점**: `scripts.run_grading.py`를 기본 진입점으로 사용한다. `grading.json`의 expectations 배열은 반드시 `text`, `passed`, `evidence` 필드를 사용해야 한다.
2. **집계**: `scripts.aggregate_benchmark`로 `benchmark.json`과 `benchmark.md`를 만든다.
3. **분석**: `agents/analyzer.md`를 기준으로 구분력 없는 assertion, 분산이 큰 eval, 시간/토큰 tradeoff를 읽는다.
4. **리뷰어 생성**: `generate_review.py`로 정성/정량 결과를 함께 보여 주는 리뷰어를 만든다.

```bash
python -m scripts.run_grading <workspace>/iteration-N
python -m scripts.run_grading <workspace>/iteration-N --resume
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
nohup python <codex-skill-creator-path>/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  > /dev/null 2>&1 &
VIEWER_PID=$!
```

iteration 2 이상에서는 `--previous-workspace <workspace>/iteration-<N-1>`도 함께 넘긴다.

리뷰어를 사용자에게 안내할 때는 다음 정도만 짧게 설명하면 된다.

- "Outputs" 탭: 프롬프트, 결과물, 이전 결과, 피드백
- "Outputs" 탭의 `AI Eval Feedback`: grader가 남긴 eval 개선 제안과 총평
- "Benchmark" 탭: pass rate, 시간, 토큰, 분석 메모
- 검토가 끝나면 "Submit All Reviews"로 `feedback.json`을 저장

### 5단계: 피드백 읽기

사용자가 검토를 마쳤다고 알려 오면 `feedback.json`을 읽고, 각 run의 `grading.json`에 들어 있는 `eval_feedback`도 함께 확인해라. 빈 사용자 피드백은 큰 문제가 없었다는 뜻이고, grader가 남긴 assertion 개선 제안이나 총평은 다음 iteration에서 eval 설계를 다듬는 입력으로 사용하면 된다.

리뷰어 서버를 띄웠다면 작업이 끝난 뒤 종료한다.

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## 스킬 개선하기

이 부분이 반복 루프의 핵심이다. 테스트 케이스를 돌렸고, 사용자가 결과를 검토했고, 이제 그 피드백을 바탕으로 스킬을 더 좋아지게 만들어야 한다.

### 개선을 어떻게 생각할 것인가

1. **피드백에서 일반화할 것.** 지금 보고 있는 예시 몇 개에만 맞는 스킬이 되지 않도록, 반복되는 근본 문제를 찾아라.
   사람 피드백뿐 아니라 grader의 `eval_feedback`, analyzer 메모도 함께 읽고 일반화하라.
2. **프롬프트를 날렵하게 유지할 것.** transcript까지 읽고, 모델이 비생산적인 일에 시간을 낭비하게 만드는 지침은 걷어내라.
3. **왜 그런지 설명할 것.** 지나치게 딱딱한 MUST 나열보다, 왜 중요한지 이해시키는 쪽이 더 강력하다.
4. **반복되는 작업은 번들화할 것.** 여러 eval에서 비슷한 스크립트를 계속 쓰면 `scripts/`로 올리는 편이 낫다.

### 반복 루프

스킬을 개선한 뒤에는 다음 순서로 진행한다.

1. 스킬에 개선 사항을 반영한다.
2. 모든 테스트 케이스를 새로운 `iteration-<N+1>/` 디렉터리로 다시 실행한다. baseline도 포함한다.
3. 리뷰어를 다시 띄우고, 필요하면 `--previous-workspace`로 이전 iteration을 연결한다.
4. 사용자가 검토를 마치고 알려 줄 때까지 기다린다.
5. 새 피드백을 읽고 다시 개선한다.

다음 중 하나가 될 때까지 계속한다.

- 사용자가 만족한다고 말할 때
- 피드백이 전부 비어 있을 때
- 더 이상 의미 있는 개선이 나오지 않을 때

---

## 고급 기능: 블라인드 비교

두 버전의 스킬을 더 엄밀하게 비교하고 싶을 때는 `agents/comparator.md`와 `agents/analyzer.md`를 읽고 블라인드 비교를 수행할 수 있다. 이 기능은 선택 사항이며, 대부분의 사용자에게는 사람이 직접 보는 리뷰 루프만으로도 충분하다.

---

## description 최적화

SKILL.md frontmatter의 description 필드는 AI가 스킬을 사용할지 결정하는 핵심 기준이다. description 최적화나 검증을 하려면, **반드시** `references/description-optimize.md`를 먼저 읽고 그 문서를 canonical workflow로 따라라.

이 루프는 skill benchmark와 목적이 다르다. skill benchmark는 실행 품질을 보고, description 최적화는 trigger 경계를 검증한다. 둘을 같은 기준으로 섞어 해석하지 마라.

---

### 패키징 및 전달 (`present_files` 도구가 있을 때만)

`present_files` 도구를 사용할 수 있는지 먼저 확인하세요. 없다면 이 단계는 건너뜁니다. 사용할 수 있다면 스킬을 패키징하고 `.skill` 파일을 사용자에게 제시하세요.

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

기존 스킬 업데이트인 경우에는 원래 이름을 유지하고, 읽기 전용 경로일 수 있으니 먼저 쓰기 가능한 위치로 복사한 뒤 패키징하는 편이 좋다.

---

## Codex 또는 헤드리스 실행 지침

이 섹션은 위 benchmark workflow를 다시 설명하는 곳이 아니다. 아래 차이점만 추가로 적용한다.

- 브라우저를 열 수 없거나 디스플레이가 없는 환경이라면, 리뷰어는 `generate_review.py --static <output_path>`로 생성한다.
- timing/token 기록이 불안정한 환경이라면 `timing.json`보다 `grading.json`, `benchmark.json`, 사용자 피드백처럼 재현 가능한 산출물을 우선한다.
- description 최적화는 계속 `references/description-optimize.md`를 source of truth로 사용한다.
- 패키징은 동일하게 `package_skill.py`로 진행하면 된다.

---

## 참조 파일

`agents/` 디렉터리에는 전문 역할용 서브에이전트 지침이 들어 있다. 해당 역할의 서브에이전트를 띄워야 할 때 읽어라.

- `agents/grader.md` — assertion을 출력 결과에 대조해 평가하는 방법
- `agents/comparator.md` — 블라인드 A/B 비교를 수행하는 방법
- `agents/analyzer.md` — 어떤 버전이 왜 이겼는지 분석하는 방법

`references/` 디렉터리에는 추가 문서가 있다.

- `references/description-optimize.md` — description trigger 개선/검증 및 최적화용 운영 reference
- `references/schemas.md` — `evals.json`, `grading.json` 등 JSON 구조 정의

빠른 체크리스트:

- 스킬의 목표와 성공 기준을 정한다.
- 초안 작성 후 benchmark와 사람 리뷰로 검증한다.
- 피드백을 반영해 반복 개선한다.
- 마지막에 description 최적화와 패키징으로 마무리한다.
