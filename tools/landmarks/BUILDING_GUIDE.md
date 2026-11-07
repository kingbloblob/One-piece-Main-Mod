# Building guide for the landmark generator

How the generator gives builds depth and detail, written down so every new module and helper follows the same
rules. Taken from the common advice of Minecraft build communities (Ponderworthy's building tips, Sportskeeda's
depth and lighting guides, the Minecraft Design wiki, Gamertag Mythras' detailing guide) and from ryan's reference
pictures in `previews/references/` (a layered fantasy castle, a sandstone throne hall with arcades, a cosy workshop
full of shelves and planters, a cathedral nave with rib vaults and hanging lamps).

The core idea in all of them: **a flat wall is the enemy**. Every surface needs something that sticks out or steps
back by one block, a change of material every few blocks, and a reason for every block to be where it is.

## 1. Depth and layering

- Walls get a **frame**: posts (logs or pillars) at the corners and every 3 to 4 blocks, with a beam ring at each
  floor. The infill sits between the posts, so the posts read as relief. In `townkit.house()` the posts and beams
  are the `post` block of the style, the infill is `wall` mixed with its `VARIANTS`.
- **Jetty** the upper floors: a timber house's second floor overhangs the first by one block, carried on a moulding
  of upside-down stairs with brackets at the posts (`JETTY` styles).
- **Set-backs**: on big buildings step the facade in and out by one or two blocks every 8 to 12 blocks, and
  break a long wall with buttresses, pilasters or a tower.
- **Foundations**: the ground course is a heavier, darker block (cobblestone, stone bricks, sandstone) with a
  skirt of slabs or stairs outside, so the house sits on the ground instead of floating on it.
- Think in three layers for any facade: frame (posts, beams, arches), infill (walls, gradients), fittings
  (windows, lamps, flower boxes, banners, trim).

## 2. Roofs

- Roofs always **overhang** the walls by at least one block. Under the eave put upside-down stairs every other
  block as brackets, and run a trim beam along the gable ends.
- Use stairs for the slope, slabs for the ridge, and full blocks under the stairs so the roof has no holes seen
  from inside. A pitched roof of 45 degrees (one up per one in) looks right at house scale; for big halls use
  a shallower slope with a step every two blocks.
- Add dormers, chimneys (up the back wall, capped with a campfire for smoke) and a different material for the
  ridge. Pagoda roofs flare at the corners with a top-half stair and a slab beyond it (`B.pagoda_roof`).

## 3. Palettes and gradients

- Pick a palette of 3 to 5 blocks per build: one main wall block, two close variants to mix in (e.g. stone bricks
  with cracked and mossy; white terracotta with calcite and diorite), one frame block, one accent.
- **Gradient** the mix: rougher and darker near the ground, cleaner higher up (`VARIANTS` + the height test in
  `house()`), or warm to cool across a facade.
- Never checkerboard. Mix at random with weights, and keep the frame a single clean block so the eye can read it.
- Concrete reads flat; terracotta, planks, bricks, tuff and deepslate read as texture. Use concrete only as an
  accent.

## 4. Windows

A window is never a single pane in a wall. The pattern in `house()`:

- two tall panes (or one on a low floor), connected to their neighbours (`finish.connections()`), set one block
  back in the frame if the wall is thick;
- a **sill** below: an upside-down stair on the ground floor, a **flower box** (`onepiece:flower_box`) upstairs;
- **shutters**: open trapdoors either side;
- a head beam above (the floor beam does this in a framed house);
- windows line up with the posts: never more than two windows between posts, never a window in a post.

## 5. Doors and entrances

- A door with a frame: beam above, a wall lamp beside it (`onepiece:wall_lamp`), a small awning of top slabs over
  the step, a slab step in front.
- Big buildings get an arched doorway (`B.arch_x`) at least 3 wide and 4 tall, flanked by pillars or
  columns with a cap.

## 5b. Signs and lettering

- Big letters use `b.text` (3x5 font, 4 blocks per letter). With `axis="x"` and `step=1` the text reads the right
  way round from the **+z (south)** side. On a face seen from -z (north), start at the right (high x) end and use
  `step=-1`. With `axis="z"`, `step=1` reads from the -x (west) side. `baratie.face_text` centres text on a long wall
  and picks the direction for you.
- A flag or a free-standing board is seen from both sides: make it two blocks thick with the text written once
  per side (see the BT flags on the Baratie), otherwise one side reads backwards.
- Letters always sit on a board or a wall; text in the air is removed by the finishing pass.

## 6. Stairs, slabs, fences and walls as detail

- Upside-down stairs are brackets, cornices, eave supports, sills and arrow-slit frames.
- Slabs break a flat top: battlements, parapets, roof ridges, table tops, shelves.
- Fences are posts, balustrades, lamp stands, table legs, railings on every drop of more than two blocks.
- Walls (cobblestone, brick) are thicker balustrades and column bases.
- All of these must **touch something**. The finishing pass (`finish.py`) removes any small group of blocks
  that floats, so attach them properly in the module instead of relying on the pass.

## 7. Interiors

- Light every room to light level 7 or more on the floor (`finish.lighting()` enforces it): chandeliers in halls
  over 6 high, hanging lanterns on chains in rooms 4 to 5 high, flush ceiling lamps in low rooms, wall lamps and
  candle sconces along walls. All of them hang on or stand on a block; nothing floats.
- Give every room a floor pattern (a border and a rug), a ceiling detail (beams every 3 blocks, a chandelier in
  the middle), and furniture against the walls with its back to a wall.
- Shelves, planters, barrels, candles and books make a room lived in. A table is stairs round a fence post with a
  carpet or pressure plate on top; chairs are stairs facing the table; beds have a bedside barrel with a candle.
- Big halls get an arcade (pillars with arches) along the sides, a raised dais at the end, banners between the
  arches, and a rib-vault or beam ceiling. Let light in from high windows too.

## 8. Checklist before saving a module

1. `python3 make.py <id> --render-only --out=DIR` and look at the cuts: dark rooms, floating stairs, bare walls?
2. Read the finish report line: many `removed floating ...` entries mean the module places things in the air;
   fix the module rather than letting the pass delete detail.
3. Every window framed, every roof overhanging, every door lit, every drop railed.
4. Place it on the test server and look at it in the real client (see `headless-client-testing`).

## 9. Placement: the build must sit *in* the ground, never on top of it

This is the first fix, because a beautiful town on a floating plate still looks wrong. It is split between the
Java site check and the generator.

### 9a. In the world (Java, `StructureSiteRules`)

What happens now: `project_start_to_heightmap: WORLD_SURFACE_WG` puts canvas y 0 at the ground height of the
**start point only** (the middle tile). The LAND score counts wet columns but never the slope: `dryMin`/`dryMax`
are measured and not used. So a site whose middle is on a rise is accepted, and every edge that is lower than the
middle floats. `beard_thin` only adds a thin, fading skirt under the pieces, which is the dirt wall in the
screenshot.

Rules:

1. **Score the slope.** LAND and COAST: add `max(0, (dryMax - dryMin) - 4) * 3` to the score, so a site with more
   than about 4 blocks of rise across the footprint loses to a flatter one in the 81-spot spiral.
2. **Set the height from the footprint, not the centre.** Once a spot is chosen, use a low percentile of the 25
   sampled dry heights (the 30th percentile works well; sinking 1 to 2 blocks into a hill looks natural,
   floating 1 block never does) as the build's y 0: `dy = p30(dryHeights) - startGround`. The terrain carving
   (`beard_thin` above the pieces, the generator's cut-back in 9b) then removes the higher ground.
3. **Never let a land build float more than 2 blocks.** If `y0 - dryMin > 6` after rule 2 the site is rejected
   (except ESSENTIAL builds, which take the best spot, and must then rely on the deep skirt in 9b).
4. `terrain_adaptation`: keep `beard_thin` for towns and open sites. For a castle or fort with a solid stone
   base use `beard_box` (it fills a whole box of ground under and around the pieces, so the plinth reads as a
   hill, as vanilla ancient cities do). `bury` is only for ruins meant to be half under ground.

### 9b. In the generator (Python)

1. **The site is not a plate.** `townkit.ground()` fills a rectangle; `pipeline.soften_edges()` then trims it
   with noise. Keep that, and also: give every land module a `relief` (see 11a) so the ground inside the site
   rises and falls by 1 to 4 blocks, and build houses on terraces (11b). A flat y 0 everywhere is what makes the
   town look stamped onto the world.
2. **Deep skirt.** The skirt in `soften_edges` reaches only 6 down. Make it 12 (`skirt=12`) and let it extend
   `reach=14` out, so that when the world is lower than the site the edge is a rolling mound, not a 4-high wall.
   Use `coarse_dirt`, `gravel`, `stone` and `moss_block` patches on slopes steeper than 1:1 (real banks erode:
   bare earth and rock show where grass can't hold).
3. **Every structure has a foundation that goes down.** Any house, wall, tower or pillar whose base is above
   the ground under it continues down as a foundation of its base block to y -8 (`foundation(b, x0, z0, x1, z1,
   y, base)`, see 15). The world fills the rest; `tiler.cull_hidden` drops whatever is buried. A post that
   ends in the air is a floating prop.
4. **Gardens, fences and paths follow the ground.** `garden()` and `path()` take `y`; read the local ground
   height (`ground_y(b, x, z)` helper, see 15) per column instead of passing one y for the whole field. A field
   on a slope is built as 2 to 3 terraced strips, each with its own y and a 1-block retaining edge of coarse dirt
   or cobblestone.

---

## 10. Silhouette and massing

Builders' first rule: the shape counts more than the blocks. Rough out the volumes before any detail, and never
let the main volume be one rectangle.

- **Compound plans.** A house is a main block plus 1 or 2 wings: L (wing on one corner), T (wing in the middle of
  a long side) or offset (two blocks overlapping by 2 to 4). Wing width is 60 to 80 % of the main block, wing
  height one floor less, or the same with a lower ridge. Pick per house from `("L", "T", "offset", "plain")` with
  weights `(4, 3, 3, 1)`.
- **Vary heights in a group.** Neighbouring houses differ by at least one floor or 2 blocks of ridge height. In
  a town, about 1 in 5 houses has 3 floors, half have 2, the rest 1 (plus a few half-storeys in the roof).
- **One tall thing per view.** Every group of 6 to 10 buildings needs a vertical accent: a tower, a chimney stack,
  a lighthouse, a dome, a tall tree. It should be at least 1.6 x the height of the roofs around it.
- **Additive pieces** that break the box (give each house 2 or more): bay window (3 wide, 1 out, on brackets or
  down to the ground, own little hip roof), porch (posts + lean-to roof), stair tower (round or square, 3 to 5
  across, taller than the house, conical or pyramid roof), balcony (1 to 2 out on upside-down stair brackets,
  fence or wall rail), lean-to shed on the back wall, an outside stair to the upper floor.
- **Set-backs on big buildings**: the upper floors step back 1 to 2 blocks every 1 to 2 floors on palaces and
  forts; a castle is a cluster of volumes (keep, towers, gatehouse, curtain wall, hall) at different heights,
  never one block.
- **Footprint size**: a single box should be odd-sized (5, 7, 9, 11) so ridges, doors and windows centre; mix
  sizes in a town (5x7 to 11x13), not one size.
- **Not too symmetrical.** A facade can be symmetric about its door, but the whole house shouldn't be: move the
  chimney to one end, add the wing on one side, a bay on the other.

---

## 11. Ground and terraforming

The official Minecraft landscaping tutorial (BlueNerd) gives the key number: **in anything organic, never more
than 7 blocks in a straight line**. That covers hill edges, paths, garden edges, banks, rows of trees. Houses can
be straight; the ground around them can't.

### 11a. Relief inside the site

- `relief(b, nx, nz, seed, amp=3, cell=18)`: raise the ground by `round(amp * noise)` blocks over the site
  (value noise like `pipeline._noise`), keep it flat (y 0) under plazas and streets, and blend over 4 blocks
  at their edges. Ground blocks below the surface: dirt to -3, then stone.
- Where the step between neighbouring columns is 2 or more, put a slope block on the low side (stair or slab of
  the ground's stone) or let it be rock: `stone`, `andesite`, `tuff`, `moss_block` in patches.
- Rocks: scatter boulders of 2 to 6 blocks (`stone`, `andesite`, `cobblestone`, `mossy_cobblestone`, a
  `stone_button`/`cobblestone_wall` on top for irregularity), half sunk into the ground, 1 per 150 to 250 m2 of
  open ground, in clusters of 1 big and 2 small.

### 11b. Terraces and retaining walls

- On relief over 2 blocks, houses sit on **terraces**: a level pad 1 to 2 blocks bigger than the house all round,
  held by a retaining wall of the base block (cobblestone, stone bricks, sandstone) on the downhill side, with
  a stair or a ramp path up. A terrace edge is never a straight 10-block line: kink it every 4 to 6 blocks, or
  put a buttress or a planter in the wall.
- Retaining walls are 1 block thicker at the foot (a stair skirt), have moss/vines on 20 % of the face, and a
  wall-block or fence rail on top where the drop is over 2.

### 11c. Paths

- Paths go from door to street to plaza, never across a whole site in one straight line. Build them as a chain
  of control points with a sideways wobble of 1 block every 4 to 6 blocks (Catmull-Rom or just a noisy offset),
  width varying by ±1 along the path.
- **Edge breakup**: the middle is `dirt_path` (or `gravel` / stone in towns), the edge cells are a random mix of
  `coarse_dirt`, `gravel`, `rooted_dirt`, `packed_mud`, with 20 to 30 % of edge cells left as grass. Stone
  streets (towns): `stone_bricks`, `cobblestone`, `andesite`, `polished_andesite`, a few `mossy_` and `cracked_`,
  edges of `cobblestone` + `gravel`.
- Where the path meets a door there is a step (slab) and a widening (a 3x3 apron).
- Paths on slopes become stairs: one stair per block of rise, with a slab landing every 3 steps.

### 11d. Planting

- Trees are not lollipops. `tree()` makes a trunk and one ellipsoid; add `tree2()` with: a trunk that leans or
  forks (1 or 2 branches of logs going out sideways from 60 % of the height), 2 to 4 overlapping leaf blobs of
  different sizes on the branch ends, a few leaf blocks removed at random from the outer shell (15 %), roots
  (1 to 3 sideways logs at the base, `rooted_dirt` round it). Heights vary 4 to 9 in one stand.
- Plant in **groups of 3 to 5 with one dominant tree**, at the edges of the site and between houses, not in a
  line and not on a grid. Leave the plazas open.
- Under and round every tree and along house walls: bushes (leaf blocks 1 to 2 high), `fern`, `short_grass`,
  `tall_grass`, flowers in clumps of one colour (3 to 7 of the same flower, not one of each), `moss_carpet`,
  `pink_petals`/`leaf_litter` under trees.
- Flower beds against house walls on the sunny (south) side: a 1-wide strip with a trapdoor or slab edge.
- Biome-specific: palms with a curved trunk (offset 1 block every 2-3 up, all one direction) and drooping fronds
  for East Blue / Alabasta / Skypiea coasts; cherry for Wano; spruce and snow for Drum; mangrove for Sabaody.

### 11e. Clutter (the "lived in" layer)

Per house 3 to 6 props outside, each touching ground or wall: barrels and crates stacked 1 to 3 (`barrel`,
`chest` under a `spruce_trapdoor`, hay bales), a woodpile (logs on their side), a cart (slabs + `oak_trapdoor`
wheels), a washing line (two fence posts joined by a row of fences on top, with banners or
`white_carpet` on trapdoors hanging from that row), pots (`decorated_pot`, `flower_pot`), a bench (stairs + trapdoor ends),
fishing gear by the sea (barrels, nets of `cobweb` only on docks, `lantern` on posts), a water trough
(`cauldron`). In towns, a well or fountain in every plaza, market stalls round it, lamp posts every 10 to 14
blocks along streets.

---

## 12. Towns that grow, not grids

Real towns grow along roads and the coast, and plots are cut from what's left. Rows of identical houses are the
look ryan hates (Nanohana today).

- **Streets first, then plots.** Lay a street graph: one main road that bends (2 to 3 bends of 10 to 30
  degrees across the town, following the relief or the shore), 2 to 4 side lanes branching at angles that are
  not 90 degrees, and alleys 1 to 2 wide. Main road 3 to 5 wide, lanes 2 to 3.
- **Plazas** where streets meet: one main plaza (12 to 20 across, not a square: a trapezoid or a shape with one
  cut corner) with the well, fountain or statue, the most important building facing it, stalls at the edges;
  1 or 2 small squares (6 to 10).
- **Plots**: walk along each street and cut plots of varying frontage (5 to 13 blocks) and depth; each house
  faces the street (door on the street side), is rotated to follow the street direction (snap to the nearest of
  the four directions, but let the plot edge be stepped), and is set back 0 to 2 blocks, different per house.
  Back gardens, sheds and trees fill what's left behind the houses.
- **Density gradient**: tight and tall (2 to 3 floors, shared walls, terraced rows of 2 to 4 *different* houses)
  near the plaza and the harbour; loose and low (1 to 2 floors, gardens, fields, a windmill) at the edge.
- **No two neighbours identical**: neighbours differ in at least two of: footprint, floors, roof type, wall
  colour, plan shape (L/T/offset).
- **The town edge** is not a fence line: it fades out into gardens, fields, single houses and trees, then the
  world's own terrain.

Pseudo-code:

```python
def town_layout(nx, nz, rnd, shore=None, plaza=(cx, cz, r)):
    main = bend_line(start, end, bends=rnd.randint(2, 3), max_turn=30, rnd=rnd)   # list of (x, z)
    lanes = [branch(main, at=t, angle=rnd.choice((-60, -45, 45, 60)), length=rnd.randint(15, 30))
             for t in pick_spread(rnd, 3)]
    roads = rasterize(main, w=2) | union(rasterize(l, w=1) for l in lanes)
    plots = []
    for seg in segments(main + lanes):
        t = 0
        while t < seg.length:
            front = rnd.choice((5, 7, 7, 9, 9, 11, 13)); depth = rnd.choice((7, 9, 11))
            setback = rnd.choice((0, 1, 1, 2))
            plots.append(Plot(seg.point(t), seg.normal, front, depth, setback))
            t += front + rnd.choice((0, 0, 1, 2, 3))      # gaps: alleys, gardens, a tree
    return roads, [p for p in plots if not overlaps(p, roads | plaza | other plots)]
```

---

## 13. Roofs: variety and shape

Section 2 covers overhangs and eaves. Add:

- **At least two roof planes meeting at an angle on every house** (a cross gable, a dormer, a wing roof, a hip
  end). A single gable over a box is the "square" look.
- **Roof types to choose from**, by style:
  - gable (East Blue cottages, Water 7 houses), **cross-gable** for L/T plans: the wing's ridge is 1 to 2 lower
    and runs into the main roof (build the main roof, then the wing roof, keep whichever block is higher in
    each cell, and put a valley of full blocks where they meet);
  - **hip** (stone halls, Marine buildings), half-hip (the gable end clipped by 2 rows);
  - **saltbox** (one long, low slope at the back over a lean-to: sheds, shacks, Syrup Village);
  - **mansard** (two slopes per side, the lower steep: Water 7 and Enies Lobby offices);
  - flat with parapet only for desert (14c) and some modern Marine builds, and then always with something on it
    (14c);
  - curved/flared for Japanese (14d) and fantasy roofs.
- **Pitch from the stairs**: a 45 degree roof (stair, stair, stair) is the default. For a **steeper** roof,
  stack two stairs/full rows per step; for a **curve** (bell or flared eave), change the pitch along the roof:
  lowest 1 to 2 rows as slabs (shallow), the middle rows stairs (45 degrees), the top rows doubled (steep).
  This reads as a curve from far away. Curves only read on roofs 9 or more wide; on small houses keep it straight.
- **Dormers**: 1 per 5 to 6 blocks of roof length, on the street side: a 3-wide box with a window and its own
  little gable roof, set into the slope, front face flush with or 1 back from the wall below.
- **Ridge and edge**: ridge of a different block (slab of a darker wood or `deepslate_tile_slab`), barge boards
  (a trim of stairs or logs) along the gable rake, a finial (fence + `lightning_rod` / lantern) at the gable
  peak on important buildings.
- **Roof colour gradient**: the lower 2 rows a shade darker, or mix 15 % of a neighbour block (`spruce` with
  `dark_oak`, `deepslate_tile` with `cobbled_deepslate`, `nether_brick` with `red_nether_brick`).
- Helper: `roof(b, plan, kind, st, full, ridge=None, curve=None)` where `plan` is a list of rectangles (main +
  wings) and `kind` is per rectangle; builds each, keeps the higher block per cell, fills valleys.

---

## 14. Wall recipes per style

Each recipe gives frame, infill, depth and fittings. "Depth" means where the wall goes in or out by a block.
All must pass the audit rule: no plain wall run longer than 5 blocks.

### 14a. Timber frame (East Blue, Loguetown, Water 7 backstreets)

- Frame: `stripped_spruce_log`/`dark_oak_log` posts every 3 to 4, beams at every floor, **diagonal braces**
  in some panels (a line of `spruce_stairs`/logs from a post foot to the beam), not all panels.
- Infill: white terracotta + calcite + diorite (or `mud_bricks`/`packed_mud` for rustic), set back 1 behind the
  frame on the ground floor where the wall is 2 thick, flush upstairs.
- Ground floor of stone (cobblestone, stone bricks) on 1 in 3 houses, timber above: the split floor reads as age.
- Jetty upstairs (exists), plus gable end jettied again under the roof.

### 14b. Stone (castles, Marine bases, Ohara, Drum)

- Pilasters/buttresses every 4 to 6 blocks, 1 out, stepping in with a stair at 2/3 height; a plinth course
  (stairs out) at the foot; a string course (slab or stair ring) at each floor; a cornice of upside-down stairs
  under the roof or parapet.
- Openings: arched (`B.arch_x`), window reveals 1 deep, a keystone or a stair lintel.
- Machicolations on towers: the parapet 1 out on a row of upside-down stair brackets with gaps between.
- Palette gradient by height (section 3) plus moss/cracked bricks near the ground and in corners, and `vine` /
  `glow_lichen` on 10 % of north faces.

### 14c. Desert / Alabasta (Nanohana, Alubarna, Yuba, Rainbase)

Alabasta in the anime: white and sand-coloured blocky houses with rounded edges, domes (white, sand, some
blue), arches and arcades, cloth awnings in bright colours, wooden beams sticking out of the walls, palm trees,
market lanes shaded by cloth. Never plain boxes with crenellations.

- **Walls**: smooth sandstone + sandstone + a few `cut_sandstone`, upper floors whiter (`white_terracotta`,
  `calcite`, `smooth_quartz` mixed in), so each house has a light gradient; 1 in 3 houses painted a pale
  colour band (orange or white terracotta). Corners softened: on houses 7 or more wide, replace the corner
  column with a stair or wall block, or set it back 1 (a chamfer).
- **Vigas**: rows of `stripped_jungle_log`/`stripped_spruce_log` sideways, sticking 1 out of the wall just
  under the roof line, every 2 blocks; on 1 in 2 houses also a row of rafters at each floor.
- **Parapet**: not crenellations on every house. Choose one of: a plain 1-high parapet of slabs; a stepped
  parapet (2 high in the middle of each side, 1 at the corners); a rounded-corner parapet (wall blocks at the
  corners); crenellations only on forts and palaces.
- **Things on the roof** (every flat roof needs 2 of these): a dome (`B.dome` r 2 to 4 over a 1-high drum with
  small windows, on 1 in 3 houses; palace domes are onion domes), a roof terrace with a cloth awning on fence
  posts, a stair-top hut (small box with a door and its own little dome), a water tank (barrel group), a
  pergola (fence posts + slabs) with vines, laundry, carpets laid out, a wind catcher (a 2x2 tower 2 to 3
  above the parapet, open on one side).
- **Openings**: arched windows (a 1-wide window with an upside-down stair each side of the head), arched
  doorways with a pointed head (two stairs meeting), `jungle_trapdoor` shutters, mashrabiya screens (a 2x3 panel
  of `jungle_trapdoor`/`spruce_fence` set in front of a window, on brackets).
- **Awnings**: cloth of coloured wool/carpet in stripes (2 colours per awning, different per shop), sloping out
  1 to 3 from the wall: top slab row at the wall, then carpets on fences or a stair row lower; between houses
  across a lane, cloths hung from wall to wall (each end touching a wall or a beam).
- **Arcades**: market streets and palace courts have a row of arches (columns of `cut_sandstone` /
  `chiseled_sandstone` caps every 3, arch heads of stairs) with a walkway behind.
- **Ground**: sand with `smooth_sandstone`/`sandstone` paving in plazas, `coarse_dirt`/`packed_mud` lanes,
  palms in groups, clay pots, rugs on the ground in front of shops.

Helper:

```python
def desert_house(b, x0, z0, w, d, floors, rnd, y=0, door="south", dome=None, color=None):
    plan = pick_plan(rnd, w, d)                  # "plain" | "L" | "offset": a list of rects
    for r, f in plan:                            # wing gets one floor less
        walls_sand(b, r, y, f, rnd, color)       # gradient sand->white, chamfered corners if w >= 7
        vigas(b, r, top_y(r, f), every=2, out=1, wood="stripped_jungle_log")
        parapet(b, r, top_y(r, f), kind=rnd.choice(("plain", "stepped", "rounded")))
    arched_windows(b, plan, y, every=3, shutters="jungle_trapdoor")
    arched_door(b, plan[0], door, y)
    awning(b, door_side(plan[0], door), y + 3, colors=rnd.sample(AWNING_COLORS, 2), out=2)
    roof_items = rnd.sample(["dome", "terrace", "stair_hut", "tank", "pergola", "wind_catcher"], 2)
    if dome or "dome" in roof_items:
        cx, cz = centre(plan[0]); b.cyl(cx, cz, 2.5, roof_y, roof_y + 1, "minecraft:smooth_sandstone")  # drum
        b.dome(cx, cz, roof_y + 2, r=rnd.choice((2, 3)), s=rnd.choice(DOME_BLOCKS), onion=False, tip=None)
    furnish_each_floor(...)
    foundation(b, plan, y, "minecraft:sandstone")  # down into the ground (9b)
```

### 14d. Japanese / Wano (Flower Capital, Ebisu, Udon, Wano houses)

- Stone base (`cobblestone`/`stone_bricks`/`tuff`) 1 to 3 high, wider than the house; the floor raised 1 above
  it with an **engawa** (veranda, 1 to 2 wide, `spruce_slab` floor on posts) along the garden side.
- Frame of dark wood (`dark_oak_log`, `stripped_dark_oak_log`) on a strict grid; panels white (`white_terracotta`
  / `birch_planks` / `white_wool`), with **shoji** as `white_stained_glass_pane` or birch trapdoors between thin
  frames.
- Roof: deep eaves (2 out), **curved and flared**: bottom row a top-half slab or upside-down stair going 1 out
  beyond the last stair, corners lifted 1 (`B.pagoda_roof` flare); tiles `deepslate_tile`, `dark_prismarine`
  or `mud_brick` for some; ridge of full blocks with end ornaments (stairs facing up). Castles and big houses:
  2 to 3 tiers, each smaller, with a hip-and-gable (irimoya) shape: hip below, small gable at the top.
- Garden: raked gravel/`gravel` bed, a pond with stepping stones, `cherry`/`azalea` trees, moss, a stone lantern
  (stone wall + `lantern` + slab), bamboo fence (`bamboo_fence`), a red torii (`red_concrete`/`crimson`
  posts and lintel, lintel overhangs 1 each side) on paths to shrines.

### 14e. Venetian / Water 7 (Water 7 town, Galley-La dock surrounds)

- Tall narrow houses (5 to 7 wide, 3 to 5 floors) shoulder to shoulder along canals, each a different pastel
  (`white_terracotta`, `light_gray`, `pink_terracotta`, `yellow_terracotta`, `orange_terracotta`,
  `light_blue_terracotta`), with a stone base (`stone_bricks`/`polished_andesite`) where the wall meets water
  and a waterline band of `mossy_stone_bricks`.
- Pointed or round **arched windows** in pairs, stone surrounds; **balconies** (1 out, `stone_brick_wall` or
  `iron_bars` rail, on upside-down stair brackets) on the main floor; awnings; flower boxes everywhere.
- Roof: red-brown tiles (`granite`/`brick` stairs or `terracotta`), low hips, chimneys with a wider top
  (Venetian funnel chimneys: 1-wide stack, 3x3 cap of stairs + slab).
- Water at the door: steps down into the canal, mooring poles (striped `log` + `white_concrete`/`red_concrete`),
  bridges arched (stairs up, slab top, wall rails), the canal edge irregular where houses project.

### 14f. Generic depth patterns (apply anywhere)

- Corner pieces: quoins (stone corner blocks alternating 1 and 2 wide), or a log post.
- Base: stair skirt + 1-block plinth (exists) + moss and grass growing over it in places.
- Under eaves: a cornice row of upside-down stairs, then the brackets.
- Windows: recessed 1 where walls are 2 thick, a stair lintel, trapdoor shutters (exists), plus an awning
  (slab or banner) over 1 in 4.
- Lamps on walls by doors (exists) and lanterns hung under balconies on a chain from the bracket.

---

## 15. Helpers to add (canvas.py / townkit.py)

| helper | what it does |
| --- | --- |
| `ground_y(b, x, z)` | highest ground block (GROUND set from pipeline) in the column, or 0 |
| `relief(b, nx, nz, seed, amp, cell, keep_flat)` | raises the site ground with smooth noise, keeps `keep_flat(x, z)` cells (streets, plazas) at 0 and blends 4 blocks round them |
| `terrace(b, rect, y, wall, rnd)` | levels a pad to y, cuts higher ground, fills lower with dirt and faces the drop with a kinked retaining wall + skirt + rail |
| `foundation(b, rect_or_plan, y, block, depth=8)` | continues the base course down to y-depth under every wall cell, so nothing hangs above lower ground |
| `plan_rects(kind, x0, z0, w, d, rnd)` | L / T / offset / plain footprints as a list of (rect, floors_delta) |
| `roof(b, rects, kinds, st, full, curve=None)` | multi-rect roof with valleys; `curve="bell"/"flare"` changes the pitch per row |
| `dormer(b, x, z, side, y, st, full, win)` | 3-wide dormer cut into a slope |
| `bay(b, x, z, side, y, floors, wall, st)` | 3-wide, 1-out bay window with brackets and its own roof |
| `awning(b, cells, y, colors, out)` | striped cloth awning on a wall or across a lane, always attached |
| `vigas(b, rect, y, every, out, wood)` | projecting beam ends |
| `parapet(b, rect, y, kind)` | plain / stepped / rounded / crenellated |
| `tree2(b, x, z, y, kind, h, rnd)` | branched tree with clustered leaves and roots |
| `palm(b, x, z, y, h, lean, rnd)` | curved trunk palm with drooping fronds |
| `boulder(b, x, z, y, r, rnd)` | half-sunk rock cluster |
| `organic_path(b, pts, w, rnd, mid, edge)` | wobbling path following `ground_y`, edge mix, stairs on slopes |
| `town_layout(...)` | streets, plazas and plots (section 12) |

All of them must call `ground_y` rather than assume y 0.

---

## 16. Ships: sails, rigging, no floating parts

`square_sail` already bellies; these rules close the gaps:

- **Sails belly with the wind, but not too much.** Real sails are elliptical, not semicircular: depth at most
  about 1/4 of the half width (`sail_belly` keeps it near that). All sails on one ship belly the **same way**
  (the wind blows from aft on a ship under way, `dir=1` toward the bow; moored ships have sails furled, see
  below). Fore-and-aft sails (jibs, lateen, spanker) curve **sideways** (to leeward, the same side for all of
  them), not forward: build them as a triangle whose cells are pushed out by `sail_depth` in z.
- **The lateen sail on dhows** (Nanohana) is a triangle hung from a long sloping yard (a line of fence or log
  from low at the bow to high aft, crossing the mast at 1/3), with the cloth curved out to one side; not a flat
  wool wall.
- **Every sail touches a yard and a mast**: head on the yard, yard on the mast (yard crosses the mast cell, or a
  fence links them), foot corners tied down by a line (fence/chain) to the rail or the next yard below.
- **Furled sails** (moored or at port): a roll of wool/`white_carpet` 1 high on top of each yard, with the yard
  still on the mast. Use furled sails on every docked ship in towns.
- **Rigging lines connect two solid blocks**: shrouds from the mast top (or the crow's nest) down to the rail on
  both sides, 3 to 4 per side, in `chain` or fence (lines are `B.line` from mast to a deadeye block on the hull
  side, which is a `spruce_trapdoor` or a log on the outside of the rail); stays from mast top to the next mast
  foot or the bowsprit. A diagonal `B.line` of fences leaves gaps on steep angles: draw it as a staircase where
  each cell touches the previous one face to face (fill the corner cell when both x and y change).
- **Chains and lanterns** hang from a block: count the chain down from its anchor; the bottom end is a lantern,
  an anchor block or a cargo net, never nothing.
- **Hull detail**: a wale (a row of stairs 1 out along the side at the deck line), gun ports in a band, a darker
  bottom (exists), a figurehead, a stern gallery with windows, anchors on the bow touching the hull.

---

## 17. Audit checklist (measurable)

Add these as checks in `make.py --render-only` (print a WARN line per failure) so a build can't pass by eye only.

1. **Site outline**: the set of ground columns (y 0 ground after `soften_edges`) is not a rectangle: its area is
   below 92 % of its bounding box, and the outline has no straight run longer than 7 blocks.
2. **Ground relief** (land builds): ground height range inside the site is at least 2 blocks, unless the module
   sets `FLAT_SITE = True` with a reason (a sea fort, a stage).
3. **Nothing floats over the ground**: for every column with a built block at its bottom, the block under it is
   solid down to the ground (`ground_y`) or to y -8. Count of failing columns = 0.
4. **Wall runs**: on every outside wall, no run of more than **5** cells of the same block in the same plane
   without a change of depth (a post, a pilaster, a window, a recess) or material. Report the longest run.
5. **Roof planes**: every house has **at least 2 roof planes meeting at an angle** (cross gable, dormer, wing,
   hip end) and an overhang of 1 or more on every side.
6. **Massing**: no two neighbouring houses (within 12 blocks) with the same footprint *and* the same floors *and*
   the same roof kind; in a town, at least 3 different heights and at least 40 % of houses with a non-rectangular
   plan.
7. **Street grid**: no more than 4 house fronts in a row on one straight line (same z or same x); setbacks
   vary.
8. **Flat roofs** (desert): each carries 2 or more roof items (dome, terrace, awning, hut, tank...).
9. **Vegetation**: at least one tree group (3+) per 400 m2 of open ground; flowers in clumps.
10. **Paths**: no straight path segment longer than 7 blocks outside streets; path edges mixed.
11. **Ships**: every sail cell's component touches a yard; every yard touches a mast; every chain/fence line
    reaches solid blocks at both ends; no flat sail (depth range across a sail at least 2).
12. **Finish report**: `removed floating` under 20 entries; fix the module if more.

---

## Sources

- Gamertag Mythras, Minecraft building tips (silhouette first, rough out shapes, layering):
  https://gamertagmythras.com/blog/minecraft/minecraft-building-tips
- Minecraft.net, "Tutorial: tips for landscaping and terraforming" (BlueNerd; never more than 7 blocks in a
  straight line in organic builds, coarse dirt erosion on banks, paths that fit the terrain):
  https://www.minecraft.net/en-us/article/tutorial--tips-for-landscaping-and-terraforming
- Minecraft.how, house design tips and medieval town building (roads first, grid vs organic, plaza and zones):
  https://minecraft.how/blog/post/minecraft-house-design-tips-1 ,
  https://minecraft.how/blog/post/build-medieval-town-minecraft , https://minecraft.how/blog/post/build-pirate-ship-minecraft
- Sportskeeda, builder tips and desert build ideas: https://sportskeeda.com/minecraft/tips-to-help-become-better-builder-minecraft ,
  https://sportskeeda.com/minecraft/7-best-minecraft-build-ideas-deserts
- AFK Gaming, 10 tips to improve a build: https://afkgaming.com/gaming/general/the-10-most-important-tips-to-improve-your-minecraft-build
- UltraServers, building tips (landscaping to blend in): https://ultraservers.com/blog/building-in-minecraft-tips-and-inspiration/
- 8bittoast, village build ideas (paths first, plaza with well and stalls): https://8bittoast.com/minecraft-build-a-village/
- Conquest Reforged and WesterosCraft gradient guides (close value/colour steps, gradients as the main detail tool):
  https://www.conquestreforged.com/guides/gradients , https://westeroscraft.com/docs/building/fundamentals/gradients
- Shockbyte and BrightChamps roof guides (gable, hip, saltbox): https://shockbyte.com/de/blog/minecraft-roof-designs ,
  https://brightchamps.com/blog/minecraft-roof/
- ExitLag, Japanese house guide (stone base, engawa, shoji, curved stepped roofs, avoid strict symmetry):
  https://www.exitlag.com/blog/minecraft-japanese-house/
- PirateMC 30-gun frigate tutorial and Planet Minecraft boat tutorial (hull shape; sails elliptical, not
  over-curved): https://piratemc.com/2020/09/09/minecraft-ship-tutorial-30-gun-frigate/ ,
  https://www.planetminecraft.com/project/tutorial-learning-how-to-build-a-boat/
- Lord of the Rings Mod wiki, building tips (shape hills as shells, then fill):
  https://lotrminecraftmod.fandom.com/wiki/Building_Tips/Building_In_Creative
- Terrain adaptation and floating structures: Lithostitched custom structures guide
  (https://www.mintlify.com/Apollounknowndev/lithostitched/guides/custom-structures), Minecraft feedback post on
  terrain adaptation limits (https://feedback.minecraft.net/hc/en-us/community/posts/39203733004685-Terrain-Adaptation-Template-Pool-Element-for-Jigsaw-structures),
  and the StructBlend / SGI Foundations mods, which fill under, cut above and slope the edges of structures
  (https://modrinth.com/project/8NXpf3Um , https://www.curseforge.com/projects/1473087)
- Project code read for this: `StructureSiteRules.java` (start-point heightmap, LAND score ignores slope),
  `pipeline.soften_edges`, `townkit.py`, `canvas.py`, ryan's screenshot of 2026-10-25.
