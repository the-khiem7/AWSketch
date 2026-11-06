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

SPEC_DEFAULTS = {"canvas": {"w": 1480, "h": 830}, "hint": "Tap any box or icon for what it does. On a phone, swipe the diagram sideways."}
FLOW_ID = re.compile(r"^[a-z][a-z0-9-]*$")
ICON_ID = re.compile(r"^[a-z0-9-]+$")
BAD_DASH = re.compile("[\u2013\u2014]")

# type -> (fill, stroke, dash, label colour, icon id or None, label x offset)
GROUP_STYLES = {
    "aws-cloud": ("none", "#232F3E", None, "#232F3E", "group-aws-cloud", 32),
    "region": ("none", "#00A4A6", "6 4", "#007D7F", "group-region", 32),
    "vpc": ("none", "#8C4FFF", None, "#232F3E", "group-virtual-private-cloud-vpc", 32),
    "public-subnet": ("#F2F6E8", "#7AA116", None, "#232F3E", "group-public-subnet", 32),
    "private-subnet": ("#E6F6F7", "#00A4A6", None, "#232F3E", "group-private-subnet", 32),
    "eks": ("#FFF7F0", "#ED7100", "3 3", "#232F3E", "amazon-elastic-kubernetes-service", 32),
    "ecs": ("#FFF7F0", "#ED7100", None, "#232F3E", "amazon-elastic-container-service", 32),
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


# An arrow end within this distance of a node box (or a clickable pool) belongs to it.
END_REACH = 14


def edge_ends(spec, edge):
    """Return (from, to, from_group, to_group) for an edge.

    Explicit `from` / `to` win; otherwise each end goes to the nearest node within END_REACH, then the nearest clickable pool, so an arrow that stops at a task inside a layer box names the task, not the box. An end that touches only a group boundary gets that group's label for the caption."""
    nodes = [(n["id"], (n["x"], n["y"], n["w"], node_height(n))) for n in spec.get("nodes", [])]
    pools = [(p["id"], (p["x"], p["y"], p["w"], p["h"])) for p in spec.get("pools", []) if p.get("clickable", True)]
    groups = [(g["label"], (g["x"], g["y"], g["w"], g["h"])) for g in spec.get("groups", []) if g.get("label")]

    def nearest(px, py):
        for cands in (nodes, pools):
            hits = [(rect_dist(px, py, *b), b[2] * b[3], i) for i, b in cands if rect_dist(px, py, *b) <= END_REACH]
            if hits:
                return min(hits)[2]
        return ""

    def group_at(px, py):
        hits = [(edge_dist(px, py, *b), b[2] * b[3], label) for label, b in groups if edge_dist(px, py, *b) <= END_REACH]
        return min(hits)[2] if hits else ""

    (ax, ay), (zx, zy) = edge["points"][0], edge["points"][-1]
    a = edge.get("from") or nearest(ax, ay)
    z = edge.get("to") or nearest(zx, zy)
    return a, z, "" if a else group_at(ax, ay), "" if z else group_at(zx, zy)


# Gap between an arrow end and the icon or box edge it touches, so the arrowhead stays visible.
END_GAP = 2


# Preferred distance between neighbouring arrow ends on one side of a node.
PORT_GAP = 20


def port_band(n, side):
    """Return (centre, usable length) of the side of a node that arrow ends spread along."""
    size, x, y, w = n.get("size", 44), n["x"], n["y"], n["w"]
    if side in ("left", "right"):
        return y + 4 + size / 2, size
    return x + w / 2, size if side == "top" else w - 16


def nudge_off_titles(spec, nodes, paths):
    """Slide an end segment that runs through a group title sideways, just clear of the title, while it still lands on the icon.

    A node in the first row of a group sits right under the group title, so a centred arrow into its top crosses the title; a short sideways move keeps both readable, where moving the nodes would unbalance the group."""
    titles = [group_title_box(g) for g in spec.get("groups", []) if g.get("label")]
    for ei, e in enumerate(spec.get("edges", [])):
        a, z, _, _ = edge_ends(spec, e)
        pts = paths[ei]
        if len(pts) < 3:
            continue
        for idx, nb, nid in ((0, 1, a), (-1, -2, z)):
            n = nodes.get(nid)
            if not n:
                continue
            (px, py), (qx, qy) = pts[idx], pts[nb]
            axis = 0 if px == qx else 1
            seg = (min(px, qx) - 1, min(py, qy) - 1, abs(qx - px) + 2, abs(qy - py) + 2)
            for t in titles:
                if not overlaps(seg, t):
                    continue
                size = n.get("size", 44)
                centre = n["x"] + n["w"] / 2 if axis == 0 else n["y"] + 4 + size / 2
                lo, hi = centre - size / 2 + 4, centre + size / 2 - 4
                for new in (t[axis] + t[2 + axis] + 4, t[axis] - 4):
                    if lo <= new <= hi:
                        pts[idx][axis] = pts[nb][axis] = new
                        break
                break


def route(spec):
    """Return (points per edge, warnings) with every arrow end placed on its node.

    Ends on one side of a node are its ports; ends that start at the same coordinate share a port (a fan from one trunk). The ports of a side are spread PORT_GAP apart, centred on the icon (left, right, top) or on the box (bottom), keeping the order the spec gives them; the corner next to a moved end moves with it, so segments stay axis-aligned. A straight two-point edge moves as a whole, so the node at its other end must sit level with the port. Then each end is pulled onto the drawn part of the node: the icon's side or top, or the box bottom under the label and sublines, END_GAP short so the arrowhead shows."""
    nodes = {n["id"]: n for n in spec.get("nodes", [])}
    paths = [[list(p) for p in e["points"]] for e in spec.get("edges", [])]
    groups, warns = {}, []
    for ei, e in enumerate(spec.get("edges", [])):
        a, z, _, _ = edge_ends(spec, e)
        pts = paths[ei]
        for idx, nb, nid in ((0, 1, a), (-1, -2, z)):
            if nid not in nodes:
                continue
            (px, py), (qx, qy) = pts[idx], pts[nb]
            if py == qy:
                side, coord = ("left" if qx < px else "right"), py
            else:
                side, coord = ("top" if qy < py else "bottom"), px
            groups.setdefault((nid, side), []).append((coord, ei, idx))
    locked = set()
    for (nid, side), ends in sorted(groups.items(), key=lambda kv: -len({c for c, _, _ in kv[1]})):
        coords = sorted({c for c, _, _ in ends})
        centre, length = port_band(nodes[nid], side)
        gap = PORT_GAP if len(coords) < 2 else min(PORT_GAP, (length - 4) / (len(coords) - 1))
        slot = {c: centre + (i - (len(coords) - 1) / 2) * gap for i, c in enumerate(coords)}
        axis = 1 if side in ("left", "right") else 0
        for c, ei, idx in ends:
            pts, new = paths[ei], slot[c]
            if len(pts) == 2:
                if ei in locked:
                    if abs(pts[0][axis] - new) > 1:
                        warns.append(f"edge {ei}: straight arrow cannot sit centred on both {nid!r} and its other end; move one node level with the other")
                    continue
                pts[0][axis] = pts[1][axis] = new
                locked.add(ei)
            else:
                nb = 1 if idx == 0 else -2
                pts[idx][axis] = pts[nb][axis] = new
    nudge_off_titles(spec, nodes, paths)
    for ei, e in enumerate(spec.get("edges", [])):
        a, z, _, _ = edge_ends(spec, e)
        pts = paths[ei]
        for idx, nb, nid in ((0, 1, a), (-1, -2, z)):
            n = nodes.get(nid)
            if not n:
                continue
            (px, py), (qx, qy) = pts[idx], pts[nb]
            size, x, y, w = n.get("size", 44), n["x"], n["y"], n["w"]
            cx, top = x + w / 2, y + 4
            if py == qy:
                pts[idx][0] = cx - size / 2 - END_GAP if qx < px else cx + size / 2 + END_GAP
                if not top <= py <= top + size:
                    warns.append(f"edge {ei}: end at y={py} misses the icon of {nid!r}")
            elif qy < py:
                pts[idx][1] = top - END_GAP
            else:
                pts[idx][1] = y + node_height(n) + END_GAP
    return paths, warns


def validate(spec, index):
    errors, warns = [], []
    canvas = spec["canvas"]
    flows = {}
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
        if g.get("label"):
            # Title at 13px semibold (7 units per char), subtitle at 12px (6.5) after an 8-unit gap, from the label offset.
            title_w = GROUP_STYLES[g["type"]][5] + 7 * len(g["label"]) + (8 + 6.5 * len(g["sub"]) if g.get("sub") else 0)
            if title_w > g.get("w", 0) - 6:
                warns.append(f"group {g['label']!r}: title and subtitle are wider than w={g.get('w')}")
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
            if kind == "edges":
                for end in ("from", "to"):
                    if end in e and e[end] not in ids:
                        errors.append(f"edge {i}: {end} {e[end]!r} is not a node or pool id")
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
    for e in spec.get("nodes", []) + [p for p in spec.get("pools", []) if p.get("clickable", True)]:
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
    # The shell captions a pressed chip with the item at the same index of the first ordered section.
    flow_count = len(spec.get("flows", []))
    ordered = [s for s in spec.get("sections", []) if s.get("ordered")]
    if flow_count and not ordered:
        warns.append(f"{flow_count} flow(s) but no ordered section; every chip caption will be empty")
    elif flow_count and len(ordered[0].get("items", [])) < flow_count:
        warns.append(f"first ordered section has {len(ordered[0].get('items', []))} item(s) for {flow_count} flow(s); later chips get no caption")
    texts = [spec.get("title", ""), spec.get("intro", ""), spec.get("hint", "")]
    texts += [t for e in spec.get("nodes", []) + spec.get("pools", []) for t in e.get("detail", [])]
    texts += [n.get("label", "") for n in spec.get("nodes", [])] + [t["text"] for t in spec.get("labels", []) + spec.get("texts", [])]
    texts += [s for sec in spec.get("sections", []) for it in sec.get("items", []) for s in (it.get("lead", ""), it.get("text", ""))]
    if any(BAD_DASH.search(t) for t in texts):
        warns.append("text contains an en or em dash; use the ASCII hyphen")
    if not errors:
        warns += layout_warnings(spec)
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
        out.append(f'<g class="node" data-id="{escape(p["id"])}" tabindex="0" role="button">' if p.get("clickable", True) else "<g>")
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
    paths, _ = route(spec)
    for i, e in enumerate(spec.get("edges", [])):
        fid = e["flow"]
        marks = ""
        if e.get("start"):
            marks += f' marker-start="url(#m-{fid})"'
        if e.get("end", True):
            marks += f' marker-end="url(#m-{fid})"'
        dash = f' stroke-dasharray="{dash_fit(paths[i], e.get("end", True))}"' if e.get("dashed") else ""
        a, z, ag, zg = (escape(v, quote=True) for v in edge_ends(spec, e))
        ends = f' data-from="{a}" data-to="{z}"' + (f' data-from-group="{ag}"' if ag else "") + (f' data-to-group="{zg}"' if zg else "")
        out.append(f'<path class="flow f-{fid}" data-e="{i}"{ends} d="{path_d(paths[i])}"{marks}{dash}></path>')
    for t in spec.get("labels", []):
        fid = t["flow"]
        out.append(f'<g class="flow f-{fid} fl" data-e="{owner(paths, spec, t)}"><rect class="flbox"></rect><text class="flabel c-{fid}" x="{t["x"]}" y="{t["y"]}" text-anchor="{t.get("anchor", "start")}">{escape(t["text"])}</text></g>')
    for b in spec.get("badges", []):
        fid = b["flow"]
        out.append(f'<g class="flow f-{fid} badge" data-e="{owner(paths, spec, b)}"><circle cx="{b["x"]}" cy="{b["y"]}" r="10" class="b-{fid}"></circle><text x="{b["x"]}" y="{b["y"] + 4}" text-anchor="middle" class="bt">{flows[fid][0]}</text></g>')
    markers = "".join(
        f'<marker id="m-{fid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" class="mk-{fid}"></path></marker>'
        for fid in flows
    )
    defs = "<defs>" + "".join(symbol_for(i, index) for i in used) + markers + "</defs>"
    head = f'<svg id="dia" viewBox="0 0 {cw} {ch}" xmlns="http://www.w3.org/2000/svg" role="group" aria-label="{escape(spec.get("title", "AWS diagram"), quote=True)}">'
    return head + defs + "\n".join(out) + "</svg>"


def path_d(points):
    d = f"M {num(points[0][0])} {num(points[0][1])}"
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        d += f" H {num(bx)}" if ay == by else f" V {num(by)}"
    return d


DASH = (7, 5)
# How far the back of the arrowhead sits behind the line end: marker refX 8 of 10, markerWidth 6, stroke 2.2.
HEAD_BACK = 8 * 0.6 * 2.2


def dash_fit(points, head):
    """Dash pattern stretched so the line starts with a dash at the node and a dash runs into the back of the arrowhead.

    A fixed pattern starts or ends in a gap on most lengths, which leaves the line detached from its icon or the head floating; the pattern is scaled by at most half a period to fit a whole number of periods instead."""
    period = sum(DASH)
    span = path_len(points) - (HEAD_BACK + DASH[0] / 2 if head else DASH[0])
    k = span / max(1, round(span / period)) / period
    return f"{num(round(DASH[0] * k, 2))} {num(round(DASH[1] * k, 2))}"


def path_len(points):
    return sum(abs(bx - ax) + abs(by - ay) for (ax, ay), (bx, by) in zip(points, points[1:]))


def seg_dist(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    return rect_dist(px, py, min(ax, bx), min(ay, by), abs(bx - ax), abs(by - ay))


def label_box(t):
    """Approximate box of a flow label: 12px semibold at about 6.6 units per character."""
    w = 6.6 * len(t["text"])
    x = t["x"] - {"start": 0, "middle": w / 2, "end": w}[t.get("anchor", "start")]
    return x, t["y"] - 10, w, 13


def owner(paths, spec, item):
    """Index of the arrow of the same flow nearest to a label or badge, so hovering a node keeps its arrows' labels."""
    if "text" in item:
        bx, by, bw, bh = label_box(item)
        px, py = bx + bw / 2, by + bh / 2
    else:
        px, py = item["x"], item["y"]
    best = [(min(seg_dist(px, py, a, b) for a, b in zip(p, p[1:])), i) for i, (e, p) in enumerate(zip(spec.get("edges", []), paths)) if e["flow"] == item["flow"]]
    return min(best)[1] if best else ""


def overlaps(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def node_text_boxes(n):
    """Boxes of a node's icon, label and sublines, as drawn."""
    size, x, y, w = n.get("size", 44), n["x"], n["y"], n["w"]
    cx, ly = x + w / 2, y + 4 + size + 15
    boxes = [(cx - size / 2, y + 4, size, size), (cx - 3.5 * len(n["label"]), ly - 11, 7 * len(n["label"]), 14)]
    boxes += [(cx - 3.1 * len(s), ly + 13 * (i + 1) - 10, 6.2 * len(s), 13) for i, s in enumerate(n.get("sub", []))]
    return boxes


def group_title_box(g):
    dx = GROUP_STYLES[g["type"]][5]
    # Measured in the browser: the 13px title runs about 6.4 units a character, the 12px subtitle about 5.6.
    w = dx + 6.4 * len(g.get("label", "")) + (8 + 5.6 * len(g["sub"]) if g.get("sub") else 0)
    return g["x"], g["y"], w, 24


def layout_warnings(spec):
    """Warnings for a drawing a person would redraw: crowded or stacked arrows, labels over text or borders, lines through titles."""
    paths, warns = route(spec)
    edges = spec.get("edges", [])
    segs = [(i, a, b) for i, p in enumerate(paths) for a, b in zip(p, p[1:])]
    for k, (i, a, b) in enumerate(segs):
        for j, c, d in segs[k + 1:]:
            if i == j:
                continue
            if a[1] == b[1] and c[1] == d[1] and 0 < abs(a[1] - c[1]) < 8:
                lo, hi = max(min(a[0], b[0]), min(c[0], d[0])), min(max(a[0], b[0]), max(c[0], d[0]))
            elif a[0] == b[0] and c[0] == d[0] and 0 < abs(a[0] - c[0]) < 8:
                lo, hi = max(min(a[1], b[1]), min(c[1], d[1])), min(max(a[1], b[1]), max(c[1], d[1]))
            else:
                continue
            if hi - lo > 4:
                warns.append(f"edges {i} and {j} run side by side less than 8 apart; give each its own lane")
    for g in [g for g in spec.get("groups", []) if g.get("label")]:
        tb = group_title_box(g)
        for i, a, b in segs:
            if overlaps(tb, (min(a[0], b[0]) - 1, min(a[1], b[1]) - 1, abs(b[0] - a[0]) + 2, abs(b[1] - a[1]) + 2)):
                warns.append(f"edge {i} crosses the title of group {g['label']!r}")
    for t in spec.get("labels", []):
        lb = label_box(t)
        for n in spec.get("nodes", []):
            if any(overlaps(lb, b) for b in node_text_boxes(n)):
                warns.append(f"label {t['text']!r} covers the icon or text of {n['id']!r}")
        for g in spec.get("groups", []):
            x, y, w, h = g["x"], g["y"], g["w"], g["h"]
            lines = [(x, y, w, 0.1), (x, y + h, w, 0.1), (x, y, 0.1, h), (x + w, y, 0.1, h)]
            if any(overlaps((lb[0] - 3, lb[1] - 3, lb[2] + 6, lb[3] + 6), l) for l in lines):
                warns.append(f"label {t['text']!r} sits on the border of group {g.get('label') or g['type']!r}; leave room between the arrow and the border")
            elif g.get("label") and overlaps(lb, group_title_box(g)):
                warns.append(f"label {t['text']!r} covers the title of group {g['label']!r}")
    # A node fed by three or more arrows from one side reads best centred on the nodes at their far ends.
    nodes = {n["id"]: n for n in spec.get("nodes", [])}
    for nid, n in nodes.items():
        for end, far in (("to", "from"), ("from", "to")):
            others = [nodes[f[far]] for f in (dict(zip(("from", "to"), edge_ends(spec, e)[:2])) for e in edges) if f[end] == nid and f[far] in nodes]
            others = [o for o in others if (o["x"] + o["w"] / 2 < n["x"]) == (others[0]["x"] + others[0]["w"] / 2 < n["x"])]
            ys = sorted({o["y"] + 4 + o.get("size", 44) / 2 for o in others})
            if len(ys) >= 3:
                mid = (ys[0] + ys[-1]) / 2
                cy = n["y"] + 4 + n.get("size", 44) / 2
                if abs(cy - mid) > 80:
                    warns.append(f"node {nid!r} joins {len(ys)} nodes but sits {abs(cy - mid):.0f} off their middle; centre it, or centre it with its partner hub")
    return warns


def flow_css(spec):
    flows = spec.get("flows", [])
    flow_vars = " ".join(f"--{f['id']}:{f['color']};" for f in flows)
    rules = []
    for f in flows:
        i = f["id"]
        rules.append(f"path.f-{i}{{stroke:var(--{i})}} .mk-{i}{{fill:var(--{i})}} .c-{i}{{fill:var(--{i})}} .b-{i}{{fill:var(--{i})}} .f-{i} .flbox{{stroke:var(--{i})}}")
    rules.append(",".join(f'body[data-flow="{f["id"]}"] .f-{f["id"]}' for f in flows) + "{opacity:1;stroke-width:3.2}")
    rules.append(",".join(f'body[data-flow="{f["id"]}"] .f-{f["id"]} .flbox' for f in flows) + "{opacity:1}")
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
    detail = {e["id"]: e["detail"] for e in spec.get("pools", []) + spec.get("nodes", []) if e.get("detail") and e.get("clickable", True)}
    chips = "\n    ".join(
        f'<button class="chip" id="f-{f["id"]}" data-f="{f["id"]}" aria-pressed="false" aria-label="Flow {i + 1}: {escape(f["label"], quote=True)}"><i style="background:var(--{f["id"]})"></i><span class="n">{i + 1}</span><span class="t">{escape(f["label"])}</span></button>'
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
