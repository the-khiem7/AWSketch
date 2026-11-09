# awsketch

An Agent Skill that draws interactive single-page AWS deployment diagrams. The agent writes a JSON spec that places every box by coordinates; a Python renderer validates it and produces one HTML page with the official AWS Architecture Icons on a white drawing sheet, nested account, region, VPC, subnet and cluster frames, numbered colour-coded flows that a chip row highlights and a timeline walks arrow by arrow, and a card that explains each component when it is clicked. On a phone the controls move to a bottom drawer.

## Requirements

- [uv](https://docs.astral.sh/uv/) to run the scripts; they use the Python standard library only.
- A browser to view the page. Fonts (IBM Plex Sans and Mono) load from Google Fonts; offline, the page falls back to system fonts.

## Layout

| Path | Content |
|---|---|
| `awsketch/SKILL.md` | Skill instructions: when to use it and the procedure |
| `awsketch/references/spec-format.md` | Every spec field, defaults and validation rules |
| `awsketch/references/layout-rules.md` | Column grid, nesting, box sizes, flow routing, palette |
| `awsketch/references/icon-catalog.md` | Generated list of icon ids |
| `awsketch/references/records.md` | Records mode: sources and decisions files kept beside a spec drawn from other documents |
| `awsketch/assets/shell.html` | Fixed page shell the renderer fills |
| `awsketch/assets/icons/` | Official AWS icons, `<kind>/<category>/<id>.svg`, indexed by `index.json` |
| `awsketch/scripts/render.py` | Spec to HTML, with `--check` and `--list-icons` |
| `awsketch/scripts/sync_aws_icons.py` | Adds icons from an AWS Architecture Icons package |
| `awsketch/scripts/records.py` | Records mode: `init`, `lint`, `check`, `routes`, `show`, `next-id`, `stamp` |

## Install

Claude Code loads skills from `.claude/skills/`. To use the skill only inside one repository without admin rights on Windows, link the skill folder with a directory junction from that repository's root:

```powershell
New-Item -ItemType Directory -Force .claude\skills | Out-Null
New-Item -ItemType Junction -Path .claude\skills\awsketch -Target <path-to-this-repo>\awsketch
```

On macOS or Linux use `ln -s <path-to-this-repo>/awsketch .claude/skills/awsketch`. The link is machine-local; do not commit it.

## Use

Ask for an AWS architecture or deployment diagram. The agent writes `diagrams/<slug>/<slug>.json` in your repository, one folder per diagram, and renders it:

```sh
uv run awsketch/scripts/render.py diagrams/<slug>/<slug>.json -o diagrams/<slug>/<slug>.html
uv run awsketch/scripts/render.py diagrams/<slug>/<slug>.json --check
uv run awsketch/scripts/render.py --list-icons
```

Errors stop the render with exit code 1; warnings are printed and the page is still written.

### Records mode

For a diagram drawn from other documents that must stay true to them, keep the spec in `docs/diagrams/<slug>/` with a sources file and a decisions file beside it, and let `records.py` tell you what changed in the sources since the last stamp:

```sh
uv run awsketch/scripts/records.py init docs/diagrams/<slug>/<slug>.json --prefix ABC
uv run awsketch/scripts/records.py check docs/diagrams/<slug>
uv run awsketch/scripts/records.py show docs/diagrams/<slug> <node-id>
uv run awsketch/scripts/records.py stamp docs/diagrams/<slug>
```

`references/records.md` holds the file format and the workflow.

## Updating the icons

Download the current package from the [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) page, then:

```sh
uv run awsketch/scripts/sync_aws_icons.py <Icon-package.zip>
```

New icons are added under `awsketch/assets/icons/`, existing ones are never overwritten, and `index.json` and `references/icon-catalog.md` are regenerated.

## AWS icons

The SVG files under `awsketch/assets/icons/` are the AWS Architecture Icons, copyright Amazon Web Services, and are included so the skill works offline from a clone. AWS publishes them for building architecture diagrams; read the terms on the [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) page before reusing them outside this skill. The maintainer has not had the redistribution terms reviewed; if AWS objects to their redistribution here, they will be removed.
