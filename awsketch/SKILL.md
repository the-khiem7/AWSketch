---
name: awsketch
description: Draw an interactive single-page AWS deployment diagram - official AWS Architecture Icons on a white drawing sheet, nested account / region / VPC / subnet / cluster boxes, numbered colour-coded flows that a chip row highlights, and a detail panel that explains each component on click. Use when the user asks for an AWS architecture diagram, an AWS deployment overview page, a picture of how a system runs on AWS, or wants an existing AWS diagram page changed. Produces an HTML file from a JSON spec through a stdlib Python renderer; not for generic flowcharts, non-AWS clouds, or data charts.
---

# awsketch

Write a JSON spec that places every box by explicit coordinates, then run the renderer. The renderer validates the spec, inlines only the icons it uses, and fills a fixed page shell, so every page has the same look and behaviour. Never hand-write the SVG or paste icon markup.

`<skill-dir>` below is the folder this SKILL.md sits in. Read `references/spec-format.md` before writing a spec and `references/layout-rules.md` before placing anything, every time; both are short and the renderer rejects what they forbid.

## Procedure

1. Gather. Collect the components, their containment (external side, AWS account, region, VPC, public and private subnets, cluster), the external actors, 2 to 6 flows (each becomes a numbered chip with its own colour), and for every component a detail triple: title, AWS service, one or two sentences on its role. Ask the user only for what is missing.
2. Icons. Run `uv run <skill-dir>/scripts/render.py --list-icons` and pick an id per component; `references/icon-catalog.md` holds the same list with categories. Prefer a 64px service icon for a service, a `res-` resource icon for a specific resource (load balancer type, NAT gateway, instance) or a generic actor (`res-users`, `res-server`). When nothing fits, use the closest icon and tell the user which one stands in.
3. Lay out. Follow `references/layout-rules.md`: columns run left to right from outside to inside, groups nest with fixed padding, and flows run orthogonally through the gutters between columns. Sketch the column x positions and widths first, then the rows.
4. Write the spec into the user's working repository, for example `diagrams/<slug>.json`, never inside `<skill-dir>`.
5. Render: `uv run <skill-dir>/scripts/render.py diagrams/<slug>.json -o diagrams/<slug>.html`. Fix every error; fix a warning unless it is a known false positive of the width estimate and the screenshot shows the text fits.
6. Look. Take a full-page screenshot at 1280px wide and check for boxes that collide, labels crossing icons or lines, arrowheads hidden under a box, and flows that cross a box instead of running in a gutter. Press a chip and click a node to confirm the highlight and the detail panel. Iterate on the spec, never on the HTML.
7. Publish only when asked: the HTML is a self-contained page (fonts from Google Fonts) and can be published as an Artifact from its repo path.

## Pitfalls

- The drawing sheet stays white in dark mode on purpose: the AWS icon colours are designed for a white background.
- Flow labels carry a white halo (`paint-order: stroke`); place them over empty sheet next to their line, not on top of an icon.
- Every edge segment must be horizontal or vertical. A diagonal is an error.
- The sheet keeps a minimum width of 1100px and scrolls sideways on a phone. Do not shrink the canvas to fit a phone.
- Node ids are the keys of the detail panel; a node without `detail` is clickable but shows nothing, which the validator warns about.
- A layer box that only groups other boxes takes `"clickable": false`.
- Use the ASCII hyphen in every text; the validator warns on an en or em dash.
- To add icons from a newer AWS package, run `uv run <skill-dir>/scripts/sync_aws_icons.py <package.zip>`; existing icons are never overwritten.
