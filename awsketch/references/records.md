# Records mode

Use records mode when a diagram is drawn from other documents (baseline packs, design notes, Terraform) and must stay true to them over time. Skip it for a diagram drawn once from a conversation. Records answer three questions on a later visit without re-reading the sources: where each drawn fact comes from, why the diagram is drawn this way, and what changed in the sources since the last reconcile.

## Files

The diagram gets its own folder; `records.py` finds the record set from the one `.json` in it.

```
docs/diagrams/<slug>/
  <slug>.json            spec: what is drawn
  <slug>.html            rendered page, never edited by hand
  <slug>.sources.md      where each fact comes from, with the stamp
  <slug>.decisions.md    why it is drawn this way, what is open, the one next step
```

Status is computed, not written: `records.py check` says whether the diagram still matches its sources, `stamped` in the sources frontmatter says when it last did, `## Open` says what is undecided. There are no phases.

## sources.md

Frontmatter: `diagram`, `document: "sources"`, `updated`, `stamped`. Sections, each one table:

| Section | Columns | Written by |
|---|---|---|
| `## Repositories` | Alias, Path | hand |
| `## Source map` | Area, Owning source, Entry point, Diagram nodes; excluded sources with the reason under the table | hand |
| `## Routes` | Route, Nodes, Source, Anchor, Fingerprint | hand, Fingerprint by `stamp` |
| `## Source files` | Source, Owner, Updated, Watermark | hand, Updated and Watermark by `stamp` |
| `## Watched folders` | Folder, Skip, Files | hand, Files by `stamp` |
| `## Verified` | Check, Result, Date | `render --check` row by `stamp`, the screenshot and walk rows by hand after step 6 |

- Source: `<alias>:<path relative to the repository>`.
- Nodes: comma-separated spec node ids or clickable pool ids, or `section:<exact section title>` for a section under the drawing.
- Anchor: `id:<ID>` (the heading whose first token is that identifier, such as `id:TB-D8`), `heading:<prefix>` (the first heading starting with that text), or `code:<regex>` (every matching line; write a literal pipe as `\|`). Prefer `id:` over `heading:` and never use a line number.
- Source files: list every baseline file of every watched folder, routed or not, plus each code file a route reads, so a new entry anywhere is reported.
- Watched folders: a folder whose new baseline files must be reported; Skip lists folder names to ignore, each with its reason in `decisions.md`.

## decisions.md

Frontmatter: `diagram`, `document: "decisions"`, `prefix` (2 to 4 uppercase letters, unique among the record sets and packs the diagram cites), `updated`.

| Section | Content |
|---|---|
| `## Next` | Exactly one line: the next step |
| `## Decisions` | `### <PREFIX>-D<n>: <subject>` with Decision, Why, Breaks if ignored, Rejected |
| `## Open` | `### <PREFIX>-Q<n>: <question>` with Options, Recommended, Blocks |

Get a new identifier from `records.py next-id <dir> D` or `Q`; never reuse one. When a decision settles a question, delete the question and write `Closes <PREFIX>-Q<n>.` in the decision. Record a rejected option with its reason, or it is proposed again. One paragraph is one line; ASCII hyphen only.

## Commands

| Command | Does |
|---|---|
| `records.py init <spec.json> --prefix <ABC>` | Writes both files beside the spec, with one empty route per node; never overwrites |
| `records.py lint <dir>` | Every node has a route; every route names a real node, pool or section; every source and anchor resolves; every routed source is listed; identifiers unique and filed under the right section; `## Next` one line; no en or em dash |
| `records.py check <dir>` | Lint, then DRIFT and MISSING routes, UPDATED source files, NEW entries past the watermark (routed or unrouted), CHANGED and UNROUTED watched files, and the diagram elements to re-check; exit 1 on any finding |
| `records.py routes <dir> <node>` | Where a node's facts live, with current line numbers |
| `records.py show <dir> <node>` | The current text of those sections |
| `records.py next-id <dir> <D\|Q>` | The next free identifier |
| `records.py stamp <dir>` | Refuses while lint fails; writes fingerprints, watermarks, file counts, the render row and `stamped` |

## Workflow

1. New diagram: gather facts from the sources (procedure step 1), write the spec, then `init`, fill Repositories, Source map, Routes, Source files and Watched folders, record the drawing decisions, `lint`.
2. Render and look (procedure steps 5 and 6); write the screenshot and walk rows of `## Verified`; `stamp`; `check` must exit 0.
3. Return visit: `check` before touching the spec. Exit 0: the diagram matches the sources. Exit 1:
   - DRIFT: `show` the node, compare with its `detail`, `sub` and edges, edit the spec.
   - MISSING: find the renamed or closed entry, fix the anchor, or drop the route when the fact left the diagram.
   - NEW unrouted: read it; add a route when it changes something drawn.
   - UNROUTED file: add it to Source files, or its folder to Skip with the reason in `decisions.md`.
4. Re-render, look, update `## Verified`, `stamp`, `check`.

Never stamp before every finding is reconciled: the stamp makes the drift invisible. Where sources disagree, draw what code shows, list the disagreement on the page, and leave the correction to the source's owner.

## Boundaries

- The page never carries a route, a source filename or a decision identifier: it may be published outside the repository.
- The record set owns no fact about the system drawn; a fact is corrected in its source first.
- `records.py` writes only `init` files and `stamp` cells inside the record set, and never touches a source.
