# Layout rules

The layout is a hand-placed column grid. Work out the columns first, then the rows, then route the flows through the gaps. All numbers are canvas units; the default canvas is 1480 by 830.

## Columns

Columns run left to right from the outside world to the innermost services. Use only the columns the architecture needs, in this order:

| Column | Holds | Typical x / width |
|---|---|---|
| External | users, partner or corporate systems, telco, inside a `corp` group when they share a network | 16 / 222 |
| Connectivity | Direct Connect, VPN, Transit Gateway, internet gateway, between the external column and the VPC | 234 to 450 |
| Public subnet | WAF, load balancers, NAT gateway, edge instances | 466 / 150 |
| Compute | cluster (`eks`) with its layer pools, or compute nodes | 630 / 336 |
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

## Flows

- Every segment is horizontal or vertical. Route a flow along a box row, turn once into a gutter, run along the gutter, and turn into the target row.
- End an arrow on the edge of the target icon or box, about 2 units short, so the arrowhead is not hidden under the box.
- Enter or leave a node sideways at the icon's middle height. A flow that has to leave or enter from below starts or ends at the bottom edge of the hit box (`y + h`, about 2 units out), never at the icon, because the label and sublines sit between the icon and that edge.
- Two flows that share a gutter run 8 to 16 units apart, never on top of each other.
- A flow that goes both ways uses `start` and `end`; a request and its reply are one edge, not two.
- Dash a flow for a path that is optional, a fallback, or crosses a trust boundary through published APIs.
- Put one badge on each flow, on its first segment, 10 units clear of any box.
- Put a label next to the segment it names, 6 units above a horizontal line or 6 units right of a vertical one.
- Use a `connector` for a box that fronts another in the same column, such as WAF above a load balancer, and a `trunk` for a physical link between the outside and AWS.

## Palette

Flow colours in order: `#2563EB` blue, `#E07A00` orange, `#7C3AED` purple, `#0E8F7E` teal, `#64748B` slate, `#DB2777` pink. Pool bar colours: `#2563EB`, `#059669`, `#7C3AED`, `#D97706`. Give each flow the colour of the pool it mostly serves when that helps the reader link them.

## Text

- Group titles are short nouns; put a qualifier in `sub`.
- A node label names the component; its sublines give a port, a size, or a role in at most about 24 characters each.
- Free `texts` explain a box in up to four lines of about 26 characters each, centred under it.
- The detail panel text is one or two sentences: what the component does in this system, not what the AWS service is in general.
