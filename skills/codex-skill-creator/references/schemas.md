# JSON 스키마

이 문서는 `codex-skill-creator`에서 사용하는 JSON 스키마를 정의합니다.

---

## trigger-eval.json

description trigger eval의 입력 파일입니다. 각 skill 디렉터리의 `evals/trigger-eval.json`에 위치합니다.

```json
[
  {
    "query": "이 작업을 자동화하는 Codex 스킬을 만들어줘",
    "should_trigger": true
  },
  {
    "query": "자바스크립트 클로저 개념만 설명해줘",
    "should_trigger": false
  }
]
```

**필드 설명**

- 각 항목은 하나의 trigger test case입니다
- `query`: 실행할 사용자 요청 문자열. 새 파일에서는 항상 이 필드를 사용하세요
- `should_trigger`: 이 query에서 skill이 활성화되어야 하는지 여부
- `prompt`: 하위 호환용 별칭. 기존 파일에서만 허용하며, 새 파일에서는 쓰지 않는 편이 좋습니다
- `case_id`: 선택 사항. 없으면 runner가 입력 순서대로 부여합니다

---

## evals.json

스킬용 eval을 정의합니다. 스킬 디렉터리 안의 `evals/evals.json`에 위치합니다.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "사용자 예시 프롬프트",
      "expected_output": "기대 결과 설명",
      "files": [
        {
          "source": "evals/files/sample1.pdf",
          "target": "docs/sample1.pdf"
        }
      ],
      "expectations": [
        "출력에 X가 포함되어야 한다",
        "스킬이 스크립트 Y를 사용해야 한다"
      ]
    }
  ]
}
```

**필드 설명**

- `skill_name`: 스킬 frontmatter의 이름과 일치해야 함
- `evals[].id`: 고유한 정수 식별자
- `evals[].prompt`: 실행할 작업
- `evals[].expected_output`: 성공 조건을 사람이 읽기 쉽게 설명한 문장
- `evals[].files`: 입력 fixture 목록(선택 사항)
- 문자열 항목은 스킬 루트 기준 상대 경로 source로 해석됨
- 객체 항목은 `{ "source": "...", "target": "..." }` 형태를 사용
- `source`: 스킬 루트 기준 fixture 경로
- `target`: benchmark container의 `workspace/` 기준 상대 경로
- `evals[].expectations`: 검증 가능한 기대 조건 목록

---

## history.json

Improve 모드에서 버전 진행 이력을 추적합니다. 워크스페이스 루트에 위치합니다.

```json
{
  "started_at": "2026-01-15T10:30:00Z",
  "skill_name": "pdf",
  "current_best": "v2",
  "iterations": [
    {
      "version": "v0",
      "parent": null,
      "expectation_pass_rate": 0.65,
      "grading_result": "baseline",
      "is_current_best": false
    },
    {
      "version": "v1",
      "parent": "v0",
      "expectation_pass_rate": 0.75,
      "grading_result": "won",
      "is_current_best": false
    },
    {
      "version": "v2",
      "parent": "v1",
      "expectation_pass_rate": 0.85,
      "grading_result": "won",
      "is_current_best": true
    }
  ]
}
```

**필드 설명**

- `started_at`: 개선 시작 시점의 ISO 타임스탬프
- `skill_name`: 개선 중인 스킬 이름
- `current_best`: 현재 최고 성능 버전 식별자
- `iterations[].version`: 버전 식별자(`v0`, `v1`, ...)
- `iterations[].parent`: 어떤 부모 버전에서 파생되었는지
- `iterations[].expectation_pass_rate`: 채점 결과 기준 통과율
- `iterations[].grading_result`: `"baseline"`, `"won"`, `"lost"`, 또는 `"tie"`
- `iterations[].is_current_best`: 현재 최고 버전 여부

---

## grading.json

grader 에이전트의 출력입니다. `<run-dir>/grading.json`에 위치합니다.

```json
{
  "expectations": [
    {
      "text": "출력에 'John Smith'라는 이름이 포함된다",
      "passed": true,
      "evidence": "Transcript 3단계에서 확인됨: 'Extracted names: John Smith, Sarah Johnson'"
    },
    {
      "text": "스프레드시트 B10 셀에 SUM 수식이 있다",
      "passed": false,
      "evidence": "스프레드시트가 생성되지 않았고, 출력은 텍스트 파일이었다."
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "total": 3,
    "pass_rate": 0.67
  },
  "execution_metrics": {
    "tool_calls": {
      "Read": 5,
      "Write": 2,
      "Bash": 8
    },
    "total_tool_calls": 15,
    "total_steps": 6,
    "errors_encountered": 0,
    "output_chars": 12450,
    "transcript_chars": 3200
  },
  "timing": {
    "executor_duration_seconds": 165.0,
    "grader_duration_seconds": 26.0,
    "total_duration_seconds": 191.0
  },
  "claims": [
    {
      "claim": "양식에는 채울 수 있는 필드가 12개 있다",
      "type": "factual",
      "verified": true,
      "evidence": "field_info.json에서 12개 필드를 세었다"
    }
  ],
  "user_notes_summary": {
    "uncertainties": ["2023년 데이터를 사용했는데 최신이 아닐 수 있음"],
    "needs_review": [],
    "workarounds": ["채울 수 없는 필드는 텍스트 오버레이로 처리함"]
  },
  "eval_feedback": {
    "suggestions": [
      {
        "assertion": "출력에 'John Smith'라는 이름이 포함된다",
        "reason": "이름만 언급한 환각 문서도 통과할 수 있다"
      }
    ],
    "overall": "현재 assertion은 존재 여부만 확인하고 정확성은 잘 보지 못한다."
  }
}
```

**필드 설명**

- `expectations[]`: 근거와 함께 채점된 expectation 목록
- `summary`: 통과/실패 집계
- `execution_metrics`: 도구 사용량과 출력 크기(`executor`의 `metrics.json`에서 가져옴)
- `timing`: 실제 경과 시간(`timing.json`에서 가져옴)
- `claims`: 출력에서 추출해 검증한 주장
- `user_notes_summary`: 실행자가 남긴 이슈 요약
- `eval_feedback`: (선택 사항) grader가 짚을 만한 문제가 있을 때만 포함되는 eval 개선 제안

---

## metrics.json

executor run의 출력입니다. `<run-dir>/outputs/metrics.json`에 위치합니다.

```json
{
  "tool_calls": {
    "Read": 5,
    "Write": 2,
    "Bash": 8,
    "Edit": 1,
    "Glob": 2,
    "Grep": 0
  },
  "total_tool_calls": 18,
  "total_steps": 6,
  "files_created": ["filled_form.pdf", "field_values.json"],
  "errors_encountered": 0,
  "output_chars": 12450,
  "transcript_chars": 3200
}
```

**필드 설명**

- `tool_calls`: 도구 유형별 호출 수
- `total_tool_calls`: 전체 도구 호출 수
- `total_steps`: 주요 실행 단계 수
- `files_created`: 생성된 출력 파일 목록
- `errors_encountered`: 실행 중 발생한 오류 수
- `output_chars`: 출력 파일 전체 문자 수
- `transcript_chars`: transcript 문자 수

---

## timing.json

한 번의 실행에 대한 실제 경과 시간 정보입니다. `<run-dir>/timing.json`에 위치합니다.

**캡처 방법:** `codex exec` 실행 직전에 `executor_start`를 기록하고, 프로세스가 끝나는 즉시 `executor_end`를 기록하세요. 이 둘의 차이로 `duration_ms`, `total_duration_seconds`, `executor_duration_seconds`를 계산합니다. `total_tokens`는 CLI 출력이나 `--json` 이벤트 로그에서 얻을 수 있을 때만 저장하면 됩니다. 얻지 못했다면 `0` 또는 미기록으로 두어도 됩니다.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3,
  "executor_start": "2026-01-15T10:30:00Z",
  "executor_end": "2026-01-15T10:32:45Z",
  "executor_duration_seconds": 165.0,
  "grader_start": "2026-01-15T10:32:46Z",
  "grader_end": "2026-01-15T10:33:12Z",
  "grader_duration_seconds": 26.0
}
```

---

## benchmark.json

Benchmark 모드의 출력입니다. `benchmarks/<timestamp>/benchmark.json`에 위치합니다.

```json
{
  "metadata": {
    "skill_name": "pdf",
    "skill_path": "/path/to/pdf",
    "executor_model": "claude-sonnet-4-20250514",
    "analyzer_model": "most-capable-model",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3
  },
  "runs": [
    {
      "eval_id": 1,
      "eval_name": "Ocean",
      "configuration": "with_skill",
      "run_number": 1,
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "time_seconds": 42.5,
        "tokens": 3800,
        "tool_calls": 18,
        "errors": 0
      },
      "expectations": [
        {"text": "...", "passed": true, "evidence": "..."}
      ],
      "notes": [
        "2023년 데이터를 사용했는데 최신이 아닐 수 있음",
        "채울 수 없는 필드는 텍스트 오버레이로 처리함"
      ]
    }
  ],
  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.85, "stddev": 0.05, "min": 0.80, "max": 0.90},
      "time_seconds": {"mean": 45.0, "stddev": 12.0, "min": 32.0, "max": 58.0},
      "tokens": {"mean": 3800, "stddev": 400, "min": 3200, "max": 4100}
    },
    "without_skill": {
      "pass_rate": {"mean": 0.35, "stddev": 0.08, "min": 0.28, "max": 0.45},
      "time_seconds": {"mean": 32.0, "stddev": 8.0, "min": 24.0, "max": 42.0},
      "tokens": {"mean": 2100, "stddev": 300, "min": 1800, "max": 2500}
    },
    "delta": {
      "pass_rate": "+0.50",
      "time_seconds": "+13.0",
      "tokens": "+1700"
    }
  },
  "notes": [
    "Assertion '출력이 PDF 파일이다'는 양쪽 설정에서 100% 통과한다 - 스킬 가치 구분력이 낮을 수 있음",
    "Eval 3은 분산이 매우 크다(50% ± 40%) - flaky하거나 모델 의존적일 수 있음",
    "스킬 없는 실행은 테이블 추출 expectation에서 일관되게 실패한다",
    "스킬은 평균 실행 시간을 13초 늘리지만 통과율을 50% 높인다"
  ]
}
```

**필드 설명**

- `metadata`: 벤치마크 실행 정보
  - `skill_name`: 스킬 이름
  - `timestamp`: 벤치마크를 실행한 시각
  - `evals_run`: 실행한 eval 이름 또는 ID 목록
  - `runs_per_configuration`: 설정별 반복 실행 횟수(예: 3)
- `runs[]`: 개별 실행 결과
  - `eval_id`: 숫자 eval 식별자
  - `eval_name`: 사람이 읽기 쉬운 eval 이름(뷰어 섹션 제목으로 사용)
  - `configuration`: 반드시 `"with_skill"` 또는 `"without_skill"`이어야 함(뷰어가 이 문자열을 그대로 사용해 그룹화하고 색상도 정함)
  - `run_number`: 실행 번호 정수(1, 2, 3...)
  - `result`: `pass_rate`, `passed`, `total`, `time_seconds`, `tokens`, `errors`를 담은 객체
- `run_summary`: 설정별 통계 집계
  - `with_skill` / `without_skill`: 각각 `pass_rate`, `time_seconds`, `tokens`의 `mean`과 `stddev` 등을 포함
  - `delta`: `"+0.50"`, `"+13.0"`, `"+1700"`처럼 표현한 차이값
- `notes`: analyzer가 남긴 자유 형식 관찰 메모

**중요:** 뷰어는 이 필드 이름을 정확히 그대로 읽습니다. `configuration` 대신 `config`를 쓰거나, `pass_rate`를 `result` 바깥 최상위에 두면 뷰어가 빈값이나 0으로 보일 수 있습니다. `benchmark.json`을 수동 생성할 때는 항상 이 스키마를 참고하세요.

---

## comparison.json

blind comparator의 출력입니다. `<grading-dir>/comparison-N.json`에 위치합니다.

```json
{
  "winner": "A",
  "reasoning": "출력 A는 모든 필수 필드를 갖춘 완전한 결과이며 서식도 적절합니다. 출력 B는 날짜 필드가 빠져 있고 서식 불일치가 있습니다.",
  "rubric": {
    "A": {
      "content": {
        "correctness": 5,
        "completeness": 5,
        "accuracy": 4
      },
      "structure": {
        "organization": 4,
        "formatting": 5,
        "usability": 4
      },
      "content_score": 4.7,
      "structure_score": 4.3,
      "overall_score": 9.0
    },
    "B": {
      "content": {
        "correctness": 3,
        "completeness": 2,
        "accuracy": 3
      },
      "structure": {
        "organization": 3,
        "formatting": 2,
        "usability": 3
      },
      "content_score": 2.7,
      "structure_score": 2.7,
      "overall_score": 5.4
    }
  },
  "output_quality": {
    "A": {
      "score": 9,
      "strengths": ["완전한 결과", "서식이 좋음", "필수 필드가 모두 있음"],
      "weaknesses": ["헤더 스타일에 경미한 불일치가 있음"]
    },
    "B": {
      "score": 5,
      "strengths": ["읽기 쉬운 출력", "기본 구조는 맞음"],
      "weaknesses": ["날짜 필드가 없음", "서식 불일치", "데이터 추출이 부분적임"]
    }
  },
  "expectation_results": {
    "A": {
      "passed": 4,
      "total": 5,
      "pass_rate": 0.80,
      "details": [
        {"text": "출력에 이름이 포함됨", "passed": true}
      ]
    },
    "B": {
      "passed": 3,
      "total": 5,
      "pass_rate": 0.60,
      "details": [
        {"text": "출력에 이름이 포함됨", "passed": true}
      ]
    }
  }
}
```

---

## analysis.json

post-hoc analyzer의 출력입니다. `<grading-dir>/analysis.json`에 위치합니다.

```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_skill": "path/to/winner/skill",
    "loser_skill": "path/to/loser/skill",
    "comparator_reasoning": "비교기가 승자를 고른 이유에 대한 짧은 요약"
  },
  "winner_strengths": [
    "다중 페이지 문서를 다루는 명확한 단계별 지침",
    "서식 오류를 잡아낸 검증 스크립트 포함"
  ],
  "loser_weaknesses": [
    "'문서를 적절히 처리하라'는 모호한 지침 때문에 일관성이 떨어짐",
    "검증 스크립트가 없어 에이전트가 즉흥적으로 대응함"
  ],
  "instruction_following": {
    "winner": {
      "score": 9,
      "issues": ["경미함: 선택적 로깅 단계를 건너뜀"]
    },
    "loser": {
      "score": 6,
      "issues": [
        "스킬의 서식 템플릿을 사용하지 않음",
        "3단계를 따르지 않고 독자적인 접근을 만듦"
      ]
    }
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "instructions",
      "suggestion": "'문서를 적절히 처리하라'를 더 명시적인 단계 안내로 교체",
      "expected_impact": "일관성 없는 동작을 낳은 모호성을 제거할 수 있음"
    }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "스킬 읽기 -> 5단계 프로세스 따르기 -> 검증 스크립트 사용",
    "loser_execution_pattern": "스킬 읽기 -> 접근이 불명확함 -> 3가지 방법 시도"
  }
}
```
