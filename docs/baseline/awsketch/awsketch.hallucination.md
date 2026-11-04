---
baseline_schema: "3.0"
pack: "awsketch"
document: "hallucination"
status: "active"
updated: "2026-11-04"
code_ref: "uncommitted"
---

# awsketch - Decisions and Open Questions

## Entry index

| ID | About | Status | Related |
|---|---|---|---|
| AK-D1 | Where the skill source lives | decided | - |
| AK-D2 | How the diagram is produced | decided | AK-D3 |
| AK-D3 | Layout by explicit coordinates | decided | AK-D2 |
| AK-D5 | Font delivery | decided | - |
| AK-D6 | Drawing sheet colour in dark mode | decided | AK-D13 |
| AK-D7 | Public repo with redistributed AWS icons | decided | AK-Q1 |
| AK-D8 | Repo-scoped junction install | decided | AK-Q2, AK-D1 |
| AK-D10 | Icon files nested by kind and category | decided | - |
| AK-D12 | Vertical flows start and end at the hit box edge, not the icon | lesson | - |
| AK-D13 | Approved page shell layout | decided | AK-D6, AK-D14, AK-D15 |
| AK-D14 | Arrow ends come from the spec, not page geometry | decided | AK-D13, AK-D15 |
| AK-D15 | Optional `from` / `to` on spec edges | decided | AK-Q3, AK-D14 |
| AK-D16 | Records mode: sources and decisions files beside the spec, instead of a baseline pack | decided | AK-D17, AK-D18 |
| AK-D17 | Render warning for missing flow captions | decided | AK-D15 |
| AK-D18 | Records lint checks spec and routes against each other and gates stamp | decided | AK-D16 |
| AK-D19 | Byte order mark hid a source file's frontmatter from records | lesson | AK-D16 |
| AK-D20 | `ecs` group type | decided | AK-Q4, AK-D13 |
| AK-D21 | Warning for a group title and subtitle wider than the group | decided | AK-Q5, AK-D17 |
| AK-D22 | `render.py` source is ASCII-only | decided | AK-Q6 |
| AK-D23 | Page motion always runs, the OS reduced-motion setting is ignored | decided | AK-D13 |

## Closed decisions

### AK-D1: Skill source lives in the standalone AWSketch repo

- Decision: `AWSketch` is the skill's own source repo; the skill folder is `awsketch/` at the repo root, same shape as `the-khiem7/aws-adr`.
- Why: installable with `npx skills add`, versioned on its own, and skill improvements are recorded here rather than in a project repo.
- Breaks if ignored: improvements land in whichever repo is open and drift apart.
- Rejected: `kait/skills/diagrams/` - kait's validator section and catalog rules add overhead and AWSketch would stay empty.

### AK-D2: JSON spec plus a stdlib Python renderer and validator

- Decision: the agent writes a JSON spec (groups, pools, nodes with x/y, flows as orthogonal waypoints, detail triples, sections); `uv run awsketch/scripts/render.py` validates it and emits the HTML, inlining only the icons the spec uses.
- Why: the page look depends on exact CSS, AWS group colours, marker definitions and about 90KB of icon SVG; a renderer makes that deterministic and keeps edits cheap.
- Breaks if ignored: hand-written SVG drifts on every diagram and costs tens of thousands of tokens per render.
- Rejected: frozen HTML shell plus layout rules with the agent hand-writing the SVG body - higher output variance and the agent must paste icon `<symbol>`s.

### AK-D3: Layout is explicit coordinates written by the agent

- Decision: the spec carries absolute x/y for every group, pool, node, edge waypoint, label and badge; the renderer derives only node height and icon/text placement.
- Why: the target look is a hand-laid column grid with flows routed through column gutters.
- Breaks if ignored: an auto-layout engine produces a different visual grammar.
- Rejected: Graphviz or ELK auto-layout - different look and an extra non-stdlib dependency.

### AK-D5: IBM Plex fonts load from Google Fonts

- Decision: load fonts through a Google Fonts `<link>` for IBM Plex Sans 400/500/600/700 and IBM Plex Mono 500, not embedded `@font-face` blocks.
- Why: output stays about 100-150KB instead of about 1.1MB, and the Artifact CSP allows Google Fonts stylesheets.
- Breaks if ignored: every diagram ships 1MB of font data.
- Rejected: embedding base64 - 1MB per file. Link by default with an embed flag - two font paths to maintain.

### AK-D6: The drawing sheet stays white in dark mode

- Decision: the `.sheet` and the SVG background stay `#FFFFFF` in both themes; only the page chrome follows the theme.
- Why: AWS icon tiles and group colours are designed for a white background.
- Breaks if ignored: dark-filled sheets make group strokes and resource icons illegible.
- Rejected: theming the SVG - AWS icon colours are fixed.
- Exception: the opt-in Night switch (AK-D13) darkens the sheet and puts every icon on a white tile, so icon colours still sit on white; system dark mode alone never darkens the sheet.

### AK-D7: The repo is public and ships the AWS icon SVGs

Closes AK-Q1.

- Decision: the repo is public and redistributes the extracted AWS Architecture Icons SVGs (and any added by `sync_aws_icons.py`).
- Why: the owner explicitly approved redistributing the icons in a public repo on 2026-10-26. AWS permits the icons for building architecture diagrams; whether the terms cover redistributing the raw SVGs was never verified, and the owner accepted that.
- Breaks if ignored: n/a for builds; if AWS terms forbid redistribution, the public repo carries the violation and the icons must be removed from it.
- Rejected: keeping the repo private until the terms are read - the owner declined the delay.
- Still unverified: the AWS icon terms text; the owner stated on 2026-10-26 that redistribution is allowed and the icons stay in the repo. `README.md` states that and links the AWS terms.

### AK-D8: Install by a junction inside the repo-scoped .claude

Closes AK-Q2.

- Decision: install with a directory junction `AWSketch/.claude/skills/awsketch` pointing at `AWSketch/awsketch`. It is repo-scoped, not user-scoped (`%USERPROFILE%/.claude/skills`).
- Why: no admin rights needed, edits show live, and the skill loads only when working inside this repo.
- Breaks if ignored: a user-scope install makes the skill load in every project and changes global state the owner did not choose.
- Rejected: user-scope junction - the owner chose repo scope. GitHub remote plus `npx skills add` - needs a push, and the skill is only needed here for now.
- Consequence: the junction is machine-local and the `skills` CLI creates mirror directories at install time, so it is never meant to be committed.

### AK-D10: Icon files are nested as `<kind>/<category>/<id>.svg`; the renderer finds them through `index.json`

- Decision: `awsketch/assets/icons/` holds `service/<category>/`, `resource/<category>/` and a flat `group/`; the category is the package's own folder name (slugged), and each `index.json` entry carries `category` and `path`.
- Decision: icon ids stay flat and unique (`res-` and `group-` prefixes already separate the kinds); the renderer resolves an id to a file only through `path`, never by building a path from the id.
- Why: 781 files in one folder are hard to browse, and the package already supplies the category folders.
- Breaks if ignored: code that builds `assets/icons/<id>.svg` finds nothing; the sync script's existence check must use `path`, or every run re-imports and rewrites all icons.
- Rejected: nesting by kind only - `service/` would still hold 302 files. Keeping the flat layout - the browsing cost stays and the category information in the package is thrown away.

### AK-D12: A flow leaving or entering a node from below uses the hit box edge, not the icon

- Decision: `references/layout-rules.md` tells the agent to enter or leave a node sideways at icon mid-height, and to start or end a vertical flow at the hit box bottom edge (`y + h`), never at the icon.
- Why: the node label and sublines sit between the icon and the box bottom, so a line from the icon's bottom crosses them.
- Lesson: in the three-tier smoke test the agent ended a flow at the S3 icon bottom and started one at the ECS icon bottom, which looked right in the spec because the coordinates were the icon edge, and the screenshot showed the line through both labels; the validator cannot see it because the line does not touch another node's hit box.
- Breaks if ignored: flows cross labels in every diagram that routes below a row, and only a screenshot catches it.
- Rejected: a validator check for a segment crossing a node's own label area - more code for a case a written rule plus the screenshot step already covers.

### AK-D13: Approved page shell layout

- Decision: the shell keeps the original horizontal flow chips in a sticky bar and adds, on desktop: rounded-rectangle shape on every container (chips and buttons 8px, bar, sheet and card 14px, no mono UI font); a timeline that is always on, where step 0 is the overview with every arrow shown, Play or Next starts at arrow 1, Back from arrow 1, Escape or any chip click (including the pressed one) returns to step 0; Back icon left of the flow caption, Play and Next icons right of it, scrubber on the bar's bottom edge in the flow colour; the hop text is screen-reader only; the diagram intro moves into the caption slot under All flows; a pressed flow lights its icons, marches its dashes and sends packets; hovering or focusing an icon lights its own arrows and ends with an "N in, N out" tip; one Pause switch stops dashes and packets; the service card is a popover next to the icon with Tab kept inside and Escape closing it; Note (inline form, kept in this browser), Night (dark blueprint sheet, icons on white tiles) and the vertical-rail switch are icon-only buttons on the left edge; tooltips on every control except flow chips, hidden by Escape and on touch screens.
- Decision (phone, max 700px): centred title; a bottom drawer holds Back / caption (2 lines, tap to open) / Play / Next / Pause, then the scrubber, then flows as numbered rounded squares scrolling sideways with Night pinned at the right; the service card floats above the drawer; Note and the rail switch are hidden; each step scrolls the current arrow into view.
- Why: overview first means nothing animates on load and no mode switch is needed; the drawer puts every phone control in thumb reach while the top of the screen stays diagram. Approved by the owner on 2026-11-02.
- Breaks if ignored: a step-through mode switch returns as an extra button; Pause missing fails WCAG 2.2.2 for the moving dashes and packets; a full-width bottom sheet on phone covers the drawer.
- Rejected: docked inspector or bottom drawer for the service card on desktop - the popover next to the icon keeps the eye on the diagram; vertical rail as the default selector - names hidden until hover; a separate Step through mode with a Done button - replaced by step 0; zoom, 3D and autoplay views - out of scope for this phase; tooltips on flow chips - removed by the owner.
- Constraint: the white tiles behind icons in Night must have no fill outside Night, or icons turn black after Night is switched off.

### AK-D14: Arrow ends come from the spec through the renderer's distance helpers

- Decision: `render.py` writes `data-from` / `data-to` on every `path.flow`, found by matching each edge's first and last point to the nearest node within 14px (`rect_dist`), then a clickable pool, else the nearest group boundary name (`edge_dist`) for the caption.
- Why: the shell's neighbourhood, spotlight and step features need edge endpoints, and the spec has none.
- Breaks if ignored: an arrow ending on a layer box is counted as the box instead of the task inside, so lit neighbours and hop captions are wrong.
- Rejected: inferring endpoints in the page from rendered path geometry - wrong on layer boxes and repeated on every page load.

### AK-D15: Spec edges take optional `from` / `to`; arrow order in `edges` is the walk order

Closes AK-Q3.

- Decision: an edge may name `from` and `to` (node or pool ids, validated); each missing end falls back to the nearest node, then pool (AK-D14). The timeline walks arrows in `edges` order, so the agent lists each flow's arrows in the order traffic moves; no `order` field.
- Why: geometry names the node an arrow touches, which is not always the logical source (an arrow that joins another line, or stops at a box edge).
- Breaks if ignored: step captions name the wrong source, and the agent has no way to correct them short of moving the drawing.
- Rejected: geometry only - wrong captions with no fix; a required `from` / `to` - breaks every existing spec; an `order` field - the list order already expresses it.

### AK-D16: A diagram that must stay true to other documents keeps two record files beside its spec, not a baseline pack

- Decision: records mode keeps `<slug>.json`, `<slug>.html`, `<slug>.sources.md` and `<slug>.decisions.md` in `docs/diagrams/<slug>/`; sources carries repositories, a source map, routes from diagram elements to source sections with a fingerprint each, source files with `updated` and the highest entry identifier, watched folders with a file count, and a Verified table; decisions carries one Next line, decisions and open questions under one prefix; status is what `records.py check` computes. Format and workflow in `references/records.md`.
- Why: the first such diagram (a platform diagram of 26 nodes drawn from six packs in two repositories) was kept as a baseline pack with a router document; its phases and introduction repeated what the spec and `check` already say, every write required the pack contract, and `packtool.sh` never checked the router, which was the part that mattered. Section fingerprints rather than file hashes or `code_ref`: a whole-file hash flags every unrelated edit, and a pack's `code_ref` lagged a commit that changed the very value the diagram drew.
- Breaks if ignored: a later visit trusts a diagram whose source changed, or re-reads every source pack to find out.
- Rejected: a baseline pack with a router document (overhead above, router unchecked); routes inside the spec (each stamp churns the spec, and route fields must never reach a published page); a new baselinedocs-family skill (keeps the pack contract the mode exists to avoid); records for every diagram (most are drawn once, so the mode is opt-in).

### AK-D17: `render.py` warns when flows have no caption item

- Decision: warn when a spec has flows but no `ordered` section, or when the first ordered section has fewer items than flows; `spec-format.md` states the rule.
- Why: the shell captions a pressed chip with the item at the same index of the page's ordered lists, a rule that lived only in `assets/shell.html`; the first records-mode spec rendered with 0 warnings and empty captions.
- Breaks if ignored: a spec that follows the documentation ships chips with no caption, silently.
- Rejected: an error (blocks specs that want no captions); a `caption` field on each flow (changes the spec format and the shell for a rule a warning covers).

### AK-D18: `records.py lint` checks the spec and the routes against each other and gates `stamp`

- Decision: lint fails on a node or clickable pool with no route, a route naming an id or `section:` title absent from the spec, an unresolved source or anchor, a routed source missing from Source files, a duplicate or misfiled identifier, a `## Next` that is not one line, an en or em dash; `check` runs lint first and `stamp` refuses while it fails; `stamp` also writes the `render.py --check` result into `## Verified`.
- Why: renaming a node in the spec left its routes orphaned and nothing reported it; a stamp over an unresolved route would record a fingerprint of nothing.
- Breaks if ignored: drift on a renamed element is never reported, and a stamp hides broken routes.
- Rejected: lint as a separate optional step (it is skipped exactly when it matters, before a stamp).

### AK-D19: A byte order mark hid a source file's frontmatter from records, so records reads `utf-8-sig`

- Lesson: after a source file was rewritten with Windows PowerShell 5.1 `Set-Content -Encoding utf8`, which prepends a UTF-8 byte order mark, `records.py check` reported its `updated` as `-` and would have stamped `-`; the first line read as `﻿---`, not `---`.
- Why it looked fine: the file rendered and diffed normally, and the edit itself was a one-line date change.
- Fix: `records.py` reads every source as `utf-8-sig`, which drops a leading mark and reads plain UTF-8 unchanged; the mark was also stripped from the file.
- Breaks if ignored: every frontmatter-based signal (Updated, the stamped date) silently goes blank for that file, and a real `updated` change is never reported.

### AK-D20: The renderer has an `ecs` group type

Closes AK-Q4.

- Decision: group type `ecs` draws an orange tint (`#FFF7F0`) with a solid orange outline (`#ED7100`) and the `amazon-elastic-container-service` icon; `eks` keeps the dashed outline.
- Why: the first ECS-based diagram drew its cluster with the `eks` type and an icon override, so the frame kept the EKS dashed outline and read as another service; owner approved on 2026-11-03.
- Breaks if ignored: an ECS cluster frame reads as EKS.
- Rejected: keep `eks` plus `icon` and document the override (the dashed EKS styling stays).

### AK-D21: The validator warns when a group title and subtitle are wider than the group

Closes AK-Q5.

- Decision: warn when the label offset + 7 units per title character + 8 + 6.5 units per subtitle character exceeds `w - 6`.
- Why: three group titles overflowed on the first records-mode diagram (a subnet title with its CIDR range in a 150-unit subnet, an account frame subtitle) and rendered with 0 warnings; only the screenshot caught them. On that diagram the warning also flagged the cluster frame, whose subtitle the earlier screenshot showed touching the right edge.
- Breaks if ignored: clipped group titles ship whenever the screenshot step is skipped or skimmed.
- Rejected: leave it to the screenshot step (missed three times on one diagram).

### AK-D22: `render.py` writes the dash check with escapes, so the source is ASCII-only

Closes AK-Q6.

- Decision: `BAD_DASH` in `render.py` and `records.py` uses the escapes for U+2013 and U+2014 instead of the literal characters.
- Why: every shipped file uses the ASCII hyphen only (introduction constraints); the detector held the two characters literally.
- Breaks if ignored: a dash scan of the shipped files flags the renderer itself, and the constraint has an unmarked exception.
- Rejected: exempt the detector from the rule (an exception nobody can see in the file).

### AK-D23: Page motion always runs; `prefers-reduced-motion` is not read

- Decision: `assets/shell.html` has no `prefers-reduced-motion` media block and no `RM` flag; dashes, packets, smooth scrolling and the 1100 ms walk step always run, and the `#motion` Pause switch is always visible; no spec field or flag turns this off (owner, 2026-11-04).
- Why: with Windows 11 "Animation effects" off, Chrome reports `reduce`, so the page showed no moving dashes or packets and hid the Pause switch; Playwright's Chrome ignores the OS setting and showed them, so the same page looked different. The owner wants the diagram to move on every machine.
- Breaks if ignored: a viewer with the OS setting off sees a static diagram with no Pause switch and cannot tell why it differs from the author's screenshot.
- Cost: a viewer who turns animation off for comfort or health still gets moving dashes and packets; the Pause switch (WCAG 2.2.2) is the only control and does not remember its state between loads.
- Rejected: a spec field `motion: always` or a render flag (owner: always on, no switch); keep the media query and tell users to emulate `no-preference` in DevTools (temporary, per DevTools session); patch generated HTML by hand (lost on re-render).

## Open questions

None.
