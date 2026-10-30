"""Registry v3 tests — resolver-witnessed objects, alias-drift regression,
governance-card budget, evidence pinning, secret boundary.

Run with: python -m pytest tests/test_registry_v3.py -v
"""

import json
import re
from pathlib import Path

import pytest

REGISTRY_PATH = Path(__file__).parent.parent
V3_DIRS = ["model_families", "model_releases", "provider_offerings",
           "runtime_routes", "probe_receipts", "routing_decisions", "governance_cards",
           "role_assessments"]


def _json_files():
    out = {}
    for d in V3_DIRS:
        base = REGISTRY_PATH / d
        if not base.exists():
            continue
        for p in base.rglob("*.json"):
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):  # routing_decisions.json is a list; separate fixture
                out[str(p.relative_to(REGISTRY_PATH))] = data
    return out


@pytest.fixture(scope="module")
def files():
    return _json_files()


@pytest.fixture(scope="module")
def decisions():
    return json.loads((REGISTRY_PATH / "routing_decisions" / "routing_decisions.json").read_text())


# ---------------------------------------------------------------------------
# Golden regression: fed deepseek-v3.2 -> deepseek-v4-pro alias drift
# ---------------------------------------------------------------------------

def test_alias_drift_regression_golden(files):
    """The 2026-10-30 witnessed case must be detected and must HOLD."""
    receipts = [f for f in files.values()
                if f.get("object_type") == "probe_receipt"
                and f.get("receipt_id") == "fed-4000-deepseek-v3-2-direct-20261030"]
    assert receipts, "golden probe receipt missing"
    r = receipts[0]
    assert r["requested_model"] == "deepseek-v3.2"
    assert r["api_resolved_model"] == "deepseek-v4-pro"
    assert r["requested_model"] != r["api_resolved_model"]
    assert r["resolution_state"] == "alias_drift"

    route = files["runtime_routes/fed_4000.json"]
    assert route["resolves_to"]["resolution_state"] == "alias_drift"
    assert route["status"] == "hold"
    assert "frozen_baseline" in route["forbidden_uses"]
    assert "model_identity_attestation" in route["forbidden_uses"]


def test_self_claim_is_never_identity_evidence(files):
    for f in files.values():
        if f.get("object_type") == "probe_receipt" and f.get("self_claimed_identity"):
            assert f["self_claim_is_identity_evidence"] is False, f["receipt_id"]


def test_catalog_only_model_is_not_alive(files):
    """/models listing and reachability must never be promoted to model_alive."""
    ds = files["provider_offerings/deepseek_direct.json"]
    assert ds["availability"]["state"] == "catalog_reachable_inference_blocked"
    assert any("never" in n.lower() and "model_alive" in n for n in ds["notes"])
    oc = files["provider_offerings/opencode_go_glm.json"]
    assert oc["availability"]["state"] != "dead"
    assert oc["failure_class"] == "billing_or_upstream_funds"


# ---------------------------------------------------------------------------
# Routing decisions: proposed, never self-ratified
# ---------------------------------------------------------------------------

def test_no_agent_self_ratification(decisions):
    for d in decisions:
        assert d["ratified"] is False, f"{d['object_key']} — agent must not self-ratify (invariant 4)"
        assert d["ratification"] == "awaiting_888"


def test_drift_route_has_hold_decision(decisions):
    holds = [d for d in decisions if d["route_key"] == "fed_4000" and d["decision"] == "HOLD"]
    assert holds, "alias-drift regression requires a HOLD decision"


def test_frozen_reference_only_for_pinned_snapshot(decisions):
    by_model = {d["object_key"]: d["decision"] for d in decisions}
    assert by_model["dashscope_direct::qwen-plus-2025-01-25"] == "FROZEN_REFERENCE"
    assert by_model["groq_lane::gpt-oss-120b"] == "HOLD"  # not pinned yet


# ---------------------------------------------------------------------------
# Knowledge cutoff honesty
# ---------------------------------------------------------------------------

def test_cutoff_never_inferred_from_snapshot_date(files):
    for f in files.values():
        if f.get("object_type") == "model_release":
            kc = f.get("knowledge_cutoff", {})
            if kc.get("status") == "unknown":
                assert kc.get("value") is None, f["model_id"]
                assert kc.get("must_not_infer_from_snapshot_date") is True, f["model_id"]


def test_unpinned_releases_have_null_artifact_hashes(files):
    gpt = files["model_releases/gpt-oss-120b.json"]
    assert gpt["version_stability"] == "pin_capable"
    assert all(v is None for v in gpt["artifact_hashes"].values())
    assert len(gpt["pin_requirements"]) >= 7


# ---------------------------------------------------------------------------
# Governance card: fail-closed shape + size budget
# ---------------------------------------------------------------------------

def test_governance_card_fail_closed(files):
    card = files["governance_cards/mgc-forge-777-example.json"]
    assert card["verdict"] == "HOLD"
    assert card["resolved_model"] == "UNKNOWN"
    assert card["identity_state"] == "UNRESOLVED"
    ceil = card["authority_ceiling"]
    assert ceil == {"propose": True, "verify": False, "authorize": False, "execute": False}
    assert "self_authorizing_judge" in card["forbidden_roles"]


def test_governance_card_size_budget(files):
    raw = (REGISTRY_PATH / "governance_cards" / "mgc-forge-777-example.json").read_bytes()
    assert len(raw) <= 2048, f"card {len(raw)}B exceeds hard_max_bytes=2048"
    for forbidden in ["probe_history", "biography", "pricing", "hazard_catalogue"]:
        assert forbidden not in json.dumps(raw.decode()), forbidden


# ---------------------------------------------------------------------------
# Evidence bindings: pinned to 40-hex revisions
# ---------------------------------------------------------------------------

def test_evidence_bindings_pinned():
    eb = json.loads((REGISTRY_PATH / "evidence_bindings.json").read_text())
    datasets = {b["dataset"]: b for b in eb["bindings"]}
    for name in ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]:
        key = f"hf://datasets/ariffazil/{name}"
        assert key in datasets, f"{name} binding missing"
        assert re.fullmatch(r"[0-9a-f]{40}", datasets[key]["revision"]), name
        assert datasets[key]["role"], name


# ---------------------------------------------------------------------------
# Secret boundary: no key material anywhere in v3 objects
# ---------------------------------------------------------------------------

def test_no_secret_material_in_v3_objects(files):
    for rel, data in files.items():
        blob = json.dumps(data)
        for marker in ["sk-", "api_key=", "AKIA", "Bearer "]:
            assert marker not in blob, f"{rel} contains '{marker}'"


# ---------------------------------------------------------------------------
# Wiring status: JUDGE corrections present as auditable data
# ---------------------------------------------------------------------------

def test_wiring_status_corrections_present():
    ws = (REGISTRY_PATH / "runtime_wiring" / "WIRING_STATUS.yaml").read_text()
    assert "substituted_with_a2a: false" in ws
    assert "UNKNOWN_SOURCE_UNRESOLVED" in ws
    assert "origin: model_invocation_envelope" in ws
    assert "hard_max_bytes: 2048" in ws
    assert "silent_hot_reload: forbidden" in ws
    assert "resolver_and_binder" in ws


def test_retrospective_probe_cannot_claim_ex_ante(files):
    """Temporal Reality Loop discipline: retrospective probes are scoped, never
    promoted to genuine ex-ante prediction evidence."""
    ra = files["role_assessments/petronas_retrospective_probe_001.json"]
    exp = ra["experiment"]
    assert exp["mode"] == "retrospective_simulation"
    assert exp["outcome_may_predate_generation"] is True
    assert "evidence_of_genuine_ex_ante_prediction" in exp["unsuitable_for"]
    assert "predictive_superiority_claim" in exp["unsuitable_for"]
    assert exp["no_tools_proves"] == "external_retrieval_disabled_only"
    for a in ra["assessments"]:
        assert a["status"] == "provisional"
        assert a["routing"].get("sole_verifier", a["routing"].get("sole_financial_verifier")) == "denied"
    for law in ["snapshot_name != verified_cutoff", "no_tools != no_parametric_leakage"]:
        assert law in ra["temporal_identity_law"]
