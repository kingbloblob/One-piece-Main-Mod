"""Thousand Sunny: the Straw Hats' brig sloop, built by Franky from Adam Wood.

Layout (+x is the bow, CZ = 0):
  x  0..12   stern tower: sick bay (y 8..10), kitchen + dining (y 12..14), library + bath with the dome on top
  x 13..16   open aft deck (floor y 11) with the Ship's Wheel; stairs + slide down to the lawn
  x 17..28   lawn deck (grass at y 7): mainmast, tree + swing, 3 cannons a side
  x 29..39   raised foredeck (floor y 11) with the men's quarters inside and the foremast
  x 40..46   the lion figurehead (sun mane cupped back at x 40-41, hollow muzzle to x 45, nose at x 46)
  below the lawn / stern: aquarium bar (stern) and the hold, floor at y 2
"""
import math
import os
from shipkit import *  # noqa: F401,F403

CUTS = (8,)  # cut just above the lawn deck to show the deck layout

ADAM = "onepiece:adam_planks"
BIRCH = "minecraft:birch_planks"
DARK = "minecraft:dark_oak_planks"
SPRUCE = "minecraft:spruce_planks"
MANGROVE = "minecraft:mangrove_planks"
GRASS = "onepiece:deck_lawn"            # grass that counts as part of a ship (real grass never sails)
RED_T = TERRACOTTA["red"]
WHITE_C = CONCRETE["white"]
YELLOW_C = CONCRETE["yellow"]
ORANGE_C = CONCRETE["orange"]
ORANGE_T = TERRACOTTA["orange"]
BLACK_C = CONCRETE["black"]
RED_C = CONCRETE["red"]
LB_GLASS = GLASS["light_blue"]
RAIL = fence("dark_oak")
WATER = "minecraft:water"
COLA = "onepiece:cola_crate[axis=y]"
BARREL = "minecraft:barrel[facing=up,open=false]"
BIRCH_STAIRS = "minecraft:birch_stairs"
DARK_SLAB = "minecraft:dark_oak_slab"

CZ = 0
DECK = 7           # lawn deck level amidships (high freeboard)
KEEL = -2
BOW_X = 39         # last hull column (the hull is lofted to x 41 and the 2 pointed tip columns are cut off)
TOP = 11           # floor of the raised fore and aft decks
MAIN_X, FORE_X = 18, 34
LION_Y = 13        # centre of the lion's face

# A small Straw Hat Jolly Roger pennant, 9 x 7: hat on 2 rows, skull on 3, crossbone ends at the 4 corners.
SH_FLAG_ROWS = [
    "KKYRRRYKK",
    "KYYYYYYYK",
    "WKWWWWWKW",
    "KWWKWKWWK",
    "KKKWWWKKK",
    "KWKKKKKWK",
    "WKKKKKKKW",
]
SH_FLAG = (SH_FLAG_ROWS, {"K": WOOL["black"], "Y": WOOL["yellow"], "R": WOOL["red"], "W": WOOL["white"]})

# The lion's mane seen from the front: a 9-wide disc ('o') with eight pointed 3-block rays ('#'), 15 x 15.
# Ray cells further than RAY_BEND from the centre are set one block further aft, so the sun cups back from the side.
SUN_ROWS = [
    ".......#.......",
    ".......#.......",
    ".#....###....#.",
    "..##.ooooo.##..",
    "..##ooooooo##..",
    "...ooooooooo...",
    "...ooooooooo...",
    "###ooooooooo###",
    "...ooooooooo...",
    "...ooooooooo...",
    "..##ooooooo##..",
    "..##.ooooo.##..",
    ".#....###....#.",
    ".......#.......",
    ".......#.......",
]
RAY_BEND = 5.8
# The face features, 7 x 7, painted on the front of the yellow muzzle: big black eyes with a white glint,
# red nose, a black grin with white teeth ('.' = plain yellow muzzle).
FACE_ROWS = [
    ".......",
    ".WK.KW.",
    ".KK.KK.",
    "...R...",
    "K.....K",
    ".KWWWK.",
    "..KKK..",
]
FACE = {"K": BLACK_C, "W": WHITE_C, "R": RED_C}


class SunnyShip(Ship):
    """Ship whose front preview really looks from the bow.

    Ship.elevation(axis="x") keeps the block with the largest -x for each pixel, i.e. the one nearest the STERN, so
    the kit's '<id>_front.png' shows the stern and hides the figurehead. This override keeps the block nearest
    the bow (largest x) instead; everything else is the kit's code."""

    def elevation(self, out, axis="z", scale=8, title=None):
        import render
        from PIL import Image, ImageDraw
        pts = {}
        for (x, y, z), s in self.blocks.items():
            if s == AIR or s.split("[")[0] in render.SKIP:
                continue
            if axis == "z":
                key, depth = (x, y), z
            else:
                key, depth = (-z, y), x
            if key not in pts or depth > pts[key][0]:
                pts[key] = (depth, s)
        if not pts:
            return
        us = [k[0] for k in pts]
        vs = [k[1] for k in pts]
        u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
        pad = 12
        W = (u1 - u0 + 1) * scale + 2 * pad
        H = (v1 - v0 + 1) * scale + 2 * pad + (30 if title else 0)
        img = Image.new("RGB", (W, H), (206, 224, 236))
        d = ImageDraw.Draw(img)
        sea_y = pad + (v1 - 0) * scale + (30 if title else 0)
        d.rectangle([0, sea_y + scale, W, H], fill=(96, 140, 210))
        depths = [p[0] for p in pts.values()]
        dmin, dmax = min(depths), max(depths)
        for (u, v), (depth, s) in pts.items():
            cols = render.block_colors(s)
            if cols is None:
                continue
            c = cols[1]
            t = 0.75 + 0.25 * ((depth - dmin) / max(1, dmax - dmin))
            c = tuple(int(min(255, cc * t)) for cc in c)
            px = pad + (u - u0) * scale
            py = pad + (v1 - v) * scale + (30 if title else 0)
            d.rectangle([px, py, px + scale - 1, py + scale - 1], fill=c)
        if title:
            d.text((pad, 8), title, fill=(30, 40, 60))
        img.save(out)
        return out


# ---------------------------------------------------------------- helpers
def outline(s, x):
    """(deck y, z cells of the hull deck at x) or (None, []) off the hull."""
    if x < 0 or x > BOW_X:
        return None, []
    dy = s.deck_y(x)
    return dy, [z for z in range(-9, 10) if s._inside(x, dy, z)]


def raise_deck(s, x0, x1, top, wall, floor, rail=None, y_from=None):
    """Walls on the hull's deck outline from the hull deck (or y_from) up to top-1, a floor at `top`, a rail
    on the edge at top+1. The inside is left hollow."""
    for x in range(x0, x1 + 1):
        dy, zs = outline(s, x)
        zset = set(zs)
        prev = set(outline(s, x - 1)[1]) if x > x0 else set()
        nxt = set(outline(s, x + 1)[1]) if x < x1 else set()
        y0 = y_from if y_from is not None else dy + 1
        for z in zs:
            edge = (z + 1 not in zset) or (z - 1 not in zset) or (z not in prev) or (z not in nxt)
            for y in range(y0, top):
                s.set(x, y, z, wall if edge else AIR)
            s.set(x, top, z, floor)
            if rail and edge:
                s.set(x, top + 1, z, rail)


def hatch_disc(s, x, z, digit, mirror=False):
    """A Soldier Dock hatch: a 7-wide round white hatch with a red rim and a number, on the hull side at z,
    centred at y 3 (its lowest block just touches the water)."""
    s.disc(x, 3, z, 3.0, RED_T, axis="z")
    s.disc(x, 3, z, 2.2, WHITE_C, axis="z")
    if mirror:
        s.text(x + 1, 1, z, digit, BLACK_C, axis="x", step=-1)
    else:
        s.text(x - 1, 1, z, digit, BLACK_C, axis="x")


def stern_window(s, x, cy, z):
    """A round red-framed window on the stern face: 3 light-blue panes stacked, rimmed in red, capped top and bottom."""
    for dy in (-1, 0, 1):
        s.set(x, cy + dy, z, LB_GLASS)
        s.set(x, cy + dy, z - 1, RED_T)
        s.set(x, cy + dy, z + 1, RED_T)
    s.set(x, cy + 2, z, RED_T)
    s.set(x, cy - 2, z, RED_T)


def lion(s):
    """The lion figurehead: mane (x 40-41), muzzle (x 41-45), eyes/nose/grin on its front (x 44-46)."""
    # the mane's back: a ring with a spoke, resting on the bow face, holds the sun up
    s.ring(BOW_X + 1, LION_Y, CZ, 5, ORANGE_T, axis="x")
    s.line((BOW_X + 1, LION_Y - 2, CZ), (BOW_X + 1, LION_Y - 4, CZ), ORANGE_T)
    # the sun mane; ray cells far from the centre bend one block aft
    n = len(SUN_ROWS)
    c = n // 2
    for j, row in enumerate(SUN_ROWS):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            dy, dz = c - j, i - c
            bent = ch == "#" and math.hypot(dy, dz) > RAY_BEND
            s.set(BOW_X + (1 if bent else 2), LION_Y + dy, CZ + dz, ORANGE_C)
    # the muzzle: a hollow rounded yellow lump jutting forward
    mx, rx, ry, rz, pw = BOW_X + 4, 2.5, 3.5, 3.5, 2.5
    s.blob(mx, LION_Y, CZ, rx, ry, rz, YELLOW_C, pw, hollow=True)

    def front(y, z):
        for x in range(int(mx + rx) + 1, BOW_X, -1):
            if abs((x - mx) / rx) ** pw + abs((y - LION_Y) / ry) ** pw + abs((z - CZ) / rz) ** pw <= 1.0:
                return x
        return None
    for j, row in enumerate(FACE_ROWS):
        for i, ch in enumerate(row):
            if ch not in FACE:
                continue
            y, z = LION_Y + 3 - j, CZ - 3 + i
            fx = front(y, z)
            if fx is None:
                continue
            s.set(fx, y, z, FACE[ch])
            if ch == "R":                                                       # the nose stands out
                s.set(fx + 1, y, z, FACE[ch])


def loose_blocks(s):
    """Blocks not face-connected to the keel (should be empty)."""
    solid = {p for p, b in s.blocks.items() if b != AIR}
    start = min(solid, key=lambda p: (p[1], abs(p[2]), abs(p[0] - 20)))
    seen = {start}
    stack = [start]
    while stack:
        x, y, z = stack.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    n = (x + dx, y + dy, z + dz)
                    if n in solid and n not in seen:
                        seen.add(n)
                        stack.append(n)
    return sorted(solid - seen)


# ---------------------------------------------------------------- the ship
def crew_rooms(s):
    """The workstations that make her a Dream Ship home (com.onepiecemod.crewship): a room for every crew job, bunks
    for the crew, a Captain's Cabin corner, the mikan garden, a bath, and the Ship's Log. Each piece goes on an empty
    cell with a floor under it; anything that lands on a wall is reported so the layout can be nudged."""
    def put(x, y, z, block):
        here, below = s.get(x, y, z), s.get(x, y - 1, z)
        if (here not in (None, AIR) and "water" not in here) or below in (None, AIR) or "water" in (below or ""):
            print(f"  !! crew room piece {block.split('[')[0]} has no room at {x} {y} {z} ({here} on {below})")
            return
        s.set(x, y, z, block)

    def f(name, facing):
        return f"onepiece:{name}[facing={facing},waterlogged=false]"

    # Ship's Log: in the galley by the door to the aft deck (sneak + right-click to make her your home)
    put(11, TOP + 1, 5, "onepiece:ship_log[facing=west]")
    # Galley (Sanji): a line of smoker, sink, counter and pot along the port wall, a dining table in the middle
    put(4, TOP + 1, -6, "minecraft:barrel[facing=up,open=false]")
    put(5, TOP + 1, -6, "minecraft:smoker[facing=south,lit=false]")
    put(6, TOP + 1, -6, f("galley_sink", "south"))
    put(7, TOP + 1, -6, f("oak_counter", "south"))
    put(8, TOP + 1, -6, f("cooking_pot", "south"))
    s.table_set(6, TOP + 1, 1, "spruce", "red")
    # Sick bay (Chopper): medicine cabinet, brewing stand and two cots along the starboard side
    put(5, 8, 6, "minecraft:brewing_stand[has_bottle_0=false,has_bottle_1=false,has_bottle_2=false]")
    put(6, 8, 6, f("medicine_cabinet", "north"))
    bed("white", 3, 8, 5, s, facing="south")
    bed("white", 8, 8, 5, s, facing="south")
    # Library (Robin) with the chart corner (Nami) and the bath under the dome
    for z in (-5, -4, -3, 3, 4, 5):
        put(2, TOP + 5, z, "minecraft:bookshelf")
    put(3, TOP + 5, -4, "minecraft:lectern[facing=east,has_book=false,powered=false]")
    put(3, TOP + 5, -5, f("book_stack", "east"))
    put(3, TOP + 5, 4, f("chart_table", "east"))
    put(4, TOP + 5, 5, f("globe", "north"))
    put(5, TOP + 5, -1, f("bathtub", "west"))
    # Aquarium bar (Brook): piano and keg by the tank, a stool at the table
    put(5, 3, -5, f("piano", "south"))
    put(6, 3, -5, f("keg", "south"))
    put(5, 3, -3, f("bar_stool", "south"))
    # Weapons factory (Usopp) and Franky's workshop in the hold, by the Cola Engine
    put(14, 3, -5, "minecraft:target[power=0]")
    put(15, 3, -5, "minecraft:fletching_table")
    put(16, 3, -5, f("powder_keg", "south"))
    put(23, 3, -5, f("tool_bench", "south"))
    put(24, 3, -5, "minecraft:anvil[facing=east]")
    # Crew hammocks along the starboard side of the hold
    for x in (12, 14, 16, 18, 20):
        put(x, 3, 5, f("hammock", "north"))
    # Zoro's training corner on the foredeck
    put(33, TOP + 1, -4, f("training_weights", "south"))
    put(35, TOP + 1, -4, f("katana_stand", "south"))
    # Captain's chair in the men's quarters
    put(33, 8, -2, f("captains_chair", "west"))
    # Nami's mikan trees on the lawn
    put(18, DECK + 1, 4, f("mikan_tree_pot", "north"))
    put(18, DECK + 1, -4, f("mikan_tree_pot", "south"))


def build():
    s = SunnyShip("thousand_sunny", "Thousand Sunny", faction="player", tiers=[], crew="Straw Hat Pirates")

    # ---- hull: round bow, round stern, very full, pale Adam wood over a dark bottom
    def under(y):
        return MANGROVE if y <= KEEL + 1 else SPRUCE

    def paint(x, y, z, kind):
        if y < 1:
            return under(y)
        return None

    # lofted from x -1 to 41; the 1-wide stern tip (x -1) and the 2 pointed bow tip columns are cut off, so the
    # stern is a full, rounded 9-wide counter at x 0 and the bow a blunt face at x 39 that carries the lion
    s.hull(-1, 43, CZ, 15, KEEL, DECK, side=ADAM, bottom=SPRUCE, deck=BIRCH, bow="round", stern="round",
           bow_len=12, stern_len=4, sheer_bow=1, sheer_stern=1, fullness=0.7, flat=0.45, bulwark=1,
           bulwark_mat=ADAM, rail=RAIL, paint=paint, inner_decks=[(2, SPRUCE)])
    for p in [p for p in s.blocks if p[0] > BOW_X or p[0] < 0]:
        del s.blocks[p]
    for fx in (0, BOW_X):
        for y in range(KEEL - 1, 10):
            for z in range(-9, 10):
                if s._inside(fx, y, z) and s.get(fx, y, z) in (None, AIR):
                    s.set(fx, y, z, under(y) if y < 1 else ADAM)
    # no hold floor in the forepeak (nobody goes there); a bulkhead closes the hold at x 29
    # (the bow face column itself keeps its planks)
    for p in [p for p in s.blocks if 29 <= p[0] < BOW_X and p[1] == 2 and s.blocks[p] == SPRUCE
              and s._inside(p[0], 1, p[2])]:
        s.set(*p, AIR)
    # rocker and rake: the bottom sweeps up at both ends in steps (stem meets the water at x 36)
    for x, cut in ((35, 0), (36, 1), (37, 2), (38, 3), (39, 4), (0, 2), (1, 1), (2, 0), (3, -1), (4, -2)):
        for p in [p for p in s.blocks if p[0] == x and p[1] < cut]:
            del s.blocks[p]
        for z in range(-9, 10):
            if s._inside(x, cut, z):
                s.set(x, cut, z, MANGROVE if cut <= 0 else SPRUCE)
    for z in range(-9, 10):                                                 # belt and braces: no hole in the bow face
        for y in range(4, 10):
            if s._inside(BOW_X, y, z) and s.get(BOW_X, y, z) in (None, AIR):
                s.set(BOW_X, y, z, ADAM)
    for y in range(3, DECK):
        for z in range(-9, 10):
            if s._inside(29, y, z) and s.get(29, y, z) in (None, AIR):
                s.set(29, y, z, SPRUCE)
    # the thick dark wale: two courses all along the side, the deck-edge course and the one under it
    for x in range(0, BOW_X + 1):
        dy = s.deck_y(x)
        for y in (dy - 1, dy):
            for z in range(-9, 10):
                if s.get(x, y, z) == ADAM:
                    s.set(x, y, z, DARK)

    # ---- Soldier Dock System: two numbered hatches a side + the paddle-wheel channel cover between them
    for side, digits in ((1, ("1", "0")), (-1, ("3", "2"))):
        z = 6 * side
        hatch_disc(s, 9, z, digits[0], mirror=side < 0)
        hatch_disc(s, 29, z, digits[1], mirror=side < 0)
        s.box(15, 2, z, 23, 4, z, RED_T)
        s.box(16, 3, z, 22, 3, z, WHITE_C)

    # ---- the lawn deck
    for x in range(17, 29):
        dy, zs = outline(s, x)
        for z in zs:
            if s.get(x, dy, z) == BIRCH:
                s.set(x, dy, z, GRASS)

    # ---- stern tower: sick bay (under the aft deck), kitchen, library, dome
    raise_deck(s, 0, 16, TOP, ADAM, BIRCH, rail=RAIL)                      # sick bay level + aft deck floor
    raise_deck(s, 1, 12, TOP + 4, ADAM, ADAM, y_from=TOP + 1)              # kitchen level, ceiling plate at y 15
    for x in range(7, 13):                                                 # vaulted under the barrel roof
        for z in range(-6, 7):
            s.set(x, TOP + 4, z, AIR)
    raise_deck(s, 1, 6, TOP + 8, ADAM, ADAM, y_from=TOP + 5)               # library level, roof plate at y 19
    # kitchen's rounded dark roof (x 7..12) with the gable against the library and the front
    s.barrel_roof(7, -7, 12, 7, TOP + 4, DARK, slab_mat=slab(DARK_SLAB, "bottom"), axis="x")
    for z in range(-7, 8):
        t = abs((z + 7) / 14 * 2 - 1)
        h = int(round((1 - t * t) * 2))
        for y in range(TOP + 4, TOP + 4 + h):
            s.set(12, y, z, ADAM)
            s.set(7, y, z, ADAM)
    s.box(9, TOP + 6, 3, 9, TOP + 8, 3, "minecraft:bricks")                # chimney
    s.set(9, TOP + 9, 3, "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]")
    # the dome over the library (bath)
    s.dome(3, TOP + 9, CZ, 3.5, ADAM)
    for x in range(1, 6):                                                  # the bath opens up into the dome
        for z in range(-2, 3):
            if (x - 3) ** 2 + z * z <= 4.5:
                s.set(x, TOP + 8, z, AIR)
    s.set(3, TOP + 13, CZ, lantern())
    # stern windows: aquarium bar (hull), portholes, and the library's big round window
    for z in (-3, 0, 3):                                                   # aquarium bar: 3 round windows
        stern_window(s, 0, 4, z)
    for z in (-2, 2):
        s.set(0, 9, z, "onepiece:porthole[facing=west]")
        s.set(1, 13, 4 * z // 2, "onepiece:porthole[facing=west]")
    s.ring(1, TOP + 6, CZ, 3, RED_T, axis="x")                             # library: the big round window
    s.disc(1, TOP + 6, CZ, 2.2, LB_GLASS, axis="x")
    # light-blue windows along the kitchen and library, portholes along the sick bay
    for x in (7, 9, 11):
        for z in (-7, 7):
            s.set(x, TOP + 2, z, LB_GLASS)
    for x in (4, 6):
        for z in (-6, 6):
            s.set(x, TOP + 2, z, LB_GLASS)
    for x in (3, 5):
        dy, zs = outline(s, x)
        s.set(x, TOP + 6, min(zs), LB_GLASS)
        s.set(x, TOP + 6, max(zs), LB_GLASS)
    for x in (6, 10, 14):
        s.set(x, 9, -7, "onepiece:porthole[facing=north]")
        s.set(x, 9, 7, "onepiece:porthole[facing=south]")
    # doors: sick bay -> lawn, kitchen -> aft deck
    s.set(16, 8, CZ, door("minecraft:spruce_door", "east", "lower"))
    s.set(16, 9, CZ, door("minecraft:spruce_door", "east", "upper"))
    s.set(12, TOP + 1, -3, door("minecraft:spruce_door", "east", "lower"))
    s.set(12, TOP + 2, -3, door("minecraft:spruce_door", "east", "upper"))
    # the Ship's Wheel on the aft deck in front of the kitchen (captain stands at x 14)
    s.helm(15, TOP + 1, CZ)
    # stairs (starboard) and the slide (port, 2 wide) from the aft deck down to the lawn
    s.stairs_run(19, 8, 5, 3, BIRCH_STAIRS, "west")
    s.stairs_run(19, 8, -6, 3, BIRCH_STAIRS, "west", w=2)
    for z in (5, -6, -5):
        s.box(17, 8, z, 17, 9, z, ADAM)
        s.set(18, 8, z, ADAM)
        s.set(16, TOP + 1, z, AIR)
    for z in (-7, 7):
        s.set(16, TOP + 2, z, lantern())

    # ---- foredeck with the men's quarters inside
    raise_deck(s, 29, BOW_X, TOP, ADAM, BIRCH, rail=RAIL)
    s.set(29, 8, CZ, door("minecraft:spruce_door", "west", "lower"))
    s.set(29, 9, CZ, door("minecraft:spruce_door", "west", "upper"))
    s.stairs_run(26, 8, 5, 3, BIRCH_STAIRS, "east")
    s.set(27, 8, 5, ADAM)
    s.box(28, 8, 5, 28, 9, 5, ADAM)
    s.set(29, TOP + 1, 5, AIR)
    for x in (31, 34):
        s.set(x, 9, -7 if x == 31 else -6, "onepiece:porthole[facing=north]")
        s.set(x, 9, 7 if x == 31 else 6, "onepiece:porthole[facing=south]")
    for z in (-6, 6):
        s.set(29, TOP + 2, z, lantern())
    # bunks in the quarters
    for (bx, bz, f) in ((32, -5, "north"), (32, 4, "south"), (35, -4, "north"), (35, 3, "south")):
        bed("red", bx, 8, bz, s, facing=f)
    s.chest(31, 8, 0, "easy")
    s.set(36, 8, 0, lantern())
    # anchors at both bows
    s.anchor(35, 7, 7, "south")
    s.anchor(35, 7, -7, "north")

    # ---- the lion figurehead, x 40..46, centred at y 13: a sun-shaped orange mane cupped back at the ray tips,
    # a hollow yellow muzzle jutting forward, and the face painted on the muzzle's front
    lion(s)
    # The Gaon Cannon fires from the lion's mouth: the game finds the bow by the Sunny Figurehead block, hidden in the muzzle.
    if s.get(44, 13, 0) in (None, AIR):
        s.set(44, 13, 0, "onepiece:figurehead_sunny[facing=east]")

    # ---- below decks: aquarium bar at the stern, the hold amidships and forward
    for x in range(1, 4):                                                  # the tank behind the stern windows
        for z in range(-3, 4):
            for y in range(3, 7):
                if s.get(x, y, z) in (None, AIR):
                    water = 1 <= x <= 2 and abs(z) <= 2 and y <= 5
                    s.set(x, y, z, WATER if water else LB_GLASS)
    s.table_set(9, 3, 0, "spruce", "red")
    s.set(7, 3, -4, BARREL)
    s.set(7, 3, 4, BARREL)
    s.set(12, 6, -3, lantern(hanging=True))
    s.set(12, 6, 3, lantern(hanging=True))
    s.open_hatch(10, DECK, 5, ladder_facing="north", down_to=3)            # sick bay -> aquarium bar
    s.open_hatch(20, DECK, -4, ladder_facing="west", down_to=3)            # lawn -> hold
    s.box(21, 3, -4, 21, 6, -4, log("spruce"))
    for (hx, hz) in ((23, 4), (26, 4), (23, -4), (28, -2), (27, 3), (28, 2)):
        s.set(hx, 3, hz, COLA)
    s.set(26, 3, -4, BARREL)
    s.set(28, 3, 4, BARREL)
    # Franky's Cola Engine powers the Coup de Burst and the Gaon Cannon (com.onepiecemod.shipcombat.ShipSpecials)
    if s.get(25, 3, 0) in (None, AIR):
        s.set(25, 3, 0, "onepiece:cola_engine")
    s.chest(28, 3, -4, "treasure")
    s.chest(17, 3, 3, "medium")
    s.set(25, 6, 0, lantern(hanging=True))

    # ---- lawn: tree with a swing, cannons through the bulwark
    s.tree(24, 8, -3, h=4, kind="oak", r=2.0)
    for z in range(-3, 3):                                                 # the branch the swing hangs from
        s.set(24, 11, z, log("oak", "z"))
    for z in (0, 2):                                                       # two chains and a 3-wide seat
        s.set(24, 10, z, fence("oak"))
        s.set(24, 9, z, fence("oak"))
    for z in range(0, 3):
        s.set(24, 8, z, slab("minecraft:oak_slab", "top"))
    s.broadside((21, 24, 27), DECK + 1, CZ, lambda x: 7, gunport=BLACK_C)
    s.set(20, 8, 6, "onepiece:rope_coil[facing=north]")
    s.set(27, 8, -5, BARREL)                                              # beside the gun, not on it

    # ---- masts, sails, rigging, flag
    # mainmast behind the lawn: plus-shaped lower mast, a huge mainsail with the Jolly Roger, a topsail,
    # the round observation room near the top and the black flag above it
    s.mast(MAIN_X, CZ, 3, 39, wood="spruce")
    s.square_sail(MAIN_X + 1, CZ, 13, 25, 8, WOOL["white"], belly=1, yard="spruce", bitmap=STRAW_HAT)
    s.square_sail(MAIN_X + 1, CZ, 28, 32, 4, WOOL["white"], belly=1, yard="spruce")
    s.sphere(MAIN_X, 37, CZ, 3, ADAM, hollow=True)
    for dx in range(-3, 4):
        for dz in range(-3, 4):
            if s.get(MAIN_X + dx, 37, dz) == ADAM and (dx, dz) != (0, 0):
                s.set(MAIN_X + dx, 37, dz, LB_GLASS)
    for y in range(34, 42):
        s.set(MAIN_X, y, CZ, log("spruce"))
    s.flag(MAIN_X, 42, CZ, SH_FLAG)
    for side in (-1, 1):
        s.line((MAIN_X, 25, CZ), (MAIN_X - 2, DECK + 1, 7 * side), RAIL)
    s.set(MAIN_X + 1, 9, CZ, lantern())
    # foremast on the foredeck with a plain white sail
    s.mast(FORE_X, CZ, 8, 21, wood="spruce")
    s.square_sail(FORE_X + 1, CZ, 16, 23, 5, WOOL["white"], belly=1, yard="spruce")
    for side in (-1, 1):
        s.line((FORE_X, 23, CZ), (FORE_X - 1, TOP + 1, 6 * side), RAIL)
    s.set(FORE_X, 29, CZ, lantern())
    # a stay from the foremast head down to the top of the mane, and one between the masts
    s.rope((FORE_X, 27, CZ), (BOW_X + 1, LION_Y + 8, CZ))
    s.rope((MAIN_X, 40, CZ), (FORE_X, 28, CZ))

    crew_rooms(s)
    loose = loose_blocks(s)
    if loose:
        print(f"  !! {len(loose)} loose blocks, e.g. {loose[:12]}")
    return s
