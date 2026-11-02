---
baseline_schema: "3.0"
pack: "awsketch"
document: "hallucination"
status: "active"
updated: "2026-11-02"
code_ref: "ab601a6"
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

## Open questions

None.
