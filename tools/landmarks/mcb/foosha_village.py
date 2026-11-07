"""Foosha Village (Windmill Village), redesigned with the Minecraft Builder skill (dossier: mcb/dossiers/foosha_village.md).

Luffy's home port on Dawn Island: a village of whitewashed timber-framed cottages with brown and red-brown roofs on a
slope that runs down to a stone quay, three tall smock windmills on the green knolls behind it, Makino's Partys Bar
facing the harbour with its PARTYS BAR board and long counter, Mayor Woop Slap's house, a market square round the
well with stalls and benches, lamp posts along the streets, wheat and vegetable fields, a fishermen's boat shed, two
wooden piers with fishing boats and Luffy's little one-sail boat. ~168 x 156, ground = y 0 at the quay, sea south.
(v2, 2026-10-29: ryan asked for builds ~50% bigger with more rooms and decor, not just magnified: more and bigger
cottages with partitioned, furnished floors and ladders, floors inside the mills, the market, the shed.)

v3 (2026-10-30, audit: "the windmills are good; the layout is a rigid grid, the show has a hillside harbour village"):
the ground now climbs from the flat harbour strip (quay, Partys Bar, the mayor's house, the boat shed) up a real hill
~18 high to the mill knolls and fields on top. The cottages are packed up the slope on stepped stone plinths along
winding lanes that fan out from the top of the quay, with a contour lane across the hill and the market square
levelled into a terrace halfway up (mcb/organic_town.py)."""
from mcb.organic_town import organic_town
import math, zlib
import numpy as np
from mcb.bridge import BigBuild, P, to_canvas

SID = "foosha_village"
TITLE = "Foosha Village"
CUTS = [3, 9, 15]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

NX, NZ = 168, 156
SEA = 126                                 # first water row (wobbles a little)
QUAY = (33, 144)                          # x range of the stone quay wall
MILLS = ((27, 21, 1.5), (87, 15, 1.7), (141, 24, 1.35))
STREET = (66, 69)                         # z rows of the main street
LANE = (68, 73)                           # x columns of the lane down to the quay
SQUARE = (71, 68, 12, 8)                  # cx, cz, rx, rz of the market square

PLASTER = ["minecraft:calcite", "minecraft:white_concrete_powder", "minecraft:white_terracotta"]
FRAME = "minecraft:stripped_spruce_log"
STONE = ["minecraft:cobblestone", "minecraft:stone_bricks", "minecraft:mossy_cobblestone"]
ROOFS = ["minecraft:dark_oak_stairs", "minecraft:spruce_stairs", "minecraft:mud_brick_stairs", "minecraft:brick_stairs"]
AIR = "minecraft:air"


def seed_of(*a):
    return zlib.crc32(repr(a).encode())


# ------------------------------------------------------------------ terrain
def height(X, Z):
    """Ground height: a gentle slope up to the north (0 at the quay, 4 at the back), knolls under the mills, all of it
    easing to 0 over the last 9 blocks of the west, east and north edges so the site meets the world there."""
    X = np.asarray(X, dtype=float); Z = np.asarray(Z, dtype=float)
    h = _hill(X, Z)
    for (mx, mz, k) in MILLS:
        d = np.sqrt((X - mx) ** 2 + (Z - mz) ** 2) / (12 * k)
        h = np.maximum(h, np.where(d < 1, HILL_TOP + 4.0 * k * (1 - d * d), 0))
    cx, cz, rx, rz = SQUARE                                # the market square is a level terrace
    q = ((X - cx) / (rx + 3)) ** 2 + ((Z - cz) / (rz + 3)) ** 2
    h = np.where(q <= 1, float(np.floor(_hill(np.array(cx, float), np.array(cz, float)))), h)
    edge = np.minimum(np.minimum(np.clip(X / 22.0, 0, 1), np.clip((NX - 1 - X) / 22.0, 0, 1)), np.clip(Z / 22.0, 0, 1))
    return np.floor(h * edge + 0.0001)


HILL_TOP = 18


def _hill(X, Z):
    t = np.clip((84 - Z) / 42.0, 0, 1)
    return 1 + (HILL_TOP - 1) * t * t * (3 - 2 * t) + 1.2 * np.sin(X * 0.09) * t * (1 - t) * 4


def H(x, z):
    return int(height(x, z))


def sea_line(x):
    return SEA + int(round(3 * math.sin(x * 0.06)))


def build_terrain(bb):
    X = np.arange(0, NX)[:, None]; Z = np.arange(0, NZ)[None, :]
    land = Z < np.array([sea_line(x) for x in range(NX)])[:, None]
    Hm = np.where(land, height(X, Z), -1)
    bb.heightfield(0, 0, NX - 1, NZ - 1, -4, lambda X_, Z_: Hm, "minecraft:dirt")
    for y in range(-1, int(Hm.max()) + 1):
        m = (Hm == y) & land
        bb.fill_where(0, y, 0, NX - 1, y, NZ - 1, lambda X_, yy, Z_, m=m: m, "minecraft:grass_block[snowy=false]")
    # the sea: sand floor, water to y 0, a sandy beach where there's no quay
    for x in range(NX):
        s = sea_line(x)
        for z in range(s, NZ):
            depth = min(7, 1 + (z - s) // 3)
            bb.fill(x, -depth - 1, z, x, -depth - 1, z, "minecraft:sand")
            bb.fill(x, -depth, z, x, 0, z, "minecraft:water[level=0]")
        if not (QUAY[0] <= x <= QUAY[1]):
            for z in range(s - 5, s):
                bb.set(x, 0, z, "minecraft:sand"); bb.set(x, -1, z, "minecraft:sandstone")


def build_quay(bb, rng):
    """Stone quay along the harbour: a wall from the sea bed, a stone-paved top with a kerb of bollards, steps down
    to the water, two wooden piers out to sea, crates, barrels, nets and fish-drying racks."""
    x1, x2 = QUAY
    for x in range(x1, x2 + 1):
        s = sea_line(x)
        for z in range(s - 7, s + 1):
            for y in range(-6, 1):
                bb.set(x, y, z, STONE[int(rng.integers(3))] if z == s else "minecraft:stone")
            bb.set(x, 0, z, "minecraft:stone_bricks" if z < s else "minecraft:polished_andesite")
            for y in range(1, 4):
                bb.set(x, y, z, AIR)
        if x % 9 == 4:
            bb.set(x, 1, s, "minecraft:andesite_wall")
    for xs in (x1 + 14, x2 - 18):            # two flights of steps down into the water
        s = sea_line(xs)
        for i in range(4):
            bb.fill(xs, -i, s + 1 + i, xs + 3, -i, s + 1 + i, "minecraft:stone_brick_stairs[facing=north,half=bottom]")
            bb.fill(xs, -i - 1, s + 1 + i, xs + 3, -i - 1, s + 1 + i, "minecraft:stone_bricks")
    # wooden piers: decks at y 0 (the town's docks must sit at the water surface for the fishers)
    for (px, length) in ((70, 24), (117, 17)):
        s = sea_line(px)
        for z in range(s + 1, s + length + 1):
            bb.fill(px - 2, 0, z, px + 2, 0, z, "minecraft:spruce_planks")
            bb.set(px - 3, 0, z, "minecraft:stripped_spruce_log[axis=z]"); bb.set(px + 3, 0, z, "minecraft:stripped_spruce_log[axis=z]")
            if (z - s) % 4 == 0:
                for dx in (-3, 3):
                    bb.fill(px + dx, -8, z, px + dx, 1, z, "minecraft:spruce_log[axis=y]")
                    bb.set(px + dx, 2, z, "minecraft:spruce_fence")
            if (z - s) % 8 == 6:
                bb.fill(px + 3, 1, z, px + 3, 2, z, "minecraft:spruce_fence")
                bb.set(px + 3, 3, z, "minecraft:lantern[hanging=false]")
    # quay clutter
    for (x, kind) in ((40, "barrel"), (41, "barrel"), (40, "barrel2"), (58, "crate"), (82, "rack"), (96, "barrel"),
                      (104, "net"), (128, "crate"), (130, "crate"), (138, "rack")):
        s = sea_line(x)
        z = s - 6
        if kind == "barrel":
            bb.set(x, 1, z, "minecraft:barrel[facing=up]")
        elif kind == "barrel2":
            bb.set(x, 2, z, "minecraft:barrel[facing=up]"); bb.set(x, 1, z, "minecraft:barrel[facing=up]")
        elif kind == "crate":
            bb.set(x, 1, z, "minecraft:spruce_planks"); bb.set(x, 2, z, "minecraft:spruce_trapdoor[facing=north,half=bottom,open=false]")
            bb.set(x + 1, 1, z, "minecraft:spruce_planks")
        elif kind == "rack":                   # fish-drying rack: two posts, a pole, hanging dried kelp
            bb.fill(x, 1, z, x, 3, z, "minecraft:spruce_fence"); bb.fill(x + 4, 1, z, x + 4, 3, z, "minecraft:spruce_fence")
            bb.fill(x + 1, 3, z, x + 3, 3, z, "minecraft:spruce_fence")
            for k in range(1, 4):
                bb.set(x + k, 2, z, "minecraft:dried_kelp_block" if k == 2 else "minecraft:iron_chain[axis=y]")
        else:
            bb.fill(x, 1, z, x, 3, z, "minecraft:spruce_fence"); bb.fill(x + 3, 1, z, x + 3, 3, z, "minecraft:spruce_fence")
            bb.fill(x + 1, 3, z, x + 2, 3, z, "minecraft:spruce_fence")
            bb.fill(x + 1, 2, z, x + 2, 2, z, "minecraft:cobweb")


def boat(bb, bx, bz, length=7, sail="minecraft:white_wool", mast=7, cargo=True):
    """A little clinker boat with one mast and a square sail, bow to the south."""
    half = length // 2
    for dz in range(-half, half + 1):
        w = 1 if abs(dz) < half else 0
        bb.fill(bx - w - 1, 0, bz + dz, bx + w + 1, 0, bz + dz, "minecraft:oak_planks")
        if abs(dz) < half:
            bb.fill(bx - w, 0, bz + dz, bx + w, 0, bz + dz, AIR)
        bb.fill(bx - w, -1, bz + dz, bx + w, -1, bz + dz, "minecraft:oak_planks")
    bb.set(bx, 0, bz + 1, "minecraft:oak_slab[type=bottom]")
    bb.fill(bx, 0, bz - 1, bx, mast, bz - 1, "minecraft:spruce_fence")
    bb.fill(bx - 2, mast, bz - 1, bx + 2, mast, bz - 1, "minecraft:spruce_fence")
    bb.fill(bx - 2, 3, bz - 2, bx + 2, mast - 1, bz - 2, sail)
    if cargo:
        bb.set(bx, 0, bz + 2, "minecraft:barrel[facing=up]")


# ------------------------------------------------------------------ houses (modules, stamped with rotation)
FH = 5                                            # storey: 4 clear + beam


def house_module(seed, w, d, floors, roof, tracker, kinds, chimney=True):
    """A Foosha cottage, door on the south (+z) face, footprint x 0..w-1, z 0..d-1, floor at y 0.
    Timber frame (posts every 3) with plaster infill, stone plinth course, framed windows with sills, flower boxes
    upstairs, a jettied upper floor, a gable roof with overhang, a chimney, a ladder up the west wall, and every floor
    furnished (wider houses split into two or three rooms). Returns (module, top y, audit lines)."""
    rng = np.random.default_rng(seed)
    m = BigBuild(seed=seed, y_min=-6, y_max=40)
    m.fill(0, -6, 0, w - 1, -1, d - 1, STONE[1])
    m.fill(-1, -6, -1, w, 0, d, STONE[0])           # plinth course, 1 wider
    m.mix(-1, -1, -1, w, 0, d, STONE, [0.6, 0.25, 0.15])
    m.fill(0, 0, 0, w - 1, 0, d - 1, "minecraft:spruce_planks")
    top = 0
    rooms = []
    for f in range(floors):
        y0 = 1 + f * (FH + 1)
        jet = 1 if f > 0 else 0                     # upper floors jut out 1 on the front and back
        z1, z2 = -jet, d - 1 + jet
        for (x, y, z) in [(x, y, z) for x in range(w) for y in range(y0, y0 + FH) for z in (z1, z2)] + \
                         [(x, y, z) for x in (0, w - 1) for y in range(y0, y0 + FH) for z in range(z1, z2 + 1)]:
            v = rng.random()
            m.set(x, y, z, PLASTER[0] if v < 0.6 else PLASTER[1] if v < 0.9 else PLASTER[2])
        m.fill(1, y0, z1 + 1, w - 2, y0 + FH - 1, z2 - 1, AIR)
        posts_x = sorted(set([0, w - 1] + list(range(3, w - 1, 3))))
        posts_z = sorted(set([z1, z2] + list(range(z1 + 3, z2, 3))))
        for x in posts_x:
            for z in (z1, z2):
                m.fill(x, y0, z, x, y0 + FH - 1, z, f"{FRAME}[axis=y]")
        for z in posts_z:
            for x in (0, w - 1):
                m.fill(x, y0, z, x, y0 + FH - 1, z, f"{FRAME}[axis=y]")
        by = y0 + FH
        m.fill(0, by, z1, w - 1, by, z1, f"{FRAME}[axis=x]"); m.fill(0, by, z2, w - 1, by, z2, f"{FRAME}[axis=x]")
        m.fill(0, by, z1, 0, by, z2, f"{FRAME}[axis=z]"); m.fill(w - 1, by, z1, w - 1, by, z2, f"{FRAME}[axis=z]")
        m.fill(1, by, z1 + 1, w - 2, by, z2 - 1, "minecraft:spruce_planks")
        if jet:   # stair mouldings under the jetty
            m.fill(0, y0 - 1, z1, w - 1, y0 - 1, z1, "minecraft:spruce_stairs[facing=south,half=top]")
            m.fill(0, y0 - 1, z2, w - 1, y0 - 1, z2, "minecraft:spruce_stairs[facing=north,half=top]")
        # windows between posts: 1 wide, 2 tall, sill stair, flower box upstairs
        for z, out in ((z1, -1), (z2, 1)):
            face = "north" if out < 0 else "south"
            for i in range(len(posts_x) - 1):
                xc = (posts_x[i] + posts_x[i + 1]) // 2
                if f == 0 and z == z2 and abs(xc - w // 2) <= 1:
                    continue                          # the door goes here
                if rng.random() < 0.12:
                    continue                          # a blank bay now and then
                m.fill(xc, y0 + 1, z, xc, y0 + 2, z, "minecraft:glass_pane")
                m.set(xc, y0 + 3, z, f"minecraft:spruce_trapdoor[facing={face},half=top,open=true]") if rng.random() < 0.3 else None
                m.set(xc, y0, z + out, f"minecraft:spruce_stairs[facing={'south' if out < 0 else 'north'},half=top]")
                if f > 0:
                    m.set(xc, y0, z + out, f"onepiece:flower_box[facing={face}]")
        for x, out in ((0, -1), (w - 1, 1)):
            for zc in range(z1 + 2, z2 - 1, 4):
                m.fill(x, y0 + 1, zc, x, y0 + 2, zc, "minecraft:glass_pane")
                m.set(x + out, y0, zc, f"minecraft:spruce_stairs[facing={'east' if out < 0 else 'west'},half=top]")
        top = by
    # ladder up the west wall through every floor
    if floors > 1:
        m.fill(1, 1, 2, 1, top - FH - 1 + 1, 2, "minecraft:ladder[facing=east]")
        for f in range(1, floors):
            m.set(1, f * (FH + 1), 2, "minecraft:ladder[facing=east]")
    # door, step, awning, wall lamp
    dx = w // 2
    m.set(dx, 1, d - 1, "minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false]")
    m.set(dx, 2, d - 1, "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
    m.set(dx, 0, d, "minecraft:stone_brick_stairs[facing=north,half=bottom]")
    m.fill(dx - 1, 4, d, dx + 1, 4, d, "minecraft:spruce_slab[type=top]")
    m.set(dx + 1, 3, d, "onepiece:wall_lamp[facing=south]")
    # furnish each floor; wide floors are split into rooms
    audit = []
    for f in range(floors):
        fy = 1 + f * (FH + 1)
        jet = 1 if f > 0 else 0
        rm = (2, 1 - jet, w - 2, d - 2 + jet)
        doors = [(dx, d - 1)] if f == 0 else []
        doors += [(1, 2)]
        kind = kinds[min(f, len(kinds) - 1)]
        if w >= 11:
            rms, pdoors = P.bsp_rooms(m, *rm, fy, FH - 1, "minecraft:spruce_planks", min_room=4, seed=seed + f, max_room=8)
            doors += list(pdoors)
            alt = {"kitchen": "living", "bedroom": "bedroom", "living": "kitchen"}
        else:
            rms, alt = [rm], {}
        for i, r in enumerate(rms):
            k = kind if i == 0 else alt.get(kind, kind)
            P.furnish_room(m, r, fy, kind=k, height=FH - 1, seed=seed + 10 * f + i, wood="spruce", tracker=tracker,
                           doors=doors)
            txt, ok = P.audit_props(m, [r], fy, FH - 1)
            if not ok:
                audit.append(txt)
        m.fill(dx, 1, d - 2, dx, 2, d - 2, AIR) if f == 0 else None     # keep the way in clear
    # gable roof, ridge along x, eaves overhang 1, gable ends in plaster with a little window
    jet = 1 if floors > 1 else 0
    P.gable_roof(m, -1, -1 - jet, w, d + jet, top + 1, roof, gable_fill=PLASTER[0], overhang=1, ends_overhang=0)
    m.fill(-1, top, -1 - jet - 1, w, top, -1 - jet - 1, AIR)
    for x in (0, w - 1):
        m.set(x, top + 2, d // 2, "minecraft:glass_pane")
    if chimney:
        cx = w - 2 if rng.random() < 0.5 else 1
        h = top + (d + 2 * jet) // 2 + 3
        m.fill(cx, 1, -1 - jet, cx, h, -1 - jet, "minecraft:bricks")
        m.set(cx, h + 1, -1 - jet, "minecraft:campfire[lit=true,signal_fire=false,facing=north]")
    return m, top, audit


def place_house(bb, mod, w, d, x0, y, z0, rot):
    """Stamp a module so its footprint's minimum corner lands on (x0, z0) whatever the rotation."""
    cs = [(0, 0), (w - 1, 0), (0, d - 1), (w - 1, d - 1)]
    rc = []
    for (cx, cz) in cs:
        for _ in range(rot % 4):
            cx, cz = -cz, cx
        rc.append((cx, cz))
    mx, mz = min(c[0] for c in rc), min(c[1] for c in rc)
    bb.stamp(mod, x0 - mx, y, z0 - mz, rot=rot, include_air=True)
    W, D = (w, d) if rot % 2 == 0 else (d, w)
    return W, D


# ------------------------------------------------------------------ hero buildings
def windmill(bb, cx, cz, k, tracker, audit):
    """Smock mill: a stone base, a tapering eight-sided white tower with timber corner posts, three floors inside on a
    central shaft with a ladder, a stage gallery with a railing, a boat-shaped dark cap, and four big lattice sails set
    as an X on the south face."""
    y0 = H(cx, cz)
    Ht = int(round(20 * k))
    r0, r1 = 5.5 * k, 3.6 * k
    def octagon(r):
        return lambda X, y, Z: (np.abs(X - cx) <= r) & (np.abs(Z - cz) <= r) & (np.abs(X - cx) + np.abs(Z - cz) <= r * 1.42)
    def rad(y):
        return r0 + (r1 - r0) * max(0.0, (y - y0) / Ht)
    for y in range(y0 - 4, y0 + Ht + 1):
        r = rad(y)
        o = octagon(r); i = octagon(r - 1)
        if y <= y0 + 4:
            bb.fill_where(int(cx - r0 - 2), y, int(cz - r0 - 2), int(cx + r0 + 2), y, int(cz + r0 + 2),
                          lambda X, yy, Z: octagon(r0 + 0.8)(X, yy, Z), STONE[1])
            if y > y0:
                bb.fill_where(int(cx - r0), y, int(cz - r0), int(cx + r0), y, int(cz + r0), lambda X, yy, Z: octagon(r0 - 0.2)(X, yy, Z), AIR)
            continue
        bb.fill_where(int(cx - r - 1), y, int(cz - r - 1), int(cx + r + 1), y, int(cz + r + 1),
                      lambda X, yy, Z: o(X, yy, Z) & ~i(X, yy, Z), PLASTER[0] if y % 6 else f"{FRAME}[axis=y]")
        bb.fill_where(int(cx - r), y, int(cz - r), int(cx + r), y, int(cz + r), lambda X, yy, Z: i(X, yy, Z), AIR)
    bb.fill_where(int(cx - r0), y0, int(cz - r0), int(cx + r0), y0, int(cz + r0), lambda X, yy, Z: octagon(r0)(X, yy, Z), "minecraft:spruce_planks")
    # timber corner posts up the eight corners: darker vertical lines that give the tower its smock look
    for y in range(y0 + 5, y0 + Ht + 1):
        r = int(round(rad(y)))
        for (sx, sz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bb.set(cx + sx * r, y, cz + sz * r, f"{FRAME}[axis=y]")
    # little windows up the tower
    for y in range(y0 + 7, y0 + Ht - 2, 6):
        r = int(round(rad(y)))
        for (sx, sz) in ((1, 0), (-1, 0)):
            bb.fill(cx + sx * r, y, cz + 2, cx + sx * r, y + 1, cz + 2, "minecraft:glass_pane")
    # central shaft with a ladder on its south face; floors at the gallery and two thirds up
    gy = y0 + int(round(7 * k))
    fy2 = y0 + int(round(14 * k))
    bb.fill(cx, y0 + 1, cz, cx, y0 + Ht, cz, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.fill(cx, y0 + 1, cz + 1, cx, fy2 + 1, cz + 1, "minecraft:ladder[facing=south]")
    for fy in (gy, fy2):
        bb.fill_where(int(cx - r0), fy, int(cz - r0), int(cx + r0), fy, int(cz + r0),
                      lambda X, y, Z, fy=fy: octagon(rad(fy) - 1)(X, y, Z) & ~((X == cx) & (Z == cz)), "minecraft:spruce_planks")
        bb.set(cx, fy, cz + 1, "minecraft:ladder[facing=south]")
    # stage gallery round the outside at the gallery floor
    gr = rad(gy) + 3
    bb.fill_where(int(cx - gr - 1), gy, int(cz - gr - 1), int(cx + gr + 1), gy, int(cz + gr + 1),
                  lambda X, y, Z: octagon(gr)(X, y, Z) & ~octagon(gr - 3.2)(X, y, Z), "minecraft:spruce_slab[type=top]")
    bb.fill_where(int(cx - gr - 1), gy + 1, int(cz - gr - 1), int(cx + gr + 1), gy + 1, int(cz + gr + 1),
                  lambda X, y, Z: octagon(gr)(X, y, Z) & ~octagon(gr - 0.9)(X, y, Z), "minecraft:spruce_fence")
    for (sx, sz) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        bb.fill(int(round(cx + sx * (gr - 2))), gy - 2, int(round(cz + sz * (gr - 2))),
                int(round(cx + sx * (gr - 2))), gy - 1, int(round(cz + sz * (gr - 2))), "minecraft:spruce_fence")
    # doors: ground door south, gallery door south
    bb.set(cx, y0 + 1, cz + int(r0 + 0.8), "minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false]")
    bb.set(cx, y0 + 2, cz + int(r0 + 0.8), "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
    rg = int(round(rad(gy + 1)))
    bb.set(cx, gy + 1, cz + rg, "minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false]")
    bb.set(cx, gy + 2, cz + rg, "minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false]")
    # inside: sacks and the composter below, millstones at the gallery floor, stores above
    q = int(rad(gy) * 0.55)
    bb.set(cx + 2, y0 + 1, cz - 2, "minecraft:composter[level=0]")
    bb.fill(cx - 3, y0 + 1, cz - 2, cx - 3, y0 + 2, cz - 2, "minecraft:hay_block[axis=y]")
    bb.set(cx - 2, y0 + 1, cz - 3, "minecraft:hay_block[axis=x]")
    bb.set(cx + 3, y0 + 1, cz + 1, "minecraft:barrel[facing=up]")
    bb.set(cx + 2, gy + 1, cz - 1, "minecraft:grindstone[face=floor,facing=north]")
    bb.set(cx - 2, gy + 1, cz - 1, "minecraft:grindstone[face=floor,facing=north]")
    bb.set(cx - 1, gy + 1, cz - q, "minecraft:hay_block[axis=y]")
    bb.set(cx + 1, gy + 1, cz - q, "minecraft:barrel[facing=up]")
    bb.set(cx - q, fy2 + 1, cz - 1, "minecraft:barrel[facing=up]")
    bb.set(cx - q, fy2 + 2, cz - 1, "minecraft:barrel[facing=up]")
    bb.set(cx + q, fy2 + 1, cz - 1, "minecraft:chiseled_bookshelf[facing=west]")
    bb.set(cx + q - 1, fy2 + 1, cz + 1, "minecraft:lantern[hanging=false]")
    # cap: a boat-shaped roof of dark stairs, long axis north-south
    top = y0 + Ht + 1
    cw = int(round(r1)) + 1
    for i in range(cw + 1):
        a, c = cx - cw + i, cx + cw - i
        if a > c:
            break
        for z in range(cz - cw - 1 + i // 2, cz + cw + 2 - i // 2):
            if a == c:
                bb.set(a, top + i, z, "minecraft:dark_oak_slab[type=bottom]")
            else:
                bb.set(a, top + i, z, "minecraft:dark_oak_stairs[facing=east,half=bottom]")
                bb.set(c, top + i, z, "minecraft:dark_oak_stairs[facing=west,half=bottom]")
                if c - a > 1:
                    bb.fill(a + 1, top + i, z, c - 1, top + i, z, "minecraft:dark_oak_planks")
    # windshaft out of the cap and the sails as an X
    hy = top + 1
    zs = cz + cw + 3
    bb.fill(cx, hy, cz, cx, hy, zs, "minecraft:stripped_dark_oak_log[axis=z]")
    bb.set(cx, hy, zs, "minecraft:dark_oak_log[axis=z]")
    R = int(round(15 * k))
    bw = 4.5 * k / 1.0 * 0.85                   # sail width
    base = math.radians(20 + (cx * 7) % 25)
    for yy in range(hy - R - 1, hy + R + 2):
        for xx in range(cx - R - 1, cx + R + 2):
            u, v = xx - cx, yy - hy
            for arm in range(4):
                th = base + arm * math.pi / 2
                along = u * math.cos(th) + v * math.sin(th)
                across = -u * math.sin(th) + v * math.cos(th)
                if along < 0.5 or along > R + 0.5:
                    continue
                if abs(across) <= 0.6:
                    blk = "minecraft:stripped_spruce_log[axis=z]"
                elif 0.6 < across <= bw and along >= 3.0:
                    edge = across > bw - 1 or along > R - 0.5 or (along % 3) < 0.9
                    blk = "minecraft:spruce_planks" if edge else "minecraft:white_wool"
                else:
                    continue
                if yy <= H(xx, zs) + 1:
                    continue
                bb.set(xx, yy, zs, blk)
                break


def partys_bar(bb, x0, z0, tracker, audit):
    """Makino's Partys Bar: a wide two-storey tavern of warm planks on a stone base, front porch with posts under a
    lean-to roof, a big PARTYS BAR false front, a fireplace, Makino's rooms upstairs, a red-brown gable roof."""
    w, d = 34, 18
    y = H(x0 + w // 2, z0 + d // 2)
    bb.fill(x0 - 1, y - 5, z0 - 1, x0 + w, y, z0 + d, STONE[0])
    bb.mix(x0 - 1, y - 1, z0 - 1, x0 + w, y, z0 + d, STONE, [0.6, 0.25, 0.15])
    bb.fill(x0, y, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:dark_oak_planks")
    WALL = ["minecraft:spruce_planks", "minecraft:oak_planks"]
    LOG = "minecraft:stripped_dark_oak_log"
    for f, (y0, hh) in enumerate(((y + 1, 6), (y + 8, 5))):
        bb.walls(x0, y0, z0, x0 + w - 1, y0 + hh - 1, z0 + d - 1, WALL[0])
        bb.mix(x0, y0, z0, x0 + w - 1, y0 + hh - 1, z0 + d - 1, WALL, [0.65, 0.35])
        bb.fill(x0 + 1, y0, z0 + 1, x0 + w - 2, y0 + hh - 1, z0 + d - 2, AIR)
        for x in list(range(x0, x0 + w, 4)) + [x0 + w - 1]:
            for z in (z0, z0 + d - 1):
                bb.fill(x, y0, z, x, y0 + hh - 1, z, f"{LOG}[axis=y]")
        for x in (x0, x0 + w - 1):
            for z in list(range(z0, z0 + d, 4)) + [z0 + d - 1]:
                bb.fill(x, y0, z, x, y0 + hh - 1, z, f"{LOG}[axis=y]")
        by = y0 + hh
        bb.fill(x0, by, z0, x0 + w - 1, by, z0, f"{LOG}[axis=x]")
        bb.fill(x0, by, z0 + d - 1, x0 + w - 1, by, z0 + d - 1, f"{LOG}[axis=x]")
        bb.fill(x0, by, z0, x0, by, z0 + d - 1, f"{LOG}[axis=z]")
        bb.fill(x0 + w - 1, by, z0, x0 + w - 1, by, z0 + d - 1, f"{LOG}[axis=z]")
        bb.fill(x0 + 1, by, z0 + 1, x0 + w - 2, by, z0 + d - 2, "minecraft:spruce_planks")
        # windows: 2 wide in each bay; tall ones on the ground floor front
        for x in range(x0 + 1, x0 + w - 3, 4):
            for z, out in ((z0, -1), (z0 + d - 1, 1)):
                if f == 0 and z == z0 + d - 1 and x0 + 13 <= x <= x0 + 18:
                    continue
                hgt = 4 if (f == 0 and out > 0) else 2
                bb.fill(x + 1, y0 + 1, z, x + 2, y0 + hgt, z, "minecraft:glass_pane")
                bb.fill(x + 1, y0, z + out, x + 2, y0, z + out,
                        f"minecraft:spruce_stairs[facing={'south' if out < 0 else 'north'},half=top]")
                if f == 1:
                    bb.fill(x + 1, y0, z + out, x + 2, y0, z + out, f"onepiece:flower_box[facing={'north' if out < 0 else 'south'}]")
        for x in (x0, x0 + w - 1):
            for zc in (z0 + 6, z0 + 10):
                bb.fill(x, y0 + 1, zc, x, y0 + 2, zc, "minecraft:glass_pane")
    # front door (double) facing the harbour
    zf = z0 + d - 1
    for dx, hinge in ((16, "left"), (17, "right")):
        bb.set(x0 + dx, y + 1, zf, f"minecraft:spruce_door[facing=south,half=lower,hinge={hinge},open=false]")
        bb.set(x0 + dx, y + 2, zf, f"minecraft:spruce_door[facing=south,half=upper,hinge={hinge},open=false]")
    bb.fill(x0 + 16, y + 3, zf, x0 + 17, y + 3, zf, "minecraft:glass_pane")
    # porch: plank deck, posts, lean-to roof of slabs, benches and barrels
    pz1, pz2 = zf + 1, zf + 5
    bb.fill(x0 - 1, y, pz1, x0 + w, y, pz2, "minecraft:spruce_planks")
    bb.fill(x0 - 1, y - 4, pz2, x0 + w, y - 1, pz2, STONE[0])
    for x in range(x0 - 1, x0 + w + 1, 5):
        bb.fill(x, y + 1, pz2, x, y + 5, pz2, "minecraft:stripped_spruce_log[axis=y]")
        bb.set(x, y + 4, pz2 + 1, "onepiece:wall_lamp[facing=south]") if (x - x0) % 10 == 4 else None
    for i, z in enumerate(range(pz1, pz2 + 2)):
        yy = y + 7 - (1 if i >= 3 else 0)
        bb.fill(x0 - 2, yy, z, x0 + w + 1, yy, z, "minecraft:mangrove_slab[type=bottom]" if i % 2 else "minecraft:mangrove_slab[type=top]")
    for x in (x0 + 3, x0 + 22):
        bb.fill(x, y + 1, pz1 + 1, x + 3, y + 1, pz1 + 1, "minecraft:spruce_stairs[facing=north,half=bottom]")
    for (x, z) in ((x0 + 9, pz1 + 1), (x0 + 10, pz1 + 1), (x0 + 30, pz1 + 2)):
        bb.set(x, y + 1, z, "minecraft:barrel[facing=up]")
    bb.fill(x0 + 15, y, pz2 + 1, x0 + 18, y, pz2 + 1, "minecraft:spruce_stairs[facing=north,half=bottom]")
    # roof: red-brown gable, ridge along x
    top = y + 13
    P.gable_roof(bb, x0 - 1, z0 - 1, x0 + w, z0 + d, top + 1, "minecraft:mud_brick_stairs", gable_fill=WALL[0],
                 overhang=1, ends_overhang=0)
    bb.fill(x0 + 21, y + 1, z0 - 2, x0 + 22, top + 12, z0 - 1, "minecraft:bricks")
    bb.set(x0 + 21, top + 13, z0 - 2, "minecraft:campfire[lit=true,signal_fire=false,facing=north]")
    # the PARTYS BAR false front: a framed board standing on the porch roof (text on the canvas)
    fb1, fb2 = y + 8, y + 27
    bb.fill(x0, fb1, zf + 1, x0 + w - 1, fb2, zf + 1, "minecraft:dark_oak_planks")
    for yy in (fb1, fb2):
        bb.fill(x0, yy, zf + 1, x0 + w - 1, yy, zf + 1, "minecraft:stripped_spruce_log[axis=x]")
    for xx in (x0, x0 + w - 1):
        bb.fill(xx, fb1, zf + 1, xx, fb2, zf + 1, "minecraft:stripped_spruce_log[axis=y]")
    bb.fill(x0 + 1, fb2 + 1, zf + 1, x0 + w - 2, fb2 + 1, zf + 1, "minecraft:spruce_slab[type=bottom]")
    bb.fill(x0 + w // 2 - 2, fb2 + 2, zf + 1, x0 + w // 2 + 1, fb2 + 2, zf + 1, "minecraft:spruce_slab[type=bottom]")
    for xx in (x0 + 3, x0 + w - 4):   # braces behind the board down to the roof
        bb.fill(xx, y + 14, zf, xx, fb2 - 1, zf, "minecraft:stripped_spruce_log[axis=y]")
    # inside: long counter with stools, bottles and barrels behind, tables, a fireplace, stairs up
    cy = y + 1
    for x in range(x0 + 4, x0 + w - 7):
        bb.set(x, cy - 1, z0 + 5, "minecraft:spruce_planks")       # counters need a solid floor or they pop off
        bb.set(x, cy, z0 + 5, "onepiece:spruce_counter[facing=south]")
        if x % 2:
            bb.set(x, cy, z0 + 7, "minecraft:spruce_trapdoor[facing=north,half=top,open=false]")
    for x in range(x0 + 2, x0 + w - 7, 2):
        bb.set(x, cy, z0 + 1, "minecraft:barrel[facing=south]")
        bb.set(x, cy + 2, z0 + 1, "minecraft:spruce_slab[type=bottom]")
    for x in range(x0 + 3, x0 + w - 7, 2):
        bb.set(x, cy + 1, z0 + 1, "minecraft:barrel[facing=south]")
    for x in (x0 + 6, x0 + 14):
        bb.set(x, cy + 1, z0 + 5, "minecraft:brewing_stand[has_bottle_0=true,has_bottle_1=true,has_bottle_2=false]")
    for (tx, tz) in ((x0 + 5, z0 + 11), (x0 + 12, z0 + 13), (x0 + 22, z0 + 11), (x0 + 27, z0 + 14)):
        bb.set(tx, cy, tz, "minecraft:spruce_fence"); bb.set(tx, cy + 1, tz, "minecraft:red_carpet")
        for (dx, dz, fc) in ((1, 0, "west"), (-1, 0, "east"), (0, -1, "south"), (0, 1, "north")):
            bb.set(tx + dx, cy, tz + dz, f"minecraft:spruce_stairs[facing={fc},half=bottom]")
    # fireplace on the west wall
    bb.fill(x0, cy, z0 + 9, x0 + 1, cy + 4, z0 + 12, "minecraft:bricks")
    bb.fill(x0 + 1, cy, z0 + 10, x0 + 1, cy + 1, z0 + 11, AIR)
    bb.set(x0 + 1, cy, z0 + 10, "minecraft:campfire[lit=true,signal_fire=false,facing=east]")
    bb.set(x0 + 1, cy, z0 + 11, "minecraft:campfire[lit=true,signal_fire=false,facing=east]")
    bb.set(x0 + 2, cy + 4, z0 + 10, "minecraft:spruce_slab[type=top]")
    P.stair_run(bb, x0 + w - 3, cy, z0 + 1, 7, 1, "south", "minecraft:spruce_stairs")
    bb.fill(x0 + w - 3, y + 7, z0 + 1, x0 + w - 3, y + 7, z0 + 5, AIR)
    # upstairs: Makino's rooms
    uy = y + 8
    rms, doors = P.bsp_rooms(bb, x0 + 1, z0 + 1, x0 + w - 5, z0 + d - 2, uy, 5, "minecraft:spruce_planks",
                             min_room=5, seed=777, max_room=10)
    kinds = ["bedroom", "living", "storage", "bedroom", "library"]
    for i, rm in enumerate(rms):
        P.furnish_room(bb, rm, uy, kind=kinds[i % len(kinds)], height=5, seed=780 + i, wood="spruce",
                       tracker=tracker, doors=list(doors) + [(x0 + w - 4, z0 + 7)])
        txt, ok = P.audit_props(bb, [rm], uy, 5)
        if not ok:
            audit.append(txt)
    bb.fill(x0 + w - 4, uy, z0 + 1, x0 + w - 4, uy + 4, z0 + d - 2, "minecraft:spruce_planks")
    bb.fill(x0 + w - 4, uy, z0 + 9, x0 + w - 4, uy + 1, z0 + 9, AIR)
    return (x0, y, z0, w, d)


def mayor_house(bb, x0, z0, tracker, audit):
    """Woop Slap's house: a stone ground floor, timber-framed upper floors and a garden wall with a gate in front."""
    w, d = 19, 14
    y = H(x0 + w // 2, z0 + d // 2)
    mod, top, au = house_module(seed_of("mayor"), w, d, 2, "minecraft:spruce_stairs", tracker, ["living", "bedroom"])
    audit += au
    place_house(bb, mod, w, d, x0, y, z0, 0)
    reg = bb.get_region(x0, y + 1, z0, x0 + w - 1, y + FH, z0 + d - 1)
    for name in PLASTER:
        if name in bb.ids:
            for (a, b_, c) in np.argwhere(reg == bb.ids[name]):
                bb.set(x0 + int(a), y + 1 + int(b_), z0 + int(c), STONE[1] if (a + c) % 5 else STONE[2])
    for x in range(x0 - 3, x0 + w + 3):
        if abs(x - (x0 + w // 2)) > 1:
            bb.set(x, y + 1, z0 + d + 4, "minecraft:cobblestone_wall")
    for z in range(z0 + d + 1, z0 + d + 4):
        bb.set(x0 - 3, y + 1, z, "minecraft:cobblestone_wall"); bb.set(x0 + w + 2, y + 1, z, "minecraft:cobblestone_wall")
    for x in range(x0 - 2, x0 + w + 2):
        if abs(x - (x0 + w // 2)) > 1 and (x % 3):
            bb.set(x, y + 1, z0 + d + 3, ["minecraft:rose_bush[half=lower]", "minecraft:peony[half=lower]", "minecraft:lilac[half=lower]"][x % 3])
            bb.set(x, y + 2, z0 + d + 3, ["minecraft:rose_bush[half=upper]", "minecraft:peony[half=upper]", "minecraft:lilac[half=upper]"][x % 3])
    return y


def boat_shed(bb, x0, z0):
    """Fishermen's shed: an open-fronted timber shed facing the quay, nets, oars, a boat on trestles."""
    w, d = 15, 10
    y = H(x0 + w // 2, z0 + d // 2)
    bb.fill(x0, y - 3, z0, x0 + w - 1, y, z0 + d - 1, STONE[0])
    bb.fill(x0, y, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:spruce_planks")
    bb.walls(x0, y + 1, z0, x0 + w - 1, y + 6, z0 + d - 1, "minecraft:spruce_planks")
    bb.fill(x0 + 1, y + 1, z0 + 1, x0 + w - 2, y + 6, z0 + d - 2, AIR)
    bb.fill(x0 + 1, y + 1, z0 + d - 1, x0 + w - 2, y + 5, z0 + d - 1, AIR)     # open front
    for x in (x0, x0 + 5, x0 + 9, x0 + w - 1):
        bb.fill(x, y + 1, z0 + d - 1, x, y + 6, z0 + d - 1, "minecraft:stripped_spruce_log[axis=y]")
    P.gable_roof(bb, x0 - 1, z0 - 1, x0 + w, z0 + d, y + 7, "minecraft:spruce_stairs", gable_fill="minecraft:spruce_planks",
                 overhang=1, ends_overhang=0, ridge_axis="x")
    for x in (x0 + 4, x0 + 10):
        bb.set(x, y + 1, z0 + 4, "minecraft:spruce_fence")
    bb.fill(x0 + 3, y + 2, z0 + 3, x0 + 11, y + 2, z0 + 5, "minecraft:oak_planks")
    bb.fill(x0 + 4, y + 2, z0 + 4, x0 + 10, y + 2, z0 + 4, "minecraft:oak_slab[type=bottom]")
    bb.fill(x0 + 1, y + 3, z0 + 1, x0 + w - 2, y + 4, z0 + 1, "minecraft:cobweb")
    for x in range(x0 + 1, x0 + w - 1, 3):
        bb.set(x, y + 1, z0 + 1, "minecraft:barrel[facing=up]")
    bb.set(x0 + 1, y + 1, z0 + 8, "minecraft:crafting_table")
    bb.set(x0 + w - 2, y + 1, z0 + 8, "minecraft:smoker[facing=west,lit=false]")


def market(bb):
    """Stalls with striped awnings round the square, benches, flower tubs."""
    cx, cz, rx, rz = SQUARE
    stalls = ((cx - 9, cz - 6, "red"), (cx + 6, cz - 6, "yellow"), (cx - 9, cz + 4, "blue"), (cx + 6, cz + 4, "lime"))
    goods = [["minecraft:melon", "minecraft:pumpkin", "minecraft:hay_block[axis=y]"],
             ["minecraft:barrel[facing=up]", "minecraft:dried_kelp_block", "minecraft:barrel[facing=up]"]]
    for i, (x, z, col) in enumerate(stalls):
        y = H(x + 1, z + 1)
        for (dx, dz) in ((0, 0), (3, 0), (0, 2), (3, 2)):
            bb.fill(x + dx, y + 1, z + dz, x + dx, y + 3, z + dz, "minecraft:spruce_fence")
        for dx in range(-1, 5):
            for dz in range(-1, 4):
                bb.set(x + dx, y + 4, z + dz, f"minecraft:{col}_wool" if (dx % 2 == 0) else "minecraft:white_wool")
        bb.fill(x + 1, y - 2, z + 2, x + 2, y, z + 2, "minecraft:spruce_planks")
        bb.fill(x + 1, y + 1, z + 2, x + 2, y + 1, z + 2, "onepiece:spruce_counter[facing=south]" if z < cz else "onepiece:spruce_counter[facing=north]")
        for j, dx in enumerate((1, 2)):
            bb.set(x + dx, y + 1, z, goods[i % 2][j])
    for (x, z, f) in ((cx - 2, cz - 7, "south"), (cx + 2, cz - 7, "south"), (cx - 2, cz + 7, "north"), (cx + 2, cz + 7, "north")):
        bb.set(x, H(x, z) + 1, z, f"minecraft:spruce_stairs[facing={f},half=bottom]")
    for (x, z) in ((cx - 12, cz), (cx + 12, cz)):
        y = H(x, z)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                bb.set(x + dx, y + 1, z + dz, "minecraft:stone_brick_wall" if (dx or dz) else "minecraft:flowering_azalea")


def lamp(bb, x, z):
    y = H(x, z)
    bb.fill(x, y + 1, z, x, y + 3, z, "minecraft:spruce_fence")
    bb.set(x, y + 4, z, "minecraft:lantern[hanging=false]")


# ------------------------------------------------------------------ assembly
HOUSES = [  # (x0, z0, w, d, floors, rot) rot 0 = door south; 2 = door north
    (9, 45, 11, 9, 1, 0), (26, 46, 12, 10, 2, 0), (45, 42, 12, 9, 1, 0), (60, 44, 11, 9, 2, 0), (86, 44, 11, 9, 1, 0),
    (103, 45, 12, 9, 2, 0), (121, 42, 12, 10, 1, 0), (142, 49, 11, 9, 1, 0),
    (12, 78, 12, 9, 2, 2), (31, 80, 11, 9, 1, 2), (49, 78, 11, 9, 2, 2), (130, 78, 12, 9, 2, 2), (150, 81, 10, 9, 1, 1),
    (8, 99, 11, 9, 1, 2), (23, 104, 10, 9, 1, 2), (121, 95, 12, 9, 2, 2), (146, 102, 11, 9, 1, 2),
]


def design():
    bb = BigBuild(seed=201, y_min=-10, y_max=100)
    rng = np.random.default_rng(201)
    build_terrain(bb)
    build_quay(bb, rng)
    tracker = P.PropTracker(201)
    audit = []
    # Luffy's dinghy at the end of the long pier, two fishing boats at the short one
    boat(bb, 76, sea_line(70) + 20, length=7, mast=7)
    boat(bb, 111, sea_line(117) + 9, length=9, sail="minecraft:light_blue_wool", mast=9)
    boat(bb, 123, sea_line(117) + 13, length=9, sail="minecraft:yellow_wool", mast=8)
    # the market square: a stone terrace (the ground there is level, see height())
    cx, cz, rx, rz = SQUARE
    for x in range(cx - rx, cx + rx + 1):
        for z in range(cz - rz, cz + rz + 1):
            if (x - cx) ** 2 / rx ** 2 + (z - cz) ** 2 / rz ** 2 <= 1:
                bb.set(x, H(x, z), z, "minecraft:stone_bricks" if (x + z) % 4 else "minecraft:cracked_stone_bricks")
    # the well on the square
    wx, wz = cx, cz
    wy = H(wx, wz)
    bb.fill(wx - 1, wy - 4, wz - 1, wx + 1, wy + 1, wz + 1, "minecraft:cobblestone")
    bb.set(wx, wy + 1, wz, AIR); bb.fill(wx, wy - 3, wz, wx, wy, wz, "minecraft:water[level=0]")
    for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bb.fill(wx + dx, wy + 2, wz + dz, wx + dx, wy + 3, wz + dz, "minecraft:spruce_fence")
    P.hip_roof(bb, wx - 1, wz - 1, wx + 1, wz + 1, wy + 4, "minecraft:spruce_stairs", overhang=1)
    market(bb)
    # cottages up the hill along winding lanes from the top of the quay
    reserved = [(cx - rx - 3, cz - rz - 3, cx + rx + 3, cz + rz + 3), (82, 84, 120, 107), (37, 94, 60, 112), (124, 110, 143, 124),
                (45, 6, 72, 29), (98, 8, 127, 40), (2, 31, 19, 43), (65, 71, 77, 81)]
    reserved += [(int(mx - 13 * k), int(mz - 13 * k), int(mx + 13 * k), int(mz + 13 * k)) for (mx, mz, k) in MILLS]
    ok = lambda x, z: 3 <= x < NX - 3 and 6 <= z < sea_line(x) - 9 and not any(
        a <= x <= c and b_ <= z <= d for (a, b_, c, d) in reserved)
    pal = [dict(walls=PLASTER, frame=FRAME, base=STONE, floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks"),
           dict(walls=PLASTER, frame="minecraft:stripped_dark_oak_log", base=STONE, floor="minecraft:oak_planks", wood="oak",
                chimney="minecraft:cobblestone")]
    S, placed = organic_town(bb, (3, 6, NX - 4, sea_line(70) - 6), (70, 98), ok, 2010, tracker, pal, ROOFS,
                             ["minecraft:dirt_path", "minecraft:coarse_dirt", "minecraft:dirt_path", "minecraft:cobblestone"],
                             52, hy=lambda x, z: H(x, z), spokes=5, rings=((44, 1.4),), width=1.4,
                             sizes=(7, 10), floors=(1, 2), kinds=("kitchen", "bedroom", "living"), plinth=STONE[0],
                             fh=5, timber=True, reserved=reserved, arc=(0.0, math.pi), base=math.pi, max_step=5)
    print("foosha cottages:", len(placed))
    # the lane down to the quay stays cobbled
    for z in range(84, sea_line(70) - 6):
        for x in range(LANE[0], LANE[1] + 1):
            bb.set(x, H(x, z), z, "minecraft:cobblestone" if (x + z) % 3 else "minecraft:mossy_cobblestone")
    # Partys Bar by the quay, mayor's house, the boat shed
    bx = partys_bar(bb, 84, 87, tracker, audit)
    mayor_house(bb, 39, 96, tracker, audit)
    boat_shed(bb, 126, 112)
    # windmills on the knolls, fields below them
    for (mx, mz, k) in MILLS:
        windmill(bb, mx, mz, k, tracker, audit)
    for (fx1, fz1, fx2, fz2, crop) in ((45, 8, 70, 27, "minecraft:wheat[age=7]"), (100, 10, 125, 30, "minecraft:carrots[age=7]"),
                                       (100, 33, 125, 38, "minecraft:potatoes[age=7]"), (4, 33, 17, 41, "minecraft:beetroots[age=3]")):
        # each field is levelled to one height: water channels on a slope spill over the lower rows, wash the crops
        # out and drop them as items when the structure generates
        fy = int(np.median([H(x, z) for x in range(fx1, fx2 + 1) for z in range(fz1, fz2 + 1)]))
        for x in range(fx1, fx2 + 1):
            for z in range(fz1, fz2 + 1):
                hgt = fy
                bb.fill(x, min(H(x, z), fy) - 3, z, x, fy - 1, z, "minecraft:dirt")
                bb.fill(x, fy + 1, z, x, max(H(x, z), fy) + 2, z, AIR)
                if x in (fx1, fx2) or z in (fz1, fz2):
                    bb.set(x, hgt + 1, z, "minecraft:oak_fence")
                elif (x - fx1) % 5 == 0:
                    bb.set(x, hgt, z, "minecraft:water[level=0]")
                else:
                    bb.set(x, hgt, z, "minecraft:farmland[moisture=7]"); bb.set(x, hgt + 1, z, crop)
        bb.set(fx1 + 2, H(fx1 + 2, fz2 + 1) + 1, fz2 + 1, "minecraft:composter[level=0]")
        bb.set(fx1 + 4, H(fx1 + 4, fz2 + 1) + 1, fz2 + 1, "minecraft:hay_block[axis=y]")
        bb.set(fx1 + 5, H(fx1 + 5, fz2 + 1) + 1, fz2 + 1, "minecraft:hay_block[axis=x]")
    # lamp posts along the lanes and down to the quay
    for (i, j) in zip(*np.nonzero(S)):
        x, z = 3 + int(i), 6 + int(j)
        if (x * 7 + z * 11) % 23 == 0 and not S[min(i + 2, S.shape[0] - 1), j] and (bb.get_region(x + 2, H(x + 2, z) + 1, z, x + 2, H(x + 2, z) + 4, z) <= 1).all():
            lamp(bb, x + 2, z)
    for z in range(88, sea_line(70) - 8, 12):
        lamp(bb, LANE[0] - 1, z); lamp(bb, LANE[1] + 1, z + 6)
    # trees and flowers
    trng = np.random.default_rng(5)
    for (tx, tz, kind) in ((6, 33, "oak"), (66, 36, "oak"), (93, 39, "birch"), (156, 36, "oak"), (3, 66, "oak"),
                           (57, 87, "birch"), (126, 72, "oak"), (24, 120, "oak"), (159, 69, "birch"), (82, 33, "oak"),
                           (40, 60, "birch"), (100, 60, "oak"), (160, 92, "oak"), (4, 88, "birch")):
        if (bb.get_region(tx - 2, H(tx, tz) + 1, tz - 2, tx + 2, H(tx, tz) + 9, tz + 2) <= 1).all():
            P.tree(bb, tx, H(tx, tz) + 1, tz, height=int(trng.integers(6, 10)), kind=kind, rng=trng)
    for _ in range(320):
        x, z = int(trng.integers(3, NX - 3)), int(trng.integers(3, SEA - 8))
        hgt = H(x, z)
        if bb.get_region(x, hgt, z, x, hgt, z)[0, 0, 0] == bb.ids.get("minecraft:grass_block[snowy=false]") and \
                bb.get_region(x, hgt + 1, z, x, hgt + 1, z)[0, 0, 0] == 0:
            bb.set(x, hgt + 1, z, ["minecraft:short_grass", "minecraft:poppy", "minecraft:dandelion", "minecraft:oxeye_daisy",
                                   "minecraft:short_grass", "minecraft:cornflower", "minecraft:short_grass"][int(trng.integers(7))])
    return bb, audit, bx


def build():
    bb, audit, (x0, y, z0, w, d) = design()
    for a in audit:
        print("audit:", a)
    b = to_canvas(bb)
    zf = z0 + d
    # PARTYS on top, a big BAR under it, on the false front (reads from the harbour, +z)
    b.text(x0 + (w - 23) // 2, y + 21, zf + 1, "PARTYS", "minecraft:white_concrete", axis="x", step=1)
    b.text(x0 + (w - 22) // 2, y + 10, zf + 1, "BAR", "minecraft:yellow_concrete", axis="x", step=1, scale=2)
    b.npc(71, H(71, 76) + 1, 76, "luffy", False)
    b.chest(x0 + w - 6, y + 1, z0 + 2, "easy", "south")
    return b, 0
