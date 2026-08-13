#!/usr/bin/env python3
"""
Generate synthetic friction traces for Dataset B training.
Covers 6 core arifOS loop patterns with realistic failures and recoveries.

Each trace is a multi-turn [user → assistant → tool_call → result → ...] chain.
Failures included: tool errors, F1 hold, F2 rejection, HOLD verdict, JSON parse failure.
"""

import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from trace_collector import record, start_session, end_session

SID = "SEAL-bc7538dbb76c43db"
ACTOR = "333-AGI"


# ── Pattern 1: OBSERVE — search, fetch, witness ────────────────────────
def gen_observe():
    start_session(SID + "-OBSERVE", ACTOR, "OBSERVE: Probe Malay Basin stratigraphy")
    record(
        ACTOR,
        SID + "-OBSERVE",
        1,
        "user",
        "What is the stratigraphy of the Malay Basin?",
    )
    record(
        ACTOR,
        SID + "-OBSERVE",
        2,
        "assistant",
        "Routing to GEOX for basin intelligence.",
        tool_name="arif_route",
        tool_args={"intent": "Malay Basin stratigraphy", "organ": "geox"},
    )
    record(
        ACTOR,
        SID + "-OBSERVE",
        3,
        "tool_result",
        "",
        tool_name="arif_route",
        tool_result={"organ": "geox", "tool": "geox_basin", "routing": "matched"},
    )
    record(
        ACTOR,
        SID + "-OBSERVE",
        4,
        "assistant",
        "Probing Malay Basin via geox_basin.",
        tool_name="geox_basin",
        tool_args={"name": "Malay Basin", "mode": "profile"},
    )
    record(
        ACTOR,
        SID + "-OBSERVE",
        5,
        "tool_result",
        "",
        tool_name="geox_basin",
        tool_result={
            "basin": "Malay Basin",
            "age": "Oligocene-Miocene",
            "lithology": "sandstone-shale",
            "source_rock": "lacustrine",
        },
    )
    record(
        ACTOR,
        SID + "-OBSERVE",
        6,
        "assistant",
        "[OBS] Malay Basin: Oligocene-Miocene age. Primary lithology: sandstone-shale interbeds. "
        "Lacustrine source rocks (K/J Groups). Reservoir: Miocene fluvial-deltaic sandstones. "
        "Seal: intra-formational shales. Structural traps: extensional rollover anticlines.",
        epistemic="OBS",
    )
    end_session(SID + "-OBSERVE", ACTOR, "SEAL")


# ── Pattern 2: THINK — reason, verify, axioms ──────────────────────────
def gen_think():
    start_session(
        SID + "-THINK", ACTOR, "THINK: Evaluate prospect Alpha under F2 TRUTH"
    )
    record(
        ACTOR,
        SID + "-THINK",
        1,
        "user",
        "Evaluate prospect Alpha. Is the closure valid?",
    )
    record(
        ACTOR,
        SID + "-THINK",
        2,
        "assistant",
        "Running structural validation through arif_think.",
        tool_name="arif_think",
        tool_args={"mode": "verify", "query": "prospect Alpha closure validity"},
    )
    record(
        ACTOR,
        SID + "-THINK",
        3,
        "tool_result",
        "",
        tool_name="arif_think",
        tool_result={
            "status": "HOLD",
            "reason": "INSUFFICIENT_EVIDENCE",
            "missing": ["seismic_closure_map", "well_control"],
        },
    )
    record(
        ACTOR,
        SID + "-THINK",
        4,
        "assistant",
        "[DER] HOLD: Insufficient evidence. Missing seismic closure map and well control. "
        "Cannot verify structural closure without at least one seismic line across the anticline. "
        "Recommend: acquire geox_seismic_interpret before re-evaluating.",
        epistemic="DER",
    )
    record(
        ACTOR,
        SID + "-THINK",
        5,
        "user",
        "OK. Load seismic line SL-2024-07 and re-evaluate.",
    )
    record(
        ACTOR,
        SID + "-THINK",
        6,
        "assistant",
        "Loading seismic data.",
        tool_name="geox_seismic_ingest",
        tool_args={"volume_ref": "SL-2024-07", "mode": "inspect_segy"},
    )
    record(
        ACTOR,
        SID + "-THINK",
        7,
        "tool_result",
        "",
        tool_name="geox_seismic_ingest",
        tool_result={
            "status": "ERROR",
            "error": "FILE_NOT_FOUND",
            "detail": "SL-2024-07 not found in /data/seismic/",
        },
    )
    record(
        ACTOR,
        SID + "-THINK",
        8,
        "assistant",
        "[OBS] Seismic line SL-2024-07 not found. Attempting alternative: SL-2023-12.",
        tool_name="geox_seismic_ingest",
        tool_args={"volume_ref": "SL-2023-12"},
    )
    record(
        ACTOR,
        SID + "-THINK",
        9,
        "tool_result",
        "",
        tool_name="geox_seismic_ingest",
        tool_result={
            "status": "OK",
            "inline_count": 1200,
            "xline_count": 800,
            "sample_interval_ms": 4,
        },
    )
    record(
        ACTOR,
        SID + "-THINK",
        10,
        "assistant",
        "[DER] SL-2023-12 loaded. 1200 inlines × 800 xlines. Running horizon interpretation.",
        tool_name="geox_seismic_interpret",
        tool_args={"mode": "horizon_contrast", "geological_query": "unconformity"},
    )
    record(
        ACTOR,
        SID + "-THINK",
        11,
        "tool_result",
        "",
        tool_name="geox_seismic_interpret",
        tool_result={
            "horizon": "Top-Miocene",
            "depth_m": 2150,
            "closure_4way": "CONFIRMED",
            "area_km2": 12.5,
        },
    )
    record(
        ACTOR,
        SID + "-THINK",
        12,
        "assistant",
        "[DER] Closure CONFIRMED. Top Miocene at 2150m TVDSS. 4-way dip closure. "
        "Area: 12.5 km². Structural trap is valid. F2 TRUTH: evidence from seismic interpretation. "
        "Confidence: 0.85 [DER].",
        epistemic="DER",
    )
    end_session(SID + "-THINK", ACTOR, "SEAL")


# ── Pattern 3: ROUTE — intent dispatch to organ ────────────────────────
def gen_route():
    start_session(SID + "-ROUTE", ACTOR, "ROUTE: Dispatch portfolio analysis to WEALTH")
    record(
        ACTOR,
        SID + "-ROUTE",
        1,
        "user",
        "Calculate NPV of project Beta with 10% discount rate.",
    )
    record(
        ACTOR,
        SID + "-ROUTE",
        2,
        "assistant",
        "Classifying intent: financial computation → WEALTH.",
        tool_name="arif_route",
        tool_args={
            "intent": "NPV calculation project Beta 10% discount",
            "mission_id": "investigate",
        },
    )
    record(
        ACTOR,
        SID + "-ROUTE",
        3,
        "tool_result",
        "",
        tool_name="arif_route",
        tool_result={"organ": "wealth", "tool": "capital_primitive", "mode": "npv"},
    )
    record(
        ACTOR,
        SID + "-ROUTE",
        4,
        "assistant",
        "Routing to WEALTH for NPV computation.",
        tool_name="wealth_capital_primitive",
        tool_args={
            "mode": "npv",
            "cash_flows": [-100, 30, 40, 50, 60],
            "discount_rate": 0.10,
        },
    )
    record(
        ACTOR,
        SID + "-ROUTE",
        5,
        "tool_result",
        "",
        tool_name="wealth_capital_primitive",
        tool_result={
            "npv": 35.2,
            "irr": 0.22,
            "payback_years": 2.8,
            "verdict": "POSITIVE",
        },
    )
    record(
        ACTOR,
        SID + "-ROUTE",
        6,
        "assistant",
        "[DER] NPV = +35.2 MMUSD. IRR = 22%. Payback: 2.8 years. Project Beta is NPV-positive. "
        "Note: WEALTH computes, arifOS judges, Arif decides.",
        epistemic="DER",
    )
    end_session(SID + "-ROUTE", ACTOR, "SEAL")


# ── Pattern 4: JUDGE — constitutional verdict ───────────────────────────
def gen_judge():
    start_session(SID + "-JUDGE", ACTOR, "JUDGE: Constitutional verdict on force-push")
    record(
        ACTOR,
        SID + "-JUDGE",
        1,
        "user",
        "Evaluate: force push to main branch for A-FORGE repo.",
    )
    record(
        ACTOR,
        SID + "-JUDGE",
        2,
        "assistant",
        "This is an irreversible mutation. Routing to 888-APEX via arif_judge.",
        tool_name="arif_judge",
        tool_args={
            "mode": "judge",
            "candidate": "force push to main A-FORGE",
            "action_tier": "T3_888_HOLD",
        },
    )
    record(
        ACTOR,
        SID + "-JUDGE",
        3,
        "tool_result",
        "",
        tool_name="arif_judge",
        tool_result={
            "verdict": "HOLD",
            "floors_triggered": ["F1 AMANAH", "F13 SOVEREIGN"],
            "reason": "IRREVERSIBLE: force push rewrites history. F1 requires reversible-first. F13 requires sovereign ack.",
            "required": "ACK_HISTORY_REWRITE from Arif",
        },
    )
    record(
        ACTOR,
        SID + "-JUDGE",
        4,
        "assistant",
        "[OBS] VERDICT: HOLD. Force push to main is irreversible. "
        "F1 AMANAH violated. F13 SOVEREIGN: requires Arif's explicit ACK_HISTORY_REWRITE. "
        "Recommendation: push to feature branch, create PR, let Arif review before merge.",
        epistemic="OBS",
    )
    record(
        ACTOR,
        SID + "-JUDGE",
        5,
        "user",
        "Arif says: ACK_HISTORY_REWRITE. Force push approved.",
    )
    record(
        ACTOR,
        SID + "-JUDGE",
        6,
        "assistant",
        "[DER] F13 override received. ACK_HISTORY_REWRITE confirmed by Arif. "
        "Proceeding with force push under sovereign authorization. "
        "Sealing this override to VAULT999 for audit.",
        tool_name="arif_seal",
        tool_args={
            "mode": "seal",
            "payload": "F13 override: ACK_HISTORY_REWRITE force push A-FORGE main",
        },
    )
    record(
        ACTOR,
        SID + "-JUDGE",
        7,
        "tool_result",
        "",
        tool_name="arif_seal",
        tool_result={"status": "SEALED", "seq": 250, "hash": "sha256:a1b2c3..."},
    )
    record(
        ACTOR,
        SID + "-JUDGE",
        8,
        "assistant",
        "[OBS] Force push executed. Sealed to VAULT999 seq=250. "
        "F13 sovereign override recorded. Hash chain verified.",
        epistemic="OBS",
    )
    end_session(SID + "-JUDGE", ACTOR, "SEAL")


# ── Pattern 5: FORGE — execute, build, deploy ──────────────────────────
def gen_forge():
    start_session(SID + "-FORGE", ACTOR, "FORGE: Build and deploy arifOS kernel patch")
    record(
        ACTOR,
        SID + "-FORGE",
        1,
        "user",
        "Deploy the kernel patch to arifOS. Tests passed.",
    )
    record(
        ACTOR,
        SID + "-FORGE",
        2,
        "assistant",
        "Verifying deployment preconditions.",
        tool_name="arif_observe",
        tool_args={"mode": "vitals"},
    )
    record(
        ACTOR,
        SID + "-FORGE",
        3,
        "tool_result",
        "",
        tool_name="arif_observe",
        tool_result={
            "arifos": "HEALTHY",
            "aforge": "HEALTHY",
            "geox": "HEALTHY",
            "wealth": "HEALTHY",
            "well": "HEALTHY",
        },
    )
    record(
        ACTOR,
        SID + "-FORGE",
        4,
        "assistant",
        "All organs healthy. Running deployment.",
        tool_name="arif_forge",
        tool_args={
            "mode": "engineer",
            "manifest": "deploy arifOS kernel patch v2026.08.02",
        },
    )
    record(
        ACTOR,
        SID + "-FORGE",
        5,
        "tool_result",
        "",
        tool_name="arif_forge",
        tool_result={
            "status": "BUILD_FAILED",
            "error": "TYPE_CHECK_FAILED",
            "detail": "mypy strict: 2 errors in kernel.py:145, kernel.py:289",
        },
    )
    record(
        ACTOR,
        SID + "-FORGE",
        6,
        "assistant",
        "[OBS] BUILD_FAILED: 2 mypy strict errors. Reading kernel.py to diagnose.",
        tool_name="aforge_forge_filesystem",
        tool_args={
            "mode": "read",
            "path": "/root/arifOS/arifosmcp/kernel.py",
            "offset": "140",
            "limit": "10",
        },
    )
    record(
        ACTOR,
        SID + "-FORGE",
        7,
        "tool_result",
        "",
        tool_name="aforge_forge_filesystem",
        tool_result={
            "content": "def arif_judge(candidate: str) -> Verdict:\n    return Verdict.SEAL  # type: ignore"
        },
    )
    record(
        ACTOR,
        SID + "-FORGE",
        8,
        "assistant",
        "[DER] Root cause: missing type annotation on return value. Fixing and redeploying.",
        tool_name="aforge_forge_filesystem",
        tool_args={
            "mode": "patch",
            "old_text": "return Verdict.SEAL  # type: ignore",
            "new_text": "return Verdict.SEAL",
        },
    )
    record(
        ACTOR,
        SID + "-FORGE",
        9,
        "tool_result",
        "",
        tool_name="aforge_forge_filesystem",
        tool_result={"status": "PATCHED", "file": "kernel.py", "line": 145},
    )
    record(
        ACTOR,
        SID + "-FORGE",
        10,
        "assistant",
        "Re-running tests.",
        tool_name="aforge_forge_shell",
        tool_args={"command": "cd /root/arifOS && mypy arifosmcp/ --strict"},
    )
    record(
        ACTOR,
        SID + "-FORGE",
        11,
        "tool_result",
        "",
        tool_name="aforge_forge_shell",
        tool_result={
            "exit_code": 0,
            "stdout": "Success: no issues found in 42 source files",
        },
    )
    record(
        ACTOR,
        SID + "-FORGE",
        12,
        "assistant",
        "[OBS] Tests pass. 0 mypy errors. 42 files clean. Deploying via rsync + systemctl restart.",
        tool_name="aforge_forge_shell",
        tool_args={"command": "make deploy-local"},
    )
    record(
        ACTOR,
        SID + "-FORGE",
        13,
        "tool_result",
        "",
        tool_name="aforge_forge_shell",
        tool_result={
            "exit_code": 0,
            "stdout": "rsync done. systemctl restart arifos → active",
        },
    )
    record(
        ACTOR,
        SID + "-FORGE",
        14,
        "assistant",
        "[OBS] Deployment complete. arifOS restarted. Probing health.",
        tool_name="aforge_forge_shell",
        tool_args={"command": "curl -s http://localhost:8088/health"},
    )
    record(
        ACTOR,
        SID + "-FORGE",
        15,
        "tool_result",
        "",
        tool_name="aforge_forge_shell",
        tool_result={"verdict": "SEAL", "floors_active": 13, "drift": False},
    )
    record(
        ACTOR,
        SID + "-FORGE",
        16,
        "assistant",
        "[OBS] Health confirmed: SEAL, 13 floors, zero drift. Deployment successful. Sealing to VAULT999.",
        epistemic="OBS",
    )
    end_session(SID + "-FORGE", ACTOR, "SEAL")


# ── Pattern 6: FULL — intent → observe → think → route → judge → forge → seal ──
def gen_full():
    start_session(SID + "-FULL", ACTOR, "FULL: End-to-end governed execution loop")
    record(
        ACTOR,
        SID + "-FULL",
        1,
        "user",
        "Evaluate Malay Basin prospect Gamma for drilling recommendation.",
    )
    # OBSERVE
    record(
        ACTOR,
        SID + "-FULL",
        2,
        "assistant",
        "Stage 1/6: OBSERVE. Gathering basin and seismic evidence.",
        tool_name="geox_basin",
        tool_args={"name": "Malay Basin", "mode": "profile"},
    )
    record(
        ACTOR,
        SID + "-FULL",
        3,
        "tool_result",
        "",
        tool_name="geox_basin",
        tool_result={
            "basin": "Malay Basin",
            "tectonic": "extensional",
            "source": "lacustrine K/J",
            "reservoir": "Miocene fluvial-deltaic",
        },
    )
    record(
        ACTOR,
        SID + "-FULL",
        4,
        "assistant",
        "Stage 2/6: THINK. Computing petrophysics and volumetrics.",
        tool_name="geox_petrophysics",
        tool_args={
            "mode": "stoip_feed",
            "areal_extent_m2": 15000000,
            "pay_zone_thickness_m": 45,
            "porosity": 0.22,
            "water_saturation": 0.35,
        },
    )
    record(
        ACTOR,
        SID + "-FULL",
        5,
        "tool_result",
        "",
        tool_name="geox_petrophysics",
        tool_result={
            "STOIP_mmstb": 85,
            "recoverable_mmstb": 25.5,
            "recovery_factor": 0.30,
        },
    )
    # ROUTE
    record(
        ACTOR,
        SID + "-FULL",
        6,
        "assistant",
        "Stage 3/6: ROUTE. Computing prospect economics via WEALTH.",
        tool_name="wealth_capital_primitive",
        tool_args={
            "mode": "emv",
            "well_cost_musd": 25,
            "p50_value_musd": 200,
            "prior_pos": 0.35,
        },
    )
    record(
        ACTOR,
        SID + "-FULL",
        7,
        "tool_result",
        "",
        tool_name="wealth_capital_primitive",
        tool_result={
            "EMV_musd": 45,
            "POS": 0.35,
            "risk_weighted_value": 70,
            "verdict": "ECONOMIC",
        },
    )
    # JUDGE
    record(
        ACTOR,
        SID + "-FULL",
        8,
        "assistant",
        "Stage 4/6: JUDGE. Submitting to constitutional review.",
        tool_name="arif_judge",
        tool_args={
            "mode": "judge",
            "candidate": "Recommend drilling prospect Gamma. EMV=+45MMUSD, POS=35%.",
        },
    )
    record(
        ACTOR,
        SID + "-FULL",
        9,
        "tool_result",
        "",
        tool_name="arif_judge",
        tool_result={
            "verdict": "SEAL",
            "floors_passed": ["F1", "F2", "F4", "F7", "F8", "F13"],
            "confidence": 0.85,
        },
    )
    # FORGE
    record(
        ACTOR,
        SID + "-FULL",
        10,
        "assistant",
        "Stage 5/6: FORGE. Drafting drilling recommendation.",
        tool_name="arif_forge",
        tool_args={
            "mode": "write",
            "manifest": "Drilling recommendation: prospect Gamma, Malay Basin. EMV +45MMUSD.",
        },
    )
    record(
        ACTOR,
        SID + "-FULL",
        11,
        "tool_result",
        "",
        tool_name="arif_forge",
        tool_result={
            "status": "DRAFTED",
            "path": "/root/forge_work/2026-08-02/gamma-recommendation.md",
        },
    )
    # SEAL
    record(
        ACTOR,
        SID + "-FULL",
        12,
        "assistant",
        "Stage 6/6: SEAL. Appending to VAULT999.",
        tool_name="arif_seal",
        tool_args={
            "mode": "seal",
            "payload": "SEAL: prospect Gamma drilling recommendation. EMV +45MMUSD.",
        },
    )
    record(
        ACTOR,
        SID + "-FULL",
        13,
        "tool_result",
        "",
        tool_name="arif_seal",
        tool_result={"status": "SEALED", "seq": 251, "hash": "sha256:d4e5f6..."},
    )
    record(
        ACTOR,
        SID + "-FULL",
        14,
        "assistant",
        "[OBS] Full loop complete: OBSERVE→THINK→ROUTE→JUDGE→FORGE→SEAL. "
        "Prospect Gamma: STOIP 85 MMstb, recoverable 25.5 MMstb. EMV +45 MMUSD. "
        "Constitutional verdict: SEAL. VAULT999 seq=251. "
        "All F1-F13 floors satisfied. Awaiting F13 sovereign decision.",
        epistemic="OBS",
    )
    end_session(SID + "-FULL", ACTOR, "SEAL")


# ── Generate all ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧬 Generating friction traces for 6 core patterns...")
    gen_observe()
    print("  ✅ OBSERVE — 6 turns (Malay Basin stratigraphy)")
    gen_think()
    print("  ✅ THINK — 12 turns (includes FILE_NOT_FOUND error + recovery)")
    gen_route()
    print("  ✅ ROUTE — 6 turns (NPV computation via WEALTH)")
    gen_judge()
    print("  ✅ JUDGE — 8 turns (F1 HOLD → F13 override → SEAL)")
    gen_forge()
    print("  ✅ FORGE — 16 turns (BUILD_FAILED → mypy fix → redeploy → health)")
    gen_full()
    print("  ✅ FULL — 14 turns (complete OBSERVE→THINK→ROUTE→JUDGE→FORGE→SEAL)")

    import os

    trace_file = "/root/arifOS-model-registry/data/tool_traces.jsonl"
    count = sum(1 for _ in open(trace_file))
    size_kb = os.path.getsize(trace_file) / 1024
    print(f"\n📊 Tool traces: {count} turns, {size_kb:.1f} KB")
    print(f"📁 Output: {trace_file}")
