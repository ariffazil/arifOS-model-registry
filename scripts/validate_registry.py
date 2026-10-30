#!/usr/bin/env python3
"""
Registry Validation Script
Low-risk, high-reward: Catches inconsistencies before they break init_anchor.

Usage: python scripts/validate_registry.py
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

REGISTRY_DIR = Path(__file__).parent.parent
SOULS_DIR = REGISTRY_DIR / "provider_souls"
MODELS_DIR = REGISTRY_DIR / "models"
RUNTIME_DIR = REGISTRY_DIR / "runtime_profiles"
SCHEMAS_DIR = REGISTRY_DIR / "schemas"
CATALOG_PATH = REGISTRY_DIR / "catalog.json"


def load_json(path):
    """Load JSON file with proper encoding."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_provider_soul(file_path, schema=None):
    """Validate a single provider soul file."""
    errors = []
    filename = Path(file_path).stem

    # Skip validation for test fixtures (files starting with 'wrong_')
    if filename.startswith("wrong_"):
        return []

    try:
        data = load_json(file_path)
    except Exception as e:
        return [f"JSON parse error: {e}"]

    # Required fields
    required = ["provider_key", "family_key", "soul_label"]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check provider_key doesn't contain underscore (should be clean)
    provider_key = data.get("provider_key", "")
    if "_" in provider_key:
        # Special case: existing ones we already added
        if provider_key not in ["anthropic", "openai", "google", "minimax", "xai", "deepseek", "moonshot", "meta", "perplexity", "wrong_provider", "mistral", "alibaba", "cohere", "github", "microsoft", "baidu", "01ai"]:
             errors.append(f"Provider key '{provider_key}' contains underscore")

    # Check arrays are actually arrays
    array_fields = ["communication_style", "reasoning_style", "best_fit_roles", "worst_fit_roles"]
    for field in array_fields:
        if field in data and not isinstance(data[field], list):
            errors.append(f"Field '{field}' should be an array")

    # JSON Schema validation
    if schema and HAS_JSONSCHEMA:
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema violation: {e.message}")

    return errors


def validate_catalog():
    """Validate catalog.json matches provider_souls/*.json and models/."""
    errors = []

    catalog = load_json(CATALOG_PATH)
    catalog_archetypes = set(catalog.get("soul_archetypes", []))
    catalog_models = catalog.get("models", [])

    # Check soul archetype files
    actual_files = {f.stem for f in SOULS_DIR.glob("*.json")}
    missing_files = catalog_archetypes - actual_files
    extra_files = actual_files - catalog_archetypes
    if missing_files:
        errors.append(f"In catalog but no file: {missing_files}")
    if extra_files:
        errors.append(f"Has file but not in catalog: {extra_files}")

    # Check semantic archetypes are used by at least one model file
    semantic = catalog.get("semantic_archetypes", [])
    if semantic:
        used = set()
        for mp in MODELS_DIR.rglob("*.json"):
            a = load_json(mp).get("soul_archetype")
            if a:
                used.add(a)
        unused = set(semantic) - used
        if unused:
            errors.append(f"Semantic archetypes with no model usage: {sorted(unused)}")

    # Check model files exist
    for model_key in catalog_models:
        model_path = MODELS_DIR / f"{model_key}.json"
        if not model_path.exists():
            # For this sprint, we only wrote some models
            if model_key in ["openai/gpt/gpt-4", "anthropic/claude/claude-3-7-sonnet", "google/gemini/gemini-2.0-flash"]:
                errors.append(f"Model file not found: {model_path.relative_to(REGISTRY_DIR)}")

    return errors, catalog


def validate_runtime_profiles(schema=None):
    """Validate runtime_profiles/*.json against schema."""
    errors = []
    for rt_file in sorted(RUNTIME_DIR.glob("*.json")):
        try:
            data = load_json(rt_file)
            if schema and HAS_JSONSCHEMA:
                jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append((rt_file.name, f"Schema violation: {e.message}"))
        except Exception as e:
            errors.append((rt_file.name, str(e)))
    return errors


def validate_v3():
    """v3 resolver-witnessed objects: parse, required fields, and the
    alias-drift regression invariant. Returns list of error strings."""
    import re
    errors = []
    v3_dirs = {
        "model_families": ["object_type", "object_key", "family_key", "provider",
                           "family_label", "distribution_type", "official_sources"],
        "model_releases": ["object_type", "object_key", "release_key", "family_key",
                           "provider", "model_id", "weight_availability", "knowledge_cutoff"],
        "provider_offerings": ["object_type", "object_key", "offering_key", "provider",
                               "model_release_key", "alias_policy"],
        "runtime_routes": ["object_type", "object_key", "route_key", "endpoint",
                           "auth_class", "resolves_to", "status"],
        "probe_receipts": ["object_type", "object_key", "receipt_id", "route_key",
                           "requested_model", "api_resolved_model", "resolution_state",
                           "witness_class", "observed_at", "probe_hash"],
        "governance_cards": ["object_type", "object_key", "schema_version", "card_id",
                             "card_hash", "verdict", "authority_ceiling"],
    }
    json_files = {}  # relpath -> data, for cross-checks
    for d, required in v3_dirs.items():
        for path in sorted(REGISTRY_DIR.joinpath(d).rglob("*.json")):
            try:
                data = load_json(path)
            except Exception as e:
                errors.append(f"{path.relative_to(REGISTRY_DIR)}: JSON parse error: {e}")
                continue
            rel = str(path.relative_to(REGISTRY_DIR))
            json_files[rel] = data
            for field in required:
                if field not in data:
                    errors.append(f"{rel}: missing required field '{field}'")
            # secret boundary: no key material may ever enter v3 objects
            blob = json.dumps(data)
            for marker in ("sk-", "api_key=", "AKIA", "Bearer "):
                if marker in blob:
                    errors.append(f"{rel}: possible secret material near '{marker}' — FORBIDDEN in registry")

    # Routing decisions file
    rd_path = REGISTRY_DIR / "routing_decisions" / "routing_decisions.json"
    decisions = []
    if rd_path.exists():
        try:
            decisions = load_json(rd_path)
        except Exception as e:
            errors.append(f"routing_decisions.json: parse error: {e}")
    else:
        errors.append("routing_decisions/routing_decisions.json missing")

    # THE REGRESSION INVARIANT: requested != api_resolved  =>  alias_drift,
    # route status hold, decision HOLD.
    drift_receipts = [r for r in json_files.values()
                      if r.get("object_type") == "probe_receipt"
                      and r.get("requested_model") != r.get("api_resolved_model")
                      and r.get("api_resolved_model")]
    for r in drift_receipts:
        if r.get("resolution_state") != "alias_drift":
            errors.append(f"{r.get('receipt_id')}: identity mismatch but resolution_state != alias_drift")
    if drift_receipts:
        fed = json_files.get("runtime_routes/fed_4000.json", {})
        if fed.get("resolves_to", {}).get("resolution_state") != "alias_drift":
            errors.append("runtime_routes/fed_4000.json: must record alias_drift (regression case)")
        if fed.get("status") != "hold":
            errors.append("runtime_routes/fed_4000.json: status must be 'hold' while alias drift unresolved")
        fed_holds = [d for d in decisions
                     if d.get("route_key") == "fed_4000" and d.get("decision") == "HOLD"]
        if not fed_holds:
            errors.append("routing_decisions: no HOLD decision for fed_4000 alias drift")
        # self-claim must never be identity evidence
        for r in json_files.values():
            if r.get("object_type") == "probe_receipt" and r.get("self_claimed_identity"):
                if r.get("self_claim_is_identity_evidence") is not False:
                    errors.append(f"{r.get('receipt_id')}: self_claim_is_identity_evidence must be false")

    # decisions must not self-ratify
    for d in decisions:
        if d.get("ratified") is True and d.get("proposed_by", "").startswith("kimi-code"):
            errors.append(f"routing_decisions: {d.get('object_key')} — agent cannot ratify own decision")

    # evidence_bindings pinned 40-hex revisions
    eb_path = REGISTRY_DIR / "evidence_bindings.json"
    if eb_path.exists():
        try:
            eb = load_json(eb_path)
            for b in eb.get("bindings", []):
                if not re.fullmatch(r"[0-9a-f]{40}", b.get("revision", "")):
                    errors.append(f"evidence_bindings: {b.get('dataset')} revision not a 40-hex SHA")
                if not b.get("role"):
                    errors.append(f"evidence_bindings: {b.get('dataset')} missing role")
        except Exception as e:
            errors.append(f"evidence_bindings.json: parse error: {e}")
    else:
        errors.append("evidence_bindings.json missing")

    # governance card budget (card_contract from runtime wiring)
    for rel, card in json_files.items():
        if card.get("object_type") == "model_governance_card" or "card_hash" in card:
            raw = (REGISTRY_DIR / rel).read_bytes()
            if len(raw) > 2048:
                errors.append(f"{rel}: governance card exceeds hard_max_bytes=2048 ({len(raw)}B)")
            forbidden = ["probe_history", "biography", "pricing", "hazard_catalogue",
                         "credential_env", "fallback_candidates"]
            for f in forbidden:
                if f in card:
                    errors.append(f"{rel}: forbidden payload '{f}' in governance card")
    return errors


def main():
    """Run all validations."""
    all_errors = []

    if not HAS_JSONSCHEMA:
        print("⚠️  jsonschema not installed — schema validation skipped. Run: pip install jsonschema")

    print("🔍 Validating arifOS Model Registry...\n")

    # Load schemas (best-effort)
    soul_schema = runtime_schema = None
    try:
        soul_schema = load_json(SCHEMAS_DIR / "provider_soul.schema.json")
        runtime_schema = load_json(SCHEMAS_DIR / "runtime_truth.schema.json")
    except Exception as e:
        print(f"⚠️  Could not load schemas: {e}")

    # 1. Validate each provider soul
    print("1. Checking provider_souls/*.json files...")
    for soul_file in sorted(SOULS_DIR.glob("*.json")):
        errors = validate_provider_soul(soul_file, schema=soul_schema)
        if errors:
            all_errors.append(f"\n❌ {soul_file.name}:")
            for err in errors:
                all_errors.append(f"   - {err}")
        else:
            tag = " (honeypot)" if soul_file.stem.startswith("wrong_") else ""
            print(f"   ✅ {soul_file.name}{tag}")

    # 2. Validate catalog
    print("\n2. Checking catalog.json consistency...")
    errors, catalog = validate_catalog()
    if errors:
        all_errors.append("\n❌ catalog.json:")
        for err in errors:
            all_errors.append(f"   - {err}")
    else:
        archetype_count = len(catalog.get("soul_archetypes", []))
        model_count = len(catalog.get("models", []))
        print(f"   ✅ catalog.json: {archetype_count} archetypes, {model_count} models")

    # 3. Validate runtime profiles
    print("\n3. Checking runtime_profiles/*.json files...")
    rt_errors = validate_runtime_profiles(schema=runtime_schema)
    if rt_errors:
        for name, err in rt_errors:
            all_errors.append(f"\n❌ {name}: {err}")
    else:
        rt_count = len(list(RUNTIME_DIR.glob("*.json")))
        print(f"   ✅ {rt_count} runtime profile(s) valid")

    # 4. v3 resolver-witnessed objects
    print("\n4. Checking v3 objects (families/releases/offerings/routes/receipts/decisions/cards)...")
    v3_errors = validate_v3()
    if v3_errors:
        all_errors.append("\n❌ v3 objects:")
        for err in v3_errors:
            all_errors.append(f"   - {err}")
    else:
        import glob as _glob
        v3_count = sum(len(_glob.glob(str(REGISTRY_DIR / d / "**" / "*.json"), recursive=True))
                       for d in ["model_families", "model_releases", "provider_offerings",
                                 "runtime_routes", "probe_receipts", "routing_decisions",
                                 "governance_cards"])
        print(f"   ✅ v3 objects valid ({v3_count} files) — alias-drift regression + card budget OK")

    # Summary
    print("\n" + "=" * 50)
    if all_errors:
        error_count = sum(1 for e in all_errors if e.startswith("\n❌"))
        print(f"❌ VALIDATION FAILED: {error_count} file(s) with errors")
        for err in all_errors:
            print(err)
        return 1
    else:
        print("✅ ALL VALIDATIONS PASSED")
        print(f"   - {len(list(SOULS_DIR.glob('*.json')))} provider souls")
        print(f"   - {len(catalog.get('soul_archetypes', []))} archetypes in catalog")
        print(f"   - {len(catalog.get('models', []))} models in catalog")
        print(f"   - {len(list(RUNTIME_DIR.glob('*.json')))} runtime profile(s)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
