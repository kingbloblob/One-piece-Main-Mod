# Interior detail: purposeful, sporadic, varied

"Detail" means each object has a reason to be there and no two nearby things are alike.
Repeating one decorative block along a surface is the opposite of detail.

## Contents
- Large rooms (longer side over 17 blocks)
- Hard rules
- Where detail goes
- Banned patterns
- Required workflow
- Examples

## Large rooms (longer side over 17 blocks)
A room whose longer side is over 17 blocks gets extra detail so the middle never feels
empty. `furnish_room(..., large_room=17)` does this automatically:
- The floor is divided into about 8x8 zones (6x6 in very big halls). Each zone gets its own
  vignette: seating group on a rug, counter island, free-standing shelf unit, workbench,
  storage stack or pedestal. `PropTracker` makes neighbouring zones differ.
- A few zones are left empty on purpose (about 10-20%), so the room still breathes.
- Bigger budgets: more secondary props (up to 22), accents (up to 2 of each type),
  story props, rugs, and lights (several lanterns, some chandeliers when the ceiling is 5+
  high). Halls over 26 blocks also get free-standing pillars.
- Spam rules still apply, scaled: no more than 3 of one prop type (2 chests) per room,
  and the same prop never within 2 blocks of its twin.
- `audit_props` warns when under 60% of the room's 6x6 patches hold anything or props
  per 100 cells fall below 4.
`bsp_rooms` splits anything bigger than `max_room` (default 12). For a grand hall pass a larger
`max_room` or skip splitting and call `furnish_room` on the hall's rectangle directly. A hero
hall should also get hand-made vignettes on top of the generated base.

## Hard rules
1. **Hierarchy:** one anchor (the room's reason to exist), a few secondary pieces, then
   at most two small accents. Never more than that per room.
2. **No repeats nearby.** The same non-bulk prop never appears twice within 3 blocks, and
   a room has at most 2 of any non-bulk prop. Only bookshelves, barrels and hay bales may
   repeat (up to 3), and not in a row on a table.
3. **Novelty props are limited per building:** brewing stand 1, jukebox 1, cartography /
   fletching table 1, stonecutter 1, blast furnace 1, cauldron 2. **Cake: never** (it needs a
   full solid block under it and breaks when placed on a slab or plate).
4. **Accents sit on something.** A candle, potted plant or lantern goes on top of a solid
   prop (barrel, crafting table, chest) or on the floor next to one; never floating, never
   in a line.
5. **Negative space.** Leave stretches of wall and floor empty on purpose. Props must not
   touch each other and never block a doorway or walkway. Target roughly 5-15 props
   per 100 floor cells (bulk props count half).
6. **Asymmetry.** Do not mirror one side of a room onto the other. Light sources vary
   (hanging lantern in an off-centre spot, candle clusters, floor lanterns).
7. **Variation across rooms.** Use one `PropTracker` per building so rarely used props
   are preferred; vary rug colours and plant types; give a room at most one unique
   "story" prop (something that says what happened here).
8. **Purpose first.** A workshop has tools and a counter, a bedroom has a bed and
   storage. Never put a function-less prop (brewing stand in a bedroom) just to add detail.

## Where detail goes
Spend detail on places people look: doorways, the focal wall, areas around windows,
and the area around the anchor piece. Plain floor and the middle of rooms stay calm.

## Banned patterns
- The same two props alternating along a surface (the brewing-stand-and-cake problem).
- A prop on every wall cell, or at every Nth block.
- Perfect left/right mirroring of furniture.
- Items facing the wall, floating items, items that block doors.
- Filling every table. A table gets nothing, or one thing.

## Required workflow
1. Make a `PropTracker(seed)` per building.
2. Generate rooms with `bsp_rooms`, then call `furnish_room(..., tracker=tracker)` for each.
3. Run `audit_props(b, rooms, y, height)` and treat FAIL lines as bugs: fix the config or
   re-seed the room, then re-run until it prints PASS.
4. Hero rooms get hand-made vignettes on top of the generated base (see below), and are
   audited too.
5. Write unusual hand-placed details as a short list in the dossier so repeats can be
   tracked.

## Examples
- Good vignette: a barrel with one candle on it, a chest beside it, a potted fern two
  blocks away, bare wall beyond.
- Good workshop: anvil and grindstone apart, a counter with a single lantern, a stack of
  barrels in one corner, nothing on the opposite wall.
- Bad: brewing stand, cake, brewing stand, cake along a table.
