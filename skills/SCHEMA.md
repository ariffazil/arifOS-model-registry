# arifOS Skills Registry — SCHEMA

Skills as first-class artefacts. When an M3 agent completes a stable
successful run, it may propose: "Convert to Skill S-####?" — never
auto-publish. Skills live in this directory as versioned YAML, go
through APEX review (git PR), and are queryable by all federation organs.

## Schema (v1, 2026-06-02)

The Skill YAML has these fields:

    id: string               # required — S-NNNN format
    name: string             # required — kebab-case, <= 64 chars
    model_family: string     # required — e.g. "minimax/minimax-m3"
    roles: list              # required — subset of [leader, worker, verifier]
    plan_template: object    # required — LongTask-style plan structure
    tool_set: list           # required — list of tool names used
    safety_profile: object   # required — f_floors_relevant, tripwires, escalation
    examples: list           # required — at least 1 (input + output)
    created_by: string       # default "forge-agent"
    created_at: datetime     # ISO 8601, default now()
    updated_at: datetime     # ISO 8601, default now()
    status: enum             # one of: draft, proposed, approved, retired
    git_commit: string|null  # set when approved
    retired_reason: string|null  # set when retired

## Status transitions

    draft    --(propose)-->  proposed  --(APEX PR merged)-->  approved
    approved --(deprecate)--> retired

## Routing rules

- Skills are loaded at agent boot from this directory.
- Approved skills are queryable via `arif_sense_observe` mode `skill_catalog`.
- Draft skills are visible only to their `created_by`.
- Retired skills are kept for audit but excluded from catalog.

## Convention

- File name: `S-NNNN-kebab-case-name.yaml` (e.g. `S-0001-m3-constitutional-deliberation.yaml`)
- One skill per file.
- Commit message: `feat(skills): add S-NNNN <name>` or `chore(skills): retire S-NNNN <reason>`.

## Examples

See sibling YAML files in this directory for working examples.

DITEMPA BUKAN DIBERI — Skills are forged, not given.
