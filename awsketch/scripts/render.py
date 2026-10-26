#!/usr/bin/env python3
"""Render an AWS deployment diagram page from a JSON spec.

Usage:
  uv run awsketch/scripts/render.py <spec.json> -o <page.html>
  uv run awsketch/scripts/render.py <spec.json> --check
  uv run awsketch/scripts/render.py --list-icons

The spec is validated first; errors stop the render (exit 1), warnings are printed and the page is still written. The page is assets/shell.html with its slots filled; only the icons the spec uses are inlined.
"""
import argparse
import json
import re
import sys
from html import escape
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ICONS = SKILL / "assets" / "icons"
SHELL = SKILL / "assets" / "shell.html"

MAX_FLOWS = 6
SPEC_DEFAULTS = {"canvas": {"w": 1480, "h": 830}, "hint": "Tap any box or icon for what it does. On a phone, swipe the diagram sideways."}
FLOW_ID = re.compile(r"^[a-z][a-z0-9-]*$")
ICON_ID = re.compile(r"^[a-z0-9-]+$")
BAD_DASH = re.compile("[–—]")

# type -> (fill, stroke, dash, label colour, icon id or None, label x offset)
GROUP_STYLES = {
    "aws-cloud": ("none", "#232F3E", None, "#232F3E", "group-aws-cloud", 32),
    "region": ("none", "#00A4A6", "6 4", "#007D7F", "group-region", 32),
    "vpc": ("none", "#8C4FFF", None, "#232F3E", "group-virtual-private-cloud-vpc", 32),
    "public-subnet": ("#F2F6E8", "#7AA116", None, "#232F3E", "group-public-subnet", 32),
    "private-subnet": ("#E6F6F7", "#00A4A6", None, "#232F3E", "group-private-subnet", 32),
    "eks": ("#FFF7F0", "#ED7100", "3 3", "#232F3E", "amazon-elastic-kubernetes-service", 32),
    "corp": ("none", "#7D8998", None, "#232F3E", "group-corporate-data-center", 32),
    "services": ("#F7F8FA", "#C7CDD6", None, "#232F3E", None, 8),
    "highlight": ("#F7F2FF", "#8C4FFF", None, "#232F3E", None, 8),
}


def load_index():
    return json.loads((ICONS / "index.json").read_text(encoding="utf-8"))


def node_height(n):
    return n.get("h") or 4 + n.get("size", 44) + 15 + 13 * len(n.get("sub", [])) + 8


def rect_dist(px, py, x, y, w, h):
    dx = max(x - px, 0, px - (x + w))
    dy = max(y - py, 0, py - (y + h))
    return (dx * dx + dy * dy) ** 0.5


def edge_dist(px, py, x, y, w, h):
    inside = x <= px <= x + w and y <= py <= y + h
    if not inside:
        return rect_dist(px, py, x, y, w, h)
    return min(px - x, x + w - px, py - y, y + h - py)


def validate(spec, index):
    errors, warns = [], []
    canvas = spec["canvas"]
    flows = {}
    if len(spec.get("flows", [])) > MAX_FLOWS:
        errors.append(f"more than {MAX_FLOWS} flows ({len(spec['flows'])})")
    for f in spec.get("flows", []):
        if not FLOW_ID.match(f.get("id", "")):
            errors.append(f"flow id {f.get('id')!r} must match [a-z][a-z0-9-]*")
        elif f["id"] in flows:
            errors.append(f"duplicate flow id {f['id']!r}")
        flows[f.get("id")] = f
    ids = {}
    for kind in ("pools", "nodes"):
        for e in spec.get(kind, []):
            if e.get("id") in ids:
                errors.append(f"duplicate id {e.get('id')!r} ({kind[:-1]})")
            ids[e.get("id")] = kind
    for n in spec.get("nodes", []):
        if n.get("icon") not in index:
            errors.append(f"node {n.get('id')!r}: unknown icon {n.get('icon')!r}")
    for g in spec.get("groups", []):
        if g.get("type") not in GROUP_STYLES:
            errors.append(f"group {g.get('label')!r}: unknown type {g.get('type')!r}")
            continue
        icon = g.get("icon", GROUP_STYLES[g["type"]][4])
        if icon and icon not in index:
            errors.append(f"group {g.get('label')!r}: unknown icon {icon!r}")
    for kind in ("edges", "labels", "badges"):
        for e in spec.get(kind, []):
            if e.get("flow") not in flows:
                errors.append(f"{kind[:-1]}: unknown flow {e.get('flow')!r}")
    for kind in ("edges", "trunks", "connectors"):
        for i, e in enumerate(spec.get(kind, [])):
            pts = e.get("points", [])
            if len(pts) < 2:
                errors.append(f"{kind[:-1]} {i}: needs at least 2 points")
            if kind == "connectors" and len(pts) != 2:
                errors.append(f"connector {i}: needs exactly 2 points")
            for a, b in zip(pts, pts[1:]):
                if a[0] != b[0] and a[1] != b[1]:
                    errors.append(f"{kind[:-1]} {i}: segment {a}->{b} is not axis-aligned")
    boxes = []
    for n in spec.get("nodes", []):
        box = (n["x"], n["y"], n["w"], node_height(n))
        boxes.append((n["id"], box))
        if box[0] < 0 or box[1] < 0 or box[0] + box[2] > canvas["w"] or box[1] + box[3] > canvas["h"]:
            errors.append(f"node {n['id']!r} extends past the {canvas['w']}x{canvas['h']} canvas")
    for i, (ida, a) in enumerate(boxes):
        for idb, b in boxes[i + 1:]:
            if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                errors.append(f"nodes {ida!r} and {idb!r} overlap")
    for n in spec.get("nodes", []):
        size = n.get("size", 44)
        if len(n["label"]) * 7 > n["w"]:
            warns.append(f"node {n['id']!r}: label {n['label']!r} is wider than w={n['w']}")
        for s in n.get("sub", []):
            if len(s) * 6.2 > n["w"]:
                warns.append(f"node {n['id']!r}: subline {s!r} is wider than w={n['w']}")
        if size > n["w"]:
            warns.append(f"node {n['id']!r}: icon size {size} is wider than w={n['w']}")
    for p in spec.get("pools", []):
        for line in p.get("lines", []):
            if len(line) * 6.6 > p["w"] - 24:
                warns.append(f"pool {p['id']!r}: line {line!r} is wider than the pool")
    for e in spec.get("nodes", []) + spec.get("pools", []):
        d = e.get("detail")
        if not d:
            warns.append(f"{e['id']!r}: clickable but has no detail")
        elif len(d) != 3:
            warns.append(f"{e['id']!r}: detail should be [title, aws service, text]")
    near = [("rect", n["x"], n["y"], n["w"], node_height(n)) for n in spec.get("nodes", [])]
    near += [("rect", p["x"], p["y"], p["w"], p["h"]) for p in spec.get("pools", [])]
    near += [("edge", g["x"], g["y"], g["w"], g["h"]) for g in spec.get("groups", [])]
    for i, e in enumerate(spec.get("edges", [])):
        pts = e.get("points", [])
        for label, pt in (("start", pts[:1]), ("end", pts[-1:])):
            for px, py in pt:
                if near and min((rect_dist if k == "rect" else edge_dist)(px, py, *r) for k, *r in near) > 8:
                    warns.append(f"edge {i} {label} ({px},{py}) is more than 8px from any node, pool or group edge")
    texts = [spec.get("title", ""), spec.get("intro", ""), spec.get("hint", "")]
    texts += [t for e in spec.get("nodes", []) + spec.get("pools", []) for t in e.get("detail", [])]
    texts += [n.get("label", "") for n in spec.get("nodes", [])] + [t["text"] for t in spec.get("labels", []) + spec.get("texts", [])]
    texts += [s for sec in spec.get("sections", []) for it in sec.get("items", []) for s in (it.get("lead", ""), it.get("text", ""))]
    if any(BAD_DASH.search(t) for t in texts):
        warns.append("text contains an en or em dash; use the ASCII hyphen")
    return errors, warns


def num(v):
    return str(int(v)) if float(v) == int(v) else f"{v:g}"


def symbol_for(icon_id, index):
    svg = (ICONS / index[icon_id]["path"]).read_text(encoding="utf-8")
    root = re.search(r"<svg\b[^>]*>", svg)
    view_box = re.search(r'viewBox="([^"]+)"', root.group(0)).group(1)
    inner = svg[root.end():svg.rindex("</svg>")]
    return f'<symbol id="i-{icon_id}" viewBox="{view_box}">{inner}</symbol>'


def build_svg(spec, index):
    cw, ch = spec["canvas"]["w"], spec["canvas"]["h"]
    flows = {f["id"]: (i + 1, f) for i, f in enumerate(spec.get("flows", []))}
    used, out = [], []

    def use(icon, x, y, size):
        if icon not in used:
            used.append(icon)
        out.append(f'<use href="#i-{icon}" x="{num(x)}" y="{num(y)}" width="{size}" height="{size}"></use>')

    out.append(f'<rect width="{cw}" height="{ch}" fill="#FFFFFF"></rect>')
    for g in spec.get("groups", []):
        fill, stroke, dash, label_color, default_icon, label_dx = GROUP_STYLES[g["type"]]
        x, y, w, h = g["x"], g["y"], g["w"], g["h"]
        if g["type"] == "highlight":
            out.append(f'<rect class="bedbox" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"></rect>')
        else:
            dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
            out.append(f'<rect class="grp" x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash_attr}></rect>')
        icon = g.get("icon", default_icon)
        if icon:
            use(icon, x, y, 26)
        if g.get("label"):
            sub = f'<tspan class="gs" dx="8">{escape(g["sub"])}</tspan>' if g.get("sub") else ""
            out.append(f'<text class="gl" x="{x + label_dx}" y="{y + 17}" fill="{label_color}">{escape(g["label"])}{sub}</text>')
    for t in spec.get("trunks", []):
        out.append(f'<path class="trunk" d="{path_d(t["points"])}"></path>')
    for c in spec.get("connectors", []):
        (x1, y1), (x2, y2) = c["points"]
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#7D8998" stroke-width="1.2" stroke-dasharray="2 3"></line>')
    for p in spec.get("pools", []):
        x, y, w, h, color = p["x"], p["y"], p["w"], p["h"], p.get("color", "#2563EB")
        out.append(f'<g class="node" data-id="{escape(p["id"])}" tabindex="0" role="button">')
        out.append(f'<rect class="poolbox" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"></rect>')
        out.append(f'<rect x="{x}" y="{y}" width="5" height="{h}" rx="2" fill="{escape(color)}"></rect>')
        out.append(f'<text class="nl" x="{x + 16}" y="{y + 22}" fill="{escape(color)}">{escape(p["title"])}</text>')
        if p.get("note"):
            out.append(f'<text class="ns" x="{x + 98}" y="{y + 22}">{escape(p["note"])}</text>')
        for i, line in enumerate(p.get("lines", [])):
            out.append(f'<text class="ns2" x="{x + 16}" y="{y + 44 + 18 * i}">{escape(line)}</text>')
        out.append("</g>")
    for n in spec.get("nodes", []):
        x, y, w, size = n["x"], n["y"], n["w"], n.get("size", 44)
        h, cx, icon_y = node_height(n), x + w / 2, y + 4
        out.append(f'<g class="node" data-id="{escape(n["id"])}" tabindex="0" role="button">')
        out.append(f'<rect class="hit" x="{num(x)}" y="{y}" width="{w}" height="{h}" rx="6"></rect>')
        use(n["icon"], cx - size / 2, icon_y, size)
        ly = icon_y + size + 15
        out.append(f'<text class="nl" x="{num(cx)}" y="{num(ly)}" text-anchor="middle">{escape(n["label"])}</text>')
        for i, s in enumerate(n.get("sub", [])):
            out.append(f'<text class="ns" x="{num(cx)}" y="{num(ly + 13 * (i + 1))}" text-anchor="middle">{escape(s)}</text>')
        out.append("</g>")
    for t in spec.get("texts", []):
        out.append(f'<text class="{escape(t.get("class", "ns2"))}" x="{t["x"]}" y="{t["y"]}" text-anchor="{t.get("anchor", "start")}">{escape(t["text"])}</text>')
    for e in spec.get("edges", []):
        fid = e["flow"]
        marks = ""
        if e.get("start"):
            marks += f' marker-start="url(#m-{fid})"'
        if e.get("end", True):
            marks += f' marker-end="url(#m-{fid})"'
        dash = ' stroke-dasharray="7 5"' if e.get("dashed") else ""
        out.append(f'<path class="flow f-{fid}" d="{path_d(e["points"])}"{marks}{dash}></path>')
    for t in spec.get("labels", []):
        fid = t["flow"]
        out.append(f'<text class="flow f-{fid} flabel c-{fid}" x="{t["x"]}" y="{t["y"]}" text-anchor="{t.get("anchor", "start")}">{escape(t["text"])}</text>')
    for b in spec.get("badges", []):
        fid = b["flow"]
        out.append(f'<g class="flow f-{fid} badge"><circle cx="{b["x"]}" cy="{b["y"]}" r="10" class="b-{fid}"></circle><text x="{b["x"]}" y="{b["y"] + 4}" text-anchor="middle" class="bt">{flows[fid][0]}</text></g>')
    markers = "".join(
        f'<marker id="m-{fid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="mk-{fid}"></path></marker>'
        for fid in flows
    )
    defs = "<defs>" + "".join(symbol_for(i, index) for i in used) + markers + "</defs>"
    head = f'<svg id="dia" viewBox="0 0 {cw} {ch}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(spec.get("title", "AWS diagram"), quote=True)}">'
    return head + defs + "\n".join(out) + "</svg>"


def path_d(points):
    d = f"M {num(points[0][0])} {num(points[0][1])}"
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        d += f" H {num(bx)}" if ay == by else f" V {num(by)}"
    return d


def flow_css(spec):
    flows = spec.get("flows", [])
    flow_vars = " ".join(f"--{f['id']}:{f['color']};" for f in flows)
    rules = []
    for f in flows:
        i = f["id"]
        rules.append(f"path.f-{i}{{stroke:var(--{i})}} .mk-{i}{{fill:var(--{i})}} .c-{i}{{fill:var(--{i})}} .b-{i}{{fill:var(--{i})}}")
    rules.append(",".join(f'body[data-flow="{f["id"]}"] .f-{f["id"]}' for f in flows) + "{opacity:1;stroke-width:3.2}")
    return flow_vars, "\n".join(rules)


def sections_html(spec):
    parts = []
    for sec in spec.get("sections", []):
        tag = "ol" if sec.get("ordered") else "ul"
        items = "".join(
            f"<li>{'<b>' + escape(it['lead']) + '</b> ' if it.get('lead') else ''}{escape(it.get('text', ''))}</li>"
            for it in sec.get("items", [])
        )
        parts.append(f"<details{' open' if sec.get('open') else ''}><summary>{escape(sec['title'])}</summary><{tag}>{items}</{tag}></details>")
    return "\n  ".join(parts)


def render(spec, index):
    flow_vars, flow_rules = flow_css(spec)
    detail = {e["id"]: e["detail"] for e in spec.get("pools", []) + spec.get("nodes", []) if e.get("detail")}
    chips = "\n    ".join(
        f'<button class="chip" id="f-{f["id"]}" data-f="{f["id"]}" aria-pressed="false"><i style="background:var(--{f["id"]})"></i>{i + 1} · {escape(f["label"])}</button>'
        for i, f in enumerate(spec.get("flows", []))
    )
    slots = {
        "title": escape(spec.get("title", "AWS diagram")),
        "intro": escape(spec.get("intro", "")),
        "flow_vars": flow_vars,
        "flow_rules": flow_rules,
        "chips": chips,
        "svg": build_svg(spec, index),
        "hint": escape(spec["hint"]),
        "sections": sections_html(spec),
        "detail_map": json.dumps(detail, ensure_ascii=False, indent=2).replace("</", "<\\/"),
    }
    page = SHELL.read_text(encoding="utf-8")
    for key, value in slots.items():
        page = page.replace("{{" + key + "}}", value)
    return page


def main():
    ap = argparse.ArgumentParser(description="Render an AWS deployment diagram page from a JSON spec.")
    ap.add_argument("spec", nargs="?")
    ap.add_argument("-o", "--output")
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--list-icons", action="store_true")
    args = ap.parse_args()
    index = load_index()
    if args.list_icons:
        for i, e in index.items():
            print(f"{i}\t{e['kind']}\t{e['category'] or '-'}\t{e['name']}")
        return 0
    if not args.spec or not (args.check or args.output):
        ap.error("give a spec and either -o <page.html> or --check")
    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read spec: {exc}", file=sys.stderr)
        return 1
    for key, value in SPEC_DEFAULTS.items():
        spec.setdefault(key, value)
    try:
        errors, warns = validate(spec, index)
    except (KeyError, TypeError, ValueError) as exc:
        print(f"error: malformed spec ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1
    for w in warns:
        print("warning: " + w, file=sys.stderr)
    for e in errors:
        print("error: " + e, file=sys.stderr)
    if errors:
        print(f"{len(errors)} error(s), {len(warns)} warning(s)", file=sys.stderr)
        return 1
    if args.check:
        print(f"ok: 0 errors, {len(warns)} warning(s)")
        return 0
    Path(args.output).write_text(render(spec, index), encoding="utf-8")
    print(f"wrote {args.output} ({len(warns)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
