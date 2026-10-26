---
baseline_schema: "2.0"
pack: "awsketch"
document: "introduction"
status: "active"
updated: "2026-10-26"
code_ref: "8b3f5c7"
---

# awsketch - Introduction

## Scope

Build `awsketch`, an Agent Skill that produces interactive single-page AWS deployment diagrams from any architecture description, without the agent hand-writing SVG each time.

In scope: the skill folder (`SKILL.md`, references, assets, scripts), an icon library, a spec-to-HTML renderer with a validator, local install, a smoke test.

Out of scope: auto-layout, non-AWS cloud icon sets, committing anything without explicit approval.

## Current truth

| Item | State |
|---|---|
| Repository | `AWSketch`, branch `main` |
| Skill code | built: renderer, validator, page shell, icon library, importer, instructions, references |
| Install | repo-scoped directory junction, machine-local |

## Page anatomy

| Part | Detail |
|---|---|
| Fonts | IBM Plex Sans and IBM Plex Mono from a Google Fonts `<link>` |
| Page CSS | Tokens on `:root`; dark mode under `prefers-color-scheme` guarded by `:root:not([data-theme="light"])` and again under `[data-theme="dark"]`; `.wrap` max 1240px with 16px gutter; `.chips`; `.sheet` white drawing sheet with `min-width:1100px` and horizontal scroll; `#detail` panel; `details` sections |
| Diagram | One `<svg viewBox="0 0 W H">`; `<defs>` holds one `<symbol>` per icon used and one arrow `<marker>` per flow |
| Icons | Official AWS Architecture Icons: 64-viewBox service tiles, 48-viewBox resource icons, 40-viewBox group icons |
| Groups | AWS group boxes with the official stroke and fill colours, a 26px group icon at the top-left corner, `.gl` label plus optional `.gs` sublabel |
| Nodes | `g.node[data-id]` with `tabindex="0" role="button"`: transparent hit rect `rx=6`, `<use>` icon centred at `y+4`, `.nl` label at `icon_y+size+15`, `.ns` sublines every 13px |
| Pools | Layer boxes: `.poolbox` rect, 5px coloured left bar, coloured `.nl` title at `y+22`, `.ns2` lines from `y+44` every 18px; a pool may contain nodes and may itself be a node |
| Flows | Orthogonal paths written as `M x y H .. V ..`, classes `flow f-<id>`, optional `stroke-dasharray="7 5"`, `marker-start` for two-way flows; `.flabel` labels with a white `paint-order` halo; numbered `.badge` circles; `.trunk` thick grey connector; dotted grey `<line>` connectors |
| Interaction | Chips set `body[data-flow]`, which dims every other flow to opacity .1; a click or Enter/Space on a node fills `#detail` from a `D` map of `[title, AWS service, text]`; on width up to 700px the panel scrolls into view |
| Page sections | `header` (h1 + intro), chips, sheet, hint line, `#detail`, `<details>` sections |
| Artifact contract | Met: colour tokens, dark mode, explicit body background, 16px phone gutter, no page-level horizontal scroll |

## Target

- `awsketch/` skill installable from this repo, triggered by requests for an AWS architecture or deployment diagram page.
- The agent writes a JSON spec; `uv run awsketch/scripts/render.py` validates it and emits one HTML page with the geometry, colours, icons, chips, panel and sections described above.

## Constraints

- Python runs through `uv` only, stdlib only in the renderer.
- ASCII hyphen only in every file the skill emits or ships.
- No paragraph hard-wrapping in any shipped Markdown.
- Diagrams written while using the skill live in the user's own repository, never in this one.
- No commit or push without explicit approval. The repo is public (AK-D7).
- Standard Windows user, no elevation: install is a repo-scoped directory junction (AK-D8).

Decisions and their reasoning: [awsketch.hallucination.md](awsketch.hallucination.md). Phases: [awsketch.roadmap.md](awsketch.roadmap.md). Code shape: [awsketch.sourcecode.md](awsketch.sourcecode.md).
