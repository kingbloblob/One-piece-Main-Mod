# Technique card: underwater birdcage pavilion on a reef (studied from a user-supplied model)

Source: "Idyllic Cage" by Dr_Bond (https://sketchfab.com/3d-models/idyllic-cage-c347e430abb24071aeba66a120ca5ac4),
CC-BY-4.0, supplied by the user and read with `scripts/mesh_blocks.py` (exact block names from a
Mineways export). Measurements and methods for learning; do not recreate the model. If a build based
on these ideas is shared, credit the author as the licence requires.
**Measured** = read from the block grid. **Inferred** = judged from shapes or colours.
Heights are blocks above the seabed base (the cage base is y0).

## Contents
- Scene layout
- The cage: height system
- The cage: bars, arches and shell
- Centrepiece and interior
- Seabed, kelp and coral
- Creatures
- Palette roles
- Reusable recipe (mcreef parts)
- Scaling rules
- Adapting to an underwater city in a bubble (e.g. Fish-Man Island)

## Scene layout (measured)
- Scene 309 x 303 blocks, 256 tall (the whole build height). Single focal object in the middle:
  the cage, radius 67 (diameter 134, so the cage covers ~43% of the scene width).
- Everything else is a ring of reef around it: kelp forests on one side (the tall dense half), coral
  heads, grey rock arches, winding sand/glass "rivers", and about 510 free-floating creatures.
- The scene is framed by tall kelp at the edges, which hides the square boundary of the plot.

## The cage: height system (measured, H = 251 from base to finial)
| Element | Height (fraction of H) | Radius (fraction of R=67) |
|---|---|---|
| Plinth + sea-lantern rim | 0 | 1.03 |
| Vertical bars | 0 to 0.58 | 1.00 |
| Collar rings (2-3 layers, stairs + slabs, project 1) | 0.30 and 0.37 | 1.00 |
| Arch springing (impost collar) | 0.58 | 1.00 |
| Arch crown + cornice ring | 0.66 | 1.00 |
| Lower dome, glass with frame ribs, flaring inward | 0.66 to 0.81 | 1.00 to 0.78 |
| Ledge: shell steps sharply inward | 0.81 to 0.82 | 0.78 to 0.66 |
| Short drum + band | 0.82 to 0.89 | 0.66 to 0.59 |
| Upper dome | 0.89 to 0.98 | 0.59 to 0 |
| Iron finial with a hanging ring (the "hook" of a birdcage) | 0.98 to 1.0 | ~0.1 |
Ratio: total height : diameter = 1.9 : 1. The straight barred wall is 2/3 of the height; the
roof (two stacked domes) is the last third. The double-dome with a ledge is what makes it read
as a birdcage rather than a gazebo.

## The cage: bars, arches and shell (measured)
- 16 bars at 22.5 degree spacing; bars about 2 blocks thick, thickening slightly near the base.
- Bay width along the circle = 2*pi*67/16 = 26 blocks; clear opening about 21-22.
- Each bay ends in a round arch: springs at 0.58 H, crown at 0.66 H (rise ~20 blocks over a ~22 span,
  so slightly taller than a semicircle). Spandrels above the arches are glass up to the cornice.
- Walls below the arches are OPEN (bars only). Only the spandrels and the domes are glazed.
- Dome glass is light grey stained glass with quartz ribs continuing each bar up to the top.
- About half of all cage faces sit on stairs and slabs: collars and cornices are stair+slab bands,
  never single full-block rings.

## Centrepiece and interior (measured from sections; sizes approximate)
- A leaning, lumpy rock spire (grey wool / stone) wrapped in coral rises from the cage floor to about
  0.33 H and carries a small round gazebo with a gold rim and a tiny spire (about 45 wide incl. coral).
- A chandelier hangs from the top on a chain: about 47 wide, its body from ~0.66 H to ~0.97 H.
  So: chandelier width ~0.35 R, drop ~0.3 H.
- Small props float or stand inside (a harp-like frame, lanterns, fish); the interior is mostly empty
  water, which keeps the cage readable through the bars.

## Seabed, kelp and coral (measured)
- Seabed is shallow: most of it is only 2-10 blocks of relief. Visual depth comes from vegetation.
- Seabed surface mix: dark blue-grey stained glass (~31% of the top surface, used for the winding
  river channels), brown wool, brown glass, cyan terracotta, prismarine, green glass, mossy stone,
  stone, clay.
- Kelp: about 180 stalks or clumps; top heights median ~80, 90th percentile ~140, the tallest reach the
  scene top (~250). Built from mixed greens: green wool, slime block, lime terracotta, emerald block,
  green stained glass, prismarine, green terracotta, melon. Thin swaying stems with blades.
- Coral: blobby branching heads in saturated colours (magenta wool, orange wool, purple, cyan, red,
  yellow terracotta) mostly in the lowest 20 blocks and wrapped around rock forms.
- Grey wool forms the rock arches and outcrops between 20 and 120 high.

## Creatures (measured from connected components floating free of the ground)
- About 510 floating objects; most (about 420) are tiny fish 3-5 blocks long.
- Repeated with copy-paste: identical sizes recur (e.g. five 8x7x8 jellyfish, several identical fish),
  so make one prefab and stamp it with rotation, as `BigBuild.stamp` does.
- Big jellyfish: 29 wide x 59 tall (bell ~1/3, tentacles ~2/3), glass bell, frilled terracotta rim,
  long thin trailing tentacles. Small jellyfish 8 x 8.
- Manta rays: span 24-27, very flat, dark top (obsidian) and pale belly (quartz) = countershading.
- Showpiece fish 20+ long (angelfish, a seahorse 30 tall); tropical fish 8-11 long.
- Schools are long curving ribbons of same-coloured fish all facing one way, not round clouds.

## Palette roles (exact block names from the export; modern IDs in mcreef.CAGE etc.)
- Frame: quartz block + quartz stairs; trim: stone slab / double stone slab (smooth stone slab).
- Glazing: light grey stained glass (domes), coloured glass on creatures.
- Light: sea lanterns (base rim, inside creatures), glowstone and gold accents on the chandelier.
- Metal: iron blocks for the finial and ring.
- Reef: prismarine, mossy cobblestone, brown wool, cyan terracotta (seabed); grey wool and stone
  (rock); magenta/orange/purple/cyan coral colours; mixed greens for kelp.
- Contrast rule: the cage is the only large white/pale object, so it pops against a dark, colourful,
  textured reef. Keep the focal structure tonally separate from its surroundings.

## Reusable recipe (`scripts/mcreef.py`, demo `examples/underwater_cage_demo.py`)
1. `seabed(...)` low relief, `sand_channel(...)` for winding rivers.
2. `birdcage_dome(b, cx, y0, cz, r, H, bars=16)` uses the measured profile (`CAGE_PROFILE`).
3. Centrepiece: `coral_spire(... height=0.33*H, radius≈0.1*r)` then `gazebo(*top)`;
   `chandelier(b, cx, y_top-2, cz, drop, r≈0.33*r_cage)`.
4. `coral_garden` and `kelp_forest` outside the cage (pass `avoid=` to keep the inside clear).
5. Creatures: `jellyfish`, `manta_ray`, `fish_school` along curved paths. Prefer one prefab
   stamped many times for repeated creatures.
6. Underwater: `flood(...)` then `waterlog(...)` with the SAME `keep_dry` function if any part must
   stay dry.
7. Large scenes: `save_sharded` (the half-scale demo is ~58k commands, 37 steps).

## Scaling rules
- Keep ratios: H : 2R = 1.9; bars = 16 while the bay stays 18-28 wide (fewer bars below r≈45,
  e.g. 12 bars at r=35); bars 2 wide (1 wide below half scale).
- Below about r=25, drop the drum and ledge and use one dome from 0.66 H to the top; drop the second
  collar ring.
- Kelp heights scale with the scene height, not the cage: median ~1/3, a few reaching the top.
- Keep at least 6 large creatures (jellyfish/rays) per 300x300 scene and tiny fish in 3-6 ribbons.

## Adapting to an underwater city in a bubble (e.g. Fish-Man Island)
This is guidance, not research: for a named place, run `references/research-workflow.md` first
(reference images, real layout, signature buildings) before using any numbers here.
- Use `bubble_dome` for an air bubble (ellipsoid shell, glass) and `flood(..., keep_dry=same shape)`
  plus `waterlog(..., keep_dry=same shape)` so the inside stays dry. Two nested bubbles are just two
  `bubble_dome` calls with different radii.
- The cage lessons carry over: one pale focal structure (a palace) against a dark colourful reef,
  ribs or framing on the big glass shell, coral and kelp kept OUTSIDE the main dry space, and
  creatures as stamped prefabs in curved ribbons.
- A city inside a bubble needs a ground mass under it (an island or tree-root shape); plan that with
  `heightfield` and the huge-build workflow in `references/huge-builds.md` (scenes of several
  hundred blocks need `save_sharded`).
