<h1 align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/hero-spin-dark.gif"><img src="assets/hero-spin.gif" alt="awsketch - AWS deployment diagrams as one interactive page. AWS service icons sit upright on three orbit rings drawn like the cloud, region and VPC frames of a diagram, with numbered flow arcs running between them." width="100%"></picture></h1>

**Ask your agent for an AWS architecture diagram and get one interactive page: official AWS icons, nested frames, numbered flows you can walk arrow by arrow, and a card that explains every component.**

<div align="center">
<p align="center"> <a href="#install"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/nav-install-dark.webp"><img src="assets/nav-install.webp" alt="Install" height="38"></picture></a> <a href="#what-you-get"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/nav-what-dark.webp"><img src="assets/nav-what.webp" alt="What you get" height="38"></picture></a> <a href="#how-it-works"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/nav-how-dark.webp"><img src="assets/nav-how.webp" alt="How it works" height="38"></picture></a> <a href="#use"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/nav-use-dark.webp"><img src="assets/nav-use.webp" alt="Use" height="38"></picture></a> <a href="#records-mode"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/nav-records-dark.webp"><img src="assets/nav-records.webp" alt="Records mode" height="38"></picture></a> <a href="#aws-icons"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/nav-aws-dark.webp"><img src="assets/nav-aws.webp" alt="AWS icons" height="38"></picture></a> </p>
</div>

<a name="install"></a>

## <picture><source media="(prefers-color-scheme: dark)" srcset="assets/icon-install-dark.webp"><img src="assets/icon-install.webp" alt="" height="30"></picture> Install

You need [Node.js](https://nodejs.org/) 22.20 or later for the installer, and [uv](https://docs.astral.sh/uv/) and a browser to use the skill. From your project's folder:

```sh
npx skills add the-khiem7/AWSketch
```

The [skills CLI](https://github.com/vercel-labs/skills) finds the awsketch skill in this repository and installs it for the coding agents it detects on your machine; Claude Code, Codex, Cursor and OpenCode are among the many it supports. By default the skill goes into the current project, so your team gets it with the repository.

<a name="what-you-get"></a>

## <picture><source media="(prefers-color-scheme: dark)" srcset="assets/icon-what-dark.webp"><img src="assets/icon-what.webp" alt="" height="30"></picture> What you get

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/product-dark.webp"><img src="assets/product.webp" alt="A page rendered by awsketch: E-commerce platform on AWS, with four numbered callouts. 1, flow chips: the Customer web chip is pressed and blue dashed arrows run from the customer through Route 53, CloudFront and WAF to the Application Load Balancer and the ECS cluster, while the other components fade back. 2, arrow walk: the previous, play and next buttons and a slider step through the flow arrow by arrow. 3, nested frames: AWS Cloud, VPC, Availability Zone, public and private subnet and ECS cluster frames. 4, component card: the load balancer is clicked and its card reads Ingress, Application Load Balancer, Spreads requests across the ECS tasks in both Availability Zones. Under the screenshot, each callout has a key card with a small glyph of the feature." width="100%"></picture>

- **The real AWS look.** Official AWS Architecture Icons on a white drawing sheet, inside nested account, region, VPC, subnet and cluster frames.
- **Flows that tell the story.** Every flow is a numbered, colour-coded chip. Press one to highlight its path; a timeline walks it arrow by arrow.
- **Answers on click.** Click any component for a card with its name, its AWS service and its role.
- **One file to share.** A single HTML page that opens in a browser. On a phone the controls move to a bottom drawer.
- **Light on dependencies.** The renderer needs only uv: it runs on the Python standard library and ships the icons, so it works offline.

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/phone-dark.webp"><img src="assets/phone.webp" alt="The same page on a phone, twice. Left, bottom drawer: the Customer web flow is being walked, and the previous, play and next buttons, the arrow slider and the numbered flow chips sit in a drawer at the bottom of the screen. Right, card on tap: the load balancer was tapped and its card, Ingress, Application Load Balancer, floats above the drawer." width="100%"></picture>

A finished example ships in [`examples/ecommerce-on-aws/`](examples/ecommerce-on-aws/): the spec and the page it renders to.

<a name="how-it-works"></a>

## <picture><source media="(prefers-color-scheme: dark)" srcset="assets/icon-how-dark.webp"><img src="assets/icon-how.webp" alt="" height="30"></picture> How it works

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/how-dark.webp"><img src="assets/how.webp" alt="The render pipeline, shown as one small diagram taking shape in four frames. Your agent writes slug.json, an excerpt of nodes with x, y and w coordinates and edges with flow points. render.py then runs four numbered steps: 1 validate icon ids, flow references and overlapping boxes, drawn as dashed boxes on a coordinate grid, each with a check mark; 2 route the arrows between the boxes, drawn as plain boxes joined by blue arrows; 3 draw the SVG with the AWS icons, where CloudFront, a load balancer, ECS and Aurora appear inside AWS Cloud and VPC frames; 4 fill the fixed page shell, a browser window with flow chips, the drawing and an arrow slider. The result is slug.html, one interactive page. Off the validate step, three outcomes: error, exit code 1; --check, no page; warning, page written." width="100%"></picture>

Your agent writes a JSON spec; the renderer validates it and fills a fixed page shell, so every diagram has the same look and behaviour. You iterate on the spec, never on the HTML.

<a name="use"></a>

## <picture><source media="(prefers-color-scheme: dark)" srcset="assets/icon-use-dark.webp"><img src="assets/icon-use.webp" alt="" height="30"></picture> Use

Ask for an AWS architecture or deployment diagram, or for a change to one you already have:

```text
Draw the AWS deployment of this repository as an awsketch page.
Add a CloudFront distribution in front of the load balancer in diagrams/shop/shop.json.
```

The agent writes `diagrams/<slug>/<slug>.json` in your repository, one folder per diagram, and renders it. `<skill-dir>` is the folder the skill was installed into, for example `.claude/skills/awsketch` or `.agents/skills/awsketch`:

```sh
uv run <skill-dir>/scripts/render.py diagrams/<slug>/<slug>.json -o diagrams/<slug>/<slug>.html
uv run <skill-dir>/scripts/render.py diagrams/<slug>/<slug>.json --check
uv run <skill-dir>/scripts/render.py --list-icons
```

Errors stop the render with exit code 1; warnings are printed and the page is still written.

<a name="records-mode"></a>

## <picture><source media="(prefers-color-scheme: dark)" srcset="assets/icon-records-dark.webp"><img src="assets/icon-records.webp" alt="" height="30"></picture> Records mode

Keep a diagram true to the documents it was drawn from. Put the spec in `docs/diagrams/<slug>/` with a sources file and a decisions file beside it, and let `records.py` tell you what changed in the sources since the last stamp.

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/sources-dark.webp"><img src="assets/sources.webp" alt="How a source document reaches the diagram. Left, a fictional design.md with three passages, each marked in its flow colour: ABC-D3 Ingress, ABC-D7 Orders database, whose second line was edited, and Queue. Threads run from each passage to awsketch's slug.sources.md routes in the centre, where each fingerprint is drawn as a strip of bars: R1 id:ABC-D3 stamped 3f9a0c71b2e4 and checked; R2 id:ABC-D7 marked DRIFT, its stamped print 9b14e2a07c5d against the print 41c7f0d8a3e9 computed now; R3 heading:Queue stamped 07cd4e9f12a6 and checked. Threads continue to the elements in slug.json, drawn in AWS Cloud, VPC and subnet frames: Load balancer in a public subnet, Orders DB in a private subnet with a red ring for the drift, Order queue outside the VPC. Caption: check re-reads every anchored passage and compares it with the fingerprint saved at the last stamp; a changed passage is reported as DRIFT on the diagram element it feeds." width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="assets/records-dark.webp"><img src="assets/records.webp" alt="The records loop for a diagram called shop, each step shown as a terminal window with its output. records.py init shop/shop.json --prefix ABC prints: wrote shop.sources.md and shop.decisions.md beside shop.json; those three files sit at the centre of the loop. When the sources change, records.py check shop lists, under Routes, DRIFT R2 id:ABC-D7 (design.md, line 12), then Source files, Watched folders, Diagram elements to re-check: orders-db: R2, and stamped 2026-11-02; 1 finding(s). records.py show shop orders-db prints the route and the passage: ABC-D7 Orders database, orders move to Aurora PostgreSQL, Multi-AZ, in the private subnets. You edit shop.json, changing the orders-db sub line from Aurora MySQL to Aurora PostgreSQL, and render again. records.py stamp shop prints stamped shop.sources.md, and R2 gets its new fingerprint 41c7f0d8a3e9." width="100%"></picture>

```sh
uv run <skill-dir>/scripts/records.py init docs/diagrams/<slug>/<slug>.json --prefix ABC
uv run <skill-dir>/scripts/records.py check docs/diagrams/<slug>
uv run <skill-dir>/scripts/records.py show docs/diagrams/<slug> <node-id>
uv run <skill-dir>/scripts/records.py stamp docs/diagrams/<slug>
```

`<skill-dir>/references/records.md` holds the file format and the workflow.

<details>
<summary><b>Updating the icons</b> - pull in a newer AWS Architecture Icons package</summary>

Download the current package from the [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) page, then:

```sh
uv run <skill-dir>/scripts/sync_aws_icons.py <Icon-package.zip>
```

New icons are added under `<skill-dir>/assets/icons/`, existing ones are never overwritten, and `index.json` and `references/icon-catalog.md` are regenerated.

</details>

<a name="aws-icons"></a>

## <picture><source media="(prefers-color-scheme: dark)" srcset="assets/icon-aws-dark.webp"><img src="assets/icon-aws.webp" alt="" height="30"></picture> AWS icons

The SVG files under `awsketch/assets/icons/` are the AWS Architecture Icons, copyright Amazon Web Services, and are included so the skill works offline from a clone. awsketch is free and non-commercial. The banner shows the icons unaltered and is not affiliated with or endorsed by AWS. Read the terms on the [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) page before reusing them outside this skill.