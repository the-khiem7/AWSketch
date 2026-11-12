# Spec format

A spec is one JSON object. Coordinates are SVG user units on the canvas; `x`, `y` are the top-left corner of a box. Every text is plain text and is HTML-escaped by the renderer.

## Top level

| Field | Type | Default | Meaning |
|---|---|---|---|
| `title` | string | `AWS diagram` | Page title and heading |
| `intro` | string | empty | One paragraph under the heading |
| `canvas` | `{w, h}` | `{1480, 830}` | Size of the drawing |
| `hint` | string | tap hint | Line under the drawing |
| `flows` | list | empty | As many as the picture needs; order gives the badge and chip numbers |
| `groups` | list | empty | Account, region, VPC, subnet, cluster and other frames |
| `pools` | list | empty | Layer boxes with a coloured bar and text lines |
| `nodes` | list | empty | Icon boxes |
| `edges` | list | empty | Flow arrows, and plain arrows that belong to no flow |
| `labels` | list | empty | Flow-coloured text on the sheet |
| `badges` | list | empty | Numbered flow circles |
| `trunks` | list | empty | Thick grey link, for a physical connection |
| `connectors` | list | empty | Thin dotted grey line between two boxes, no flow; an end that touches a node moves onto the node's icon edge |
| `texts` | list | empty | Free grey text |
| `sections` | list | empty | Collapsible text blocks under the drawing |

## flows

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Lowercase CSS identifier, `[a-z][a-z0-9-]*`, unique |
| `label` | yes | Chip text after the number |
| `color` | yes | Hex colour of lines, labels, badges and chip dot |

## groups

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | One of the types below |
| `x`, `y`, `w`, `h` | yes | Frame box |
| `label` | no | Bold title in the top-left corner |
| `sub` | no | Grey text after the title |
| `icon` | no | Icon id that replaces the type's default icon |

| Type | Look | Default icon |
|---|---|---|
| `aws-cloud` | dark outline | `group-aws-cloud` |
| `region` | teal dashed outline, teal title | `group-region` |
| `vpc` | purple outline | `group-virtual-private-cloud-vpc` |
| `public-subnet` | green fill and outline | `group-public-subnet` |
| `private-subnet` | teal fill and outline | `group-private-subnet` |
| `eks` | orange tint, orange dashed outline | `amazon-elastic-kubernetes-service` |
| `ecs` | orange tint, solid orange outline | `amazon-elastic-container-service` |
| `corp` | grey outline | `group-corporate-data-center` |
| `services` | light grey fill, no icon | none |
| `highlight` | light purple box with a purple outline, no title | none |

Groups are drawn in list order, so list an outer group before the groups inside it.

## pools

| Field | Required | Default | Meaning |
|---|---|---|---|
| `id` | yes | - | Unique among pools and nodes |
| `x`, `y`, `w`, `h` | yes | - | Box |
| `color` | no | `#2563EB` | Bar and title colour |
| `title` | yes | - | Title on the first row |
| `note` | no | empty | Grey text on the title row, 98 units right of `x` |
| `lines` | no | empty | Text rows, 18 units apart |
| `detail` | yes when clickable | - | `[title, aws service, text]` for the panel |
| `clickable` | no | `true` | `false` for a box that only holds other boxes |

Pools are drawn before nodes, so a node placed inside a pool sits on top of it.

## nodes

| Field | Required | Default | Meaning |
|---|---|---|---|
| `id` | yes | - | Unique among pools and nodes; the component card key |
| `icon` | yes | - | Icon id from `--list-icons` |
| `x`, `y`, `w` | yes | - | Hit box position and width |
| `h` | no | derived | Hit box height; derived as `4 + size + 15 + 13 * len(sub) + 8` |
| `size` | no | `44` | Icon size, centred at the top of the box |
| `label` | yes | - | Bold text under the icon |
| `sub` | no | empty | Smaller lines under the label, 13 units apart |
| `detail` | yes | - | `[title, aws service, text]` for the panel |

## edges

| Field | Required | Default | Meaning |
|---|---|---|---|
| `flow` | no | - | Flow id. Leave it out for a plain arrow: grey, always shown, outside the chips, the step walk and the hover highlight, and routed like any other arrow |
| `points` | yes | - | Two or more `[x, y]`; each segment horizontal or vertical |
| `dashed` | no | `false` | Dashed line |
| `start` | no | `false` | Arrowhead at the first point |
| `end` | no | `true` | Arrowhead at the last point |
| `from` | no | nearest node to the first point | Node or pool id the arrow leaves; set it when the arrow joins another line or stops at a box edge, so the step caption names the real source |
| `to` | no | nearest node to the last point | Node or pool id the arrow reaches |

The renderer moves each end onto its node: ends on one side of a node are spread 20 units apart and centred, and each end then touches the icon side, the icon top or the box bottom (layout rules, Flows). The spec gives the side, by the direction of the end segment, and the order. A dashed line's pattern is stretched slightly so it starts on a dash and a dash runs into the arrowhead.

The page walks arrows in the order they appear in `edges`, flow by flow, so list each flow's arrows in the order traffic moves; plain arrows are not walked and carry no label or badge, because a label and a badge name a flow. Without `from` / `to`, each end goes to the node box within 14 units, then a clickable pool; an end that touches only a group boundary is named after that group.

## labels, badges, trunks, connectors, texts

| List | Fields |
|---|---|
| `labels` | `flow`, `x`, `y` (text baseline), `text`, `anchor` (`start`, `middle` or `end`; default `start`) |
| `badges` | `flow`, `x`, `y` (circle centre); the number comes from the flow's position in `flows` |
| `trunks` | `points`, two or more, axis-aligned |
| `connectors` | `points`, exactly two, axis-aligned |
| `texts` | `x`, `y`, `text`, `anchor` (default `start`), `class` (`ns2` default, `ns` smaller, `nl` bold) |

## sections

| Field | Default | Meaning |
|---|---|---|
| `title` | - | Summary line |
| `open` | `false` | Expanded on load |
| `ordered` | `false` | Numbered list instead of bullets |
| `items` | - | List of `{lead, text}`; `lead` is bold and optional |

The page captions a pressed chip with the item at the same index of the ordered lists, so the first `ordered` section holds one item per flow, in `flows` order. Without it every chip caption is empty; with too few items the later chips have none. Keep other sections unordered.

## Validation

Errors stop the render and exit 1: unreadable or malformed JSON, unknown icon or group type, duplicate id, unknown flow id, a flow id that is not a CSS identifier, a segment that is not horizontal or vertical, a connector without exactly two points, two node hit boxes that overlap, a node past the canvas, an edge `from` or `to` that is not a node or pool id.

Warnings print and the page is still written: flows without an ordered section or with fewer ordered items than flows, a group title and subtitle wider than the group (7 units per title character, 6.5 per subtitle character, plus the icon offset; the layout checks use the measured 6.4 and 5.6), a label wider than 7 units per character at the node width, a subline wider than 6.2 units per character, an icon wider than its node, a pool line wider than the pool, an edge end more than 8 units from every node, pool and group edge, a clickable box without a three-part `detail`, an en or em dash in any text; and layout warnings: a straight arrow that cannot sit centred at both ends, an end that misses the icon, two arrows side by side less than 8 apart, an arrow through a group title, a label over a node's icon or text, a label on a group border or over a group title, a label on the line of any arrow, a badge more than 2 units off its own arrow, a hub that joins three or more nodes but sits more than 80 units off their middle.

Each flow label and badge belongs to the nearest segment of its flow in the spec points, and moves across with that segment when the renderer shifts the arrow onto a port: up or down for a horizontal segment, left or right for a vertical one. Hovering a node keeps the labels and badges of its arrows, and a highlighted arrow shows its label in a box.

## Minimal example

```json
{
  "title": "Three-tier web app on AWS",
  "intro": "One region, one VPC, two Availability Zones.",
  "canvas": {"w": 1000, "h": 420},
  "flows": [{"id": "web", "label": "Web requests", "color": "#2563EB"}, {"id": "data", "label": "Data", "color": "#0E8F7E"}],
  "groups": [
    {"type": "aws-cloud", "x": 150, "y": 16, "w": 834, "h": 388, "label": "AWS Cloud"},
    {"type": "vpc", "x": 164, "y": 48, "w": 806, "h": 342, "label": "VPC"}
  ],
  "nodes": [
    {"id": "users", "icon": "res-users", "x": 16, "y": 150, "w": 120, "label": "Users", "detail": ["Users", "Browser", "Reach the app over HTTPS."]},
    {"id": "alb", "icon": "res-elastic-load-balancing-application-load-balancer", "x": 200, "y": 150, "w": 130, "label": "Application LB", "sub": ["HTTPS 443"], "detail": ["Ingress", "Application Load Balancer", "Terminates TLS and spreads requests."]}
  ],
  "edges": [{"flow": "web", "points": [[110, 175], [242, 175]]}],
  "badges": [{"flow": "web", "x": 170, "y": 175}]
}
```
