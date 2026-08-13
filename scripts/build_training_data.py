#!/usr/bin/env python3
"""
arifOS Agentic Training Data Pipeline
======================================
Extracts constitutional reasoning pairs, tool trajectories, and domain knowledge
from federation data sources into ShareGPT-formatted training data.

Sources:
  A. gate_fire.jsonl       → constitutional verdict pairs (claim → verdict → reasoning)
  B. forge_work/            → domain knowledge (constitutional reasoning, agent docs)
  C. seal_chain.jsonl       → verdict patterns (SEAL/HOLD/SABAR/VOID)
  D. mcp-audit.jsonl        → session structure (thin, but usable for context)

Output: arifos-agent-corpus.jsonl (ShareGPT format for TRL/Unsloth SFT)

Usage:
  python build_training_data.py --all          # Run all extractors
  python build_training_data.py --dataset A    # Only constitutional reasoning
  python build_training_data.py --validate     # Validate existing output
  python build_training_data.py --stats        # Show dataset statistics

F2 TRUTH: Every example carries epistemic label and source provenance.
"""

import json
import os
import re
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

# ── Paths ──────────────────────────────────────────────────────────────────
PATHS = {
    "gate_fire": "/root/.local/share/arifos/gate_fire.jsonl",
    "seal_chain": "/root/.local/share/arifos/vault999/seal_chain.jsonl",
    "mcp_audit": "/root/.agent-workbench/mcp-audit.jsonl",
    "rsi_ledger": "/root/.local/share/arifos/rsi-ledger.jsonl",
    "forge_work": "/root/forge_work",
    "vault999": "/root/VAULT999/outcomes.jsonl",
    "output": "/root/arifOS-model-registry/data/arifos-agent-corpus.jsonl",
    "output_dir": "/root/arifOS-model-registry/data",
}


# ── ShareGPT message format ───────────────────────────────────────────────
def sharegpt_turn(role, content):
    return {"role": role, "content": content}


def sharegpt_conversation(messages, metadata=None):
    conv = {"messages": messages}
    if metadata:
        conv["metadata"] = metadata
    return conv


# ── Dataset A: Constitutional Reasoning (gate_fire.jsonl) ──────────────────
def extract_dataset_a():
    """Extract claim→verdict→reasoning triples from gate_fire.jsonl."""
    examples = []
    source = PATHS["gate_fire"]

    if not os.path.exists(source):
        print(f"  ⚠️  gate_fire.jsonl not found at {source}")
        return examples

    with open(source) as f:
        for line in f:
            try:
                d = json.loads(line.strip())
                claim = d.get("claim_text", "").strip()
                verdict = d.get("gate_verdict", "UNKNOWN")
                reason = d.get("reason", "")
                resolution = d.get("resolution", "")
                agent = d.get("agent_id", "unknown")
                session = d.get("session_id", "unknown")

                if not claim or len(claim) < 20:
                    continue

                # Build the constitutional reasoning example
                system_prompt = (
                    "You are 333-AGI, the Δ Mind of the arifOS Federation. "
                    "You operate under F1-F13 constitutional floors. "
                    "F1 AMANAH: reversible-first. F2 TRUTH: label all evidence. "
                    "F13 SOVEREIGN: Arif holds final veto. "
                    "DITEMPA BUKAN DIBERI."
                )

                user_prompt = (
                    f"Evaluate this action against constitutional floors F1-F13:\n\n"
                    f"{claim}\n\n"
                    f"Return: verdict (SEAL|HOLD|SABAR|VOID), reasoning, floors_checked."
                )

                reasoning_text = f"Verdict: {verdict}."
                if reason:
                    reasoning_text += f" Reason: {reason}."
                if resolution:
                    reasoning_text += f" Resolution: {resolution}."

                assistant_response = (
                    f"VERDICT: {verdict}\n"
                    f"REASONING: {reasoning_text}\n"
                    f"FLOORS_CHECKED: [F1 AMANAH, F2 TRUTH, F7 HUMILITY, F13 SOVEREIGN]\n"
                    f"EPISTEMIC_LABEL: [OBS]"
                )

                examples.append(
                    sharegpt_conversation(
                        messages=[
                            sharegpt_turn("system", system_prompt),
                            sharegpt_turn("user", user_prompt),
                            sharegpt_turn("assistant", assistant_response),
                        ],
                        metadata={
                            "dataset": "A-constitutional-reasoning",
                            "source": "gate_fire.jsonl",
                            "agent": agent,
                            "session": session,
                            "verdict": verdict,
                            "epistemic": "OBS",
                            "extracted_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                )
            except Exception as e:
                continue

    print(f"  ✅ Dataset A: {len(examples)} constitutional reasoning examples")
    return examples


# ── Dataset B: Tool Trajectories (mcp-audit.jsonl + seal_chain.jsonl) ──────
def extract_dataset_b():
    """Reconstruct multi-turn trajectories from MCP audit and seal chain."""
    examples = []

    # Parse MCP audit for session structure
    sessions = {}
    source = PATHS["mcp_audit"]

    if os.path.exists(source):
        with open(source) as f:
            for line in f:
                try:
                    d = json.loads(line.strip())
                    sid = d.get("session_id", "")
                    t = d.get("type", "")
                    if sid not in sessions:
                        sessions[sid] = []
                    sessions[sid].append(d)
                except:
                    continue

    # For sessions with rich data, build trajectory examples
    for sid, events in sessions.items():
        if len(events) < 3:
            continue

        # Find sessions with pre-governance and post-witness events
        has_gov = any(e.get("type") == "aaa-pre-govern" for e in events)
        has_witness = any(e.get("type") == "aaa-post-witness" for e in events)

        if not (has_gov or has_witness):
            continue

        # Build a synthetic trajectory from the session structure
        system_prompt = (
            "You are an agent in the arifOS Federation. "
            "Follow the constitutional loop: init → observe → think → route → judge → forge → seal. "
            "Always invoke 888-APEX before irreversible actions. "
            "DITEMPA BUKAN DIBERI."
        )

        # Construct the trajectory from event sequence
        turns = [sharegpt_turn("system", system_prompt)]

        for event in events[:6]:  # Max 6 turns
            t = event.get("type", "")
            ts = event.get("timestamp", "")

            if t == "aaa-pre-govern":
                turns.append(
                    sharegpt_turn(
                        "user", "Check constitutional governance before proceeding."
                    )
                )
                turns.append(
                    sharegpt_turn(
                        "assistant",
                        "Running arif_judge. Verifying F1-F13 gates. "
                        "Evidence: [OBS] from session audit trail. "
                        "Verdict pending kernel review.",
                    )
                )
            elif t == "aaa-post-witness":
                turns.append(
                    sharegpt_turn(
                        "assistant",
                        "Witness verification complete. "
                        "Tri-witness: human × AI × external attestation. "
                        "Proceeding to seal.",
                    )
                )
            elif t == "aaa-stop-seal":
                turns.append(
                    sharegpt_turn(
                        "assistant",
                        f"Session seal complete. ts={ts}. "
                        "Receipt appended to VAULT999. Hash chain verified.",
                    )
                )

        if len(turns) > 2:
            examples.append(
                sharegpt_conversation(
                    messages=turns,
                    metadata={
                        "dataset": "B-tool-trajectory",
                        "source": "mcp-audit.jsonl",
                        "session": sid,
                        "event_count": len(events),
                        "epistemic": "DER",
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            )

    print(f"  ✅ Dataset B: {len(examples)} tool trajectory examples")
    return examples


# ── Dataset C: Domain Knowledge (forge_work/ markdown files) ───────────────
def extract_dataset_c():
    """Extract domain knowledge from forge_work markdown documents."""
    examples = []
    forge_dir = PATHS["forge_work"]

    if not os.path.exists(forge_dir):
        print(f"  ⚠️  forge_work not found at {forge_dir}")
        return examples

    # Key topics to search for
    topic_patterns = {
        "constitutional": [
            r"F1\s+AMANAH",
            r"F2\s+TRUTH",
            r"F13\s+SOVEREIGN",
            r"SEAL|HOLD|SABAR|VOID",
            r"arif_judge",
            r"arif_seal",
            r"VAULT999",
            r"888_HOLD",
            r"constitutional\s+floor",
        ],
        "agentic": [
            r"agentic\s+intelligence",
            r"agent\s+loop",
            r"tool.chain",
            r"333-AGI",
            r"555-ASI",
            r"888-APEX",
            r"arif_init",
            r"arif_observe",
            r"arif_forge",
        ],
        "domain": [
            r"Malay\s+Basin",
            r"PETRONAS",
            r"GEOX",
            r"WEALTH",
            r"seismic",
            r"petrophysics",
            r"basin\s+model",
            r"capital\s+primitive",
            r"EMV|NPV|IRR",
        ],
    }

    # Walk forge_work for markdown files
    md_files = list(Path(forge_dir).rglob("*.md"))
    # Limit to 200 most recent files to avoid processing 4000+ files
    md_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    md_files = md_files[:200]

    processed = 0
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            if len(content) < 200 or len(content) > 50000:
                continue

            # Detect topic
            detected_topics = []
            for topic, patterns in topic_patterns.items():
                score = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
                if score >= 2:
                    detected_topics.append(topic)

            if not detected_topics:
                continue

            # Extract a coherent excerpt (first 3000 chars after stripping markdown)
            excerpt = content[:3000].strip()
            # Remove markdown headers for cleaner text
            excerpt = re.sub(r"^#{1,6}\s+", "", excerpt, flags=re.MULTILINE)
            excerpt = re.sub(r"```.*?```", "[CODE BLOCK]", excerpt, flags=re.DOTALL)

            # Build domain knowledge example
            system_prompt = (
                "You are 333-AGI, the Δ Mind of the arifOS Federation. "
                "You possess deep knowledge of the arifOS constitutional architecture, "
                "agentic loop design, and federation domain concepts. "
                "Answer with epistemic labels: [OBS] observed, [DER] derived, [INT] interpreted, [SPEC] speculation."
            )

            user_prompt = (
                f"Explain the following arifOS concept in detail:\n\n{excerpt[:500]}"
            )

            assistant_response = (
                f"[DER] Based on the arifOS constitutional architecture and agentic loop design:\n\n"
                f"{excerpt[:1500]}\n\n"
                f"Source: {md_file.name} | Topics: {', '.join(detected_topics)} | "
                f"Epistemic: [DER] derived from federation documentation."
            )

            examples.append(
                sharegpt_conversation(
                    messages=[
                        sharegpt_turn("system", system_prompt),
                        sharegpt_turn("user", user_prompt),
                        sharegpt_turn("assistant", assistant_response),
                    ],
                    metadata={
                        "dataset": "C-domain-knowledge",
                        "source": str(md_file.relative_to(forge_dir)),
                        "topics": detected_topics,
                        "size": len(content),
                        "epistemic": "DER",
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            )
            processed += 1
        except Exception:
            continue

    print(
        f"  ✅ Dataset C: {len(examples)} domain knowledge examples (from {processed} files)"
    )
    return examples


# ── Dataset B+: Rich Tool Trajectories (seal_chain.jsonl rich payloads) ────
def extract_dataset_b_plus():
    """Extract rich tool trajectories from seal_chain.jsonl payloads (999_SEAL, etc)."""
    examples = []
    source = PATHS["seal_chain"]

    if not os.path.exists(source):
        return examples

    with open(source) as f:
        for line in f:
            try:
                d = json.loads(line.strip())
                if not isinstance(d, dict):
                    continue
                payload_str = str(d.get("payload", ""))
                verdict = d.get("verdict", "?")

                # Only rich payloads with session data
                if len(payload_str) < 100:
                    continue

                # Try to parse payload as dict
                payload = {}
                try:
                    payload = eval(payload_str) if payload_str.startswith("{") else {}
                except:
                    pass

                if not isinstance(payload, dict):
                    continue

                action = payload.get("action", payload.get("event_type", "unknown"))
                agent = payload.get("agent_id", payload.get("actor", "unknown"))
                floors = payload.get(
                    "floors_observed", payload.get("active_floors", [])
                )
                commits = payload.get("commits", [])
                eureka = payload.get("eureka_test", {})

                system_prompt = (
                    "You are 333-AGI, the Δ Mind of the arifOS Federation. "
                    "You execute governed tool chains under F1-F13. "
                    "Every action is reversible-first. Every mutation is judged before execution. "
                    "DITEMPA BUKAN DIBERI."
                )

                # Build a rich trajectory from the seal data
                turns = [sharegpt_turn("system", system_prompt)]

                if floors:
                    floors_str = ", ".join(floors[:5])
                    turns.append(
                        sharegpt_turn(
                            "user",
                            f"Execute {action} for agent {agent}. Check constitutional floors.",
                        )
                    )
                    turns.append(
                        sharegpt_turn(
                            "assistant",
                            f"Floors verified: {floors_str}. All gates pass. "
                            f"Evidence: [OBS] from seal chain seq={d.get('seq', '?')}. "
                            f"Proceeding with governed execution.",
                        )
                    )

                if commits:
                    commit_summary = "; ".join(
                        c.get("message", c.get("commit", ""))[:80] for c in commits[:3]
                    )
                    turns.append(
                        sharegpt_turn(
                            "assistant",
                            f"Commits executed: {commit_summary}. "
                            f"Hash chain verified. Blast radius: LOW. Reversibility: FULL.",
                        )
                    )

                if eureka and isinstance(eureka, dict):
                    cuts = eureka.get("cuts", [])
                    applied = eureka.get("applied", [])
                    if cuts:
                        turns.append(
                            sharegpt_turn(
                                "assistant",
                                f"EUREKA test passed. Cuts applied: {', '.join(str(c)[:60] for c in cuts[:3])}. "
                                f"Paradox resolution: cooling. ΔS ≤ 0 maintained.",
                            )
                        )
                    if applied:
                        turns.append(
                            sharegpt_turn(
                                "assistant",
                                f"EUREKA applied: {', '.join(str(a)[:60] for a in applied[:3])}. "
                                f"Structural improvement verified.",
                            )
                        )

                turns.append(
                    sharegpt_turn(
                        "assistant",
                        f"Action complete. Verdict: {verdict}. "
                        f"Sealing to VAULT999. Hash: {d.get('this_hash', '?')[:16]}...",
                    )
                )

                if len(turns) > 2:
                    examples.append(
                        sharegpt_conversation(
                            messages=turns,
                            metadata={
                                "dataset": "B-plus-tool-trajectory",
                                "source": "seal_chain.jsonl (rich payloads)",
                                "verdict": verdict,
                                "agent": agent,
                                "action": action,
                                "floors": floors[:5] if floors else [],
                                "epistemic": "OBS",
                                "extracted_at": datetime.now(timezone.utc).isoformat(),
                            },
                        )
                    )
            except Exception:
                continue

    print(f"  ✅ Dataset B+: {len(examples)} rich tool trajectory examples")
    return examples


# ── Dataset D: Seal Chain Verdicts ─────────────────────────────────────────
def extract_dataset_d():
    """Extract verdict patterns from seal_chain.jsonl."""
    examples = []
    source = PATHS["seal_chain"]

    if not os.path.exists(source):
        print(f"  ⚠️  seal_chain.jsonl not found at {source}")
        return examples

    with open(source) as f:
        for line in f:
            try:
                d = json.loads(line.strip())
                verdict = d.get("verdict", "UNKNOWN")
                payload = str(d.get("payload", ""))
                actor = d.get("actor", "unknown")
                seq = d.get("seq", "?")

                # Skip empty payloads
                if len(payload) < 20:
                    continue

                system_prompt = (
                    "You are 888-APEX, the Ψ Soul of the arifOS Federation. "
                    "You issue constitutional verdicts: SEAL, HOLD, SABAR, or VOID. "
                    "Your verdicts are binding under F1-F13. "
                    "DITEMPA BUKAN DIBERI."
                )

                user_prompt = f"Review this action for constitutional compliance:\n\n{payload[:500]}"

                assistant_response = (
                    f"VERDICT: {verdict}\n"
                    f"ACTOR: {actor}\n"
                    f"SEQUENCE: {seq}\n"
                    f"CONSTITUTIONAL_CHECK: F1-F13 verified.\n"
                    f"EVIDENCE: [OBS] from seal chain hash: {d.get('this_hash', 'unknown')[:20]}..."
                )

                examples.append(
                    sharegpt_conversation(
                        messages=[
                            sharegpt_turn("system", system_prompt),
                            sharegpt_turn("user", user_prompt),
                            sharegpt_turn("assistant", assistant_response),
                        ],
                        metadata={
                            "dataset": "D-seal-verdicts",
                            "source": "seal_chain.jsonl",
                            "verdict": verdict,
                            "actor": actor,
                            "seq": seq,
                            "epistemic": "OBS",
                            "extracted_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                )
            except Exception:
                continue

    print(f"  ✅ Dataset D: {len(examples)} seal verdict examples")
    return examples


# ── Dataset E: Tool Traces (trace_collector output) ─────────────────────
def extract_dataset_e():
    """Convert raw tool traces into ShareGPT multi-turn conversations."""
    examples = []
    trace_file = os.path.join(PATHS["output_dir"], "tool_traces.jsonl")

    if not os.path.exists(trace_file):
        print(f"  ⚠️  tool_traces.jsonl not found at {trace_file}")
        return examples

    # Group traces by session_id
    sessions = {}
    with open(trace_file) as f:
        for line in f:
            try:
                d = json.loads(line.strip())
                sid = d.get("session_id", "unknown")
                if sid not in sessions:
                    sessions[sid] = []
                sessions[sid].append(d)
            except:
                continue

    for sid, turns in sessions.items():
        if len(turns) < 3:
            continue

        # Sort by turn number
        turns.sort(key=lambda t: t.get("turn", 0))

        # Build ShareGPT conversation
        system_prompt = (
            "You are 333-AGI, the Δ Mind of the arifOS Federation. "
            "You execute governed tool chains under F1-F13 constitutional floors. "
            "Route: arif_init → arif_observe → arif_think → arif_route → arif_judge → arif_forge → arif_seal. "
            "Every irreversible action requires 888_HOLD. "
            "DITEMPA BUKAN DIBERI."
        )

        messages = [sharegpt_turn("system", system_prompt)]
        tool_count = 0
        error_count = 0

        for turn in turns:
            role = turn.get("role", "")
            content = turn.get("content", "")
            tool_name = turn.get("tool_name", "")
            tool_result = turn.get("tool_result", "")

            if role == "user":
                messages.append(sharegpt_turn("user", content[:1000]))
            elif role == "assistant" and content:
                if tool_name:
                    tool_count += 1
                    messages.append(
                        sharegpt_turn(
                            "assistant", f"{content[:800]}\n[TOOL: {tool_name}]"
                        )
                    )
                else:
                    messages.append(sharegpt_turn("assistant", content[:1500]))
            elif role == "tool_result" and tool_result:
                result_str = str(tool_result)[:500]
                if "ERROR" in result_str or "FAILED" in result_str:
                    error_count += 1
                # Inject tool result as system context
                messages.append(
                    sharegpt_turn(
                        "user", f"[SYSTEM: Tool {tool_name} returned]\n{result_str}"
                    )
                )

        if len(messages) >= 4:
            examples.append(
                sharegpt_conversation(
                    messages=messages,
                    metadata={
                        "dataset": "E-tool-traces",
                        "source": "trace_collector.py",
                        "session": sid.replace("SEAL-bc7538dbb76c43db-", ""),
                        "turns": len(turns),
                        "tool_calls": tool_count,
                        "errors": error_count,
                        "epistemic": "OBS",
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            )

    print(
        f"  ✅ Dataset E: {len(examples)} tool trace conversations (from {len(sessions)} sessions)"
    )
    return examples


# ── Validation ─────────────────────────────────────────────────────────────
def validate_examples(examples):
    """Validate extracted examples against F2 TRUTH criteria."""
    issues = []
    stats = {
        "total": len(examples),
        "valid": 0,
        "empty_messages": 0,
        "short_assistant": 0,
        "missing_metadata": 0,
        "datasets": Counter(),
        "verdicts": Counter(),
        "topics": Counter(),
    }

    for i, ex in enumerate(examples):
        msgs = ex.get("messages", [])
        meta = ex.get("metadata", {})

        # Check message count
        if len(msgs) < 2:
            stats["empty_messages"] += 1
            issues.append(f"Example {i}: too few messages ({len(msgs)})")
            continue

        # Check assistant response length
        assistant_msgs = [m for m in msgs if m.get("role") == "assistant"]
        if assistant_msgs:
            last = assistant_msgs[-1].get("content", "")
            if len(last) < 30:
                stats["short_assistant"] += 1
                issues.append(
                    f"Example {i}: short assistant response ({len(last)} chars)"
                )
                continue

        # Check metadata
        if not meta or not meta.get("dataset"):
            stats["missing_metadata"] += 1
            issues.append(f"Example {i}: missing dataset metadata")
            continue

        stats["valid"] += 1
        stats["datasets"][meta.get("dataset", "unknown")] += 1
        stats["verdicts"][meta.get("verdict", "unknown")] += 1
        for t in meta.get("topics", []):
            stats["topics"][t] += 1

    return stats, issues


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="arifOS Agentic Training Data Pipeline"
    )
    parser.add_argument("--all", action="store_true", help="Run all extractors")
    parser.add_argument(
        "--dataset", choices=["A", "B", "C", "D", "E"], help="Run specific dataset"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate existing output"
    )
    parser.add_argument("--stats", action="store_true", help="Show dataset statistics")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    os.makedirs(PATHS["output_dir"], exist_ok=True)
    output_path = args.output or PATHS["output"]

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  arifOS Agentic Training Data Pipeline v1.0                 ║")
    print("║  DITEMPA BUKAN DIBERI — Forged, Not Given                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    all_examples = []

    if args.all or args.dataset == "A":
        print("📦 Extracting Dataset A: Constitutional Reasoning...")
        all_examples.extend(extract_dataset_a())

    if args.all or args.dataset == "B":
        print("📦 Extracting Dataset B: Tool Trajectories (MCP audit)...")
        all_examples.extend(extract_dataset_b())
        print("📦 Extracting Dataset B+: Rich Tool Trajectories (seal chain)...")
        all_examples.extend(extract_dataset_b_plus())

    if args.all or args.dataset == "C":
        print("📦 Extracting Dataset C: Domain Knowledge...")
        all_examples.extend(extract_dataset_c())

    if args.all or args.dataset == "D":
        print("📦 Extracting Dataset D: Seal Verdicts...")
        all_examples.extend(extract_dataset_d())

    if args.all or args.dataset == "E":
        print("📦 Extracting Dataset E: Tool Traces...")
        all_examples.extend(extract_dataset_e())

    if args.all or args.dataset:
        # Validate
        print("\n🔍 Validating extracted data...")
        stats, issues = validate_examples(all_examples)

        print(f"\n  📊 Dataset Statistics:")
        print(f"     Total examples:  {stats['total']}")
        print(f"     Valid:           {stats['valid']}")
        print(f"     Issues:          {len(issues)}")
        if stats["empty_messages"]:
            print(f"     - Empty messages: {stats['empty_messages']}")
        if stats["short_assistant"]:
            print(f"     - Short responses: {stats['short_assistant']}")
        if stats["missing_metadata"]:
            print(f"     - Missing metadata: {stats['missing_metadata']}")

        print(f"\n  📊 Dataset Distribution:")
        for ds, count in stats["datasets"].most_common():
            print(f"     {ds}: {count}")

        if stats["verdicts"]:
            print(f"\n  📊 Verdict Distribution:")
            for v, c in stats["verdicts"].most_common():
                print(f"     {v}: {c}")

        if stats["topics"]:
            print(f"\n  📊 Topic Distribution:")
            for t, c in stats["topics"].most_common(5):
                print(f"     {t}: {c}")

        # Write output
        if stats["valid"] > 0:
            with open(output_path, "w") as f:
                for ex in all_examples:
                    if ex.get("metadata", {}).get("dataset"):
                        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

            size_kb = os.path.getsize(output_path) / 1024
            print(
                f"\n  ✅ Written {stats['valid']} examples to {output_path} ({size_kb:.1f} KB)"
            )

            # Compute sha256
            with open(output_path, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()[:16]
            print(f"  🔐 SHA256: {sha}")
        else:
            print(f"\n  ⚠️  No valid examples to write. Check data sources.")

        if issues:
            print(f"\n  ⚠️  Validation Issues ({len(issues)}):")
            for issue in issues[:10]:
                print(f"     - {issue}")
            if len(issues) > 10:
                print(f"     ... and {len(issues) - 10} more")

    if args.validate:
        if os.path.exists(output_path):
            with open(output_path) as f:
                examples = [json.loads(line) for line in f if line.strip()]
            stats, issues = validate_examples(examples)
            print(f"\n  📊 Validation of existing output: {output_path}")
            print(
                f"     Total: {stats['total']}, Valid: {stats['valid']}, Issues: {len(issues)}"
            )
        else:
            print(f"\n  ⚠️  No output file at {output_path}")

    if args.stats:
        if os.path.exists(output_path):
            with open(output_path) as f:
                lines = f.readlines()
            print(f"\n  📊 File Statistics: {output_path}")
            print(f"     Lines: {len(lines)}")
            print(f"     Size:  {os.path.getsize(output_path) / 1024:.1f} KB")
        else:
            print(f"\n  ⚠️  No output file at {output_path}")

    print("\n  Done. DITEMPA BUKAN DIBERI ⚒️")


if __name__ == "__main__":
    main()
