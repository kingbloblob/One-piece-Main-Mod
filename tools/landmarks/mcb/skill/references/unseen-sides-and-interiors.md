# Designing what the references do not show

Use when the photos cover only some sides, or when interiors, backs and roofs must be
invented. The aim is to infer the design rules from what is visible, apply them to
what is not, and flag every invention so it can be corrected.

## Contents
- Coverage matrix
- Style grammar card
- The four-sided rule
- Fiction, lost or partial structures
- Interiors
- Checking every angle
- What to ask the user

## Coverage matrix
Put this table in the dossier before building.
| Zone | Seen? (full/partial/none) | Strategy | Confidence |
|---|---|---|---|
| front facade, left, right, back, roof, courtyard, each interior level | | continue / mirror / derive from rules / invent from genre | high/med/low |
Strategies: *continue* a pattern that clearly wraps around; *mirror* when the subject is
symmetric (confirm from a plan or aerial view); *derive* from the style grammar;
*invent* from genre analogues only when nothing else exists. Mark every derived or
invented zone "design choice (not from references)".

## Style grammar card
Extract at least 8 rules from the references, then use them to generate unseen parts:
1. Palette roles and rough ratios (base, wall, trim, roof, accent).
2. Proportions: storey height, bay width, window-to-wall ratio, roof pitch, tower-to-body ratio.
3. Module list: window types, doors, balconies, arches, roof ends, trim profiles.
4. Rhythm: spacing and repetition, and where it breaks (landmarks).
5. Hierarchy: where ornament is dense (entrance, main facade) and where it thins out.
6. Symmetry: strict, loose, or none.
7. Structural logic and tech level: what holds it up, what the culture can build.
8. Function: what each part is for (this drives interiors).

## The four-sided rule
- **Hero facade:** full detail, as in the references.
- **Side facades:** same grammar and materials, about 60% of the ornament, with the same
  corner treatment wrapping 2-4 blocks round each corner.
- **Back:** a service face with the same proportions and materials, simpler but
  intentional: doors, stairs, chimneys, pipes, storage, awnings. Never a blank wall.
- **Roof:** designed, because players fly: ridge lines, chimneys, skylights, gutters,
  and the plan shape visible from above.
- **Every side:** no flat wall panel larger than about 6x6 blocks without relief, trim,
  windows or a module (`verify.flatness`).

## Fiction, lost or partial structures
Infer from the world's logic: culture, technology, climate, purpose. Pick 2-3 real
analogues (for a canal shipbuilding city: arsenals, canal houses, aqueducts) and note
which ideas are borrowed. One search for "typical interior of <analogue>" is enough.
Record these as analogue-based design choices, never as canon.

## Interiors
1. **Spend by visibility.**
   - *Hero interiors* (entrance halls, main chambers, anything seen through large doors or
     windows): designed and researched like exteriors.
   - *Standard interiors:* generated with `mcparts.bsp_rooms` (rooms and doorways that are
     always connected) and `furnish_room` (props by room kind: living, bedroom, workshop,
     kitchen, storage, library).
   - *Hidden interiors:* build only a 3-block-deep furnished space behind each window and
     door; keep the rest solid. Players cannot tell, and it costs almost nothing.
2. **Program from function.** List the spaces the building needs and what sits next to
   what (entry, living, kitchen, stairs; workshop floor, storage, office). Assign room
   kinds from that list.
3. **Continuity.** Interior floors, beams and trim come from the same palette family as the
   exterior, usually a warmer wood-heavy variant.
4. **Windows open into rooms,** not onto partition walls: place windows first, then align
   partitions to them or shift them.
5. **Headroom and light:** at least 3 blocks clear, a ceiling light per room.
6. **Multi-storey:** stack floors on the same grammar storey height and align a stair
   module between them.
7. **Verify** connectivity, headroom and window alignment with a few checks, not images.

## Checking every angle
After each stage run `render_elevations()` (one contact sheet: top, south, north, east,
west) and `verify.flatness()`. Check: silhouette reads from all four sides, corners wrap,
the back is intentional, the roof looks designed from above. Fix the config and re-export.

## What to ask the user
Give a 3-line summary of the coverage matrix and ask them to veto at most two high-impact
design choices (for example "the back faces get X"). Do not ask about every unseen zone.
