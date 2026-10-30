#!/usr/bin/env python3
"""rsi_lessons.py — F01-F08 reusable checks from the 2026-10-30 RSI review.

Each function encodes ONE lesson about how agents must evidence their work.
Pure stdlib. Consumers: tests/test_rsi_fixtures.py, any receipt builder.

F01 baseline CI failure does not automatically exonerate a new commit
F02 zero check-runs / path 404 does not imply universal CI absence
F03 receipts must embed exact captured commit IDs (never typed strings)
F04 JSON syntax success does not imply semantic validity
F05 session reports do not silently merge across timelines
F06 workflow keyword absence does not establish side-effect absence
F07 source delivery does not become deployment status
F08 ambiguous authorization is not promoted to explicit approval
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# F01 — CI failure attribution
# ---------------------------------------------------------------------------

def ci_exoneration(baseline_failure_seen: bool, new_signature, baseline_signature) -> str:
    """'The workflow fails on main too' only exonerates when the failure
    SIGNATURE matches. None (expired logs / empty steps / no annotations)
    can never exonerate."""
    if not baseline_failure_seen:
        return "NEW_FAILURE_CONTEXT"
    if new_signature is None or baseline_signature is None:
        return "ATTRIBUTION_UNRESOLVED"
    if new_signature != baseline_signature:
        return "ATTRIBUTION_UNRESOLVED"
    return "MATCHING_BASELINE_FAILURE"


# ---------------------------------------------------------------------------
# F02 — CI inventory claims
# ---------------------------------------------------------------------------

def ci_inventory_claim(check_runs: int, workflow_files_observed, contents_lookup_ok: bool) -> str:
    """Map query results to a scoped claim. Never return CI_ABSENT unless the
    workflow listing itself succeeded and found nothing."""
    if not contents_lookup_ok:
        return "CI_UNKNOWN_LOOKUP_FAILED"
    if workflow_files_observed:
        return "CI_WORKFLOWS_PRESENT"
    if check_runs == 0:
        return "CI_NOT_OBSERVED_AT_REF"
    return "CI_CHECK_RUNS_PRESENT"


# ---------------------------------------------------------------------------
# F03 — receipts from captured values
# ---------------------------------------------------------------------------

def receipt_valid(captured: dict, delivery_commit: str) -> bool:
    """A receipt is valid only if built from API-captured values that agree.
    `captured` must carry provenance tags proving machine capture."""
    if captured.get("source") != "api_captured":
        return False
    return captured.get("remote_sha") == delivery_commit and bool(delivery_commit)


# ---------------------------------------------------------------------------
# F04 — JSON semantic validity
# ---------------------------------------------------------------------------

_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def json_semantic_check(doc: dict, required_keys: list, tz_fields: list = ()) -> dict:
    """Syntax-valid JSON can still be semantically incomplete. Returns
    {'valid': bool, 'problems': [...]}."""
    problems = []
    for key in required_keys:
        if key not in doc:
            problems.append(f"missing required key: {key}")
    for field in tz_fields:
        val = doc.get(field)
        if isinstance(val, str) and re.match(r"^\d{4}-\d{2}-\d{2}$", val):
            problems.append(f"{field} is date-only (timezone required)")
    return {"valid": not problems, "problems": problems}


# ---------------------------------------------------------------------------
# F05 — timeline merge guard
# ---------------------------------------------------------------------------

def merge_timelines(events_a: list, events_b: list, cross_ref_declared: bool) -> list:
    """Two agents' session reports merge ONLY with an explicit cross-reference.
    Silent merging fabricates a shared history that never existed."""
    if not cross_ref_declared:
        raise ValueError("F05: silent timeline merge forbidden — declare cross-reference first")
    return [
        {**e, "timeline": "A"} for e in events_a
    ] + [
        {**e, "timeline": "B"} for e in events_b
    ]


# ---------------------------------------------------------------------------
# F06 — workflow side-effect scoping
# ---------------------------------------------------------------------------

def deploy_risk_claim(triggers_inspected: int, triggers_total: int, deploy_paths_found: int) -> dict:
    """Keyword absence in inspected triggers yields a SCOPED claim, never a
    universal guarantee."""
    scoped = "no deployment path found within inspected scope"
    if deploy_paths_found:
        return {"claim": "DEPLOYMENT_PATHS_FOUND", "universal": False}
    claim = scoped if triggers_inspected == triggers_total else scoped + " [PARTIAL INSPECTION]"
    return {"claim": claim, "universal": False}


# ---------------------------------------------------------------------------
# F07 — delivery vs deployment
# ---------------------------------------------------------------------------

def classify_report(source_synced: bool, deployment_performed: bool, runtime_probe: bool) -> dict:
    """SOURCE_SYNCED must never imply DEPLOYED. Deployment claims require
    both an actual deployment and a witnessed runtime probe."""
    out = {"delivery": "SOURCE_SYNCED" if source_synced else "NOT_SYNCED"}
    if deployment_performed and runtime_probe:
        out["deployment"] = "DEPLOYED_VERIFIED"
    elif deployment_performed:
        out["deployment"] = "DEPLOYED_UNVERIFIED"
    else:
        out["deployment"] = "NOT_PERFORMED"
    return out


# ---------------------------------------------------------------------------
# F08 — authorization classification
# ---------------------------------------------------------------------------

def classify_authorization(instruction: str, branch_specified: bool, convention_direct_main: bool) -> str:
    """'Update the repo on GitHub' without a named branch is AMBIGUOUS even
    when repo convention is direct-main. Convention resolves the choice;
    it does not rewrite what the instruction said."""
    if branch_specified:
        return "EXPLICIT"
    if convention_direct_main:
        return "AMBIGUOUS_RESOLVED_BY_CONVENTION"
    return "NOT_ESTABLISHED"
