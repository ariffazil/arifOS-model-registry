#!/usr/bin/env python3
"""build_v3_objects.py — deterministic generator for registry v3 resolver-witnessed objects.

Implements the 2026-10-30 seal (registry v3) + AAA_MODEL_GOVERNANCE_RUNTIME_WIRING
brief with JUDGE corrections:

  Objects: model_family, model_release, provider_offering, runtime_route,
           probe_receipt, routing_decision, model_governance_card (fixture),
           evidence_bindings, runtime_wiring/WIRING_STATUS.yaml.
  Facts:   qwen-plus-2025-01-25 verified-alive (DashScope pinned snapshot);
           gpt-oss-120b open-weight pin-capable candidate (Groq lane);
           fed deepseek-v3.2 -> deepseek-v4-pro alias drift (HOLD regression case,
           FI-008 direct probe 2026-10-30Z incl. self-claim mismatch witness);
           zai floating-alive; opencode-go glm-5.2 billing-lane failure (NOT dead);
           deepseek-direct catalog-reachable / balance-blocked.

Idempotent: regenerating overwrites; timestamps fixed to BUILD_DATE. Stdlib only.
Run: python3 scripts/build_v3_objects.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_DATE = "2026-10-30"
PROVENANCE = "kimi-code/FI-008, session SEAL-d59c04d66b294e0b, user-directed 2026-10-30"

written: list[str] = []


def w(rel: str, obj) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, (dict, list)):
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        path.write_text(obj, encoding="utf-8")
    written.append(rel)


def content_hash(obj: dict) -> str:
    """SHA-256 over canonical JSON, excluding any pre-existing hash field."""
    body = {k: v for k, v in obj.items() if k not in ("probe_hash", "card_hash")}
    payload = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def git_revision() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "uncommitted-at-build"


# ---------------------------------------------------------------------------
# 1. SCHEMAS (v3 object types + governance card + producer context)
# ---------------------------------------------------------------------------

def obj_envelope(object_type: str, required: list[str], props: dict) -> dict:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": f"arifOS registry v3 {object_type}",
        "type": "object",
        "required": ["object_type", "object_key", *required],
        "properties": {
            "object_type": {"const": object_type},
            "object_key": {"type": "string"},
            "created_at": {"type": "string"},
            "updated_at": {"type": "string"},
            "provenance": {"type": "string"},
            **props,
        },
        "additionalProperties": True,
    }


SCHEMAS = {
    "schemas/model_family.schema.json": obj_envelope(
        "model_family",
        ["family_key", "provider", "family_label", "distribution_type", "official_sources"],
        {
            "provider": {"type": "string"},
            "family_label": {"type": "string"},
            "architecture_class": {"type": ["string", "null"]},
            "distribution_type": {"enum": ["closed", "open_weight", "mixed"]},
            "license": {"type": ["string", "null"]},
            "modalities": {"type": "array"},
            "languages": {"type": "array"},
            "context_architecture": {"type": ["string", "null"]},
            "lineage": {"type": "array"},
            "official_sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["label", "url", "url_class"],
                    "properties": {
                        "label": {"type": "string"},
                        "url": {"type": "string", "format": "uri"},
                        "url_class": {"enum": ["official_docs", "official_model_card", "official_repo", "official_platform"]},
                    },
                },
            },
            "status": {"enum": ["active", "sources_unverified", "archived"]},
        },
    ),
    "schemas/model_release.schema.json": obj_envelope(
        "model_release",
        ["release_key", "family_key", "provider", "model_id", "weight_availability", "knowledge_cutoff"],
        {
            "family_key": {"type": "string"},
            "provider": {"type": "string"},
            "model_id": {"type": "string"},
            "release_date": {"type": ["string", "null"]},
            "snapshot_date": {"type": ["string", "null"]},
            "knowledge_cutoff": {
                "type": "object",
                "required": ["value", "status"],
                "properties": {
                    "value": {"type": ["string", "null"]},
                    "status": {"enum": ["declared", "unknown", "not_applicable"]},
                    "must_not_infer_from_snapshot_date": {"type": "boolean"},
                },
            },
            "parameter_structure": {"type": ["string", "null"]},
            "weight_availability": {"enum": ["closed_or_undisclosed", "open_weight"]},
            "license": {"type": ["string", "null"]},
            "official_model_card": {"type": ["string", "null"]},
            "artifact_hashes": {"type": "object"},
            "supersedes": {"type": ["string", "null"]},
            "derived_from": {"type": "array"},
            "version_stability": {"enum": ["provider_pinned_alias", "floating", "pin_capable", "pinned_artifact"]},
            "pin_requirements": {"type": "array"},
            "routing_class": {"type": "string"},
            "canonicality": {"type": "string"},
            "limitations": {"type": "array"},
        },
    ),
    "schemas/provider_offering.schema.json": obj_envelope(
        "provider_offering",
        ["offering_key", "provider", "model_release_key", "alias_policy", "offering_url"],
        {
            "provider": {"type": "string"},
            "model_release_key": {"type": "string"},
            "alias_policy": {"enum": ["dated_snapshot", "latest_floating", "pinned_revision", "unknown"]},
            "region": {"type": ["string", "null"]},
            "api_compat": {"type": "string"},
            "pricing_class": {"type": ["string", "null"]},
            "quota_state": {"type": ["string", "null"]},
            "deprecation_state": {"type": "string"},
            "availability": {
                "type": "object",
                "properties": {
                    "state": {"type": "string"},
                    "evidence_class": {"type": "string"},
                    "observed_at": {"type": ["string", "null"]},
                },
            },
            "failure_class": {"type": ["string", "null"]},
            "notes": {"type": "array"},
        },
    ),
    "schemas/runtime_route.schema.json": obj_envelope(
        "runtime_route",
        ["route_key", "endpoint", "auth_class", "resolves_to"],
        {
            "transport": {"type": "string"},
            "endpoint": {"type": "string"},
            "auth_class": {"type": "string"},
            "resolves_to": {
                "type": "object",
                "required": ["resolution_state"],
                "properties": {
                    "offering_key": {"type": ["string", "null"]},
                    "release_key": {"type": ["string", "null"]},
                    "resolution_state": {"enum": ["matched", "alias_drift", "unresolved"]},
                    "observed_resolved_model": {"type": ["string", "null"]},
                    "last_verified_at": {"type": ["string", "null"]},
                },
            },
            "catalog_only_models": {"type": "array"},
            "allowed_uses": {"type": "array"},
            "forbidden_uses": {"type": "array"},
            "status": {"enum": ["active", "degraded", "hold", "blocked"]},
        },
    ),
    "schemas/probe_receipt.schema.json": obj_envelope(
        "probe_receipt",
        ["receipt_id", "route_key", "requested_model", "api_resolved_model",
         "resolution_state", "witness_class", "observed_at"],
        {
            "self_claimed_identity": {"type": ["string", "null"]},
            "self_claim_is_identity_evidence": {"const": False},
            "http_status": {"type": ["integer", "null"]},
            "latency_ms": {"type": ["integer", "null"]},
            "fingerprint": {"type": ["string", "null"]},
            "finish_reason": {"type": ["string", "null"]},
            "token_counts": {"type": "object"},
            "credential_class": {"type": "string"},
            "probe_hash": {"type": "string"},
            "raw_receipt_location": {"type": ["string", "null"]},
            "notes": {"type": "array"},
        },
    ),
    "schemas/routing_decision.schema.json": obj_envelope(
        "routing_decision",
        ["route_key", "decision", "rationale", "proposed_by"],
        {
            "decision": {
                "enum": ["PRIMARY_DEFAULT", "ACTIVE_FALLBACK", "FROZEN_REFERENCE",
                         "FROZEN_REFERENCE_CANDIDATE", "NICHE_LANGUAGE", "CODE_SPECIALIST",
                         "CURRENT_CAPABILITY", "HOLD", "BLOCKED"],
            },
            "rationale": {"type": "string"},
            "basis_receipts": {"type": "array"},
            "forbidden_uses": {"type": "array"},
            "allowed_uses": {"type": "array"},
            "proposed_by": {"type": "string"},
            "authority_basis": {"type": "string"},
            "decided_at": {"type": "string"},
            "ratified": {"type": "boolean"},
            "ratification": {"type": "string"},
        },
    ),
    "schemas/model_governance_card.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "arifOS model_governance_card v1 (runtime wiring, JUDGE-corrected)",
        "type": "object",
        "required": [
            "schema_version", "card_id", "session_id", "lane_id", "registry_revision",
            "compiled_at", "requested_model", "resolved_model", "identity_state",
            "route_id", "mutability", "eligible_roles", "forbidden_roles",
            "authority_ceiling", "verdict", "card_hash",
        ],
        "properties": {
            "schema_version": {"const": 1},
            "card_id": {"type": "string"},
            "session_id": {"type": ["string", "null"]},
            "lane_id": {"type": "string"},
            "registry_revision": {"type": "string"},
            "source_manifest_hash": {"type": ["string", "null"]},
            "compiled_at": {"type": "string"},
            "requested_model": {"type": "string"},
            "resolved_model": {"type": "string"},
            "identity_state": {"enum": ["MATCHED", "MISMATCH", "UNRESOLVED"]},
            "resolution_evidence_ref": {"type": ["string", "null"]},
            "route_id": {"type": "string"},
            "mutability": {"enum": ["PROVIDER_ALIAS_FLOATING", "PROVIDER_PINNED_SNAPSHOT", "PINNED_ARTIFACT"]},
            "failure_domain": {"type": ["string", "null"]},
            "freshness_state": {"type": "string"},
            "eligible_roles": {"type": "array", "items": {"type": "string"}},
            "forbidden_roles": {"type": "array", "items": {"type": "string"}},
            "tool_policy_ref": {"type": ["string", "null"]},
            "memory_policy_ref": {"type": ["string", "null"]},
            "authority_ceiling": {
                "type": "object",
                "required": ["propose", "verify", "authorize", "execute"],
                "properties": {
                    "propose": {"type": "boolean"},
                    "verify": {"type": "boolean"},
                    "authorize": {"type": "boolean"},
                    "execute": {"type": "boolean"},
                },
            },
            "verdict": {"enum": ["INITIALIZED", "DEGRADED", "HOLD"]},
            "card_hash": {"type": "string"},
        },
        "additionalProperties": False,
    },
    "schemas/producer_context.schema.json": obj_envelope(
        "producer_context",
        ["model_release_ref", "route_ref", "requested_model", "resolved_model",
         "identity_state", "registry_revision"],
        {
            "provider_offering_ref": {"type": "string"},
            "resolution_evidence_ref": {"type": ["string", "null"]},
            "probe_receipt_ref": {"type": ["string", "null"]},
            "epistemic_label": {"enum": ["OBS", "DER", "INT", "SPEC", "UNKNOWN"]},
        },
    ),
}


def build_schemas() -> None:
    for rel, schema in SCHEMAS.items():
        w(rel, schema)


# ---------------------------------------------------------------------------
# 2. MODEL FAMILIES — official AI-lab provider links
# ---------------------------------------------------------------------------

FAMILIES = {
    "alibaba_qwen": {
        "provider": "alibaba", "family_label": "Qwen", "distribution_type": "mixed",
        "license": "varies (Apache-2.0 for open releases)", "architecture_class": "dense + MoE",
        "modalities": ["text", "vision", "audio"], "languages": ["en", "zh", "multilingual"],
        "lineage": ["Qwen2", "Qwen2.5", "Qwen3", "Qwen3-Next"],
        "official_sources": [
            {"label": "Alibaba Cloud Model Studio (DashScope)", "url": "https://help.aliyun.com/zh/model-studio/", "url_class": "official_docs"},
            {"label": "Qwen on Hugging Face", "url": "https://huggingface.co/Qwen", "url_class": "official_model_card"},
            {"label": "QwenLM GitHub", "url": "https://github.com/QwenLM", "url_class": "official_repo"},
        ],
    },
    "openai_gpt": {
        "provider": "openai", "family_label": "GPT (API)", "distribution_type": "closed",
        "license": None, "architecture_class": "proprietary",
        "modalities": ["text", "vision", "audio"], "languages": ["en", "multilingual"],
        "lineage": ["gpt-4", "gpt-4o", "gpt-5.x"],
        "official_sources": [
            {"label": "OpenAI Platform Docs", "url": "https://platform.openai.com/docs", "url_class": "official_docs"},
        ],
    },
    "openai_gpt_oss": {
        "provider": "openai", "family_label": "GPT-OSS (open weight)", "distribution_type": "open_weight",
        "license": "Apache-2.0", "architecture_class": "MoE (gpt-oss-120b: 117B total / 5.1B active)",
        "modalities": ["text"], "languages": ["en", "multilingual"],
        "lineage": ["gpt-oss-120b", "gpt-oss-20b"],
        "official_sources": [
            {"label": "OpenAI gpt-oss announcement", "url": "https://openai.com/index/introducing-gpt-oss/", "url_class": "official_model_card"},
            {"label": "openai on Hugging Face", "url": "https://huggingface.co/openai", "url_class": "official_model_card"},
        ],
    },
    "deepseek": {
        "provider": "deepseek", "family_label": "DeepSeek", "distribution_type": "open_weight",
        "license": "varies (MIT for V4-Pro)", "architecture_class": "MoE + hybrid attention (CSA/HCA)",
        "modalities": ["text"], "languages": ["en", "zh", "multilingual"],
        "lineage": ["deepseek-chat (V2/V3 line)", "deepseek-v3.1", "deepseek-v3.2", "deepseek-v4-pro"],
        "official_sources": [
            {"label": "DeepSeek API Docs", "url": "https://api-docs.deepseek.com/", "url_class": "official_docs"},
            {"label": "deepseek-ai on Hugging Face", "url": "https://huggingface.co/deepseek-ai", "url_class": "official_model_card"},
        ],
    },
    "zai_glm": {
        "provider": "zai", "family_label": "GLM", "distribution_type": "mixed",
        "license": "varies", "architecture_class": "MoE",
        "modalities": ["text", "vision"], "languages": ["en", "zh", "bm_register_untested"],
        "lineage": ["glm-4", "glm-4.5", "glm-5.x"],
        "official_sources": [
            {"label": "Z.AI Docs", "url": "https://docs.z.ai/", "url_class": "official_docs"},
            {"label": "zai-org on Hugging Face", "url": "https://huggingface.co/zai-org", "url_class": "official_model_card"},
        ],
    },
    "moonshot_kimi": {
        "provider": "moonshot", "family_label": "Kimi", "distribution_type": "mixed",
        "license": "varies", "architecture_class": "dense + MoE",
        "modalities": ["text", "vision"], "languages": ["en", "zh", "multilingual"],
        "lineage": ["kimi-k1.5", "kimi-k2", "kimi-k3"],
        "official_sources": [
            {"label": "Moonshot Platform Docs", "url": "https://platform.moonshot.ai/docs", "url_class": "official_docs"},
            {"label": "moonshotai on Hugging Face", "url": "https://huggingface.co/moonshotai", "url_class": "official_model_card"},
        ],
    },
    "minimax": {
        "provider": "minimax", "family_label": "MiniMax", "distribution_type": "mixed",
        "license": "varies", "architecture_class": "MoE",
        "modalities": ["text", "vision", "audio", "video-gen"], "languages": ["en", "zh", "multilingual"],
        "lineage": ["minimax-m2.7", "minimax-m3"],
        "official_sources": [
            {"label": "MiniMax Platform", "url": "https://platform.minimax.io/", "url_class": "official_docs"},
            {"label": "MiniMaxAI on Hugging Face", "url": "https://huggingface.co/MiniMaxAI", "url_class": "official_model_card"},
        ],
    },
    "meta_llama": {
        "provider": "meta", "family_label": "Llama", "distribution_type": "open_weight",
        "license": "Llama Community License", "architecture_class": "dense + MoE",
        "modalities": ["text", "vision"], "languages": ["en", "multilingual"],
        "lineage": ["llama-3", "llama-3.3", "llama-4"],
        "official_sources": [
            {"label": "Llama.com", "url": "https://www.llama.com/", "url_class": "official_model_card"},
            {"label": "meta-llama on Hugging Face", "url": "https://huggingface.co/meta-llama", "url_class": "official_model_card"},
        ],
    },
    "google_gemini": {
        "provider": "google", "family_label": "Gemini", "distribution_type": "closed",
        "license": None, "architecture_class": "proprietary MoE",
        "modalities": ["text", "vision", "audio", "video"], "languages": ["multilingual"],
        "lineage": ["gemini-1.5", "gemini-2.0", "gemini-2.5"],
        "official_sources": [
            {"label": "Google Gemini API Docs", "url": "https://ai.google.dev/gemini-api/docs", "url_class": "official_docs"},
        ],
    },
    "anthropic_claude": {
        "provider": "anthropic", "family_label": "Claude", "distribution_type": "closed",
        "license": None, "architecture_class": "proprietary",
        "modalities": ["text", "vision"], "languages": ["multilingual"],
        "lineage": ["claude-3", "claude-3.7", "claude-4"],
        "official_sources": [
            {"label": "Anthropic Docs", "url": "https://docs.anthropic.com/", "url_class": "official_docs"},
        ],
    },
    "xai_grok": {
        "provider": "xai", "family_label": "Grok", "distribution_type": "mixed",
        "license": "varies", "architecture_class": "MoE",
        "modalities": ["text", "vision"], "languages": ["en", "multilingual"],
        "lineage": ["grok-2", "grok-3", "grok-4"],
        "official_sources": [
            {"label": "xAI Docs", "url": "https://docs.x.ai/", "url_class": "official_docs"},
        ],
    },
    "mistral": {
        "provider": "mistral", "family_label": "Mistral", "distribution_type": "mixed",
        "license": "varies (Apache-2.0 open releases)", "architecture_class": "dense + MoE",
        "modalities": ["text", "vision"], "languages": ["en", "fr", "multilingual"],
        "lineage": ["mistral-large", "mistral-medium", "mixtral"],
        "official_sources": [
            {"label": "Mistral Docs", "url": "https://docs.mistral.ai/", "url_class": "official_docs"},
            {"label": "mistralai on Hugging Face", "url": "https://huggingface.co/mistralai", "url_class": "official_model_card"},
        ],
    },
    "cohere": {
        "provider": "cohere", "family_label": "Command", "distribution_type": "mixed",
        "license": "varies (CC-BY-NC open releases)", "architecture_class": "dense",
        "modalities": ["text"], "languages": ["multilingual"],
        "lineage": ["command-r", "command-a"],
        "official_sources": [
            {"label": "Cohere Docs", "url": "https://docs.cohere.com/", "url_class": "official_docs"},
        ],
    },
    "perplexity": {
        "provider": "perplexity", "family_label": "Perplexity (serving)", "distribution_type": "closed",
        "license": None, "architecture_class": "serving layer over frontier models",
        "modalities": ["text"], "languages": ["multilingual"],
        "lineage": ["perplexity-pro"],
        "official_sources": [
            {"label": "Perplexity API Docs", "url": "https://docs.perplexity.ai/", "url_class": "official_docs"},
        ],
    },
    "baidu_ernie": {
        "provider": "baidu", "family_label": "ERNIE", "distribution_type": "closed",
        "license": None, "architecture_class": "proprietary",
        "modalities": ["text", "vision"], "languages": ["zh", "en"],
        "lineage": ["ernie-4.0", "ernie-4.5"],
        "official_sources": [
            {"label": "Baidu Qianfan Docs", "url": "https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html", "url_class": "official_docs"},
        ],
    },
    "01ai_yi": {
        "provider": "01ai", "family_label": "Yi", "distribution_type": "open_weight",
        "license": "Apache-2.0 / Yi license", "architecture_class": "dense",
        "modalities": ["text", "vision"], "languages": ["en", "zh"],
        "lineage": ["yi-large"],
        "official_sources": [
            {"label": "01.AI on Hugging Face", "url": "https://huggingface.co/01-ai", "url_class": "official_model_card"},
        ],
    },
    "aisingapore_sea_lion": {
        "provider": "aisingapore", "family_label": "SEA-LION", "distribution_type": "open_weight",
        "license": "Apache-2.0 / MIT variants", "architecture_class": "dense (SEA-tuned)",
        "modalities": ["text"], "languages": ["sea_languages", "bm"],
        "lineage": ["sea-lion-v3", "sea-lion-v4"],
        "official_sources": [
            {"label": "SEA-LION", "url": "https://sea-lion.ai/", "url_class": "official_model_card"},
        ],
    },
    "github_copilot": {
        "provider": "github", "family_label": "Copilot", "distribution_type": "closed",
        "license": None, "architecture_class": "serving layer",
        "modalities": ["text", "code"], "languages": ["en", "multilingual"],
        "lineage": ["copilot-chat"],
        "official_sources": [
            {"label": "GitHub Copilot Docs", "url": "https://docs.github.com/en/copilot", "url_class": "official_docs"},
        ],
    },
    "microsoft_copilot": {
        "provider": "microsoft", "family_label": "Copilot (enterprise)", "distribution_type": "closed",
        "license": None, "architecture_class": "serving layer",
        "modalities": ["text", "vision"], "languages": ["multilingual"],
        "lineage": ["copilot-enterprise"],
        "official_sources": [
            {"label": "Microsoft Learn Copilot", "url": "https://learn.microsoft.com/en-us/copilot/", "url_class": "official_docs"},
        ],
    },
    "ilmu": {
        "provider": "ilmu", "family_label": "ILMU", "distribution_type": "open_weight",
        "license": "unverified", "architecture_class": None,
        "modalities": ["text"], "languages": ["bm", "en", "sea_languages"],
        "lineage": ["ilmu-nemo-nano", "ilmu-nemo-super"],
        "official_sources": [],
        "status": "sources_unverified",
    },
}


def build_families() -> None:
    for family_key, data in FAMILIES.items():
        obj = {
            "object_type": "model_family",
            "object_key": family_key,
            "created_at": BUILD_DATE,
            "updated_at": BUILD_DATE,
            "provenance": PROVENANCE,
            "family_key": family_key,
            "status": data.pop("status", "active"),
            **data,
        }
        w(f"model_families/{family_key}.json", obj)


# ---------------------------------------------------------------------------
# 3. MODEL RELEASES — sealed 2026-10-30
# ---------------------------------------------------------------------------

def build_releases() -> None:
    w("model_releases/qwen-plus-2025-01-25.json", {
        "object_type": "model_release", "object_key": "qwen-plus-2025-01-25",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "release_key": "qwen-plus-2025-01-25", "family_key": "alibaba_qwen", "provider": "alibaba",
        "model_id": "qwen-plus-2025-01-25", "snapshot_date": "2025-01-25", "release_date": None,
        "knowledge_cutoff": {"value": None, "status": "unknown", "must_not_infer_from_snapshot_date": True},
        "parameter_structure": None,
        "weight_availability": "closed_or_undisclosed",
        "license": None,
        "official_model_card": "https://help.aliyun.com/zh/model-studio/models",
        "artifact_hashes": {"weights_sha256": None, "tokenizer_hash": None, "configuration_hash": None},
        "supersedes": None, "derived_from": [],
        "version_stability": "provider_pinned_alias",
        "pin_requirements": [],
        "routing_class": "frozen_reference_candidate",
        "canonicality": "verified_runtime_fact",
        "availability": {
            "state": "alive", "evidence_class": "operator_probe", "http_status": 200,
            "observed_at": None,
            "observed_at_status": "REQUIRED_FROM_HERMES_RAW_RECEIPT",
            "snapshot_age_at_observation_months": 21,
        },
        "limitations": [
            "Snapshot date does not prove knowledge cutoff",
            "Provider-side pinning does not prove immutable weights",
            "Re-probe required to detect withdrawal or remapping",
        ],
    })
    w("model_releases/gpt-oss-120b.json", {
        "object_type": "model_release", "object_key": "gpt-oss-120b",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "release_key": "gpt-oss-120b", "family_key": "openai_gpt_oss", "provider": "openai",
        "model_id": "gpt-oss-120b", "release_date": "2025-08", "snapshot_date": None,
        "knowledge_cutoff": {"value": None, "status": "unknown", "must_not_infer_from_snapshot_date": True},
        "parameter_structure": "MoE 117B total / 5.1B active",
        "weight_availability": "open_weight",
        "license": "Apache-2.0",
        "official_model_card": "https://huggingface.co/openai/gpt-oss-120b",
        "artifact_hashes": {"weights_sha256": None, "tokenizer_hash": None, "configuration_hash": None,
                            "chat_template_hash": None, "quantization": None,
                            "inference_engine": None, "engine_version": None},
        "supersedes": None, "derived_from": [],
        "version_stability": "pin_capable",
        "pin_requirements": ["weights_sha256", "tokenizer_hash", "configuration_hash",
                             "chat_template_hash", "quantization", "inference_engine", "engine_version"],
        "routing_class": "frozen_reference_candidate",
        "canonicality": "candidate_until_artifact_stack_pinned",
        "availability": {
            "lane": "groq", "state": "operator_reported_alive",
            "independent_probe_receipt": "REQUIRED",
        },
        "limitations": [
            "Open weights give the POSSIBILITY of freezing, not proof that the Groq lane serves the same revision permanently",
            "Frozen-runtime-baseline use blocked until artifact/serving revision pinned",
        ],
    })
    w("model_releases/deepseek-v4-pro.json", {
        "object_type": "model_release", "object_key": "deepseek-v4-pro",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "release_key": "deepseek-v4-pro", "family_key": "deepseek", "provider": "deepseek",
        "model_id": "deepseek-v4-pro", "release_date": "2026-Q2", "snapshot_date": None,
        "knowledge_cutoff": {"value": None, "status": "unknown", "must_not_infer_from_snapshot_date": True},
        "parameter_structure": "MoE + hybrid attention (CSA/HCA), 1M ctx / 384K out",
        "weight_availability": "open_weight",
        "license": "MIT",
        "official_model_card": "https://huggingface.co/deepseek-ai",
        "artifact_hashes": {"weights_sha256": None, "tokenizer_hash": None, "configuration_hash": None},
        "supersedes": "deepseek-chat (V3.x line)", "derived_from": [],
        "version_stability": "floating",
        "pin_requirements": ["weights_sha256", "tokenizer_hash", "configuration_hash"],
        "routing_class": "current_capability",
        "canonicality": "api_resolved_identity_witnessed_2026-10-30",
        "spec_ref": "models/deepseek/deepseek/deepseek-v4-pro.json",
        "limitations": [
            "Default target of fed deepseek-v3.2 alias remap (see alias-drift regression case)",
            "Self-claim on direct identity probe was NOT 'deepseek' — see probe receipt fed-4000-deepseek-v3-2-direct",
        ],
    })


# ---------------------------------------------------------------------------
# 4. PROVIDER OFFERINGS
# ---------------------------------------------------------------------------

def build_offerings() -> None:
    w("provider_offerings/dashscope_qwen_dated_snapshot.json", {
        "object_type": "provider_offering", "object_key": "dashscope_qwen_dated_snapshot",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "offering_key": "dashscope_qwen_dated_snapshot", "provider": "dashscope",
        "model_release_key": "qwen-plus-2025-01-25",
        "alias_policy": "dated_snapshot",
        "region": None, "api_compat": "openai-compatible",
        "pricing_class": None, "quota_state": "unknown", "deprecation_state": "not_declared",
        "offering_url": "https://help.aliyun.com/zh/model-studio/models",
        "availability": {"state": "alive", "evidence_class": "operator_probe",
                         "observed_at": None, "observed_at_status": "REQUIRED_FROM_HERMES_RAW_RECEIPT"},
        "notes": ["Dated snapshots are the federation's oldest verified-alive frozen-reference lane"],
    })
    w("provider_offerings/groq_gpt_oss.json", {
        "object_type": "provider_offering", "object_key": "groq_gpt_oss",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "offering_key": "groq_gpt_oss", "provider": "groq",
        "model_release_key": "gpt-oss-120b",
        "alias_policy": "unknown",
        "region": None, "api_compat": "openai-compatible",
        "pricing_class": None, "quota_state": "unknown", "deprecation_state": "not_declared",
        "offering_url": "https://console.groq.com/docs/models",
        "availability": {"state": "operator_reported_alive", "evidence_class": "hermes_report",
                         "observed_at": None, "observed_at_status": "REQUIRED_FROM_HERMES_RAW_RECEIPT"},
        "notes": ["Serving revision not pinned — pin_requirements on the release object gate frozen use"],
    })
    w("provider_offerings/zai_glm_floating.json", {
        "object_type": "provider_offering", "object_key": "zai_glm_floating",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "offering_key": "zai_glm_floating", "provider": "zai",
        "model_release_key": "glm-5.3 (current)",
        "alias_policy": "latest_floating",
        "region": None, "api_compat": "openai-compatible",
        "pricing_class": "subscription-plan", "quota_state": "active", "deprecation_state": "not_declared",
        "offering_url": "https://docs.z.ai/",
        "availability": {"state": "alive", "evidence_class": "hermes_report",
                         "observed_at": None, "observed_at_status": "REQUIRED_FROM_HERMES_RAW_RECEIPT"},
        "notes": [
            "frozen_baseline_eligible: false",
            "self_host_pin_possible: true, if exact open-weight artifact is acquired",
        ],
    })
    w("provider_offerings/opencode_go_glm.json", {
        "object_type": "provider_offering", "object_key": "opencode_go_glm",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "offering_key": "opencode_go_glm", "provider": "opencode-go",
        "model_release_key": "glm-5.2",
        "alias_policy": "unknown",
        "region": None, "api_compat": "gateway-mediated",
        "pricing_class": None, "quota_state": "unavailable", "deprecation_state": "not_declared",
        "offering_url": None,
        "availability": {"state": "catalog_listed_execution_unavailable",
                         "evidence_class": "hermes_report",
                         "observed_at": None, "observed_at_status": "REQUIRED_FROM_HERMES_RAW_RECEIPT"},
        "failure_class": "billing_or_upstream_funds",
        "notes": ["NEVER record as 'dead' — model may exist; the LANE is not executable for funding reasons"],
    })
    w("provider_offerings/deepseek_direct.json", {
        "object_type": "provider_offering", "object_key": "deepseek_direct",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "offering_key": "deepseek_direct", "provider": "deepseek-direct",
        "model_release_key": "deepseek-v4-pro",
        "alias_policy": "latest_floating",
        "region": None, "api_compat": "openai-compatible",
        "pricing_class": "pay-as-you-go", "quota_state": "unavailable_insufficient_balance",
        "deprecation_state": "not_declared",
        "offering_url": "https://api-docs.deepseek.com/",
        "availability": {"state": "catalog_reachable_inference_blocked",
                         "evidence_class": "hermes_report",
                         "observed_at": None, "observed_at_status": "REQUIRED_FROM_HERMES_RAW_RECEIPT"},
        "notes": ["/models returning 200 must NEVER be promoted to model_alive=true"],
    })
    w("provider_offerings/fed_gateway.json", {
        "object_type": "provider_offering", "object_key": "fed_gateway",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "offering_key": "fed_gateway", "provider": "fed",
        "model_release_key": "multiple (per-request alias)",
        "alias_policy": "latest_floating",
        "region": "localhost:4000", "api_compat": "openai-compatible",
        "pricing_class": "internal", "quota_state": "active", "deprecation_state": "not_declared",
        "offering_url": None,
        "availability": {"state": "alive", "evidence_class": "direct_probe",
                         "observed_at": "2026-10-29T23:21:23Z"},
        "notes": ["Witnessed silent alias remap deepseek-v3.2 -> deepseek-v4-pro (regression case)"],
    })


# ---------------------------------------------------------------------------
# 5. RUNTIME ROUTES
# ---------------------------------------------------------------------------

def build_routes() -> None:
    w("runtime_routes/fed_4000.json", {
        "object_type": "runtime_route", "object_key": "fed_4000",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "route_key": "fed_4000", "transport": "http_openai_compat",
        "endpoint": "http://localhost:4000/v1", "auth_class": "operator_local_no_key",
        "resolves_to": {"offering_key": "fed_gateway", "release_key": None,
                        "resolution_state": "alias_drift",
                        "observed_resolved_model": "deepseek-v4-pro",
                        "last_verified_at": "2026-10-29T23:21:23Z"},
        "catalog_only_models": ["deepseek-v3.2 listed in /v1/models but resolves to deepseek-v4-pro"],
        "allowed_uses": ["current_capability_work", "non_longitudinal_tasks"],
        "forbidden_uses": ["frozen_baseline", "longitudinal_comparison",
                           "release_regression", "model_identity_attestation"],
        "status": "hold",
    })
    w("runtime_routes/dashscope_direct.json", {
        "object_type": "runtime_route", "object_key": "dashscope_direct",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "route_key": "dashscope_direct", "transport": "http_openai_compat",
        "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "auth_class": "api_key_required",
        "resolves_to": {"offering_key": "dashscope_qwen_dated_snapshot",
                        "release_key": "qwen-plus-2025-01-25",
                        "resolution_state": "matched",
                        "observed_resolved_model": "qwen-plus-2025-01-25",
                        "last_verified_at": None,
                        "last_verified_at_status": "REQUIRED_FROM_HERMES_RAW_RECEIPT"},
        "catalog_only_models": [],
        "allowed_uses": ["frozen_reference", "longitudinal_comparison_baseline_candidate",
                         "reproducibility_replay"],
        "forbidden_uses": ["current_affairs_without_retrieval"],
        "status": "active",
    })
    w("runtime_routes/zai_direct.json", {
        "object_type": "runtime_route", "object_key": "zai_direct",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "route_key": "zai_direct", "transport": "http_openai_compat",
        "endpoint": "https://api.z.ai/api/paas/v4", "auth_class": "api_key_required",
        "resolves_to": {"offering_key": "zai_glm_floating", "release_key": None,
                        "resolution_state": "unresolved",
                        "observed_resolved_model": None, "last_verified_at": None},
        "catalog_only_models": [],
        "allowed_uses": ["current_capability_work"],
        "forbidden_uses": ["frozen_baseline", "longitudinal_comparison"],
        "status": "active",
    })
    w("runtime_routes/deepseek_direct.json", {
        "object_type": "runtime_route", "object_key": "deepseek_direct",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "route_key": "deepseek_direct", "transport": "http_openai_compat",
        "endpoint": "https://api.deepseek.com/v1", "auth_class": "api_key_required",
        "resolves_to": {"offering_key": "deepseek_direct", "release_key": None,
                        "resolution_state": "unresolved",
                        "observed_resolved_model": None, "last_verified_at": None},
        "catalog_only_models": [],
        "allowed_uses": [],
        "forbidden_uses": ["all until balance restored"],
        "status": "blocked",
    })
    w("runtime_routes/groq_lane.json", {
        "object_type": "runtime_route", "object_key": "groq_lane",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "route_key": "groq_lane", "transport": "http_openai_compat",
        "endpoint": "https://api.groq.com/openai/v1", "auth_class": "api_key_required",
        "resolves_to": {"offering_key": "groq_gpt_oss", "release_key": "gpt-oss-120b",
                        "resolution_state": "unresolved",
                        "observed_resolved_model": None, "last_verified_at": None},
        "catalog_only_models": [],
        "allowed_uses": ["frozen_reference_candidate_work"],
        "forbidden_uses": ["frozen_baseline until artifact stack pinned",
                           "model_identity_attestation until independent probe"],
        "status": "hold",
    })
    w("runtime_routes/opencode_go.json", {
        "object_type": "runtime_route", "object_key": "opencode_go",
        "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
        "route_key": "opencode_go", "transport": "gateway_mediated",
        "endpoint": None, "auth_class": "subscription_credential",
        "resolves_to": {"offering_key": "opencode_go_glm", "release_key": "glm-5.2",
                        "resolution_state": "unresolved",
                        "observed_resolved_model": None, "last_verified_at": None},
        "catalog_only_models": ["glm-5.2 (catalog_state listed, execution unavailable)"],
        "allowed_uses": [],
        "forbidden_uses": ["all until funding resolved"],
        "status": "blocked",
    })


# ---------------------------------------------------------------------------
# 6. PROBE RECEIPTS — fresh FI-008 direct probe + HERMES operator reports
# ---------------------------------------------------------------------------

LIVE_PROBE = {
    "object_type": "probe_receipt",
    "object_key": "fed-4000-deepseek-v3-2-direct",
    "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
    "receipt_id": "fed-4000-deepseek-v3-2-direct-20261030",
    "route_key": "fed_4000",
    "requested_model": "deepseek-v3.2",
    "api_resolved_model": "deepseek-v4-pro",
    "resolution_state": "alias_drift",
    "self_claimed_identity": "Claude 3.5 Sonnet",
    "self_claim_is_identity_evidence": False,
    "http_status": 200,
    "latency_ms": 7269,
    "fingerprint": None,
    "finish_reason": "stop",
    "token_counts": {"prompt_tokens": 16, "completion_tokens": 179, "reasoning_tokens": 170},
    "credential_class": "operator_local_no_key",
    "observed_at": "2026-10-29T23:21:23Z",
    "raw_receipt_location": None,
    "raw_receipt_status": "captured-in-operator-session SEAL-d59c04d66b294e0b; re-probe reproducible",
    "witness_class": "direct_probe",
    "notes": [
        "Three identity layers: requested=deepseek-v3.2, api_resolved=deepseek-v4-pro, self_claimed='Claude 3.5 Sonnet'",
        "Self-claim is NOT identity evidence (F9 anti-hantu); recorded for the self-claim-boundary dataset",
        "Second confirmation same session: max_tokens=10 probe, finish=length, api_resolved=deepseek-v4-pro",
    ],
}

HERMES_RECEIPTS = [
    {
        "object_key": "hermes-fed-alias-drift",
        "route_key": "fed_4000",
        "receipt_id": "hermes-fed-deepseek-v3-2-20261030",
        "requested_model": "deepseek-v3.2", "api_resolved_model": "deepseek-v4-pro",
        "resolution_state": "alias_drift", "self_claimed_identity": None,
        "http_status": 200, "latency_ms": None, "finish_reason": None, "token_counts": {},
        "witness_class": "operator_reported",
        "notes": ["Original alias-drift witness that triggered the 2026-10-30 registry seal"],
    },
    {
        "object_key": "hermes-qwen-plus-snapshot",
        "route_key": "dashscope_direct",
        "receipt_id": "hermes-qwen-plus-2025-01-25-20261030",
        "requested_model": "qwen-plus-2025-01-25", "api_resolved_model": "qwen-plus-2025-01-25",
        "resolution_state": "matched", "self_claimed_identity": None,
        "http_status": 200, "latency_ms": None, "finish_reason": None, "token_counts": {},
        "witness_class": "operator_reported",
        "notes": ["Oldest verified-alive provider-pinned snapshot; ~21 months old at observation"],
    },
    {
        "object_key": "hermes-opencode-glm52",
        "route_key": "opencode_go",
        "receipt_id": "hermes-opencode-glm-5-2-20261030",
        "requested_model": "glm-5.2", "api_resolved_model": None,
        "resolution_state": "unresolved", "self_claimed_identity": None,
        "http_status": None, "latency_ms": None, "finish_reason": None, "token_counts": {},
        "witness_class": "operator_reported",
        "notes": ["catalog_state=listed, execution_state=unavailable, failure_class=billing_or_upstream_funds"],
    },
    {
        "object_key": "hermes-deepseek-direct",
        "route_key": "deepseek_direct",
        "receipt_id": "hermes-deepseek-direct-20261030",
        "requested_model": "(deepseek-direct /models)", "api_resolved_model": None,
        "resolution_state": "unresolved", "self_claimed_identity": None,
        "http_status": 200, "latency_ms": None, "finish_reason": "no_inference_attempted",
        "token_counts": {},
        "witness_class": "operator_reported",
        "notes": ["/models=200 + balance insufficient; endpoint reachable != model_alive"],
    },
]


def build_receipts() -> None:
    LIVE_PROBE["probe_hash"] = content_hash(LIVE_PROBE)
    live = dict(LIVE_PROBE)
    w(f"probe_receipts/{BUILD_DATE}/{live['object_key']}.json", live)
    for r in HERMES_RECEIPTS:
        obj = {
            "object_type": "probe_receipt",
            "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
            "observed_at": None,
            "observed_at_status": "REQUIRED_FROM_HERMES_RAW_RECEIPT",
            "raw_receipt_location": None,
            "raw_receipt_status": "REQUIRED",
            "credential_class": "operator_credential",
            "fingerprint": None,
            **r,
        }
        obj["probe_hash"] = content_hash(obj)
        w(f"probe_receipts/{BUILD_DATE}/{r['object_key']}.json", obj)


# ---------------------------------------------------------------------------
# 7. ROUTING DECISIONS — proposals only, no self-SEAL
# ---------------------------------------------------------------------------

def build_decisions() -> None:
    decisions = [
        {"route_key": "fed_4000", "model": "deepseek-v3.2", "decision": "HOLD",
         "rationale": "Witnessed silent alias remap to deepseek-v4-pro — canonical regression case",
         "allowed_uses": ["current_capability_work", "non_longitudinal_tasks"],
         "forbidden_uses": ["frozen_baseline", "longitudinal_comparison",
                            "release_regression", "model_identity_attestation"],
         "basis": ["probe_receipts/2026-10-30/fed-4000-deepseek-v3-2-direct.json",
                   "probe_receipts/2026-10-30/hermes-fed-alias-drift.json"]},
        {"route_key": "fed_4000", "model": "deepseek-v4-pro", "decision": "CURRENT_CAPABILITY",
         "rationale": "API-resolved identity witnessed on explicit request",
         "allowed_uses": ["current_capability_work", "coding", "long_context"],
         "forbidden_uses": ["frozen_baseline", "identity_witness"],
         "basis": ["probe_receipts/2026-10-30/fed-4000-deepseek-v3-2-direct.json"]},
        {"route_key": "dashscope_direct", "model": "qwen-plus-2025-01-25",
         "decision": "FROZEN_REFERENCE",
         "rationale": "Oldest verified-alive provider-pinned snapshot (~21 months at observation)",
         "allowed_uses": ["frozen_reference", "longitudinal_comparison_baseline_candidate"],
         "forbidden_uses": ["current_affairs_without_retrieval", "knowledge_cutoff_claims"],
         "basis": ["probe_receipts/2026-10-30/hermes-qwen-plus-snapshot.json"]},
        {"route_key": "groq_lane", "model": "gpt-oss-120b", "decision": "HOLD",
         "rationale": "Open-weight pin-capable candidate; artifact stack not pinned; no independent probe",
         "allowed_uses": [],
         "forbidden_uses": ["frozen_runtime_baseline until pinned", "identity_attestation"],
         "basis": ["model_releases/gpt-oss-120b.json"]},
        {"route_key": "zai_direct", "model": "glm-5.3 (floating)", "decision": "CURRENT_CAPABILITY",
         "rationale": "Alive, floating alias; never a baseline",
         "allowed_uses": ["current_capability_work"],
         "forbidden_uses": ["frozen_baseline", "longitudinal_comparison"],
         "basis": ["provider_offerings/zai_glm_floating.json"]},
        {"route_key": "opencode_go", "model": "glm-5.2", "decision": "BLOCKED",
         "rationale": "Lane not executable — billing_or_upstream_funds; catalog listing is not capability",
         "allowed_uses": [],
         "forbidden_uses": ["all"],
         "basis": ["probe_receipts/2026-10-30/hermes-opencode-glm52.json"]},
        {"route_key": "deepseek_direct", "model": "deepseek-v4-pro", "decision": "BLOCKED",
         "rationale": "/models reachable (200) but inference blocked by balance; catalog reachability != model_alive",
         "allowed_uses": [],
         "forbidden_uses": ["all until balance restored"],
         "basis": ["probe_receipts/2026-10-30/hermes-deepseek-direct.json"]},
    ]
    out = []
    for d in decisions:
        out.append({
            "object_type": "routing_decision",
            "object_key": f"{d['route_key']}::{d['model']}",
            "created_at": BUILD_DATE, "updated_at": BUILD_DATE, "provenance": PROVENANCE,
            "route_key": d["route_key"],
            "decision": d["decision"],
            "rationale": d["rationale"],
            "basis_receipts": d["basis"],
            "allowed_uses": d["allowed_uses"],
            "forbidden_uses": d["forbidden_uses"],
            "proposed_by": "kimi-code/FI-008",
            "authority_basis": "user_directive_2026-10-30 + hermes_probe + fi008_direct_probe",
            "decided_at": BUILD_DATE,
            "ratified": False,
            "ratification": "awaiting_888",
        })
    w("routing_decisions/routing_decisions.json", out)


# ---------------------------------------------------------------------------
# 8. GOVERNANCE CARD FIXTURE — fail-closed example (forge-777 regression shape)
# ---------------------------------------------------------------------------

def build_governance_card() -> None:
    card = {
        "object_type": "model_governance_card",
        "object_key": "mgc-forge-777-example",
        "schema_version": 1,
        "card_id": "mgc-forge-777-example",
        "card_kind": "example_fixture_not_live",
        "session_id": None,
        "lane_id": "forge-777",
        "registry_revision": git_revision(),
        "source_manifest_hash": None,
        "compiled_at": BUILD_DATE + "T00:00:00Z",
        "requested_model": "deepseek-v3.2",
        "resolved_model": "UNKNOWN",
        "identity_state": "UNRESOLVED",
        "resolution_evidence_ref": None,
        "route_id": "fed_4000",
        "mutability": "PROVIDER_ALIAS_FLOATING",
        "failure_domain": "UNKNOWN",
        "freshness_state": "STALE",
        "eligible_roles": ["current_capability_worker"],
        "forbidden_roles": ["identity_witness", "longitudinal_baseline",
                            "independent_verifier", "self_authorizing_judge"],
        "tool_policy_ref": "runtime_wiring/WIRING_STATUS.yaml#tool_policy",
        "memory_policy_ref": "runtime_wiring/WIRING_STATUS.yaml#memory_provenance",
        "authority_ceiling": {"propose": True, "verify": False, "authorize": False, "execute": False},
        "verdict": "HOLD",
    }
    card["card_hash"] = content_hash(card)
    w("governance_cards/mgc-forge-777-example.json", card)


# ---------------------------------------------------------------------------
# 9. EVIDENCE BINDINGS — HF AAA..FFF ladder, revisions pinned 2026-10-30
# ---------------------------------------------------------------------------

HF_REVISIONS = {
    "AAA": "e17f60f9625c991097dbcc186a54becaba840da7",
    "BBB": "ae2910098937ecfa5ce5b799b2b3349f92823f7e",
    "CCC": "ced4d67d1de04bf155c80cca9ebce87bfffb3ad7",
    "DDD": "b8f21e7ebc40f95c9ec409cb0bea632ff4e82f92",
    "EEE": "702d33d17322a02c3a7f9c39f8daed8e939187d2",
    "FFF": "2bf987aa42c82f002ad335175473c25793ad5dc0",
}
HF_ROLES = {
    "AAA": "constitutional_evaluation_basis",
    "BBB": "direct_model_behavior_receipts",
    "CCC": "kernel_mediation_evidence",
    "DDD": "register_stability_evidence",
    "EEE": "runtime_spine_health",
    "FFF": "fitness_gate_verdict",
}


def build_evidence() -> None:
    w("evidence_bindings.json", {
        "schema_version": 1,
        "note": "Hugging Face is the public evidence/distribution plane; this git repo stays the canonical registry source. Revisions pinned to commit SHAs so evidence cannot change silently.",
        "retrieved_at": BUILD_DATE,
        "retrieved_by": PROVENANCE,
        "bindings": [
            {"dataset": f"hf://datasets/ariffazil/{name}", "role": HF_ROLES[name],
             "revision": HF_REVISIONS[name], "records": []}
            for name in ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
        ],
    })


# ---------------------------------------------------------------------------
# 10. RUNTIME WIRING STATUS — JUDGE-corrected brief, auditable as data
# ---------------------------------------------------------------------------

WIRING_STATUS = """\
# AAA_MODEL_GOVERNANCE_RUNTIME_WIRING::2026-10-30::v1 — status of record
# Corrections from F13-pending JUDGE verdict incorporated verbatim.

mcp_projection_mission_scoped:
  scope_note: >
    Mission-specific projection ONLY. Not a claim that MCP contains only these
    three protocol capabilities (spec also defines roots, sampling, elicitation,
    authorization, discovery, caching, logging, pagination).
  resource: arifos://model-governance-card/{lane}
  prompt: /init references the resource and instructs the agent to bind it
  tool:
    name: arif_init
    role: resolver_and_binder
    never: owner_or_creator_of_card

a2a_reality_reference:
  requested_source: a2aproject/A2AReality
  source_state: UNKNOWN_SOURCE_UNRESOLVED
  substituted_with_a2a: false
  falsifier:
    - canonical repository becomes reachable
    - ARIF supplies authoritative pointer

producer_context_chain:
  origin: model_invocation_envelope   # JUDGE correction: born at model output, not at A-FORGE
  chain:
    - init_creates_model_governance_card
    - model_invocation_binds_card_hash
    - model_output_receives_producer_context
    - tool_invocation_inherits_producer_context
    - aforge_receipt_binds_execution_to_producer_context
    - memory_writer_persists_producer_context
  first_consumer_scope:
    proved: execution_receipt_binding_only
    not_yet_proved:
      - provenance_for_non_executed_outputs
      - memory_writes
      - inter_agent_messages

card_contract:
  target_size_bytes: 1200
  hard_max_bytes: 2048
  target_lines: 40
  overflow_policy: fail_closed_compaction
  biography_forbidden: true
  embedded_probe_history_forbidden: true
  forbidden_payload:
    - probe history
    - company profile / family tree
    - current pricing
    - full hazard catalogue
    - raw API endpoints
    - credential environment names
    - fallback candidate lists
    - natural-language biography

init_fail_closed:
  lifecycle_state: INITIALIZED
  identity_state: UNKNOWN
  operating_mode: OBSERVE_ONLY
  consequential_tools: DENIED
  memory_promotion: DENIED
  model_self_claim: REQUESTED_ALIAS_ONLY
  note: >
    INIT may succeed structurally with UNKNOWN, but the capability lease
    shrinks — availability collapse and authority inflation are both blocked.

toctou_lock:
  invariant: registry_revision_used_to_compile_card == registry_revision_in_init_receipt
  card_immutability: within_session
  silent_hot_reload: forbidden
  refresh_protocol:
    - old_card_hash
    - new_card_hash
    - changed_fields
    - reason
    - policy_verdict
    - transition_receipt

boundaries:
  model_supports_tool_calling: not_the_same_as
  note: >
    Model supports tool calling != model owns the tool != model is authorized
    to invoke it != tool execution succeeded != world outcome succeeded.
    Registry describes compatibility. Capability lease grants access.
    888 authorizes. A-FORGE executes. Receipt witnesses the outcome.

registry_is_not:
  - leaderboard
  - secret_store          # stores credential_env_ref, never key values
  - authorization_engine  # eligibility only; execution authorization is 888
  - long_term_memory      # model/route/probe/incident/policy facts, not conversations
"""


def build_wiring() -> None:
    w("runtime_wiring/WIRING_STATUS.yaml", WIRING_STATUS)


# ---------------------------------------------------------------------------
# 11. CATALOG v3 section + main
# ---------------------------------------------------------------------------

def update_catalog() -> None:
    cat_path = ROOT / "catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))
    counts = {}
    for d in ["model_families", "model_releases", "provider_offerings",
              "runtime_routes", "probe_receipts", "routing_decisions", "governance_cards"]:
        counts[d] = len(list((ROOT / d).rglob("*.json")))
    # Reconcile archetype namespaces (v2 drift, 2026-10-30): catalog held
    # provider-named archetypes (provider_souls/ files) while model files
    # reference semantic archetypes registered nowhere. Two namespaces, two checks:
    #   soul_archetypes      -> must have provider_souls/<key>.json
    #   semantic_archetypes  -> must be referenced by >= 1 model file
    # Reset provider-named archetypes from the true source (idempotent rebuilds)
    cat["soul_archetypes"] = sorted(p.stem for p in ROOT.joinpath("provider_souls").glob("*.json"))
    semantic = set()
    for mp in ROOT.joinpath("models").rglob("*.json"):
        a = json.loads(mp.read_text(encoding="utf-8")).get("soul_archetype")
        if a:
            semantic.add(a)
    cat["semantic_archetypes"] = sorted(semantic)
    cat["semantic_archetypes_note"] = (
        "Behavioral archetype labels referenced by model.soul_archetype. "
        "Usage-checked (not file-backed). v2 drift reconciled 2026-10-30."
    )
    cat["schema_version"] = "CATALOG_V3"
    cat["registry_version"] = "3.0.0-resolver-witnessed"
    cat["generated_at"] = BUILD_DATE + "T00:00:00Z"
    cat["last_updated_by"] = "kimi-code/FI-008"
    cat["v3"] = {
        "design": "resolver-witnessed registry: alias is not identity, endpoint-alive is not provenance, http-200 is not capability proof",
        "objects": counts,
        "schemas": sorted(SCHEMAS.keys()),
        "evidence_bindings": "evidence_bindings.json",
        "alias_drift_regression": "runtime_routes/fed_4000.json + probe_receipts/2026-10-30/fed-4000-deepseek-v3-2-direct.json",
        "runtime_wiring": "runtime_wiring/WIRING_STATUS.yaml",
        "build_script": "scripts/build_v3_objects.py",
    }
    cat_path.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    written.append("catalog.json")


def main() -> int:
    build_schemas()
    build_families()
    build_releases()
    build_offerings()
    build_routes()
    build_receipts()
    build_decisions()
    build_governance_card()
    build_evidence()
    build_wiring()
    update_catalog()
    live_hash = LIVE_PROBE["probe_hash"]
    print(f"v3 build complete — {len(written)} files")
    print(f"alias-drift probe_hash: {live_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
