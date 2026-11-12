# Layout rules

The layout is a hand-placed column grid. Work out the columns first, then the rows, then route the flows through the gaps. All numbers are canvas units; the default canvas is 1480 by 830.

## Columns

Columns run left to right from the outside world to the innermost services. Use only the columns the architecture needs, in this order:

| Column | Holds | Typical x / width |
|---|---|---|
| External | users, partner or corporate systems, telco, inside a `corp` group when they share a network | 16 / 222 |
| Connectivity | Direct Connect, VPN, Transit Gateway, internet gateway, between the external column and the VPC | 234 to 450 |
| Public subnet | WAF, load balancers, NAT gateway, edge instances | 466 / 150 |
| Compute | cluster (`ecs` or `eks`) with its layer pools, or compute nodes | 630 / 336 |
| Private data subnet | databases, caches | 980 / 188 |
| Regional services | `services` group outside the VPC: S3, ECR, KMS, secrets, logging, AI services | 1196 / 244 |

Leave a gutter of at least 14 units between neighbouring columns; flows run in these gutters.

## Nesting

- An inner group starts 14 units right of its parent's left edge and ends 14 units before its right edge.
- The first row inside a group starts 28 units below the group's top edge, under the group title; a group nested directly in another one starts 30 units lower than its parent.
- Example chain: AWS Cloud at y 16, Region at y 48 (14 in), VPC at y 78, subnets and cluster at y 106.
- Groups in the same parent share the same top and bottom edge.
- The `highlight` group marks a pair or set of boxes that belong together (for example a private endpoint and the service behind it); give it 10 units of space around its boxes.

## Boxes

- Node width: 110 to 130 for a short label, 150 to 200 for a long one; the label must fit at about 7 units per character.
- Icon size: 44 for most nodes, 48 for a node that leads its column, 36 to 40 in a dense column, 60 for the one service the diagram is about.
- Keep at least 8 units between node hit boxes; the validator rejects any overlap.
- Pools inside a cluster: `x` 12 units inside the cluster, width the cluster width minus 24, 10 units between pools. Height: 44 plus 18 per line, plus about 12.
- Nodes inside a pool sit 28 units below the pool's top and 5 units in from its left edge, side by side, 6 units apart.
- Two nodes that sit in a vertical line in one column keep the same centre x.
- Leave about 60 units between rows (a row step of 160 for two-line nodes), so badges, labels and turns fit between them.
- Centre a node within its group: equal room left and right.
- A hub that joins three or more nodes in another column sits at their vertical middle; two hubs in a chain (for example a VPC origin above a load balancer) sit as a pair around that middle. The renderer warns when a hub sits more than 80 units off.
- Place a node in the first row of a group close beside the group title, not far from it: an arrow into its top that would cross the title is slid sideways by the renderer.

## Flows

- Every segment is horizontal or vertical. Route a flow along a box row, turn once into a gutter, run along the gutter, and turn into the target row.
- Take the shortest path: leave a node from the side that faces the target, including its top edge, instead of looping around below it.
- The renderer places every arrow end on its node; the spec only has to put each end on the right side, in the right order:
  - Ends on one side of a node are its ports, spread 20 units apart and centred on the icon (left, right, top) or the box (bottom), in the order the spec gives them. Ends at the same coordinate share one port, so a fan from one trunk stays one line.
  - A sideways end touches the icon's side, a downward end the icon's top, an upward end the box bottom under the label and sublines, each 2 units short so the arrowhead shows.
  - The corner next to a moved end moves with it. A straight two-point arrow moves as a whole, so place the node at its other end level with the port; the renderer warns when it cannot centre both ends.
  - An end segment that would cross a group title slides sideways until it clears the title by 4 units, as long as it still lands on the icon.
- On a path with three turns, put the middle segment near the start, so the last segment into the target is the long one and the arrowhead reads clearly.
- Two arrows that leave one side and turn in opposite directions (one up, one down) may turn at the same x; only arrows that turn the same way need their own lanes.
- Two flows that share a gutter run 14 to 16 units apart, never on top of each other; the renderer warns below 8.
- A flow that goes both ways uses `start` and `end`; a request and its reply are one edge, not two.
- Dash a flow for a path that is optional, a fallback, or crosses a trust boundary through published APIs.
- Put one badge on each flow, on its first segment, 10 units clear of any box.
- Put a label next to the segment it names, 6 units above a horizontal line or 6 units right of a vertical one. A horizontal label may sit centred across a vertical line, whose stroke the label's white halo covers; prefer that to widening a gutter for the label.
- Write labels and badges against the spec points, not against where the ports will land. The renderer moves each label and badge across with the segment it was written next to, so two arrows spread 20 apart onto ports keep a label above the upper one, a label below the lower one, and each badge on its own line.
- Keep a label clear of node text and group borders; leave a group's edge 14 units beyond a lane that carries a label. Do not shift whole columns to make room for one label.
- Use a `connector` for a box that fronts another in the same column, such as WAF above a load balancer, and a `trunk` for a physical link between the outside and AWS. A connector is written between the two boxes; the renderer moves each end that touches a node onto its icon edge, so the line leaves no gap.
- Give a link that carries no traffic of its own, but needs an arrowhead, an edge with no `flow`: it is a plain grey arrow, routed with ports like the others, always visible, and absent from the chips and the step walk.

## Target architecture

- A page that shows the target architecture draws planned components and planned flows as normal solid flows. A dash keeps its meaning (optional, fallback, trust boundary, replication stream); never dash or grey a flow because it is not live yet.
- List what is not live in the diagram's decisions record, so drift is found when each element goes live.

## Stand-in icons

- A component with no AWS icon (a Solace broker, Keycloak, Docker Hub) takes the closest official icon, with the real product name in the label.
- Record the stand-in and the reason in the decisions record.
- Never pick an icon that implies a managed AWS service the component is not.

## Chip row

- The slim chip bar under the title scrolls sideways when the flows do not fit; six flows with short names fit at 1100px. Order `flows` so the most important come first.

## Palette

Flow colours in order: `#2563EB` blue, `#E07A00` orange, `#7C3AED` purple, `#0E8F7E` teal, `#64748B` slate, `#DB2777` pink, then `#0891B2` cyan, `#65A30D` green, `#B45309` brown, `#BE123C` crimson. The renderer sets no limit on flows; past ten, pick colours that stay apart on a white sheet. Pool bar colours: `#2563EB`, `#059669`, `#7C3AED`, `#D97706`. Give each flow the colour of the pool it mostly serves when that helps the reader link them.

## Text

- Group titles are short nouns; put a qualifier in `sub`.
- A node label names the component; its sublines give a port, a size, or a role in at most about 24 characters each.
- Free `texts` explain a box in up to four lines of about 26 characters each, centred under it.
- The component card text is one or two sentences: what the component does in this system, not what the AWS service is in general.
