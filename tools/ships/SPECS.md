# Ship specs: what each famous ship looks like in the show

These are the builder's references for `tools/ships/<id>.py`. Every ship must match its spec: shape, proportions,
colours, figurehead, sails, flags and signature details. "Similar" is not good enough; a fan should recognise the
ship at a glance, from the side and from the front.

## How a ship script works

**Never use natural blocks** (dirt, grass, sand, stone, gravel, clay, ice, snow, moss, coral...): the game treats them as
land, not ship, so they get left behind the moment the ship docks and sets sail again. For a lawn use
`onepiece:deck_lawn`, for planters and soil `onepiece:deck_soil` (both look like grass/dirt and plants grow on them).
`build.py` warns about any natural block it finds.

```python
from shipkit import *          # Ship, hull helpers, WOOL/CONCRETE/TERRACOTTA/GLASS dicts, emblems, fence(), stairs(), slab(), log(), lantern()...

CUTS = (3,)                    # optional: heights for cut-away preview pictures

def build():
    s = Ship("going_merry", "Going Merry", faction="player")          # faction: player | pirate | marine
    CZ = 0                                                            # centre line (z); +x is the bow
    info = s.hull(x0=0, length=28, cz=CZ, beam=9, keel_y=-4, deck_y=3, side="minecraft:oak_planks", ...)
    ...                                                               # masts, sails, cabins, figurehead
    s.helm(x, y, z)                                                   # exactly one Ship's Wheel, on a deck, facing +x
    return s
```

Run `MC_ASSETS=/root/mc/client/assets PYTHONDONTWRITEBYTECODE=1 python3 build.py <id> --res=/root/opbuild/src/main/resources --previews=/root/shiptest/prev`
from `tools/ships/`. It prints the block count and writes previews: `<id>_se.png`, `<id>_nw.png` (isometric),
`<id>_side.png` (flat side view, bow to the right), `<id>_front.png` (from the bow) and `<id>_cut<N>.png`.
LOOK at every picture (Read the png) and fix what doesn't match the spec. Repeat until it does.

Rules:
- The sea surface is y 0. Blocks at y <= 0 are under water. Deck of a small ship ~ y 3, of a big ship ~ y 5-6.
- One Ship's Wheel (`s.helm`) on an open deck with a free block behind it (x-1) for the captain, nothing above for 2 blocks.
- Block budget: ships under 2,500 blocks for small ones, 4,500 max for the biggest. `s.count()` tells you. Hollow hulls and
  cabins (the kit hollows the hull for you). Interiors are optional: a hold with chests/barrels and one furnished cabin is plenty.
- Every ship needs: a hull with the right plan shape (sharp or round bow, flat or round stern), a figurehead built from
  blocks (big enough to read: 4-8 blocks tall), masts with yards and sails, rigging (a few `s.shrouds`/`s.rope` lines), a flag
  with the crew's emblem at the top of the main mast, cannons on both sides (`s.broadside`, enemy ships need them to fight),
  railings, lanterns on deck, and loot chests (`s.chest(x, y, z, "pirate"|"marine"|"treasure"|"easy"|"medium"|"hard")`) for
  enemy ships: at least one in the hold.
- No floating blocks: every block must touch another block of the ship (ropes/fences are fine as lines).
- Use only real block ids. Vanilla: `minecraft:<name>`; mod blocks that exist: `onepiece:ships_wheel`, `onepiece:cannon`,
  `onepiece:anchor`, `onepiece:porthole[facing=..]`, `onepiece:rope_coil`, `onepiece:adam_planks`, `onepiece:adam_log[axis=y]`,
  `onepiece:palm_planks`, `onepiece:sakura_planks`, `onepiece:marine_bricks`, `onepiece:mikan_bush`, `onepiece:sake_barrel[axis=y]`,
  `onepiece:cola_crate`, `onepiece:paper_lantern[hanging=true]`, `onepiece:wano_lacquer_planks`, `onepiece:wano_roof_tiles`,
  `onepiece:bubble_glass`, `onepiece:lab_panel`, `onepiece:lab_light`, `onepiece:pearl_block`. Do NOT invent other `onepiece:` ids.
- Stairs/slabs: `stairs("minecraft:oak_stairs", "east")` and `slab("minecraft:oak_slab", "top")` give full state strings.
  Fences: `fence("oak")`. Panes: `pane()` or `pane("light_blue")`. Logs: `log("spruce", "x")`. Lanterns: `lantern(hanging=True)`.
- Sail emblems: `s.square_sail(..., bitmap=STRAW_HAT)` (or SKULL, GULL, BUGGY, RED_HAIR, HEART_BLACK/HEART_WHITE, KID, WHITEBEARD,
  ALVIDA, BLACK_CAT), or `pattern=stripes(WOOL["red"], WOOL["white"])`. Flags: `s.flag(x, y, z, STRAW_HAT, w=9, h=7)` draws a
  flag flying toward +z. Paint a bitmap on a wall or hull with `s.paint_wall(x, y, z, bitmap, axis="z"|"x")`. Letters:
  `s.text(x, y, z, "MARINE", WOOL["blue"], axis="z")` (3x5 font, bottom-left at x,y,z, letters along +z at fixed x; use axis="x"
  for letters along +x at fixed z).
- Figureheads: build them from blocks with `s.blob(cx, cy, cz, rx, ry, rz, block, power)` (rounded lumps), `s.disc`, `s.ring`,
  `s.box`, `s.line`, `s.sphere`. They sit at the bow (max x of the hull), on top of the stem, facing +x.
- Interiors: `I.furnish(s, x0, y, z0, x1, z1, h, "kitchen"|"captain"|"barracks"|"storage"|"dining"|"library", theme)` fills an
  empty room; themes "pirate", "marine", "shipyard", "royal". The room must already be hollow with a floor at y-1.
- Keep the file self-contained: constants at the top, `build()` returning the Ship. Don't edit shipkit.py; add helpers in your file.

## Going Merry (player ship, caravel, ~30 blocks long, deck ~ y 3)

The Straw Hats' first ship, Kaya's gift from Syrup Village. A small, stubby, cheerful caravel.
- Hull: warm light tan planks (`minecraft:oak_planks`, some `minecraft:stripped_oak_log[axis=x]` courses), a dark brown wale
  stripe along the side just under the deck (`minecraft:dark_oak_planks`), darker wood under the waterline (`minecraft:spruce_planks`).
  Sharp bow, flat rounded transom stern. Beam about 9-10, hull length ~26 plus the figurehead.
- Upper works painted WHITE: the bulwark (the wall around the deck edge) and the whole bow above the wale are white
  (`minecraft:white_concrete` / `minecraft:white_terracotta`), and the white at the bow ends in a scalloped "sheep's wool" edge
  (alternate white blocks one lower, like curls). Railings on top: oak fences.
- Figurehead: a big sheep (ram) head, ~8 blocks tall on a white neck rising from the stem, at the very front. Show look:
  a SMOOTH white face (`minecraft:white_concrete`) with a long rounded snout pointing forward, big black eyes on the SIDES
  of the face (not painted on the front), a black smile line along each side of the snout, a curly wool mane
  (`minecraft:white_wool`, bumpy tufts on top) over the crown and the back of the head, and one golden ram's horn coiled
  flat against each side behind the eye (`minecraft:yellow_terracotta` ridge, `minecraft:orange_terracotta` groove). Carved
  from per-|z| side profiles (HEAD_PROFILES in going_merry.py). Don't paint a face grid on the front: it reads as a cow/panel.
- Under the figurehead at the bow: ONE cannon pointing forward (`s.cannon(x, y, z, "east")`) through a round port.
- Decks: a raised foredeck at the bow (2 above the main deck) with white railings; the open main deck in the middle with a hatch
  down to the storage hold; a two-storey stern castle: lower floor = store room / lounge with round portholes (`onepiece:porthole`),
  upper floor = the galley (Sanji's kitchen: smoker, furnace, tables, barrels) with a door onto the main deck and round portholes;
  on its roof the poop deck with white railings, the Ship's Wheel at its front edge facing the bow, and the three mikan
  (tangerine) trees (`onepiece:mikan_bush` on top of `minecraft:oak_leaves` or `s.fruit_tree`) in a planter box.
- ONE main mast amidships (slightly forward of centre), tall (~16 above deck), with a barrel-shaped crow's nest near the top,
  a yard and a big white square mainsail bearing the Straw Hat Jolly Roger (`bitmap=STRAW_HAT`), shrouds/ratlines to both sides,
  and the black Straw Hat flag (`s.flag(..., STRAW_HAT_ON_BLACK)` on black wool background: paint the flag black first) at the top.
- A short mizzen mast on the poop deck with a triangular lateen sail in RED AND WHITE vertical stripes (`s.tri_sail` with
  `pattern=stripes(WOOL["red"], WOOL["white"])`).
- Stern: round-topped transom with two portholes, a dark wood rudder hanging below (reaches under water), lanterns at the corners.
- Anchor (`onepiece:anchor`) at the port bow. Rope coils and barrels on deck. Lanterns on the mast and cabin.
- Budget: ~2,000-2,800 blocks.

## Thousand Sunny (player ship, brig sloop, ~48-50 blocks long, deck ~ y 5)

The Straw Hats' second ship, built by Franky from Adam Wood. Big, fat, round and sunny.
- Hull: ROUND bow (`bow="round"`), very full sections (`fullness=0.7`), high freeboard, beam ~15, hull length ~40 plus the lion.
  Pale Adam wood planks (`onepiece:adam_planks` for the upper hull, `minecraft:birch_planks` deck), a thick dark wale band
  (`minecraft:dark_oak_planks`, 2 courses), and the lower hull dark (`minecraft:spruce_planks`) with the very bottom
  (`minecraft:mangrove_planks`, reddish). Stern: tall, rounded (`stern="round"`), with two rows of round windows (aquarium bar
  below, library above) framed in red (`minecraft:red_terracotta`) and glass `GLASS["light_blue"]`.
- Soldier Dock System: on BOTH sides of the hull, two big round hatches (discs ~5 across, `s.disc` + `s.ring`) in red-rimmed
  white, each with a number painted on it (0 and 1 on one side, 2 and 3 on the other; use dark blocks for the digits with `s.text`
  or small bitmaps). Also a long paddle-wheel channel cover between them.
- Figurehead: the lion head, 8-9 blocks tall, at the bow: bright yellow face (`minecraft:yellow_concrete`), a huge orange mane
  (`minecraft:orange_concrete` / `minecraft:orange_terracotta`) shaped like a sun with pointed rays all around the face, big round
  black eyes with white highlights, a red nose (`minecraft:red_concrete`), a grinning mouth (black line) with white teeth. The mane
  rays must stick out past the face on all sides so it reads as a sun from the front.
- Decks: raised foredeck at the bow (holding the lion; the men's quarters inside, with bunks), the LAWN deck in the middle:
  `minecraft:grass_block` deck with a small tree (`s.tree`, 4-5 tall) and a swing hanging from it (fences + a slab seat), and a
  slide (stairs) coming down from the aft deck; a raised aft deck with the kitchen + dining room building (pale walls, a rounded
  dark roof via `s.barrel_roof`, a chimney, light-blue windows, a door to the lawn); the Ship's Wheel on the aft deck in front of
  the kitchen; behind/above the kitchen a third level: the library and bath with a big round window and a small dome
  (`s.dome`). Below the lawn deck: the aquarium bar (a room with `GLASS["light_blue"]` tank walls and `minecraft:water` inside)
  reachable by a hatch and ladder, and a hold with chests and `onepiece:cola_crate`s.
- TWO masts: the foremast on the foredeck (shorter) with one white square sail (plain), and the tall mainmast behind the lawn with
  a huge white mainsail bearing the Straw Hat Jolly Roger (`bitmap=STRAW_HAT`, sail ~17 wide x 13 tall) plus a smaller topsail,
  and the round observation room (a hollow sphere ~3 radius, pale wood with light-blue windows) as the crow's nest near the top,
  the black Straw Hat flag above it. Shrouds to both sides.
- Railings: dark wood (`fence("dark_oak")`) around every deck. Lanterns. Anchors at both bows (port and starboard).
- Cannons: 3 per side on the lawn-deck level through round ports.
- Budget: ~4,000-4,500 blocks (watch it: hollow everything, no solid blobs).

## Marine Warship (enemy, tiers 0-2, ~38 blocks long) and Marine Battleship (enemy, tiers 3-5, ~52 blocks long)

The Navy's standard ships. White, blue and clean.
- Hull: WHITE (`minecraft:white_concrete`) with a wide royal-blue band along the upper hull (`minecraft:blue_concrete`, 2 courses
  just under the deck) and light-blue trim (`minecraft:light_blue_concrete`) at the waterline; grey bottom
  (`minecraft:gray_concrete`) under water. Sharp bow, flat stern. Deck `minecraft:birch_planks`. Bulwark white, rails birch fence.
- Figurehead: a big white seagull with wings swept back along the bow, yellow beak (`minecraft:yellow_concrete`), black eyes.
  The gull is 4-6 blocks tall and its wings run 6-8 blocks back along both sides of the bow.
- Masts: 3 for the battleship, 2 for the warship; birch logs; white square sails. The MAIN sail reads "MARINE" in blue letters
  (`s.text(...)`) with the blue gull mark (`GULL`) above the word; other sails carry just the gull. White flags with the blue gull.
- Stern castle: a 2-storey (warship) or 3-storey (battleship) white block with blue roofs (`minecraft:blue_concrete` /
  `minecraft:blue_terracotta`), rows of windows (`pane("light_blue")`), a balcony; the bridge on top with the Ship's Wheel.
- Guns: a row of gun ports (black squares in the hull side with cannons behind) on the gun deck plus cannons on the weather deck;
  the battleship has two gun rows. `s.broadside` with gunport=CONCRETE["black"].
- Inside: barracks, an armory with `minecraft:chest` loot "marine", a brig with `onepiece:prison_bars`, and a captain's cabin
  (theme "marine").
- Budget: warship ~2,500, battleship ~4,200.

## Big Top (Buggy the Clown's ship, enemy, tiers 0-1, ~30 blocks long)

A floating circus.
- Hull: colourful: mustard yellow planks (`minecraft:yellow_terracotta`) with a red wale, blue bulwark (`minecraft:blue_concrete`)
  and a dark bottom. Sharp bow, flat stern.
- Figurehead: an ELEPHANT head with a long trunk curling down toward the water and two big ears: grey (`minecraft:light_gray_concrete`
  / `minecraft:gray_concrete`), with white tusks (`minecraft:white_concrete`), black eyes and a red circus headband.
- The CIRCUS TENT: a big conical big-top in red-and-white vertical stripes (`minecraft:red_wool` / `minecraft:white_wool`) sitting
  on the main deck amidships, 10-12 blocks across, with a pole and a small flag on its peak and a yellow scalloped edge.
  Inside the tent: a ring, a cannon (the Buggy Ball cannon) and loot.
- One mast with a white sail bearing Buggy's mark (`BUGGY`: skull with a red nose), Buggy's flag on top. Cannons on both sides.
- Colours loud and clownish: red, white, yellow, blue. Lanterns, barrels, a cage (`minecraft:iron_bars`) for Richie the lion.
- Budget ~2,200.

## Red Force (Shanks' ship, enemy, tiers 4-5, ~46 blocks long)

The Red Hair Pirates' flagship. Big and red.
- Hull: deep red (`minecraft:red_terracotta` with `minecraft:mangrove_planks` courses), gold trim along the wale and rails
  (`minecraft:gold_block` sparingly, `minecraft:yellow_terracotta`), dark bottom. Sharp bow, high rounded stern with gold-framed windows.
- Figurehead: a huge red DRAGON head with golden horns, an open jaw with white teeth and a long neck rising from the stem (8-9 tall,
  the neck arching up and forward).
- 3 masts, red flags, large white (cream, `minecraft:white_wool`) sails; the mainsail bears the Red Hair Jolly Roger (`RED_HAIR`:
  skull with three scars over the left eye, crossed sabres). Shrouds, lanterns, cannons on both sides (4 per side).
- Big captain's cabin in the stern (theme "royal"), a hold with "treasure" chests.
- Budget ~3,800.

## Polar Tang (Trafalgar Law's submarine, enemy, tiers 2-3, ~36 blocks long, surfaced)

The Heart Pirates' yellow submarine.
- Body: a long rounded cigar (`s.hull` with bow="round", stern="round", fullness=0.75, keep_inside=False, or build it from
  `s.blob`), bright YELLOW (`minecraft:yellow_concrete`) above the water, light green (`minecraft:lime_concrete`) below the waterline,
  with dark riveted bands (`minecraft:gray_concrete` rings) every 8 blocks. The top is a flat wooden deck (`minecraft:spruce_planks`)
  with a rail. Two torpedo tubes (black discs) in the rounded bow. No figurehead.
- A conning tower amidships: yellow, 4-5 tall, 5 wide, with round portholes, a hatch, a railing on top, a periscope (iron bars /
  chain) and the Ship's Wheel on top of the tower. A short mast with the Heart Pirates flag (white smiley on black) and a small
  black sail with the white smiley.
- The Heart Pirates smiley (`HEART_BLACK`, black on yellow) painted large on BOTH sides of the body.
- Cannons: 2 per side on the deck. Inside: a crew room and the sick bay with loot "medicine".
- Budget ~1,800.

## Victoria Punk (Eustass Kid's ship, enemy, tiers 3-5, ~42 blocks long)

The Kid Pirates' ship: dark, spiky, metal.
- Hull: dark (`minecraft:dark_oak_planks` with `minecraft:blackstone` courses) armoured with iron plates (`minecraft:iron_block`
  patches, `minecraft:iron_bars` spikes along the rail), red accents (`minecraft:red_terracotta` wale). Sharp bow, tall stern.
- Figurehead: a giant SKULL, 8 tall, bone white (`minecraft:bone_block`/`minecraft:white_concrete`) with glowing red eyes
  (`minecraft:redstone_block`), a spiky metal crest (iron bars/blackstone) like Kid's hair, and jaws open over the stem.
- 2 tall masts; dark red sails (`minecraft:red_wool`) with Kid's mark in black and white (`KID`); black flags with KID.
- Cannons 4 per side, scrap metal on deck (anvils, chains), a forge below (blast furnace, theme "pirate"), loot "hard".
- Budget ~3,500.

## Miss Love Duck (Alvida's ship, enemy, tier 0, ~28 blocks long)

A pink ship with a duck figurehead.
- Hull: pink (`minecraft:pink_terracotta` and `minecraft:pink_concrete`) with white trim and a red wale; cream deck.
- Figurehead: a big yellow DUCK head (`minecraft:yellow_concrete`) with an orange bill (`minecraft:orange_concrete`), black eyes and
  a red bow (`minecraft:red_wool`) under its chin.
- One mast with a pink sail bearing Alvida's mark (`ALVIDA`: skull with a heart), hearts painted on the hull sides
  (`minecraft:red_wool`), a pink flag. Cannons 2 per side. A perfumed cabin (theme "royal"). Budget ~1,800.

## Bezan Black (Kuro's Black Cat Pirates, enemy, tier 1, ~32 blocks long)

A black ship with a cat's head.
- Hull: black (`minecraft:black_concrete` and `minecraft:dark_oak_planks`), purple trim (`minecraft:purple_terracotta` wale),
  dark deck (`minecraft:spruce_planks`).
- Figurehead: a black CAT head with pointed ears, yellow eyes (`minecraft:yellow_concrete`), white whiskers (`minecraft:white_concrete`)
  and fangs.
- Two masts, black sails with the Black Cat Jolly Roger (`BLACK_CAT`), black flags. Cannons 3 per side. Hold with "medium" loot.
- Budget ~2,200.
