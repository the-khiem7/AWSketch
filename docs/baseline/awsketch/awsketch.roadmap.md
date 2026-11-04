---
baseline_schema: "3.0"
pack: "awsketch"
document: "roadmap"
status: "active"
updated: "2026-11-04"
code_ref: "uncommitted"
---

# awsketch - Roadmap

## Status

| Phase | Subject | Depends on | Status |
|---|---|---|---|
| AK-P1 | Repo scaffold | - | complete |
| AK-P2 | Icon index and layout | AK-P1 | complete |
| AK-P3 | Official icon package importer | AK-P2 | complete |
| AK-P4 | Page shell | AK-P1 | complete |
| AK-P5 | Renderer and validator | AK-P3, AK-P4 | complete |
| AK-P6 | Browser verification | AK-P5 | complete |
| AK-P7 | Skill instructions and references | AK-P5, AK-P6 | complete |
| AK-P8 | Install and smoke test | AK-P7 | complete |
| AK-P9 | UI Shell enhancement | AK-P4, AK-P5 | complete |
| AK-P10 | Records mode | AK-P9 | complete |
| AK-P11 | Validator and group type follow-ups | AK-P10 | complete |
| AK-P12 | Motion ignores reduced-motion | AK-P9 | complete |

## Next action

All phases (AK-P1 to AK-P12) are complete. No next action is planned; the open item is that the AWS icon terms text is still unverified (AK-D7, public repo with redistributed icons).

## AK-P1: Phase 1 - Repo scaffold

- Deliver: empty folders `awsketch/{references,assets/icons,scripts}`.
- Status: complete.
- Evidence: the three folders exist under `awsketch/`.
- Acceptance: the three folders exist.

## AK-P2: Phase 2 - Icon index and layout

- Deliver: the icon library layout and `awsketch/assets/icons/index.json` shape (AK-D10, files nested by kind and category).
- Status: complete.
- Evidence: every index entry carries `name`, `kind`, `category`, `path`, `viewBox`, `size`; ids are `[a-z0-9-]` only.

## AK-P3: Phase 3 - Official icon package importer

- Deliver: `awsketch/scripts/sync_aws_icons.py <zip-or-folder>` that globs `**/*.svg`, classifies by `Arch_` / `Res_` / group filename, writes each as a standalone `<svg>` that opens in a browser (the renderer converts it to a `<symbol>` when inlining), and regenerates `index.json` and `awsketch/references/icon-catalog.md`.
- Acceptance: run against a real downloaded AWS Architecture Icons package; every icon file parses as XML; a second run adds 0 icons; the generic icons exist (`res-user`, `res-users`, `res-server`, `res-servers`, `res-internet`).
- Gate: the package folder naming is verified against the real download, not assumed.
- Status: complete.
- Evidence: package layout read from the real zip (`Architecture-Service-Icons_<date>/Arch_<Category>/<size>/Arch_<Name>_<size>.svg`, `Resource-Icons_<date>/Res_<Category>/Res_<Name>_48.svg`, `Architecture-Group-Icons_<date>/<Name>_32.svg`; no license file inside). `sync_aws_icons.py` took the 64px service, 48px resource (including the General-Icons Light set) and group icons: 781 icons (302 service, 466 resource, 13 group); every file parses as XML; a second run adds 0 and the id set is `[a-z0-9-]` only; no dangling `url(#...)` reference.
- Risk: the package layout and download URL change between AWS releases.
- Source: the AWS Architecture Icons page lists `Icon-package_07312026.<hash>.zip` on `d1.awsstatic.com` (observed 2026-10-26, release date inferred from the file name). The page states no redistribution terms; a third-party source says the zip link shows terms to accept before download. The owner accepted the terms and approved the download on 2026-10-26.

## AK-P4: Phase 4 - Page shell

- Deliver: `awsketch/assets/shell.html` - the page CSS, a Google Fonts `<link>` (AK-D5, fonts by link), header, chips container, sheet, hint, `#detail`, sections slot and the interaction script, with `{{placeholders}}` for generated parts.
- Acceptance: the shell has no `@font-face` block, and the flow-colour variables and per-flow rules are placeholders.
- Gate: the filled shell passes the Artifact page contract checks (title, tokens, dark mode, body background, 16px gutter).
- Status: complete.
- Evidence: a filled shell gives a 116KB page; every contract check passed (non-empty title, viewport meta, `:root` tokens, guarded dark-mode media query, `[data-theme="dark"]` override, body background, 16px gutter, sheet scrolls horizontally, only Google Fonts hosts, no external script, no leftover placeholder).
- Placeholders: `{{title}}`, `{{intro}}`, `{{flow_vars}}`, `{{flow_rules}}`, `{{chips}}`, `{{svg}}`, `{{hint}}`, `{{sections}}`, `{{detail_map}}`.
- Risk: the Google Fonts link was not fetched.

## AK-P5: Phase 5 - Renderer and validator

- Deliver: `awsketch/scripts/render.py` with `render <spec> -o <html>`, `--check`, `--list-icons`; builders for groups, pools, nodes, edges, labels, badges, trunks, connectors, texts, the `D` map, chips and sections; validator per [awsketch.sourcecode.md](awsketch.sourcecode.md).
- Acceptance: a negative spec with an unknown icon, a diagonal edge segment and two overlapping nodes yields exactly 3 errors and a non-zero exit.
- Gate: stdlib only; `uv run` with no `--with` flags.
- Status: complete.
- Evidence: the negative spec yields exactly 3 errors and exit 1; a small valid spec renders with 0 warnings, exit 0, a well-formed SVG, no unfilled slot, only the used icons inlined, and escaped title and detail text; `uv run` ran it with no `--with` flags.

## AK-P6: Phase 6 - Browser verification

- Deliver: a rendered multi-group sample page checked in a browser; non-clickable layer boxes in the renderer for a box that only holds nodes.
- Acceptance: `render.py --check` reports 0 errors; a 1280px full-page screenshot shows the groups, icons, chips and panel; clicking chip 3 leaves only the third flow at opacity 1; clicking a node and pressing Enter on a focused node fill `#detail`; at 390px the page has no horizontal scroll and the sheet scrolls internally.
- Status: complete.
- Evidence: `render.py --check` gives 0 errors; in headless Chrome pressing chip 3 gives the third flow opacity 1 and the others 0.1, clicking a node and pressing Enter on a focused node fill `#detail`, and inside a 390px frame the page width is 375 while the sheet (1100 wide) scrolls inside its 341px box.
- Revisions: the shell's dim rule was after the per-flow highlight rules and won at equal specificity, so it moved before them; the renderer gained non-clickable layer boxes.
- Risk: only headless Chrome was used, because the Playwright tool blocks `file:` and localhost URLs; the 390px check ran in a 390px frame, not a 390px window, because headless Chrome's smallest window is about 500px; the offline fallback font look was not compared.

## AK-P7: Phase 7 - Skill instructions and references

- Deliver: `awsketch/SKILL.md` (triggers, 7-step procedure: gather, icons, lay out, write spec, render, look, publish; pitfalls); `awsketch/references/spec-format.md`; `awsketch/references/layout-rules.md`; `awsketch/references/icon-catalog.md`; repo `README.md` with install steps and the icon-terms note (AK-D7, public repo with redistributed icons, terms text still unverified).
- Acceptance: every spec field the renderer accepts is documented; ASCII hyphen only; no hard-wrapped paragraphs.
- Status: complete.
- Evidence: every field name `render.py` reads from a spec appears in `spec-format.md` (grep; the only unmatched name, `path`, is an icon index field); the minimal example in `spec-format.md` renders with 0 errors and 0 warnings; no en or em dash in the four files; no multi-line prose paragraph outside the YAML frontmatter.
- Risk: no agent has yet followed `SKILL.md` end to end; the README install steps are exercised in AK-P8.

## AK-P8: Phase 8 - Install and smoke test

- Deliver: directory junction `.claude/skills/awsketch` -> `awsketch/` at the repo root (AK-D8, repo-scoped junction install), created with `New-Item -ItemType Junction`.
- Acceptance: the skill appears in the skill list when Claude Code runs inside this repo; given "3-tier web app: ALB, ECS, RDS, S3", it produces a spec that passes `--check` and an HTML page whose screenshot shows no collisions.
- Status: complete.
- Evidence: junction `.claude/skills/awsketch` created with `New-Item -ItemType Junction` (no elevation), LinkType Junction, target `awsketch/`, and `SKILL.md` reads through it; the three-tier spec (users, ALB, ECS, RDS, S3, CloudWatch; three flows), written by following `SKILL.md`, passes `--check` with 0 errors and 0 warnings when run through the junction path; the first 1280px screenshot showed one flow crossing two node labels, fixed by rerouting it to the hit box edges and by a new layout rule (AK-D12, vertical flows use the box edge); the second screenshot shows no collisions.
- Evidence: after `/reload-skills` in this repo the skill list grew from 107 to 108 and `awsketch` appears in it with its description (2026-10-26).
- Risk: the junction is machine-local and must not be committed.

## AK-P9: Phase 9 - UI Shell enhancement

- Deliver: the shell layout approved in AK-D13: desktop overview-first timeline with flow chips, Back / Play / Next around the flow caption, scrubber on the bar edge, spotlight and neighbourhood animation, packets with one Pause switch, tooltips, Note / Night / vertical-rail switches on the left edge; phone bottom drawer. `render.py` emits `data-from` / `data-to` per flow path (AK-D14).
- Acceptance: validator still passes; the sample spec renders with every flow path carrying `data-from` / `data-to`; no page errors at 1280 and 390; desktop and phone layouts match AK-D13; axe reports no serious violation; every control reachable by keyboard with visible focus; reduced motion stops dashes and packets (last clause reversed by AK-D23, see AK-P12).
- Gate: AK-Q3 answered before the step order is called correct; closed by AK-D15 (optional spec `from` / `to`).
- Status: complete.
- Evidence: `render.py --check` on the 48-component sample gives 0 errors and 0 warnings; 31 of 31 flow paths carry `data-from` / `data-to`, 3 ends named by the ECS cluster boundary; an edge `to` naming an unknown id fails with exit 1; in Chrome at 1280 (light and dark) and at 390 with touch emulation there are no page errors; axe-core 4.10.2 reports no violations on load, with the card open, and at 390; Pay flow arrow 2 reads "Payment webhook queue to Payment confirmer"; clicking the pressed chip returns the scrubber to 0; a note is placed and kept. `SKILL.md`, `README.md`, `spec-format.md` and `layout-rules.md` describe the new shell.
- Risk: specs without `from` / `to` still name the node an arrow touches (AK-D15); on a phone the diagram stays a 1100px sheet panned sideways; no screen reader was run, only axe.

## AK-P10: Phase 10 - Records mode

- Deliver: `references/records.md` and `scripts/records.py` (records kept beside a spec drawn from other documents, AK-D16, with lint, AK-D18); `render.py` warning for missing flow captions and the caption rule in `spec-format.md` (AK-D17); `SKILL.md` procedure step 8 and a Records mode section; `README.md` rows and usage.
- Acceptance: the first records-mode diagram (a 26-node platform diagram) converts from its baseline pack to a record set with `lint` and `check` at 0 findings; a broken copy is caught by `lint` and refused by `stamp`; `init` writes both files and never overwrites; the two sample specs give no caption warning.
- Status: complete.
- Evidence: on the converted record set (71 routes, 32 source files, 2 watched folders) `lint` gives 0 findings and `check` exits 0 after `stamp`; on a copy with a renamed node, a wrong anchor and a duplicate identifier `lint` gives 5 findings and `stamp` refuses; `init` on a copy of `examples/platform-on-aws.json` wrote both files, a second `init` refused, `next-id` gave `PLT-D1`; `render.py --check` on both sample specs shows no caption warning; the moved page walked all 24 arrows of 6 flows with every chip caption and no page error in Edge.
- Risk: drift findings say a source changed, not whether the diagram must change; a source edit that does not touch a routed section or add an entry is not reported; the Source map and routes are maintained by hand.

## AK-P11: Phase 11 - Validator and group type follow-ups

- Deliver: `ecs` group type (AK-D20); group title overflow warning (AK-D21); ASCII-only dash check in `render.py` (AK-D22); `spec-format.md`, `layout-rules.md` and `sourcecode` updated.
- Acceptance: a spec with a narrowed group and an en dash in its title gets both warnings; the two sample specs gain no new warning; the first records-mode diagram renders with its cluster as `ecs` and 0 warnings; `render.py` holds no non-ASCII character.
- Status: complete.
- Evidence: the negative spec gave `group 'Private app': title and subtitle are wider than w=120` and the dash warning; `examples/platform-on-aws.json` kept its 2 earlier label warnings and `diagrams/ecommerce-on-aws.json` stayed at 0; the records-mode diagram first warned on its cluster title, then rendered with 0 warnings after the cluster became `ecs` with a shorter title, and the screenshot at 1280 showed the solid orange frame with the ECS icon and the title inside it; a scan of `render.py` found 0 non-ASCII characters.
- Risk: the width estimate is per character, so a title of wide glyphs can still overflow without a warning.

## AK-P12: Phase 12 - Motion ignores reduced-motion

- Deliver: `assets/shell.html` without the `prefers-reduced-motion` media block and the `RM` flag (AK-D23); `awsketch.sourcecode.md` motion row updated.
- Acceptance: with `prefers-reduced-motion: reduce` emulated, a pressed flow still carries the `march` animation and packets, and `#motion` is visible; no `RM` or `reduced-motion` text left in the shell or in a rendered page.
- Status: complete.
- Evidence: two sample specs and two Atlantic diagrams re-rendered with 0 occurrences of `reduced-motion` or `RM`; in Chrome under Playwright with `reducedMotion: reduce`, pressing chip 4 of a 4-flow diagram gave `.flow.on` animation `march`, 6 packets, `#motion` display `flex` and not hidden, 0 console errors.
- Risk: not run on a Windows machine with "Animation effects" off, only emulated; keyboard and axe checks of AK-P9 were not repeated.

## Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Offline view falls back to Segoe UI | Labels render wider and may overflow | Text-fit warning uses Plex metrics plus 5% headroom |
| Icon terms text unverified | Public repo may have to drop the icons if AWS terms forbid redistribution | AK-D7 |
| Icon package layout varies | Importer misclassifies files | AK-P3 gate |
