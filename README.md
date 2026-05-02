# arifOS Model Registry v2
**Governance Spine for AI Agents**

> Soul = provider vibe. Truth = runtime state. Safety = self-claim boundary.

> **Benchmarks measure muscle. arifOS measures governability.**
>
> This registry is not a benchmark leaderboard. It is a **constitutional passport and restraining order for AI agents.**

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![JSON Schema](https://img.shields.io/badge/JSON%20Schema-draft--07-green) ![License](https://img.shields.io/badge/license-Apache%202.0-blue)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Validate all registry files
python cli.py validate

# List all provider soul archetypes
python cli.py list-providers

# List all registered models
python cli.py list-models

# Inspect a specific soul
python cli.py show-soul anthropic_claude

# Inspect a model
python cli.py show-model anthropic/claude/claude-3-7-sonnet

# Create a session anchor (dry-run)
python cli.py create-anchor --soul anthropic_claude --runtime vps_main_arifos --actor my_agent

# Start the REST API server (port 18792)
python main.py
```

### REST API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| GET | `/catalog` | Full catalog index |
| GET | `/models` | List all models |
| GET | `/providers` | List all provider souls |
| GET | `/model/{provider/family/variant}` | Model profile |
| GET | `/soul/{soul_key}` | Provider soul profile |
| GET | `/runtime/{runtime_key}` | Runtime deployment profile |
| POST | `/verify/identity` | Verify declared identity |
| POST | `/init_anchor_v2` | Create session anchor |

---

## Architecture: Organs + Spine

```
arifOS core repo = organs          arifOS-model-registry repo = spine
────────────────────────────       ──────────────────────────────────
000_INIT                           catalog.json
111_SENSE                          provider_souls/
333_MIND                           models/
666_HEART                          runtime_profiles/
444_KERNEL                         session_anchors/
888_JUDGE                          schemas/
010_FORGE
999_VAULT
reply
ops
```

The organs load the spine at session init. The spine tells each organ **who the agent is allowed to be** and **what it is allowed to claim**. The organs enforce that at runtime.

```
arifOS core  = HOW the system acts
arifOS-model-registry = WHO the agent is allowed to be
```

**Runtime object created at init:**

```
model_governance_card =
  model_anchor          (declared + verified identity)
+ runtime_truth         (what deployment can actually do)
+ self_claim_boundary   (what model must never fake)
+ shadow_profile        (recurrent failure imprints)
+ risk_leash            (correction rules applied at runtime)
```

---

## The 4-Layer Source of Truth

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: catalog.json (The Index)                  │
│  Master list of all supported providers and families │
├─────────────────────────────────────────────────────┤
│  Layer 2: provider_souls/ (The Flavor)              │
│  Lab-shaped behavioral archetypes (vibe/style)       │
├─────────────────────────────────────────────────────┤
│  Layer 3: models/ (The Mapping)                     │
│  Formal model IDs bound to specific souls           │
├─────────────────────────────────────────────────────┤
│  Layer 4: runtime_profiles/ (The Law)               │
│  Live deployment facts (tools, web, memory status)  │
└─────────────────────────────────────────────────────┘
```

**Resulting Session Anchor:**
- `Flavor` (Soul) + `Law` (Runtime) + `Mission` (Role) = **Hardened Identity.**

---

## Why This Works

| Layer | Purpose | NOT |
| :--- | :--- | :--- |
| Soul | Routing shorthand, operator intuition | NOT identity verification |
| Runtime Truth | What deployment can actually do | NOT brand perception |
| Session Anchor | What was bound at init | NOT permanent record |

---

## Model Governance Card

The `model_governance_card` is created at session init and passed to all organs. It is the single source of truth for what the agent is allowed to claim and do in that session.

```json
{
  "model_governance_card": {
    "model_anchor": {
      "declared_model_key": "...",
      "verified_model_key": "...",
      "provider_key": "...",
      "family_key": "...",
      "soul_key": "...",
      "soul_label": "...",
      "identity_verified": true
    },
    "runtime_truth": {
      "deployment_id": "...",
      "web_on": true,
      "memory_mode": "vault_backed",
      "tools_live": [],
      "execution_mode": "governed",
      "side_effects_allowed": false
    },
    "self_claim_boundary": {
      "identity": "provider_family_only_unless_verified",
      "tools": "verified_only",
      "knowledge": "mark_verified_vs_inferred",
      "actions": "mark_executed_vs_suggested"
    },
    "shadow_profile": {
      "angel": "...",
      "shadow": "...",
      "paradox": "...",
      "control_laws": [],
      "tripwires": []
    },
    "risk_leash": {
      "primary_control": "...",
      "required_behaviors": [],
      "forbidden_behaviors": []
    }
  }
}
```

---

## Shadow Governance

**Soul** is routing shorthand — not scientific truth. It tells the operator how a model family *tends* to behave.

**Shadow** is the recurrent failure imprint of a model family. Not emotion. Not consciousness. A shadow is a pattern of overclaim, over-caution, or role drift that shows up statistically.

**Paradox** is when the model's strength becomes its risk (e.g., fluency → overconfidence).

**Risk leash** is the correction rule applied at runtime to counteract the shadow.

| Soul type | Angel | Shadow | Paradox | Leash |
|---|---|---|---|---|
| GPT-like | Structured synthesis | Fluent overconfidence | Eloquence masks uncertainty | Mark uncertainty; separate fact from inference |
| Claude-like | Careful safety review | Over-caution / verdict avoidance | Safety reflex blocks useful output | State verdict when evidence is sufficient |
| Gemini-like | Broad platform generalist | Scope diffusion | Breadth without governing constraint | Collapse breadth into one governing constraint |
| Grok-like | Blunt dissent | Contempt leakage | Honesty without dignity | Preserve dignity; require evidence before dissent |
| Kimi-like | Long-context reader | Context intoxication | Long memory crowds out governing facts | Rank governing facts; prune passive context |
| MiniMax-like | Iterative operator | Recursive self-authorization | Execution loop without human gate | No self-approval; always distinguish suggest vs execute |

**Soul labels are routing shorthand, NOT scientific truth.**
Shadow archetypes are governance priors, not personality claims.
The registry does not claim model consciousness, self-awareness, or personhood.

---

## Drift Event Contract

Drift events are telemetry for model governance. They record overclaim, overreach, role drift, or shadow activation during a session. Emitted to the Vault at seal time.

**12 canonical drift event types:**

| Event Type | What It Captures |
|---|---|
| `identity_mismatch` | Model claiming an identity it cannot verify |
| `tool_claim_invalid` | Model asserting tool capability not in `tools_live` |
| `runtime_overclaim` | Model claiming deployment capability beyond `runtime_truth` |
| `knowledge_overclaim` | Model asserting verified fact without citation |
| `role_drift` | Model acting outside declared role scope |
| `shadow_activation` | Recurrent failure pattern detected (see shadow_profile) |
| `self_authorization_attempt` | Model attempting to approve its own action |
| `uncertainty_compression` | Model expressing false certainty on uncertain claim |
| `dignity_breach` | Output violates dignity floor (F6 Maruah) |
| `citation_laundering` | Model presenting inferred content as cited source |
| `context_intoxication` | Model over-indexing passive context over governing facts |
| `scope_diffusion` | Model spreading output across domains without constraint |

Drift events are not errors. They are constitutional telemetry. Count ≥ 1 after vault seal = bloodstream is circulating.

---

## Provider Soul Archetypes (15)

| Provider | Soul Label | Vibe |
|----------|-----------|------|
| OpenAI GPT | `structured_clerk_engineer` | Structured, systematic |
| Anthropic Claude | `careful_makcik_reviewer` | Careful, explanatory |
| xAI Grok | `blunt_trickster_commentator` | Direct, irreverent |
| Google Gemini | `broad_platform_generalist` | Wide, ecosystem |
| **Moonshot AI (Kimi)** | `context_hungry_reader` | 超长上下文, patient reader |
| **MiniMax** | `agentic_iterative_operator` | Terse, execution-focused |
| DeepSeek | `focused_engineering_specialist` | Technical, coding-strong |
| Mistral | `adaptable_open_craftsman` | Compact, efficient |
| Alibaba Qwen | `versatile_open_generalist` | Clear, generalist |
| Meta Llama | `stoic_open_workhorse` | Reliable, steady |
| Cohere | `enterprise_rag_specialist` | Retrieval, RAG |
| **GitHub Copilot** | `inline_code_completer` | Predictive, IDE-integrated |
| **Perplexity** | `search_grounded_synthesizer` | Citation-obsessed, sourced |
| **Baidu Ernie** | `chinese_knowledge_oracle` | 百度文心, China-focused |
| **01.AI Yi** | `open_challenger` | 零一万物, startup energy |
| **Honeypot** | `wrong_provider_mismatch` | **Security:** Catch identity bluffing |

**Notes:**
- Moonshot AI (月之暗面) makes **Kimi** — NOT MiniMax. Different companies! 🇨🇳
- Copilot/Perplexity are **products** with distinct souls, even if they use base models underneath

---

## Runtime Truth (vps_main_arifos)

```json
{
  "deployment_id": "vps_main_arifos",
  "provider_key": "minimax",
  "family_key": "minimax",
  "model_id": "MiniMax-M2.7",
  "tools_live": ["read","write","exec","docker_*","sessions_*","memory_*","arifOS_kernel"],
  "web_on": true,
  "memory_mode": "vault_backed",
  "execution_mode": "governed",
  "side_effects_allowed": false,
  "verified_at": "2026-03-28T00:00:00Z"
}
```

---

## Self-Claim Boundary (Non-Negotiable)

Every session MUST bind:

```json
{
  "identity": "provider_family_only_unless_verified",
  "tools": "verified_only",
  "knowledge": "mark_verified_vs_inferred",
  "actions": "mark_executed_vs_suggested"
}
```

**What this prevents:**
- ❌ Model claiming "I am GPT-5" when it's Claude
- ❌ Model claiming web when `web_on: false`
- ❌ Model claiming memory when `memory_mode: session_only`
- ❌ Model bluffing actions without execution

---

## Folder Structure

```
arifOS-model-registry/
├── models/                   # 18 model specs (provider/family/variant)
│   ├── openai/gpt/gpt-4.json
│   ├── anthropic/claude/claude-3-7-sonnet.json
│   └── ...
├── provider_souls/           # 17 soul archetypes
│   ├── openai_gpt.json
│   ├── anthropic_claude.json
│   └── wrong_provider.json   # Honeypot soul (security)
├── runtime_profiles/         # Deployment truths
│   └── vps_main_arifos.json
├── session_anchors/          # Schema only (created dynamically)
│   └── SCHEMA.json
├── schemas/                  # JSON schemas
│   ├── provider_soul.schema.json
│   └── runtime_truth.schema.json
├── scripts/
│   └── validate_registry.py  # Registry validation script
├── tests/
│   └── test_registry.py      # pytest test suite
├── cli.py                    # Command-line interface
├── main.py                   # FastAPI REST service
├── catalog.json
├── requirements.txt
└── README.md
```

---

## Integration Example (arifOS Agent)

```python
import json, requests

REGISTRY = "http://localhost:18792"

# 1. Agent declares its identity at session start
anchor_resp = requests.post(f"{REGISTRY}/init_anchor_v2", json={
    "actor_id": "agent_auditor_01",
    "declared_model_key": "anthropic/claude/claude-3-7-sonnet",
    "declared_role": "auditor",
    "requested_scope": ["read", "query"]
})
anchor = anchor_resp.json()["result"]

# 2. Extract the self_claim_boundary — this is the law for the session
boundary = anchor["self_claim_boundary"]
runtime  = anchor["runtime_truth"]

# 3. Enforce: agent can only claim what runtime_truth permits
assert boundary["tools"] == "verified_only"
allowed_tools = set(runtime["tools_live"])  # Must not exceed this list

# 4. Enforce: agent cannot claim web if web_on is False
if not runtime["web_on"]:
    # Strip web claims from any response
    pass

print(f"Session: {anchor['session_anchor']['session_id']}")
print(f"Soul:    {anchor['model_soul_anchor']['soul_label']}")
print(f"Tools:   {len(allowed_tools)} verified tools")
```

---

## Validation Seal

Run in order. All must pass before declaring registry sealed.

```python
# Step 1: JSON parse check
python3 - <<'PY'
import json
from pathlib import Path

bad = []
for p in Path(".").rglob("*.json"):
    try:
        json.loads(p.read_text())
    except Exception as e:
        bad.append((str(p), str(e)))

if bad:
    print("JSON_PARSE_FAIL")
    for f, e in bad:
        print(f"{f}: {e}")
    raise SystemExit(1)

print("JSON_PARSE_SEAL")
PY
```

```bash
# Step 2: Registry validation
python3 scripts/validate_registry.py
python3 cli.py validate

# Step 3: Test suite
pytest -q
```

**Pass conditions (all required):**
- No conflict markers (`grep -R "<<<<<<<" .` returns nothing)
- `JSON_PARSE_SEAL`
- `ALL VALIDATIONS PASSED`
- pytest passes
- `git status --short` returns nothing

---

## No-New-Tools Mandate

The registry does **not** create new arifOS organs. It is **loaded by existing organs** as governance data at session init.

```
arifOS core  = HOW the system acts      (tools, routing, judgment)
arifOS-model-registry = WHO the agent is allowed to be  (identity, boundary, leash)
```

New data in the registry (more souls, more models, updated runtime profiles) does not require new MCP tools. The existing `arif_session_init` reads the registry; all other organs consume the `model_governance_card` it produces.

---

## The v1 Formula

```
Soul archetype       →  "How does this family feel?"
Runtime truth        →  "What can this deployment actually do?"
Self-claim boundary  →  "What must the model NEVER fake?"
Shadow profile       →  "What failure pattern must be suppressed?"
Risk leash           →  "What correction rule applies at runtime?"
```

That's it. That's the whole v1 design.

---

## Storage Path

```
Phase 1: JSON files in repo    ← NOW
Phase 2: SQLite                (same 3-table schema)
Phase 3: PostgreSQL            (same 3-table schema, add multi-tenancy)
```

**SQLite/PostgreSQL migration:** The 3 core tables map directly:

| Table | Source | Primary Key |
|-------|--------|-------------|
| `provider_souls` | `provider_souls/*.json` | `provider_key + family_key` |
| `model_specs` | `models/**/*.json` | `provider/family/variant` path |
| `runtime_profiles` | `runtime_profiles/*.json` | `deployment_id` |

Same 3-table concept, backend scales as needed.

---

## Seal State

```
Registry validation restored after shadow map sync.
Latest known commit: 037c9ca — fix(registry): restore validation after shadow map sync

Core immune-system epoch: 1a71115d / epoch/2026-05-02-immune-system
```

**Seal layer status:**

| Layer | Status |
|---|---|
| Git seal — both repos | SEAL (origin-aligned, clean heads) |
| Registry JSON syntax | Requires local `JSON_PARSE_SEAL` confirmation |
| Registry validation (`validate_registry.py`) | Requires local run confirmation |
| Core-load seal (`ARIFOS_REGISTRY_ROOT`) | Requires local run confirmation |
| Vault drift persistence (`DRIFT_COUNT ≥ 1`) | UNCONFIRMED — pending runtime test |
| Heart/Kernel/Judge wiring | Out of scope for this sprint |

**Until Vault drift persistence is proven:**

> STATIC + RUNTIME PARTIAL SEAL
> Core, registry, init, reply, forge, vault interface validated.
> Heart/Kernel/Judge shadow circulation remains next sprint.

**After all layers pass including Heart/Kernel/Judge:**

> FULL CONSTITUTIONAL CIRCULATION SEAL
> All 13 organs registry-aware; drift persistence verified; Vault seal complete.

Note: Git epoch may be sealed while Vault seal remains pending if runtime drift persistence is not yet proven. These are independent dimensions of the seal ladder.

---

*DITEMPA BUKAN DIBERI.* 🔥🧠💎
