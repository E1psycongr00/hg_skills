# Design Summary

- Repeated job:
- Success criteria:
- Assumptions:
- Why this split is better than one generalist agent:

# TOML Files

기본 산출물은 이 섹션이다. `.codex/config.toml`이나 부모 프롬프트 예시는 기본 출력에 넣지 않는다.

## `.codex/agents/agent_name.toml`

파일 경로의 basename과 TOML 내부 `name`은 완전히 같아야 한다.

```toml
name = "agent_name"
description = "..."
model = "gpt-5.4"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
developer_instructions = """
...
"""
```

# Open Questions

- ...
