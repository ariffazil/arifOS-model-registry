#!/usr/bin/env python3
"""
arifFlow Middleware Tap — Tool Trace Collector
===============================================
Captures [prompt → tool_call → result → next_tool_call] chains
for Dataset B (agentic tool trajectory training data).

Inject this at the execution boundary — wherever a tool is called
and its result is received. Write the turn. That's it.

Usage (inline):
    from trace_collector import record
    record("333-AGI", session_id, turn=1, role="user",
           content="Analyze Malay Basin prospect Alpha")
    record("333-AGI", session_id, turn=2, role="assistant",
           tool_name="geox_basin", tool_args={"name":"Malay Basin"})
    record("333-AGI", session_id, turn=3, role="tool_result",
           tool_name="geox_basin", tool_result={...})

Injection point (arifFlow MCP shim):
    Add after line ~160 in /root/arifFlow/mcp/arifflow-mcp.py,
    inside the flow_ingest handler, after the daemon POST succeeds:

        from trace_collector import record as trace_record
        trace_record(actor_id, session_id, step_number, "assistant",
                     tool_name="flow_ingest", tool_result=result)

Output: /root/arifOS-model-registry/data/tool_traces.jsonl
"""

import json
import os
from datetime import datetime, timezone

TRACE_FILE = "/root/arifOS-model-registry/data/tool_traces.jsonl"


def record(
    actor_id,
    session_id,
    turn,
    role,
    content="",
    tool_name=None,
    tool_args=None,
    tool_result=None,
    epistemic="OBS",
    cost_ns=0,
    floor_verdict=None,
):
    """Record one turn of the agentic loop."""
    os.makedirs(os.path.dirname(TRACE_FILE), exist_ok=True)
    entry = {
        "actor_id": actor_id,
        "session_id": session_id,
        "turn": turn,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": str(content)[:3000] if content else "",
        "tool_name": tool_name,
        "tool_args": json.dumps(tool_args)[:1500] if tool_args else None,
        "tool_result": str(tool_result)[:3000] if tool_result else None,
        "epistemic": epistemic,
        "cost_ns": cost_ns,
        "floor_verdict": floor_verdict,
    }
    # Remove None values for cleanliness
    entry = {k: v for k, v in entry.items() if v is not None}
    with open(TRACE_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def start_session(session_id, actor_id, intent):
    """Record session start."""
    record(
        actor_id,
        session_id,
        0,
        "system",
        content=f"SESSION_START: {intent}",
        epistemic="OBS",
    )


def end_session(session_id, actor_id, verdict="SEAL"):
    """Record session close."""
    record(
        actor_id,
        session_id,
        999,
        "system",
        content=f"SESSION_CLOSE: verdict={verdict}",
        epistemic="OBS",
        floor_verdict=verdict,
    )


# ── CLI for bash-based recording ─────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print(
            "Usage: trace_collector.py <actor> <session> <turn> <role> [content] [tool_name] [epistemic]"
        )
        sys.exit(1)
    actor = sys.argv[1]
    sid = sys.argv[2]
    turn = int(sys.argv[3])
    role = sys.argv[4]
    content = sys.argv[5] if len(sys.argv) > 5 else ""
    tool = sys.argv[6] if len(sys.argv) > 6 else None
    epistemic = sys.argv[7] if len(sys.argv) > 7 else "OBS"
    record(actor, sid, turn, role, content=content, tool_name=tool, epistemic=epistemic)
    print(f"✅ Recorded turn {turn} for {actor} [{role}]")
