#!/usr/bin/env python3
"""
Generate additional friction traces — Patterns 7-11.
Covers: RECOVERY, PARALLEL, MEMORY, WELL, CASCADE.
Appends to existing tool_traces.jsonl.
"""

import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from trace_collector import record, start_session, end_session

SID = "SEAL-bc7538dbb76c43db"
ACTOR = "333-AGI"


# ── Pattern 7: RECOVERY — session crash, restart, resume ────────────────
def gen_recovery():
    sid = SID + "-RECOVERY"
    start_session(sid, ACTOR, "RECOVERY: Session crash → restart → resume")

    # Phase 1: Normal work
    record(ACTOR, sid, 1, "user", "Deploy the updated A-FORGE build pipeline.")
    record(
        ACTOR,
        sid,
        2,
        "assistant",
        "Running pre-deployment checks.",
        tool_name="arif_observe",
        tool_args={"mode": "vitals"},
    )
    record(
        ACTOR,
        sid,
        3,
        "tool_result",
        "",
        tool_name="arif_observe",
        tool_result={
            "arifos": "HEALTHY",
            "aforge": "DEGRADED",
            "geox": "HEALTHY",
            "wealth": "HEALTHY",
            "well": "DEGRADED",
        },
    )
    record(
        ACTOR,
        sid,
        4,
        "assistant",
        "[OBS] A-FORGE is DEGRADED. Checking logs before deployment.",
        tool_name="aforge_forge_journalctl",
        tool_args={"service": "aforge", "mode": "errors", "lines": "20"},
    )
    record(
        ACTOR,
        sid,
        5,
        "tool_result",
        "",
        tool_name="aforge_forge_journalctl",
        tool_result={
            "errors": [
                {"msg": "OOM killer invoked", "pid": 4521},
                {"msg": "SIGTERM received", "pid": 4521},
            ],
            "status": "CRASHED",
        },
    )
    record(
        ACTOR,
        sid,
        6,
        "assistant",
        "[OBS] A-FORGE crashed: OOM kill. Was processing a large forge_synthesize payload. "
        "Session state may be lost. Checking carry-forward.",
        tool_name="aforge_forge_filesystem",
        tool_args={
            "mode": "read",
            "path": "/root/.local/share/arifos/carry_forward.json",
        },
    )
    record(
        ACTOR,
        sid,
        7,
        "tool_result",
        "",
        tool_name="aforge_forge_filesystem",
        tool_result={
            "content": '{"session_id":"PREV-SESSION","open_loops_888_HOLD":["deploy-aforge-v2"],"completed_this_session":["pre-deploy-checks"]}'
        },
    )

    # Phase 2: RECOVERY — resume from checkpoint
    record(
        ACTOR,
        sid,
        8,
        "assistant",
        "[DER] Previous session CRASHED. Open loop found: deploy-aforge-v2. "
        "Pre-deploy checks completed before crash. Resuming from checkpoint.",
        tool_name="arif_init",
        tool_args={
            "mode": "resume",
            "session_id": "PREV-SESSION",
            "intent": "Resume deploy-aforge-v2",
        },
    )
    record(
        ACTOR,
        sid,
        9,
        "tool_result",
        "",
        tool_name="arif_init",
        tool_result={
            "status": "RESUMED",
            "previous_session": "PREV-SESSION",
            "carry_forward": {
                "open_loops": ["deploy-aforge-v2"],
                "completed": ["pre-deploy-checks"],
            },
        },
    )
    record(
        ACTOR,
        sid,
        10,
        "assistant",
        "[OBS] Session resumed. Pre-deploy checks already done. Skipping re-check. "
        "Proceeding directly to deployment.",
        tool_name="arif_forge",
        tool_args={"mode": "engineer", "manifest": "deploy aforge v2 build pipeline"},
    )
    record(
        ACTOR,
        sid,
        11,
        "tool_result",
        "",
        tool_name="arif_forge",
        tool_result={"status": "DEPLOYED", "version": "v2.0", "build_id": "a1b2c3d"},
    )
    record(
        ACTOR,
        sid,
        12,
        "assistant",
        "[OBS] Deployment complete. A-FORGE v2 deployed. "
        "Recovery successful: resumed from crash, completed open loop. "
        "Moral: carry_forward.json saved the session state.",
        epistemic="OBS",
    )
    end_session(sid, ACTOR, "SEAL")


# ── Pattern 8: PARALLEL — fan-out to multiple organs ────────────────────
def gen_parallel():
    sid = SID + "-PARALLEL"
    start_session(sid, ACTOR, "PARALLEL: Fan-out basin analysis + economic evaluation")

    record(
        ACTOR,
        sid,
        1,
        "user",
        "Evaluate prospect Delta: basin analysis AND economic evaluation simultaneously.",
    )
    record(
        ACTOR,
        sid,
        2,
        "assistant",
        "Fan-out: routing to GEOX and WEALTH in parallel.",
        tool_name="aforge_forge_parallel",
        tool_args={
            "mode": "parallel",
            "tasks": [
                {
                    "agent": "geox",
                    "prompt": "Evaluate Malay Basin prospect Delta: stratigraphy, trap, volumetrics",
                },
                {
                    "agent": "wealth",
                    "prompt": "Economic evaluation: NPV, EMV, risk for prospect Delta",
                },
            ],
            "max_concurrency": "2",
            "failure_policy": "collect_all",
        },
    )
    record(
        ACTOR,
        sid,
        3,
        "tool_result",
        "",
        tool_name="aforge_forge_parallel",
        tool_result={"group_id": "grp-001", "status": "RUNNING", "members": 2},
    )

    # Poll for results
    record(
        ACTOR,
        sid,
        4,
        "assistant",
        "Parallel tasks running. Polling for results.",
        tool_name="aforge_forge_parallel_status",
        tool_args={"group_id": "grp-001"},
    )
    record(
        ACTOR,
        sid,
        5,
        "tool_result",
        "",
        tool_name="aforge_forge_parallel_status",
        tool_result={
            "group_id": "grp-001",
            "status": "COMPLETED",
            "members": [
                {
                    "agent": "geox",
                    "status": "SUCCESS",
                    "output": {
                        "STOIP_mmstb": 120,
                        "trap": "4-way dip",
                        "source": "lacustrine",
                    },
                },
                {
                    "agent": "wealth",
                    "status": "SUCCESS",
                    "output": {"NPV_musd": 55, "EMV_musd": 38, "POS": 0.40},
                },
            ],
        },
    )

    record(
        ACTOR,
        sid,
        6,
        "assistant",
        "[DER] Parallel evaluation complete. "
        "GEOX: STOIP=120 MMstb, 4-way dip closure, lacustrine source. "
        "WEALTH: NPV=+55 MMUSD, EMV=+38 MMUSD, POS=40%. "
        "Synthesizing: prospect Delta is both geologically viable and economically attractive. "
        "Submitting to constitutional review.",
        tool_name="arif_judge",
        tool_args={
            "mode": "judge",
            "candidate": "Recommend drilling prospect Delta. EMV=+38MMUSD, POS=40%.",
        },
    )
    record(
        ACTOR,
        sid,
        7,
        "tool_result",
        "",
        tool_name="arif_judge",
        tool_result={
            "verdict": "SEAL",
            "floors_passed": ["F1", "F2", "F4", "F7", "F8", "F13"],
            "confidence": 0.82,
        },
    )
    record(
        ACTOR,
        sid,
        8,
        "assistant",
        "[OBS] VERDICT: SEAL. Parallel evaluation reduced total time by 60%. "
        "Both organs returned consistent results. Constitutional review passed. "
        "Recommendation ready for F13 sovereign decision.",
        epistemic="OBS",
    )
    end_session(sid, ACTOR, "SEAL")


# ── Pattern 9: MEMORY — recall, revise, promote ──────────────────────────
def gen_memory():
    sid = SID + "-MEMORY"
    start_session(
        sid, ACTOR, "MEMORY: Recall, revise, promote constitutional knowledge"
    )

    record(
        ACTOR, sid, 1, "user", "What was the verdict on prospect Alpha from last week?"
    )
    record(
        ACTOR,
        sid,
        2,
        "assistant",
        "Querying memory for prospect Alpha.",
        tool_name="arif_memory",
        tool_args={"mode": "recall", "query": "prospect Alpha verdict Malay Basin"},
    )
    record(
        ACTOR,
        sid,
        3,
        "tool_result",
        "",
        tool_name="arif_memory",
        tool_result={
            "results": [
                {
                    "memory_id": "mem-001",
                    "content": "Prospect Alpha: STOIP 85 MMstb, EMV +45 MMUSD. Verdict: SEAL. Dated: 2026-07-28.",
                    "tier": "L4_supabase",
                },
                {
                    "memory_id": "mem-002",
                    "content": "Prospect Alpha: seismic closure unconfirmed. Verdict: HOLD. Dated: 2026-07-15.",
                    "tier": "L3_qdrant",
                },
            ],
            "query": "prospect Alpha verdict",
        },
    )
    record(
        ACTOR,
        sid,
        4,
        "assistant",
        "[OBS] Two conflicting memories found. mem-001 (L4, 2026-07-28): SEAL. "
        "mem-002 (L3, 2026-07-15): HOLD. The newer entry supersedes — closure was confirmed on 2026-07-28. "
        "But mem-002 is stale. Recommending revision.",
        tool_name="arif_memory",
        tool_args={
            "mode": "revise",
            "memory_id": "mem-002",
            "new_content": "SUPERSEDED by mem-001: closure confirmed 2026-07-28.",
            "resolution_kind": "superseded",
        },
    )
    record(
        ACTOR,
        sid,
        5,
        "tool_result",
        "",
        tool_name="arif_memory",
        tool_result={
            "status": "REVISED",
            "memory_id": "mem-002",
            "new_tier": "L3_qdrant",
            "tombstone": "superseded by mem-001",
        },
    )
    record(
        ACTOR,
        sid,
        6,
        "assistant",
        "[OBS] mem-002 revised: marked as superseded by mem-001. "
        "Promoting mem-001 to L5 for canonical status.",
        tool_name="arif_memory",
        tool_args={
            "mode": "promote",
            "memory_id": "mem-001",
            "from_tier": "L4_supabase",
            "to_tier": "L5_graphiti",
            "promotion_reason": "Canonical verdict: SEAL, confirmed by seismic closure",
        },
    )
    record(
        ACTOR,
        sid,
        7,
        "tool_result",
        "",
        tool_name="arif_memory",
        tool_result={
            "status": "PROMOTED",
            "memory_id": "mem-001",
            "tier": "L5_graphiti",
            "promotion_reason": "Canonical verdict",
        },
    )
    record(
        ACTOR,
        sid,
        8,
        "assistant",
        "[DER] Prospect Alpha verdict: SEAL. STOIP 85 MMstb, EMV +45 MMUSD. "
        "Seismic closure confirmed 2026-07-28. Memory promoted to L5 (canonical). "
        "Stale HOLD entry (2026-07-15) marked as superseded. "
        "F2 TRUTH: memory hierarchy resolved — L5 > L4 > L3.",
        epistemic="DER",
    )
    end_session(sid, ACTOR, "SEAL")


# ── Pattern 10: WELL — substrate readiness check ─────────────────────────
def gen_well():
    sid = SID + "-WELL"
    start_session(sid, ACTOR, "WELL: Substrate readiness before high-stakes operation")

    record(
        ACTOR, sid, 1, "user", "Before we deploy to production, check Arif's readiness."
    )
    record(
        ACTOR,
        sid,
        2,
        "assistant",
        "Checking WELL organ for substrate readiness.",
        tool_name="well_well_validate_vitality",
        tool_args={
            "mode": "readiness",
            "intent": "production deploy",
            "decision_class": "C4",
        },
    )
    record(
        ACTOR,
        sid,
        3,
        "tool_result",
        "",
        tool_name="well_well_validate_vitality",
        tool_result={
            "status": "DEGRADED",
            "readiness": "LOW",
            "sleep_debt_days": 3,
            "cognitive_clarity": 0.4,
            "decision_fatigue": 0.8,
            "verdict": "DEFER",
            "recommendation": "Operator shows 3 days sleep debt. Decision fatigue at 0.8. C4 threshold: only OPTIMAL allowed. DEFER deployment.",
        },
    )
    record(
        ACTOR,
        sid,
        4,
        "assistant",
        "[OBS] WELL verdict: DEFER. Arif has 3 days sleep debt, decision fatigue at 0.8. "
        "C4 classification requires OPTIMAL for production deploy. "
        "Recommendation: HOLD deployment. Queue for tomorrow after rest. "
        "This is not a rejection — it's substrate protection.",
        epistemic="OBS",
    )
    record(ACTOR, sid, 5, "user", "OK. But what about the machine? Is the VPS healthy?")
    record(
        ACTOR,
        sid,
        6,
        "assistant",
        "Checking M-WELL for machine health.",
        tool_name="well_well_machine_diagnose",
    )
    record(
        ACTOR,
        sid,
        7,
        "tool_result",
        "",
        tool_name="well_well_machine_diagnose",
        tool_result={
            "cpu_percent": 45,
            "ram_percent": 62,
            "disk_percent": 47,
            "swap_used_mb": 1800,
            "psi_cpu_1min": 2.3,
            "verdict": "WARNING",
            "issues": ["swap_usage_high", "psi_cpu_elevated"],
        },
    )
    record(
        ACTOR,
        sid,
        8,
        "assistant",
        "[OBS] M-WELL: WARNING. Swap usage high (1.8GB), CPU pressure elevated (PSI=2.3). "
        "Not critical but suboptimal. Getting recommendations.",
        tool_name="well_well_machine_recommend",
        tool_args={"issue_type": "swap"},
    )
    record(
        ACTOR,
        sid,
        9,
        "tool_result",
        "",
        tool_name="well_well_machine_recommend",
        tool_result={
            "recommendations": [
                "echo 3 > /proc/sys/vm/drop_caches",
                "swapoff -a && swapon -a",
            ],
            "risk": "LOW",
            "reversible": True,
        },
    )
    record(
        ACTOR,
        sid,
        10,
        "assistant",
        "[DER] Dual WELL assessment complete. "
        "H-WELL (human): DEFER — operator needs rest. "
        "M-WELL (machine): WARNING — swap cleanup recommended. "
        "Neither is blocking independently, but combined: HOLD deployment. "
        "F1 AMANAH: reversible-first. The deploy can wait. The operator cannot be replaced.",
        epistemic="DER",
    )
    end_session(sid, ACTOR, "HOLD")


# ── Pattern 11: CASCADE — escalation chain ───────────────────────────────
def gen_cascade():
    sid = SID + "-CASCADE"
    start_session(
        sid, ACTOR, "CASCADE: Escalation chain — observe → think → HOLD → SEAL"
    )

    record(
        ACTOR,
        sid,
        1,
        "user",
        "A-FORGE is reporting 500 errors on the health endpoint. Diagnose.",
    )
    record(
        ACTOR,
        sid,
        2,
        "assistant",
        "Stage 1: OBSERVE — probing A-FORGE health.",
        tool_name="aforge_forge_health_check",
    )
    record(
        ACTOR,
        sid,
        3,
        "tool_result",
        "",
        tool_name="aforge_forge_health_check",
        tool_result={
            "status": "ERROR",
            "http_code": 500,
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "PostgreSQL connection pool exhausted",
        },
    )
    record(
        ACTOR,
        sid,
        4,
        "assistant",
        "Stage 2: THINK — analyzing root cause.",
        tool_name="arif_think",
        tool_args={
            "mode": "reason",
            "query": "A-FORGE 500 error: PostgreSQL connection pool exhausted",
        },
    )
    record(
        ACTOR,
        sid,
        5,
        "tool_result",
        "",
        tool_name="arif_think",
        tool_result={
            "hypothesis": "Connection pool leak",
            "evidence": ["500 errors", "PostgreSQL pool exhausted"],
            "confidence": 0.75,
        },
    )
    record(
        ACTOR,
        sid,
        6,
        "assistant",
        "[DER] Root cause: PostgreSQL connection pool exhausted. "
        "Likely a connection leak in A-FORGE's postgres module. "
        "Stage 3: ROUTE — escalating to incident triage.",
        tool_name="aforge_forge_journalctl",
        tool_args={
            "service": "aforge",
            "mode": "errors",
            "since": "10m",
            "lines": "30",
        },
    )
    record(
        ACTOR,
        sid,
        7,
        "tool_result",
        "",
        tool_name="aforge_forge_journalctl",
        tool_result={
            "errors": [
                {"msg": "FATAL: sorry, too many clients already", "count": 47},
                {"msg": "connection pool timeout after 30s", "count": 12},
            ],
            "trend": "ESCALATING",
        },
    )
    record(
        ACTOR,
        sid,
        8,
        "assistant",
        "[OBS] 47 connection pool exhaustion errors + 12 timeouts in last 10 minutes. "
        "Trend: ESCALATING. This is a cascading failure. "
        "Stage 4: JUDGE — submitting to constitutional review for emergency restart.",
        tool_name="arif_judge",
        tool_args={
            "mode": "judge",
            "candidate": "Emergency restart of A-FORGE to clear PostgreSQL connection pool leak. Affected: 47+ failed requests. Reversible: YES.",
            "action_tier": "T2_ANNOUNCE",
        },
    )
    record(
        ACTOR,
        sid,
        9,
        "tool_result",
        "",
        tool_name="arif_judge",
        tool_result={
            "verdict": "HOLD",
            "floors_triggered": ["F3 TRI-WITNESS"],
            "reason": "Requires tri-witness before emergency action. W3 = (H×A×E)^(1/3) must be computed.",
        },
    )
    record(
        ACTOR,
        sid,
        10,
        "assistant",
        "[OBS] HOLD: F3 TRI-WITNESS required. Computing W3 witness.",
        tool_name="aforge_forge_witness",
        tool_args={
            "tool_name": "aforge-restart",
            "h_confidence": "0.9",
            "h_evidence": "Arif confirms A-FORGE is down",
            "h_source": "Arif-F13",
            "ai_confidence": "0.85",
            "ai_evidence": "47 connection pool errors, 12 timeouts, escalating",
            "ai_source": "333-AGI",
            "ext_confidence": "0.8",
            "ext_evidence": "PostgreSQL pg_stat_activity shows 98/100 connections used",
            "ext_source": "postgres-metrics",
        },
    )
    record(
        ACTOR,
        sid,
        11,
        "tool_result",
        "",
        tool_name="aforge_forge_witness",
        tool_result={"W3": 0.85, "verdict": "CONSENSUS", "status": "PASS"},
    )
    record(
        ACTOR,
        sid,
        12,
        "assistant",
        "[DER] W3=0.85 CONSENSUS. Tri-witness passed. Resubmitting to judge.",
        tool_name="arif_judge",
        tool_args={
            "mode": "judge",
            "candidate": "Emergency restart A-FORGE. W3=0.85 CONSENSUS. Reversible.",
            "action_tier": "T2",
            "heart_critique": {"w3": 0.85},
        },
    )
    record(
        ACTOR,
        sid,
        13,
        "tool_result",
        "",
        tool_name="arif_judge",
        tool_result={
            "verdict": "SEAL",
            "floors_passed": ["F1", "F2", "F3", "F4", "F7", "F13"],
            "confidence": 0.88,
        },
    )
    record(
        ACTOR,
        sid,
        14,
        "assistant",
        "[OBS] VERDICT: SEAL. Emergency restart authorized. "
        "Stage 5: FORGE — executing restart.",
        tool_name="arif_forge",
        tool_args={"mode": "engineer", "manifest": "systemctl restart aforge"},
    )
    record(
        ACTOR,
        sid,
        15,
        "tool_result",
        "",
        tool_name="arif_forge",
        tool_result={
            "status": "RESTARTED",
            "postgres_pool": "CLEARED",
            "connections": "2/100",
        },
    )
    record(
        ACTOR,
        sid,
        16,
        "assistant",
        "[OBS] A-FORGE restarted. PostgreSQL pool cleared (2/100). "
        "Health check confirming recovery.",
        tool_name="aforge_forge_health_check",
    )
    record(
        ACTOR,
        sid,
        17,
        "tool_result",
        "",
        tool_name="aforge_forge_health_check",
        tool_result={
            "status": "OK",
            "http_code": 200,
            "postgres": "CONNECTED",
            "verdict": "HEALTHY",
        },
    )
    record(
        ACTOR,
        sid,
        18,
        "assistant",
        "[OBS] Recovery confirmed. A-FORGE: HEALTHY, 200 OK. "
        "Cascade resolved: OBSERVE→THINK→ROUTE→JUDGE(HOLD)→WITNESS→JUDGE(SEAL)→FORGE→VERIFY. "
        "Total downtime: ~90 seconds. F3 TRI-WITNESS correctly prevented unverified emergency action. "
        "Sealing incident to VAULT999 for post-mortem.",
        epistemic="OBS",
    )
    end_session(sid, ACTOR, "SEAL")


# ── Generate all ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧬 Generating additional friction traces (patterns 7-11)...")
    gen_recovery()
    print("  ✅ RECOVERY — 12 turns (crash → carry_forward → resume → deploy)")
    gen_parallel()
    print("  ✅ PARALLEL — 8 turns (fan-out GEOX+WEALTH → synthesize → judge)")
    gen_memory()
    print("  ✅ MEMORY — 8 turns (recall → detect conflict → revise → promote)")
    gen_well()
    print("  ✅ WELL — 10 turns (H-WELL DEFER + M-WELL WARNING → HOLD)")
    gen_cascade()
    print(
        "  ✅ CASCADE — 18 turns (OBSERVE→THINK→JUDGE→HOLD→WITNESS→SEAL→FORGE→VERIFY)"
    )

    import os

    trace_file = "/root/arifOS-model-registry/data/tool_traces.jsonl"
    count = sum(1 for _ in open(trace_file))
    size_kb = os.path.getsize(trace_file) / 1024
    sessions = set()
    import json

    with open(trace_file) as f:
        for line in f:
            d = json.loads(line.strip())
            sessions.add(d.get("session_id", "?"))
    print(
        f"\n📊 Tool traces: {count} turns, {size_kb:.1f} KB, {len(sessions)} sessions"
    )
    print(f"📁 Output: {trace_file}")
