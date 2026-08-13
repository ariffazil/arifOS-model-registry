# arifFlow Middleware Tap — Injection Point

## Where to inject

**File:** `/root/arifFlow/mcp/arifflow-mcp.py`
**Location:** Line ~160, inside the `flow_ingest` handler, after daemon POST succeeds.

## The injection (3 lines)

```python
# After: result = json.loads(resp.read().decode())
# Add:
try:
    from trace_collector import record as trace_record
    trace_record(actor_id, session_id, step_number, "assistant",
                 tool_name="flow_ingest", 
                 tool_result=json.dumps(result)[:2000],
                 epistemic=epistemic_label,
                 cost_ns=cost_ns,
                 floor_verdict=floor_verdict)
except ImportError:
    pass  # Tap not installed — no-op, never break the loop
```

## Non-invasive design

- Import inside try/except — tap missing → loop continues
- Write is fire-and-forget — no latency impact
- Failures in tap never propagate to the loop
- Zero modification to the Rust daemon

## What it captures

Every `flow_ingest` call writes one turn to the trace file. Over a day, this produces 100-500 turns covering:

- Execute steps (tool called, what it returned)
- Verify steps (verification outcome)
- Cool steps (cooling receipt)
- Seal steps (VAULT999 append)

## Installation

```bash
# Symlink the collector into arifFlow's Python path
ln -sf /root/arifOS-model-registry/scripts/trace_collector.py \
       /root/arifFlow/src/py/arifflow/trace_collector.py

# Restart (if injection added to MCP shim)
systemctl restart arifflow
```

## Output

```
/root/arifOS-model-registry/data/tool_traces.jsonl
```