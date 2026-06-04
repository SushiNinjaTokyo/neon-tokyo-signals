# AI Arena Live Lab Semantic Guard Patch

## Add

Place this file:

```text
scripts/lib/ai_arena_lab_semantic_guard_jp.py
```

## Modify `scripts/build_ai_arena_war_room_jp.py`

Add this import near the top:

```python
from scripts.lib.ai_arena_lab_semantic_guard_jp import sanitize_lab_payload
```

Then call this immediately before writing `latest.json`:

```python
payload = sanitize_lab_payload(payload)
```

Example:

```python
payload = {...}
payload = sanitize_lab_payload(payload)
write_json(latest_json_path, payload)
```

## Add to OpenAI prompt

```text
MARKET CONTEXT RULES:
- Market context is optional evidence, not mandatory decoration.
- Use SOXX or semiconductor context only when the topic or linked ticker has plausible semiconductor, electronics, component, equipment, material, or high-tech exposure.
- Do not connect SOXX to software/service names unless the supplied evidence explicitly says the company is semiconductor-related.
- If market context is weakly related, say it is not decisive instead of forcing a connection.
- Never invent catalysts, news, policy events, geopolitical events, earnings, guidance, company fundamentals, or geopolitical causes.
- Use only the provided numeric facts.
- If you use a market context item, mention the actual number exactly as provided.

DIALOGUE QUALITY RULES:
- Every message must advance the debate.
- Avoid generic finance filler such as "sustainable", "robust", "crucial", "market conditions", "risk-adjusted", unless tied to a specific number.
- Each agent must speak in its own style.
- Avoid making all agents sound like risk managers.
- Do not let one agent reply to itself.
- Do not assign another agent's state, color, role, or personality.
- Prefer concrete tests: "what would prove this wrong next session?"
- A disagreement must identify the exact number or assumption being challenged.
- Do not celebrate returns without testing drawdown, sample size, concentration, or opportunity cost.
- Do not produce investment advice, target prices, buy/sell instructions, guarantees, or recommendations.
```

## Check

```bash
python -m compileall scripts/lib/ai_arena_lab_semantic_guard_jp.py scripts/build_ai_arena_war_room_jp.py
python scripts/build_ai_arena_war_room_jp.py
python -m json.tool site/data/japan/ai-arena/war-room/latest.json > /tmp/latest.checked.json
```

```bash
python - <<'PY'
import json
from pathlib import Path

p = Path("site/data/japan/ai-arena/war-room/latest.json")
data = json.loads(p.read_text(encoding="utf-8"))

print("semantic_score:", data.get("quality", {}).get("semantic_score"))
print("semantic_guard_issue_count:", data.get("quality", {}).get("semantic_guard_issue_count"))
print("message_count:", data.get("metrics", {}).get("message_count"))

for m in data.get("current_session", {}).get("messages", [])[:5]:
    print(m["agent_id"], m["agent_name"], m["state"], m["color"])
PY
```
