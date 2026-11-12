---
baseline_schema: "3.0"
pack: "awsketch"
document: "hallucination"
status: "active"
updated: "2026-11-10"
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
| AK-D12 | Vertical flows start and end at the hit box edge, not the icon | lesson; top end superseded by AK-D24 | AK-D24 |
| AK-D13 | Approved page shell layout | decided; hover tip removed by AK-D27 | AK-D6, AK-D14, AK-D15, AK-D27 |
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
| AK-D24 | Renderer places arrow ends on nodes as centred, spread ports | decided | AK-D3, AK-D12, AK-D28 |
| AK-D25 | Dashed pattern stretched to fit the line | lesson | AK-D24 |
| AK-D26 | March animation starts from offset 0 | lesson | AK-D25 |
| AK-D27 | Hover keeps linked labels in a still box; no in/out tip | decided; `owner()` replaced by `attach()` in AK-D37 | AK-D13, AK-D37 |
| AK-D28 | Layout warnings for crowded, stacked or covered drawing | decided | AK-D21, AK-D24 |
| AK-D29 | No limit on the number of flows | decided | AK-D13, AK-D30 |
| AK-D30 | An edge may belong to no flow | decided | AK-D13, AK-D14, AK-D29 |
| AK-D31 | Connector ends are pulled onto the icon edge | decided | AK-D24 |
| AK-D32 | Each diagram lives in its own folder | decided | AK-D16 |
| AK-D33 | A target-architecture page draws planned flows as normal solid flows | decided | AK-D16 |
| AK-D34 | A component with no AWS icon takes a stand-in icon and a recorded reason | decided | AK-D16 |
| AK-D35 | A link-only source edit is reconciled by comparison, then stamped | decided | AK-D16, AK-D18 |
| AK-D36 | The chip row scrolls sideways past about five flows | lesson | AK-D29 |
| AK-D37 | Labels and badges stayed put while routing moved their arrow | lesson | AK-D3, AK-D24, AK-D27, AK-D28 |

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

### AK-D24: The renderer places every arrow end on its node as centred, spread ports

- Decision: `route()` in `render.py` groups edge ends by node and side (side from the end segment's direction), merges ends at one coordinate into one port, spreads ports `PORT_GAP` 20 apart centred on the icon (left, right, top) or box (bottom) in spec order, moves the neighbouring corner along, slides an end segment that crosses a group title sideways while it still lands on the icon (`nudge_off_titles()`), then pulls each end onto the icon side, the icon top or the box bottom, `END_GAP` 2 short. A two-point straight edge moves as a whole; a conflict at its other end is a warning. Owner approved on 2026-11-05.
- Why: the hit box is wider than the icon, so an arrow at the box side left a gap once the hover outline was gone; hand-placed ends on the 35-node Atlantic diagram were 10 apart, off-centre on the NAT node, and crossed the ECS cluster title.
- Breaks if ignored: every spec must hand-compute icon edges and port spacing, and the drawing shows gaps and lopsided arrow groups.
- Rejected: validator warnings only, with the agent placing ends (owner wanted the centring automatic); jogging a straight edge whose two ends disagree (adds a step in a long line; the warning asks for the node to move instead); moving the nodes of a group to clear a title (unbalances the group, owner chose the sideways nudge).
- Supersedes the top-end half of AK-D12: a downward end now stops at the icon top; an upward end still uses the box bottom.

### AK-D25: A dashed line's pattern is stretched to fit a whole number of periods

- Lesson: a fixed `7 5` pattern ended in a gap on most lengths, so the arrowhead floated. The first fix set `stroke-dashoffset` so the line ended on a dash, but the last 10.5 units of the line sit under the arrowhead (marker `refX` 8 of 10 at width 6, stroke 2.2), so the visible gap moved to just behind the head; the second fix aimed a dash at the head's back but left the start in a gap, which read as the line starting at the box edge.
- Fix: `dash_fit()` scales dash and gap by at most half a period so the line starts on a dash and a dash is centred on the back of the arrowhead (`HEAD_BACK`); no offset.
- Breaks if ignored: dashed arrows look detached at one end.

### AK-D26: The march keyframes start from offset 0

- Lesson: once dashed lines carried a static `stroke-dashoffset`, the `march` animation (`to -16`) started from that value, travelled a distance that was not one period, and jumped at every loop, which read as lag.
- Fix: `@keyframes march{from{stroke-dashoffset:0}to{stroke-dashoffset:-16}}`, and the animation applies to `path.flow` only.
- Breaks if ignored: any per-path offset makes the moving dashes stutter.

### AK-D27: Hovering a node keeps its arrows' labels and badges, in a still box; the in/out tip is gone

- Decision: `render.py` gives each `path.flow`, label group `g.fl` and badge a `data-e` index; a label or badge belongs to the nearest arrow of its flow (`owner()`). `nbOn()` adds `.link` to them, and a linked, pressed or walked label shows a white box with a flow-coloured outline (`.flbox`, sized from the text's `getBBox()` after fonts load) instead of the dash animation. The "N in, N out" tip of AK-D13 is removed. Owner request on 2026-11-05.
- Why: the neighbourhood rule dimmed every `.flow` element, labels included, so hovering a node hid the very annotations of its arrows; labels inherited the marching dash and glow, which made text hard to read.
- Breaks if ignored: hover shows unlabeled arrows, and a highlighted label flickers.
- Rejected: keep the tip (owner removed it); estimate the box width in Python (wrong when the fallback font loads).

### AK-D28: The validator warns on drawings a person would redraw

- Decision: `layout_warnings()` warns on two arrows side by side under 8 apart, an arrow through a group title, a label over a node's icon or text, a label within 3 of a group border or over a group title, a hub joining 3 or more nodes in one column more than 80 off their middle, a straight edge that cannot be centred at both ends, and an end missing the icon. Group title width in these checks uses 6.4 per title and 5.6 per subtitle character, measured in Chrome (the AK-D21 overflow warning keeps 7 and 6.5).
- Why: on the Atlantic diagram each of these was found by the owner in a screenshot after a 0-warning render.
- Breaks if ignored: the same defects ship whenever the screenshot step is skimmed.
- Rejected: errors instead of warnings (each has legitimate exceptions, such as a label laid across a vertical line); shifting whole columns to clear a label (tried, widened empty space; the owner allowed a label across a vertical line instead).

### AK-D29: The renderer sets no limit on the number of flows

- Decision: `MAX_FLOWS` and its `more than 6 flows` error are removed from `render.py`; `spec-format.md`, `SKILL.md` and the sourcecode validator table no longer state a limit; the palette in `layout-rules.md` grows from six to ten colours. Owner, 2026-11-05.
- Why: the cap was a constant and a sentence with no decision behind it; the combined Atlantic diagram outgrew its six flows when the Event Mesh account was deepened. The chip row already scrolls sideways (`.chips{overflow-x:auto}`) and the phone drawer already scrolls its numbered squares.
- Breaks if ignored: unrelated paths are folded into one chip to stay under the cap, and their captions and walk order become wrong.
- Rejected: a higher cap (still arbitrary); a warning above six (the owner wants no limit).

### AK-D30: An edge may belong to no flow

- Decision: an edge with no `flow` renders as a plain arrow: stroke `#7D8998` 1.6 wide, its own `m-plain` marker, `start`, `end` and `dashed` as for any edge, routed by `route()` (ports, title nudge, layout warnings). It has no `data-from` / `data-to`, so it is outside the chips, the step walk and the hover highlight, and it is never dimmed. A label or badge still names a flow, and a named `flow` must exist (unknown flow stays an error). Owner, 2026-11-05.
- Why: the rule that every arrow names a flow came from the page being a flow walker (AK-D13) and was never recorded as a decision; a link that carries no traffic of its own, such as a gateway to the address it fronts, had only the arrowless dotted connector.
- Breaks if ignored: such links are drawn as invented flows (wrong colour, chip and caption) or as lines with no direction.
- Rejected: a neutral pseudo-flow with its own chip (a chip for lines that are not a flow); arrowheads on `connectors` (two points only, no routing); shell changes to walk plain arrows (they carry no traffic to narrate).

### AK-D31: Connector ends are pulled onto the icon edge

- Decision: `snap_connector()` moves each connector end within `END_REACH` of a node onto the icon side (a horizontal line meeting the icon's height) or onto the icon top or box bottom (a vertical line meeting the icon or box width), with no gap because the line has no arrowhead; an end touching no node stays where the spec put it.
- Why: a connector is written between two hit boxes, which are wider than the icons, so each end left 40 to 110 units of gap on the Atlantic diagram; arrows already had this fix (AK-D24).
- Breaks if ignored: every spec must compute icon edges by hand, and dotted lines read as stopping short of their boxes.
- Rejected: leave the gap and document it (read as a broken line); the agent computes the icon edges (the cost AK-D24 removed for arrows).

### AK-D32: Each diagram lives in its own folder, `diagrams/<slug>/`

- Decision: the agent writes `diagrams/<slug>/<slug>.json` and renders `diagrams/<slug>/<slug>.html` beside it, one folder per diagram, never loose files in `diagrams/`; `SKILL.md` steps 4 and 5 and `README.md` say so. Records mode keeps `docs/diagrams/<slug>/` (AK-D16), so both modes now use one folder per slug. Owner, 2026-11-09.
- Why: the owner wants a folder per diagram for better management [user]; a folder holds the spec, the page and anything the owner adds for that diagram, and a diagram moved into records mode gains the two record files without moving its spec [agent].
- Breaks if ignored: three or more diagrams in `diagrams/` leave six or more loose files whose pairs are told apart only by name.
- Rejected: flat `diagrams/<slug>.json` and `.html` (the rule before this entry; files of several diagrams mix) [user]; a folder only in records mode (leaves the common case flat) [agent].

### AK-D33: A page that shows the target architecture draws planned flows as normal solid flows

- Decision: planned components and flows are drawn like live ones; a dash keeps its meaning (optional, fallback, trust boundary, replication stream); what is not live is listed in the diagram's decisions record so drift is found when each element goes live; `references/layout-rules.md` section Target architecture says so. Owner, 2026-11-10.
- Why: the page is the target, and a dashed or greyed style turns it into a status board that goes stale as parts land; seen on the Solace PROD and UAT diagrams, where peering, the image pull from ECR and the AMQP consumer were not live [user].
- Breaks if ignored: a reader takes a dashed line as an optional path, or a later render silently drops the plan.
- Rejected: dashed or greyed planned flows (mixes two meanings of dash) [user]; a separate "planned" flow colour (the palette is spent on flow identity, and the status changes every release) [agent].

### AK-D34: A component with no AWS icon takes the closest official icon, a label with its real name, and a recorded reason

- Decision: a component without an AWS icon (a Solace broker, Keycloak, Docker Hub) uses the closest official icon, carries the real product name in its label, and the stand-in and the reason are recorded in the decisions record; never an icon that implies a managed AWS service the component is not; `references/layout-rules.md` section Stand-in icons says so. Owner, 2026-11-10.
- Why: the Solace diagrams needed an EC2 icon for the broker and an SQS icon for Solace queues, and without the label and the record a reader mistakes the EC2 icon for a managed broker [user].
- Breaks if ignored: the page reads as if SQS or a managed AWS broker were deployed.
- Rejected: shipping non-AWS brand icons in the icon set (the set is the official AWS package, redistributed under AK-D7) [agent].

### AK-D35: A source edit that only removes or repoints a link still shows as drift; it is reconciled by comparison, then stamped

- Decision: after such an edit `records.py check` reports DRIFT or UPDATED; `show` the node, compare with its `detail`, confirm nothing drawn changed, then `stamp`; never stamp before the comparison; `references/records.md` Workflow says so. Owner, 2026-11-10.
- Why: removing links to deleted diagrams from the Solace documents changed two routed sections and four source files in the check report, and no drawn fact [user].
- Breaks if ignored: stamping without the comparison makes real drift invisible.
- Rejected: teaching `records.py` to ignore link-only edits (it cannot tell a link edit from a fact edit in the same line) [agent].

### AK-D36: The chip row scrolls sideways when the flows do not fit at 1280px

- Decision: the shell is unchanged; `references/layout-rules.md` section Chip row says the row scrolls sideways past about five flows and tells the agent to order `flows` so the important ones come first. Owner, 2026-11-10.
- Why: the Solace UAT page with six flows hid the sixth chip off screen at 1280px [user].
- Breaks if ignored: a reader never sees the later flows' chips.
- Rejected: wrapping the chip row onto several lines (a shell layout change that AK-D13 approved otherwise) [agent].

### AK-D37: Labels and badges stayed at their spec coordinates while `route()` moved their arrow onto a port

- Lesson: two opposite arrows between the same two nodes (a request and its reply) were written 34 apart at y 466 and 500, with each label and badge placed against those lines; `route()` (AK-D24) spread both ends onto ports 20 apart, so the lines moved to 456 and 476 while labels and badges stayed where written. One label landed on its own line, the other 40 below it, and a badge sat between the two lines; on the GitLab OIDC diagrams the badge of one flow read as the other flow's [user]. The bundled example had the same defect on its "LLM calls" label and badge 3.
- Why it looked fine: the spec coordinates were correct against the spec points, and `layout_warnings()` checked labels against nodes and group borders but never against arrows, so the render gave 0 warnings.
- Fix: `attach()` in `render.py` replaces `owner()`; it matches each label and badge to the nearest segment of its flow in the spec points and moves it across by the distance routing moved that segment (y for a horizontal segment, x for a vertical one), and still returns the arrow index for `data-e`. `layout_warnings()` now warns on a label on the line of any arrow and on a badge more than 2 off its own arrow, both after the move. `references/layout-rules.md` Flows and `references/spec-format.md` Validation say so [agent].
- Breaks if ignored: any pair of arrows on one node side reads with crossed labels and badges, and nothing in the render output says so.
- Rejected: placing labels against the routed ports by hand (the agent must predict port positions, the cost AK-D24 removed for arrow ends) [agent]; a warning only (each spec still needs a manual fix after every routing change) [agent]; a `label` field on each edge (changes the spec format and every existing spec) [agent].

## Open questions

None.
