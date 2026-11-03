#!/usr/bin/env python3
"""Records for a diagram that is drawn from other documents and must stay current.

A record set sits beside the spec, in the diagram's own folder:

  <slug>.json          the spec: what is drawn
  <slug>.sources.md    where each drawn fact comes from, with the fingerprint of that source at the last stamp
  <slug>.decisions.md  why the diagram is drawn this way, what is open, the one next step

Usage:
  uv run awsketch/scripts/records.py init <spec.json> --prefix <ABC>
  uv run awsketch/scripts/records.py lint <dir|spec.json>
  uv run awsketch/scripts/records.py check <dir|spec.json>
  uv run awsketch/scripts/records.py routes <dir|spec.json> <node-id>
  uv run awsketch/scripts/records.py show <dir|spec.json> <node-id>
  uv run awsketch/scripts/records.py next-id <dir|spec.json> <D|Q>
  uv run awsketch/scripts/records.py stamp <dir|spec.json>

Anchors in the Routes table:
  id:TB-D8         the heading whose first token is that identifier
  heading:Current  the first heading whose text starts with that string
  code:<regex>     every line of the file matching the regex; write a literal pipe as \\|

A section runs from its heading to the next heading of the same or higher level, and its fingerprint covers the heading line, so a status written into an entry title counts as a change. Exit status: 0 clean, 1 findings or errors, 2 usage. Only init and stamp write, and only inside the record set.
"""
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

RENDER = Path(__file__).resolve().parent / "render.py"
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
ENTRY_ID = re.compile(r"^([A-Z]{1,4}-[A-Z]{0,2})(\d+)\b")
OWN_ID = re.compile(r"^### ([A-Z]{2,4})-([DQ])(\d+): \S")
BAD_DASH = re.compile("[\u2013\u2014]")
BASELINE_NAMES = {"introduction", "roadmap", "hallucination", "sourcecode", "useguide", "index"}


class RecordSet:
    def __init__(self, target):
        target = Path(target).resolve()
        if target.is_file():
            self.spec_path = target
        else:
            specs = sorted(target.glob("*.json"))
            if len(specs) != 1:
                sys.exit(f"records: expected one spec .json in {target}, found {len(specs)}")
            self.spec_path = specs[0]
        self.dir = self.spec_path.parent
        self.slug = self.spec_path.stem
        self.sources_path = self.dir / f"{self.slug}.sources.md"
        self.decisions_path = self.dir / f"{self.slug}.decisions.md"

    def spec(self):
        return json.loads(self.spec_path.read_text(encoding="utf-8"))

    def sources(self):
        if not self.sources_path.exists():
            sys.exit(f"records: no {self.sources_path.name}; run init first")
        return self.sources_path.read_text(encoding="utf-8").splitlines()


def cells(line):
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip()[1:-1])]


def unquote(text):
    return text.strip().strip("`").replace("\\|", "|")


def row(values):
    return "| " + " | ".join(values) + " |"


def table(lines, title):
    """Return the indexes of the data rows of the first table under `## title`, or None when the section is absent."""
    start = next((i for i, l in enumerate(lines) if l.strip() == f"## {title}"), None)
    if start is None:
        return None
    rows, header = [], False
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("## "):
            break
        if not line.startswith("|"):
            if rows or header:
                break
            continue
        if not header:
            header = True
        elif set(line.replace("|", "").strip()) <= set("-: "):
            continue
        else:
            rows.append(i)
    return rows


def repos(lines):
    return {unquote(cells(lines[i])[0]): Path(unquote(cells(lines[i])[1])) for i in table(lines, "Repositories") or []}


def resolve(repo_map, source):
    alias, _, rel = unquote(source).partition(":")
    if alias not in repo_map:
        raise KeyError(f"unknown repository alias {alias!r} in {unquote(source)}")
    return repo_map[alias] / rel


def read(path):
    try:
        return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").split("\n")
    except (FileNotFoundError, IsADirectoryError):
        return None


def section(text, anchor):
    """Return (first line number, section lines) or None."""
    kind, _, value = unquote(anchor).partition(":")
    if kind == "code":
        rx = re.compile(value)
        hits = [(n, l) for n, l in enumerate(text, 1) if rx.search(l)]
        return (hits[0][0], [l for _, l in hits]) if hits else None
    if kind not in {"id", "heading"}:
        raise ValueError(f"unknown anchor kind in {unquote(anchor)}")
    for n, line in enumerate(text):
        m = HEADING.match(line)
        if not m:
            continue
        title = m.group(2)
        if kind == "id" and title.split(":")[0].split(" ")[0] != value:
            continue
        if kind == "heading" and not title.startswith(value):
            continue
        level, end = len(m.group(1)), len(text)
        for k in range(n + 1, len(text)):
            h = HEADING.match(text[k])
            if h and len(h.group(1)) <= level:
                end = k
                break
        return n + 1, text[n:end]
    return None


def fingerprint(lines):
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(l.rstrip() for l in lines).strip())
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]


def frontmatter(text, key):
    if not text or text[0].strip() != "---":
        return "-"
    for line in text[1:20]:
        if line.strip() == "---":
            break
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return "-"


def watermark(text):
    top = {}
    for line in text:
        m = HEADING.match(line)
        e = ENTRY_ID.match(m.group(2)) if m else None
        if e:
            top[e.group(1)] = max(top.get(e.group(1), 0), int(e.group(2)))
    return " ".join(f"{k}{v}" for k, v in sorted(top.items())) or "-"


def entries_above(text, mark):
    limits = {e.group(1): int(e.group(2)) for e in (ENTRY_ID.match(t) for t in mark.split()) if e}
    found = []
    for line in text:
        m = HEADING.match(line)
        e = ENTRY_ID.match(m.group(2)) if m else None
        if e and int(e.group(2)) > limits.get(e.group(1), 0):
            found.append(m.group(2)[:110])
    return found


def routes(lines):
    out = []
    for i in table(lines, "Routes") or []:
        c = cells(lines[i])
        out.append({"row": i, "id": c[0], "nodes": [n.strip() for n in unquote(c[1]).split(",") if n.strip()],
                    "source": c[2], "anchor": c[3], "print": c[4], "cells": c})
    return out


def watched_files(folder, skip):
    return sorted(p for p in folder.rglob("*.md")
                  if p.stem.split(".")[-1] in BASELINE_NAMES
                  and not any(part in p.relative_to(folder).parts for part in skip))


def skip_list(cell):
    return [s.strip() for s in unquote(cell).split(",") if s.strip() and s.strip() != "-"]


def targets(spec):
    ids = {n["id"] for n in spec.get("nodes", [])} | {p["id"] for p in spec.get("pools", []) if p.get("clickable", True)}
    sections = {f"section:{s['title']}" for s in spec.get("sections", [])}
    return ids, sections


# ---- lint ----------------------------------------------------------------

def lint(rs):
    """Return a list of findings; an empty list means the record set is consistent with its spec."""
    bad = []
    spec, lines = rs.spec(), rs.sources()
    for name in ("Repositories", "Source map", "Routes", "Source files", "Watched folders", "Verified"):
        if table(lines, name) is None:
            bad.append(f"{rs.sources_path.name}: missing section '## {name}'")
    repo_map = repos(lines)
    ids, sections = targets(spec)
    covered, seen = set(), set()
    for r in routes(lines):
        if r["id"] in seen:
            bad.append(f"route {r['id']}: duplicate route id")
        seen.add(r["id"])
        if not r["nodes"]:
            bad.append(f"route {r['id']}: lists no node")
        for n in r["nodes"]:
            if n in ids or n in sections:
                covered.add(n)
            else:
                bad.append(f"route {r['id']}: node {n!r} is not a node, clickable pool or section title in the spec")
        if unquote(r["source"]) in {"", "-"} or unquote(r["anchor"]) in {"", "-"}:
            bad.append(f"route {r['id']}: source or anchor not filled in")
            continue
        try:
            path = resolve(repo_map, r["source"])
            text = read(path)
            if text is None:
                bad.append(f"route {r['id']}: source file not found: {path}")
            elif section(text, r["anchor"]) is None:
                bad.append(f"route {r['id']}: anchor {unquote(r['anchor'])} not found in {path.name}")
        except (KeyError, ValueError, re.error) as exc:
            bad.append(f"route {r['id']}: {exc}")
    for n in sorted(ids - covered):
        bad.append(f"node {n!r}: no route names it")
    listed = set()
    for i in table(lines, "Source files") or []:
        try:
            listed.add(resolve(repo_map, cells(lines[i])[0]).resolve())
        except KeyError as exc:
            bad.append(f"Source files: {exc}")
    for r in routes(lines):
        try:
            if resolve(repo_map, r["source"]).resolve() not in listed:
                bad.append(f"route {r['id']}: its source is missing from '## Source files'")
        except KeyError:
            pass
    bad += lint_decisions(rs)
    for path in (rs.sources_path, rs.decisions_path):
        if path.exists() and BAD_DASH.search(path.read_text(encoding="utf-8")):
            bad.append(f"{path.name}: contains an en or em dash; use the ASCII hyphen")
    return bad


def lint_decisions(rs):
    bad = []
    if not rs.decisions_path.exists():
        return [f"no {rs.decisions_path.name}"]
    text = rs.decisions_path.read_text(encoding="utf-8").splitlines()
    prefix = frontmatter(text, "prefix")
    if prefix == "-":
        bad.append(f"{rs.decisions_path.name}: frontmatter has no prefix")
    group, seen = None, set()
    for line in text:
        if line.startswith("## "):
            group = line[3:].strip()
            continue
        if not line.startswith("### "):
            continue
        m = OWN_ID.match(line)
        if not m:
            bad.append(f"{rs.decisions_path.name}: heading is not '### {prefix}-D<n>: ...' or '### {prefix}-Q<n>: ...': {line[:80]}")
            continue
        key = f"{m.group(1)}-{m.group(2)}{m.group(3)}"
        if m.group(1) != prefix:
            bad.append(f"{key}: prefix differs from frontmatter prefix {prefix}")
        if key in seen:
            bad.append(f"{key}: duplicate identifier")
        seen.add(key)
        if (m.group(2), group) not in {("D", "Decisions"), ("Q", "Open")}:
            bad.append(f"{key}: sits under '## {group}', expected '## {'Decisions' if m.group(2) == 'D' else 'Open'}'")
    if "## Next" not in text:
        bad.append(f"{rs.decisions_path.name}: missing section '## Next'")
    else:
        body = []
        for line in text[text.index("## Next") + 1:]:
            if line.startswith("## "):
                break
            if line.strip():
                body.append(line)
        if len(body) != 1:
            bad.append(f"{rs.decisions_path.name}: '## Next' must hold exactly one line")
    return bad


# ---- commands ------------------------------------------------------------

def cmd_lint(rs):
    bad = lint(rs)
    for b in bad:
        print(f"LINT {b}")
    print(f"lint: {len(bad)} finding(s)")
    return 1 if bad else 0


def cmd_check(rs):
    bad = lint(rs)
    if bad:
        for b in bad:
            print(f"LINT {b}")
        print("check stopped: fix the lint findings first")
        return 1
    lines = rs.sources()
    repo_map, cache, affected, drift = repos(lines), {}, {}, 0
    print("Routes")
    for r in routes(lines):
        path = resolve(repo_map, r["source"])
        text = cache.setdefault(path, read(path))
        hit = section(text, r["anchor"]) if text is not None else None
        state = "MISSING" if hit is None else ("DRIFT" if fingerprint(hit[1]) != r["print"] else None)
        if not state:
            continue
        drift += 1
        for n in r["nodes"]:
            affected.setdefault(n, []).append(r["id"])
        where = f"line {hit[0]}" if hit else "anchor not found"
        print(f"  {state:7} {r['id']:4} {unquote(r['anchor'])}  ({path.name}, {where})")
    if not drift:
        print("  all routes match their stamp")
    print("Source files")
    for i in table(lines, "Source files"):
        c = cells(lines[i])
        path = resolve(repo_map, c[0])
        text = cache.setdefault(path, read(path))
        if text is None:
            drift += 1
            print(f"  MISSING {unquote(c[0])}")
            continue
        if frontmatter(text, "updated") != c[2]:
            print(f"  UPDATED {path.name}: {c[2]} -> {frontmatter(text, 'updated')}")
        if c[3] != "-":
            new = entries_above(text, c[3])
            if new:
                drift += 1
                routed = {unquote(r["anchor"])[3:] for r in routes(lines)
                          if unquote(r["anchor"]).startswith("id:") and resolve(repo_map, r["source"]).resolve() == path.resolve()}
                print(f"  NEW     {path.name}: {len(new)} entries past the stamp")
                for t in new:
                    print(f"            {'routed' if t.split(':')[0].split(' ')[0] in routed else 'unrouted':8} {t}")
    print("Watched folders")
    listed = {resolve(repo_map, cells(lines[i])[0]).resolve() for i in table(lines, "Source files")}
    for i in table(lines, "Watched folders"):
        c = cells(lines[i])
        folder = resolve(repo_map, c[0])
        files = watched_files(folder, skip_list(c[1]))
        if str(len(files)) != c[2]:
            drift += 1
            print(f"  CHANGED {unquote(c[0])}: {c[2]} baseline files at stamp, {len(files)} now")
        for p in files:
            if p.resolve() not in listed:
                print(f"  UNROUTED {p.relative_to(folder)}")
    if affected:
        print("Diagram elements to re-check")
        for n in sorted(affected):
            print(f"  {n}: {', '.join(affected[n])}")
    print(f"stamped {frontmatter(lines, 'stamped')}; {drift} finding(s)")
    return 1 if drift else 0


def cmd_routes(rs, node, show):
    lines = rs.sources()
    repo_map, found = repos(lines), False
    for r in routes(lines):
        if node not in r["nodes"]:
            continue
        found = True
        path = resolve(repo_map, r["source"])
        text = read(path)
        hit = section(text, r["anchor"]) if text is not None else None
        print(f"{r['id']} {unquote(r['anchor'])} - {path} ({f'line {hit[0]}' if hit else 'NOT FOUND'})")
        if show and hit:
            print("\n".join(hit[1]).rstrip() + "\n")
    if not found:
        print(f"records: no route names {node!r}", file=sys.stderr)
        return 1
    return 0


def cmd_next_id(rs, kind):
    text = rs.decisions_path.read_text(encoding="utf-8").splitlines()
    prefix = frontmatter(text, "prefix")
    nums = [int(m.group(3)) for m in (OWN_ID.match(l) for l in text) if m and m.group(2) == kind]
    cited = [int(n) for n in re.findall(rf"\b{re.escape(prefix)}-{kind}(\d+)\b", "\n".join(text))]
    print(f"{prefix}-{kind}{max(nums + cited + [0]) + 1}")
    return 0


def render_result(rs):
    done = subprocess.run([sys.executable, str(RENDER), str(rs.spec_path), "--check"], capture_output=True, text=True)
    m = re.search(r"(\d+) error\(s\), (\d+) warning\(s\)|ok: 0 errors, (\d+) warning\(s\)", done.stdout + done.stderr)
    if not m:
        return "render --check gave no result"
    return f"{m.group(1)} errors, {m.group(2)} warnings" if m.group(1) else f"0 errors, {m.group(3)} warnings"


def cmd_stamp(rs):
    bad = lint(rs)
    if bad:
        for b in bad:
            print(f"LINT {b}")
        print("stamp refused: fix the lint findings first")
        return 1
    lines = rs.sources()
    repo_map, today = repos(lines), date.today().isoformat()
    for r in routes(lines):
        c = r["cells"]
        c[4] = fingerprint(section(read(resolve(repo_map, r["source"])), r["anchor"])[1])
        lines[r["row"]] = row(c)
    for i in table(lines, "Source files"):
        c = cells(lines[i])
        text = read(resolve(repo_map, c[0]))
        c[2], c[3] = frontmatter(text, "updated"), watermark(text)
        lines[i] = row(c)
    for i in table(lines, "Watched folders"):
        c = cells(lines[i])
        c[2] = str(len(watched_files(resolve(repo_map, c[0]), skip_list(c[1]))))
        lines[i] = row(c)
    for i in table(lines, "Verified"):
        c = cells(lines[i])
        if unquote(c[0]) == "render --check":
            c[1], c[2] = render_result(rs), today
            lines[i] = row(c)
    for k, l in enumerate(lines[:12]):
        if l.startswith("stamped:"):
            lines[k] = f'stamped: "{today}"'
        if l.startswith("updated:"):
            lines[k] = f'updated: "{today}"'
    rs.sources_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"stamped {rs.sources_path.name}")
    return 0


def cmd_init(spec_path, prefix):
    rs = RecordSet(spec_path)
    if not re.fullmatch(r"[A-Z]{2,4}", prefix or ""):
        print("records: init needs --prefix of 2 to 4 uppercase letters, unique among the record sets and packs the diagram cites", file=sys.stderr)
        return 2
    for p in (rs.sources_path, rs.decisions_path):
        if p.exists():
            print(f"records: {p.name} already exists; init never overwrites", file=sys.stderr)
            return 1
    spec, today = rs.spec(), date.today().isoformat()
    ids = [n["id"] for n in spec.get("nodes", [])] + [p["id"] for p in spec.get("pools", []) if p.get("clickable", True)]
    route_rows = "\n".join(row([f"R{k}", n, "-", "-", "-"]) for k, n in enumerate(ids, 1))
    rs.sources_path.write_text(f"""---
diagram: "{rs.slug}"
document: "sources"
updated: "{today}"
stamped: "-"
---

# {spec.get('title', rs.slug)} - Sources

Where each drawn fact comes from. Edit Route, Nodes, Source and Anchor by hand; `records.py stamp` writes the Fingerprint, Updated, Watermark, Files and render columns.

## Repositories

| Alias | Path |
|---|---|
| repo | `<absolute path>` |

## Source map

| Area | Owning source | Entry point | Diagram nodes |
|---|---|---|---|

## Routes

| Route | Nodes | Source | Anchor | Fingerprint |
|---|---|---|---|---|
{route_rows}

## Source files

| Source | Owner | Updated | Watermark |
|---|---|---|---|

## Watched folders

| Folder | Skip | Files |
|---|---|---|

## Verified

| Check | Result | Date |
|---|---|---|
| render --check | - | - |
| screenshot at 1280 | - | - |
| chips, walk and card | - | - |
""", encoding="utf-8")
    rs.decisions_path.write_text(f"""---
diagram: "{rs.slug}"
document: "decisions"
prefix: "{prefix}"
updated: "{today}"
---

# {spec.get('title', rs.slug)} - Decisions

## Next

Fill the routes in {rs.sources_path.name}, then run records.py lint.

## Decisions

## Open
""", encoding="utf-8")
    print(f"wrote {rs.sources_path.name} and {rs.decisions_path.name} beside {rs.spec_path.name}")
    return 0


def main(argv):
    cmds = {"init", "lint", "check", "routes", "show", "next-id", "stamp"}
    if len(argv) < 2 or argv[0] not in cmds:
        print(__doc__, file=sys.stderr)
        return 2
    cmd = argv[0]
    if cmd == "init":
        prefix = argv[argv.index("--prefix") + 1] if "--prefix" in argv[:-1] else None
        return cmd_init(argv[1], prefix)
    rs = RecordSet(argv[1])
    if cmd in {"routes", "show", "next-id"} and len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    if cmd == "lint":
        return cmd_lint(rs)
    if cmd == "check":
        return cmd_check(rs)
    if cmd == "stamp":
        return cmd_stamp(rs)
    if cmd == "next-id":
        return cmd_next_id(rs, argv[2]) if argv[2] in {"D", "Q"} else 2
    return cmd_routes(rs, argv[2], cmd == "show")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
