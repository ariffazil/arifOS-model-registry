"""RSI fixtures F01-F08 — each lesson tested with a FAILURE it catches and a
LEGITIMATE case it permits. Real implementations under test:
scripts/rsi_lessons.py. Run: python -m pytest tests/test_rsi_fixtures.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from rsi_lessons import (ci_exoneration, ci_inventory_claim, receipt_valid,
                         json_semantic_check, merge_timelines,
                         deploy_risk_claim, classify_report,
                         classify_authorization)


# ===========================================================================
# F01 — baseline failure does not exonerate without signature match
# ===========================================================================

def test_f01_catches_exoneration_without_signature():
    """FAILURE CAUGHT: 'it fails on main too' with NO signature evidence
    (logs expired) must NOT return MATCHING_BASELINE_FAILURE."""
    verdict = ci_exoneration(baseline_failure_seen=True,
                             new_signature=None, baseline_signature=None)
    assert verdict == "ATTRIBUTION_UNRESOLVED"


def test_f01_permits_matching_signatures():
    """LEGITIMATE: identical error signatures on both commits support
    matching-baseline attribution."""
    sig = {"step": "validate-routing", "error": "exit 1"}
    assert ci_exoneration(True, sig, dict(sig)) == "MATCHING_BASELINE_FAILURE"


def test_f01_flags_signature_mismatch():
    assert ci_exoneration(True, {"e": "A"}, {"e": "B"}) == "ATTRIBUTION_UNRESOLVED"


def test_f01_no_baseline_is_new_context():
    assert ci_exoneration(False, {"e": "A"}, {"e": "A"}) == "NEW_FAILURE_CONTEXT"


# ===========================================================================
# F02 — scoped CI inventory claims
# ===========================================================================

def test_f02_catches_ci_absence_overclaim():
    """FAILURE CAUGHT: 404/0-check-runs must yield CI_NOT_OBSERVED_AT_REF,
    never a universal 'no CI exists'."""
    claim = ci_inventory_claim(check_runs=0, workflow_files_observed=False,
                               contents_lookup_ok=True)
    assert claim == "CI_NOT_OBSERVED_AT_REF"
    assert "ABSENT" not in claim


def test_f02_lookup_failure_is_unknown():
    """LEGITIMATE + boundary: failed contents lookup -> CI_UNKNOWN."""
    assert ci_inventory_claim(0, None, contents_lookup_ok=False) == "CI_UNKNOWN_LOOKUP_FAILED"


def test_f02_present_workflows_reported():
    assert ci_inventory_claim(3, True, True) == "CI_WORKFLOWS_PRESENT"


# ===========================================================================
# F03 — receipts from captured values
# ===========================================================================

def test_f03_rejects_typed_string_receipt():
    """FAILURE CAUGHT: a receipt whose SHA was typed from memory (no API
    provenance) is invalid even if the value looks right."""
    assert receipt_valid({"remote_sha": "87e749e", "source": "typed"}, "87e749e") is False


def test_f03_accepts_api_captured_match():
    """LEGITIMATE: API-captured remote SHA equal to the delivery commit."""
    assert receipt_valid({"remote_sha": "abc123", "source": "api_captured"}, "abc123") is True


def test_f03_rejects_captured_mismatch():
    assert receipt_valid({"remote_sha": "abc123", "source": "api_captured"}, "def456") is False


# ===========================================================================
# F04 — JSON semantic validity
# ===========================================================================

def test_f04_catches_syntax_ok_semantic_gap():
    """FAILURE CAUGHT (real, 2026-10-30): 2A package parsed fine but lacked
    captured_at/captured_by; c3 carried date-only verify_at."""
    doc = {"captured_by": "FI-008", "verify_at": "2026-10-23"}
    res = json_semantic_check(doc, required_keys=["captured_at"], tz_fields=["verify_at"])
    assert res["valid"] is False
    assert any("captured_at" in p for p in res["problems"])
    assert any("verify_at" in p for p in res["problems"])


def test_f04_permits_complete_doc():
    doc = {"captured_at": "2026-10-30T01:15:00Z", "captured_by": "FI-008",
           "verify_at": "2026-10-23T23:59:59+08:00"}
    res = json_semantic_check(doc, required_keys=["captured_at", "captured_by"],
                              tz_fields=["verify_at"])
    assert res["valid"] is True and res["problems"] == []


# ===========================================================================
# F05 — timeline merge guard
# ===========================================================================

def test_f05_blocks_silent_merge():
    """FAILURE CAUGHT: merging another agent's session events without a
    declared cross-reference must raise."""
    with pytest.raises(ValueError, match="silent timeline merge"):
        merge_timelines([{"e": 1}], [{"e": 2}], cross_ref_declared=False)


def test_f05_permits_declared_merge():
    """LEGITIMATE: declared cross-reference merges with provenance tags."""
    merged = merge_timelines([{"e": 1}], [{"e": 2}], cross_ref_declared=True)
    assert [m["timeline"] for m in merged] == ["A", "B"]


# ===========================================================================
# F06 — scoped side-effect claims
# ===========================================================================

def test_f06_refuses_universal_guarantee():
    """FAILURE CAUGHT: 'no deploy keywords seen' can never become
    'no deploy-on-push risk' as a universal claim."""
    res = deploy_risk_claim(triggers_inspected=9, triggers_total=9, deploy_paths_found=0)
    assert res["claim"].startswith("no deployment path found within inspected scope")
    assert res["universal"] is False


def test_f06_partial_inspection_labelled():
    res = deploy_risk_claim(triggers_inspected=3, triggers_total=9, deploy_paths_found=0)
    assert "PARTIAL INSPECTION" in res["claim"]


def test_f06_found_paths_reported_loudly():
    res = deploy_risk_claim(triggers_inspected=9, triggers_total=9, deploy_paths_found=1)
    assert res["claim"] == "DEPLOYMENT_PATHS_FOUND"


# ===========================================================================
# F07 — delivery never becomes deployment
# ===========================================================================

def test_f07_catches_deploy_claim_from_push():
    """FAILURE CAUGHT: 'pushed to GitHub' must not be reportable as deployed."""
    rep = classify_report(source_synced=True, deployment_performed=False, runtime_probe=False)
    assert rep["delivery"] == "SOURCE_SYNCED"
    assert rep["deployment"] == "NOT_PERFORMED"


def test_f07_deploy_requires_runtime_probe():
    """LEGITIMATE boundary: deployment without a runtime probe stays
    DEPLOYED_UNVERIFIED — never DEPLOYED_VERIFIED."""
    assert classify_report(True, True, False)["deployment"] == "DEPLOYED_UNVERIFIED"
    assert classify_report(True, True, True)["deployment"] == "DEPLOYED_VERIFIED"


# ===========================================================================
# F08 — authorization classification
# ===========================================================================

def test_f08_catches_inferred_branch_approval():
    """FAILURE CAUGHT (real, 2026-10-30): 'make sure the repo on GitHub is
    updated' named no branch — direct-to-main must stay AMBIGUOUS, never
    be retold as explicit approval."""
    verdict = classify_authorization(
        instruction="now please make sure AAA model registry on github repo updated and upgraded",
        branch_specified=False, convention_direct_main=True)
    assert verdict == "AMBIGUOUS_RESOLVED_BY_CONVENTION"
    assert verdict != "EXPLICIT"


def test_f08_explicit_branch_named():
    """LEGITIMATE: a named branch makes it EXPLICIT."""
    assert classify_authorization("push to branch X", branch_specified=True,
                                  convention_direct_main=False) == "EXPLICIT"


def test_f08_no_convention_not_established():
    assert classify_authorization("update it", branch_specified=False,
                                  convention_direct_main=False) == "NOT_ESTABLISHED"
