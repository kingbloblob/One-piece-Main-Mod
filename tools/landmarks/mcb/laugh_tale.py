"""Laugh Tale v2, the final island of the Grand Line, redesigned with the Minecraft Builder skill
(dossier: mcb/dossiers/laugh_tale.md).

An irregular island whose ground fades out to its beaches (no square plot): steep sea cliffs round the north and
west, rolling jungle wilderness with giant trees swallowing the ruins of an ancient city, a cove on the south side with
the Roger Pirates' old landing (quay, anchor stone, their long-cold camp), a broken colonnade avenue through the Sun
Gate of Joy Boy, two ring walls of ancient stone, and in the middle the stepped temple of the Void Century: the hall
of murals, the Poneglyph chamber, the Hall of Joy Boy with his straw hat, archive rooms, and at its heart the treasure
room, where a great pile of gold carries Joy Boy's chest and Gol D. Roger waits for whoever made it. Peaceful inside.
176 x 176. y 0 = ground. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, furnish, set_if_air, lamp_post, cornice
from mcb.bridge import to_canvas
from mcb import nature as NT

SID = "laugh_tale"
TITLE = "Laugh Tale (the final island)"
CUTS = [2, 9, 20]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 176
CX, CZ = 88, 84                       # island centre
TX, TZ = 88, 70                       # temple centre
COVE = (88, 158, 20, 22)              # cove ellipse (x, z, rx, rz)
GATE_Z = 125                          # the Sun Gate on the avenue
RINGS = (38, 46)
TIERS = (29, 24, 19, 14, 9)           # temple tier half widths
TH = 7                                # tier height
PILE = (TX, TZ - 9)                   # the gold pile (centre)
ROGER = (TX, TZ + 2)

STONES = ["minecraft:stone_bricks", "minecraft:mossy_stone_bricks", "minecraft:cracked_stone_bricks"]
CHIS = "minecraft:chiseled_stone_bricks"
SB_ST = "minecraft:stone_brick_stairs"
MSB_ST = "minecraft:mossy_stone_brick_stairs"
GOLD = "minecraft:gold_block"
GLYPH = "onepiece:ancient_glyph_stone"
SGOLD = "onepiece:shandora_gold_bricks"
FLOOR = "minecraft:polished_deepslate"
ROCK = [("minecraft:stone", 0.42), ("minecraft:andesite", 0.18), ("minecraft:tuff", 0.12),
        ("minecraft:mossy_cobblestone", 0.12), ("minecraft:grass_block", 0.10), ("minecraft:gravel", 0.06)]
SAND = [("minecraft:sand", 0.8), ("minecraft:gravel", 0.08), ("minecraft:sandstone", 0.06), ("minecraft:clay", 0.06)]

SHORE = NT.outline(CX, CZ, 80, 967)


def in_cove(X, Z):
    x, z, rx, rz = COVE
    return ((X - x) / rx) ** 2 + ((Z - z) / rz) ** 2 < 1


def flatness(X, Z):
    """0 where the town must stay flat (temple, rings, avenue, cove landing), 1 well away from them."""
    d_t = np.hypot(X - TX, Z - TZ) - (RINGS[1] + 4)
    d_a = np.where((Z > TZ) & (Z < COVE[1]), np.abs(X - TX) - 8, 99)
    d_c = np.hypot((X - COVE[0]) / COVE[2], (Z - COVE[1]) / COVE[3]) * COVE[2] - COVE[2] - 6
    d = np.minimum(np.minimum(d_t, d_a), d_c)
    return np.clip(d / 12.0, 0, 1)


def height(X, Z):
    """Ground height: rolling jungle hills, a ring of steep cliffs round the north and west, all fading to the beach."""
    d = SHORE(X, Z)
    inland = np.clip((d - 3) / 16.0, 0, 1)
    hills = NT.fbm(X, Z, 9671, 30) * 11 * inland
    a = np.arctan2(Z - CZ, X - CX)                                  # north-west = -3pi/4
    w = np.clip(np.cos(a + 2.2) * 1.6 - 0.25, 0, 1)                  # strongest NW, nothing on the south
    rise = np.clip((d - 4) / 7.0, 0, 1) * np.clip((40 - d) / 18.0, 0, 1)
    ridge = w * rise * (20 + 14 * NT.fbm(X, Z, 9672, 18))
    h = np.maximum(hills, ridge) * flatness(X, Z)
    h = np.where(d < 2.5, -1, h)
    return np.round(h)


def land(X, Z):
    return (SHORE(X, Z) > 0) & ~in_cove(X, Z)


# ------------------------------------------------------------------ ground
def terrain(bb):
    H = lambda X, Z: height(X, Z)
    NT.cover(bb, 0, 0, N - 1, N - 1, H, SAND, 9601, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) < 6),
             under="minecraft:sandstone", core="minecraft:sandstone")
    NT.cover(bb, 0, 0, N - 1, N - 1, H, ROCK, 9602, mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & (H(X, Z) >= 13),
             under="minecraft:stone", core="minecraft:stone")
    NT.cover(bb, 0, 0, N - 1, N - 1, H, NT.JUNGLE, 9603,
             mask=lambda X, Z: land(X, Z) & (SHORE(X, Z) >= 6) & (H(X, Z) < 13), core="minecraft:stone")
    # the cove: water to y 0 over a sandy bottom that deepens to the open sea
    x, z, rx, rz = COVE

    def cove_depth(X, Z):
        t = ((X - x) / rx) ** 2 + ((Z - z) / rz) ** 2
        return np.where(t < 1, np.round(-1 - 6 * (1 - t) ** 0.5 - 2 * np.clip((Z - z) / rz, 0, 1)), 99)
    for y in range(-10, 1):
        bb.fill_where(x - rx, y, z - rz, x + rx, y, min(N - 1, z + rz), lambda X, yy, Z: (cove_depth(X, Z) < yy) & (SHORE(X, Z) > -3),
                      "minecraft:water")
        bb.fill_where(x - rx, y, z - rz, x + rx, y, min(N - 1, z + rz),
                      lambda X, yy, Z: (cove_depth(X, Z) == yy) & (SHORE(X, Z) > -3), "minecraft:sand")
        bb.fill_where(x - rx, y, z - rz, x + rx, y, min(N - 1, z + rz),
                      lambda X, yy, Z: (cove_depth(X, Z) - 1 == yy) & (SHORE(X, Z) > -3), "minecraft:sandstone")


def hy(x, z):
    return int(height(np.array([[x]]), np.array([[z]]))[0, 0])


# ------------------------------------------------------------------ the temple
def temple(bb, tracker, audit):
    rng = np.random.default_rng(9604)
    for k, hw in enumerate(TIERS):
        y0, y1 = 1 + k * TH, (k + 1) * TH
        bb.mix(TX - hw, y0, TZ - hw, TX + hw, y1, TZ + hw, STONES, [0.62, 0.24, 0.14])
        # frieze band: chiseled stone with gold every fourth block, glyph panels between
        for i in range(-hw, hw + 1):
            blk = GOLD if i % 4 == 0 else (GLYPH if i % 4 == 2 else CHIS)
            for (x, z) in ((TX + i, TZ - hw), (TX + i, TZ + hw), (TX - hw, TZ + i), (TX + hw, TZ + i)):
                bb.set(x, y1 - 1, z, blk)
        # pilasters every 6 and a stair cornice at each tier's lip
        for i in range(-hw + 3, hw - 2, 6):
            for (x, z, dx, dz) in ((TX + i, TZ - hw - 1, 0, 0), (TX + i, TZ + hw + 1, 0, 0),
                                   (TX - hw - 1, TZ + i, 0, 0), (TX + hw + 1, TZ + i, 0, 0)):
                bb.fill(x, y0, z, x, y1 - 2, z, "minecraft:polished_andesite")
        cornice(bb, TX - hw, TZ - hw, TX + hw, TZ + hw, y1, SB_ST)
        if k:
            bb.fill(TX - hw - 1, y0 - 1, TZ - hw - 1, TX + hw + 1, y0 - 1, TZ + hw + 1, "minecraft:stone_bricks")
    # the base course and the ground plinth
    bb.fill(TX - TIERS[0] - 2, -2, TZ - TIERS[0] - 2, TX + TIERS[0] + 2, 0, TZ + TIERS[0] + 2, "minecraft:stone_bricks")
    bb.fill(TX - TIERS[0] - 2, 0, TZ - TIERS[0] - 2, TX + TIERS[0] + 2, 0, TZ + TIERS[0] + 2, "minecraft:polished_andesite")
    top = len(TIERS) * TH
    # summit shrine: four gold-capped pillars, a stepped gold roof and the sun disc of Joy Boy
    s = 4
    bb.fill(TX - s, top + 1, TZ - s, TX + s, top + 1, TZ + s, "minecraft:polished_andesite")
    for (x, z) in ((TX - s, TZ - s), (TX + s, TZ - s), (TX - s, TZ + s), (TX + s, TZ + s)):
        bb.fill(x, top + 2, z, x, top + 7, z, "minecraft:chiseled_stone_bricks")
        bb.set(x, top + 7, z, GOLD)
    for i in range(4):
        bb.fill(TX - s - 1 + i, top + 8 + i, TZ - s - 1 + i, TX + s + 1 - i, top + 8 + i, TZ + s + 1 - i, SGOLD if i % 2 == 0 else GOLD)
    bb.set(TX, top + 2, TZ, "minecraft:lodestone")
    bb.set(TX, top + 7, TZ, "minecraft:lantern[hanging=true]")
    sun_disc(bb, TX, top + 18, TZ, 5, "x")
    bb.fill(TX, top + 12, TZ, TX, top + 12, TZ, GOLD)
    # the climb to the summit up the north face
    for i in range(top + 1):
        z = TZ - 40 + i
        if z > TZ - s - 1:
            break
        if z < TZ - TIERS[0]:                                       # solid ramp under the part outside the temple
            bb.mix(TX - 3, -2, z, TX + 3, i - 1, z, STONES, [0.6, 0.25, 0.15]) if i > 0 else None
        bb.fill(TX - 3, i, z, TX + 3, i, z, st(SB_ST, "south"))
        bb.fill(TX - 3, i + 1, z, TX + 3, i + 4, z, AIR)
        yb = -2 if z < TZ - TIERS[0] else i
        bb.fill(TX - 4, yb, z, TX - 4, i + 1, z, "minecraft:stone_bricks")
        bb.fill(TX + 4, yb, z, TX + 4, i + 1, z, "minecraft:stone_bricks")
    interior(bb, tracker, audit, rng)


def sun_disc(bb, cx, cy, cz, r, axis):
    """Joy Boy's sun: a gold disc with a ring and twelve rays, upright on plane `axis`."""
    for a in range(0, 360, 3):
        t = math.radians(a)
        for rr in np.arange(0, r + 0.5, 0.5):
            u, v = round(rr * math.cos(t)), round(rr * math.sin(t))
            blk = GOLD if rr > r - 1.2 or rr < 1.5 else "minecraft:yellow_terracotta"
            if axis == "x":
                bb.set(cx + u, cy + v, cz, blk)
            else:
                bb.set(cx, cy + v, cz + u, blk)
    for k in range(12):
        t = math.radians(k * 30 + 15)
        for rr in range(r + 1, r + 3 + (k % 2) * 2):
            u, v = round(rr * math.cos(t)), round(rr * math.sin(t))
            if axis == "x":
                bb.set(cx + u, cy + v, cz, SGOLD)
            else:
                bb.set(cx, cy + v, cz + u, SGOLD)


def chandelier(bb, x, ytop, z, drop=3):
    bb.fill(x, ytop - drop, z, x, ytop - 1, z, "minecraft:iron_chain[axis=y]")
    y = ytop - drop - 1
    bb.set(x, y, z, GOLD)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bb.set(x + dx, y, z + dz, "minecraft:polished_blackstone_wall")
        bb.set(x + dx, y - 1, z + dz, "minecraft:lantern[hanging=true]")
    bb.set(x, y - 1, z, "minecraft:lantern[hanging=true]")


def ceiling_lights(bb, x1, z1, x2, z2, y, step):
    """Hidden lights: ochre froglights set into the ceiling on a staggered grid (no clutter, no dark corners)."""
    for i, x in enumerate(range(x1, x2 + 1, step)):
        for z in range(z1 + (i % 2) * (step // 2), z2 + 1, step):
            g = bb.get_region(x, y, z, x, y, z)[0, 0, 0]
            if g not in (0, 1):
                bb.set(x, y, z, "minecraft:ochre_froglight")


def interior(bb, tracker, audit, rng):
    # ---- the treasure room: the heart of the temple
    x1, x2, z1, z2, h = TX - 14, TX + 14, TZ - 19, TZ + 6, 14
    bb.fill(x1, 1, z1, x2, h, z2, AIR)
    bb.fill(x1, 0, z1, x2, 0, z2, FLOOR)
    bb.ring(PILE[0], 0, PILE[1], 7, 8, 0, GOLD)
    for x in range(x1, x2 + 1, 4):                               # gold inlay lines to the door
        bb.set(x, 0, z2, "minecraft:polished_deepslate")
    bb.fill(TX, 0, PILE[1] + 9, TX, 0, z2, SGOLD)
    # colonnade down both sides, glyph murals between the columns, gold capitals, sconces
    for x in (x1 + 2, x2 - 2):
        for z in range(z1 + 3, z2, 5):
            bb.fill(x, 1, z, x, h - 1, z, CHIS)
            bb.set(x, h - 1, z, GOLD)
            bb.set(x, 1, z, "minecraft:polished_andesite")
    for z in range(z1 + 1, z2):
        for (x, f) in ((x1, "east"), (x2, "west")):
            bb.set(x - (1 if x == x1 else -1), 4, z, GLYPH)
            if z % 5 == 0:
                bb.set(x - (1 if x == x1 else -1), 6, z, GOLD)
    for x in range(x1, x2 + 1):
        for y in range(3, 11):
            bb.set(x, y, z1 - 1, GLYPH if (x + y) % 3 else CHIS)
    sun_disc(bb, TX, 9, z1 - 1, 4, "x")
    for (x, z) in ((TX - 7, TZ - 15), (TX + 7, TZ - 15), (TX - 7, TZ - 3), (TX + 7, TZ - 3), (TX, TZ + 3)):
        chandelier(bb, x, h + 1, z, drop=6 if (x + z) % 2 else 7)
    for z in range(z1 + 3, z2, 5):                                # candelabras in front of every column
        for x in (x1 + 3, x2 - 3):
            if abs(z - ROGER[1]) > 4 or abs(x - ROGER[0]) > 4:
                bb.set(x, 1, z, "onepiece:candelabra[facing=north]")
    ceiling_lights(bb, x1 + 2, z1 + 2, x2 - 2, z2 - 2, h + 1, 5)
    gold_pile(bb, rng)
    # coins and treasure piles round the pile's foot, never on Roger's floor
    for _ in range(60):
        a, rr = rng.uniform(0, 6.283), rng.uniform(6.5, 10.5)
        x, z = round(PILE[0] + rr * math.cos(a)), round(PILE[1] + rr * math.sin(a))
        if abs(x - ROGER[0]) <= 5 and z >= ROGER[1] - 5:
            continue
        if x1 + 3 < x < x2 - 3 and z1 < z < z2:
            set_if_air(bb, x, 1, z, "minecraft:light_weighted_pressure_plate" if rng.random() < 0.7 else
                       f"onepiece:treasure_pile[facing={('north', 'east', 'south', 'west')[int(rng.integers(4))]}]")
    # ---- the entrance hall of murals, from the south door
    e1, e2 = TZ + 8, TZ + 25
    bb.fill(TX - 9, 1, e1, TX + 9, 10, e2, AIR)
    bb.fill(TX - 9, 0, e1, TX + 9, 0, e2, "minecraft:polished_andesite")
    bb.fill(TX - 1, 0, e1, TX + 1, 0, e2, FLOOR)
    for z in range(e1 + 2, e2, 4):
        for x in (TX - 7, TX + 7):
            bb.fill(x, 1, z, x, 9, z, CHIS)
            bb.set(x, 9, z, GOLD)
            bb.set(x, 1, z, "minecraft:polished_andesite")
        for y in range(3, 8):
            bb.set(TX - 10, y, z + 1, GLYPH)
            bb.set(TX + 10, y, z + 1, GLYPH)
        bb.set(TX - 6 if z % 8 == 2 else TX + 6, 10, z, "minecraft:lantern[hanging=true]")
    ceiling_lights(bb, TX - 8, e1 + 1, TX + 8, e2 - 1, 11, 4)
    bb.fill(TX - 2, 1, TZ + 7, TX + 2, 6, TZ + 7, AIR)               # into the treasure room
    bb.fill(TX - 3, 7, TZ + 7, TX + 3, 7, TZ + 7, CHIS)
    bb.fill(TX - 2, 1, e2, TX + 2, 6, TZ + TIERS[0] + 2, AIR)        # the great door out
    bb.fill(TX - 3, 7, TZ + TIERS[0] - 1, TX + 3, 8, TZ + TIERS[0] + 1, GOLD)
    for x in (TX - 3, TX + 3):
        bb.fill(x, 1, TZ + TIERS[0] + 1, x, 6, TZ + TIERS[0] + 1, CHIS)
    # ---- west: the Poneglyph chamber and the archive
    w1, w2 = TX - 26, TX - 17
    bb.fill(w1, 1, TZ - 12, w2, 9, TZ + 4, AIR)
    bb.fill(w1, 0, TZ - 12, w2, 0, TZ + 4, FLOOR)
    bb.fill(TX - 16, 1, TZ - 6, TX - 15, 5, TZ - 2, AIR)             # doorway from the treasure room
    bb.fill(w1 + 1, 1, TZ - 5, w1 + 2, 1, TZ - 1, "minecraft:polished_andesite")
    bb.fill(w1 + 1, 2, TZ - 4, w1 + 1, 4, TZ - 2, "onepiece:poneglyph")
    for (x, z) in ((w1 + 3, TZ - 6), (w1 + 3, TZ)):
        bb.set(x, 1, z, CHIS)
        bb.set(x, 2, z, "minecraft:candle[candles=3,lit=true,waterlogged=false]")
    bb.set(w1 + 6, 1, TZ - 3, "minecraft:lectern[facing=west,has_book=false,powered=false]")
    chandelier(bb, w1 + 5, 10, TZ - 3, drop=2)
    ceiling_lights(bb, w1 + 1, TZ - 11, w2 - 1, TZ + 3, 10, 4)
    for z in range(TZ - 12, TZ + 5, 3):
        bb.set(w1 - 1, 5, z, GLYPH)
    rooms, doors = P.bsp_rooms(bb, w1, TZ - 26, w2, TZ - 14, 1, 6, "minecraft:stone_bricks", min_room=5, seed=seed_of("ltw1"), max_room=10)
    rooms2, doors2 = P.bsp_rooms(bb, w1, TZ + 6, w2, TZ + 24, 1, 6, "minecraft:stone_bricks", min_room=5, seed=seed_of("ltw2"), max_room=10)
    for (a, b) in ((TZ - 13, TZ - 13), (TZ + 5, TZ + 5)):
        bb.fill(w1 + 4, 1, a, w1 + 5, 3, b, AIR)
    furnish(bb, rooms + rooms2, 1, 6, ["library", "storage", "library", "living"], seed_of("ltwf"), tracker,
            doors=doors + doors2 + [(w1 + 4, TZ - 13), (w1 + 4, TZ + 5)], wood="dark_oak", audit=audit)
    # ---- east: the Hall of Joy Boy (his straw hat on a pedestal) and the old camp rooms
    e1x, e2x = TX + 17, TX + 26
    bb.fill(e1x, 1, TZ - 12, e2x, 9, TZ + 4, AIR)
    bb.fill(e1x, 0, TZ - 12, e2x, 0, TZ + 4, FLOOR)
    bb.fill(TX + 15, 1, TZ - 6, TX + 16, 5, TZ - 2, AIR)
    hx, hz = e2x - 4, TZ - 4
    bb.fill(hx - 1, 1, hz - 1, hx + 1, 2, hz + 1, "minecraft:polished_andesite")
    bb.cylinder(hx, 3, hz, 3, 3, "minecraft:yellow_terracotta")    # the brim
    bb.cylinder(hx, 4, hz, 1, 4, "minecraft:red_terracotta")       # the red band
    bb.cylinder(hx, 5, hz, 1, 5, "minecraft:yellow_terracotta")    # the crown
    for z in range(TZ - 12, TZ + 5):
        for y in range(2, 8):
            bb.set(e2x + 1, y, z, GLYPH if (y + z) % 4 else GOLD)
    sun_disc(bb, e2x + 1, 6, TZ - 4, 3, "z")
    chandelier(bb, e1x + 3, 10, TZ - 4, drop=2)
    ceiling_lights(bb, e1x + 1, TZ - 11, e2x - 1, TZ + 3, 10, 4)
    rooms, doors = P.bsp_rooms(bb, e1x, TZ - 26, e2x, TZ - 14, 1, 6, "minecraft:stone_bricks", min_room=5, seed=seed_of("lte1"), max_room=10)
    rooms2, doors2 = P.bsp_rooms(bb, e1x, TZ + 6, e2x, TZ + 24, 1, 6, "minecraft:stone_bricks", min_room=5, seed=seed_of("lte2"), max_room=10)
    for (a, b) in ((TZ - 13, TZ - 13), (TZ + 5, TZ + 5)):
        bb.fill(e1x + 4, 1, a, e1x + 5, 3, b, AIR)
    furnish(bb, rooms + rooms2, 1, 6, ["storage", "bedroom", "workshop", "kitchen"], seed_of("ltef"), tracker,
            doors=doors + doors2 + [(e1x + 4, TZ - 13), (e1x + 4, TZ + 5)], wood="spruce", audit=audit)
    # the side wings open into the entrance hall too
    for x in (TX - 16, TX + 10):
        bb.fill(x, 1, TZ + 15, x + 6, 4, TZ + 16, AIR)


def gold_pile(bb, rng):
    """The One Piece: a heaped mound of gold, raw gold and Berry blocks, gold plates (coins) and treasure piles on its
    slopes, a stepped gold dais on top, and Joy Boy's chest facing Roger and the door."""
    px, pz = PILE
    R, Hh = 6.6, 5

    def hgt(X, Z):
        r = np.hypot(X - px, Z - pz)
        bump = 0.9 * (NT.noise(X, Z, 9611, 3) - 0.5)
        return np.where(r <= R, Hh * (1 - (r / R) ** 1.7) + bump, -1)
    X = np.arange(px - 8, px + 9)[:, None]
    Z = np.arange(pz - 8, pz + 9)[None, :]
    Hm = np.round(hgt(X, Z)).astype(int)
    mats = ["minecraft:gold_block", "minecraft:raw_gold_block", "onepiece:berry_block", "minecraft:gold_block"]
    for i in range(Hm.shape[0]):
        for j in range(Hm.shape[1]):
            top = Hm[i, j]
            if top < 1:
                continue
            x, z = px - 8 + i, pz - 8 + j
            for y in range(1, top + 1):
                bb.set(x, y, z, mats[int(NT.noise(x * 2 + y, z * 2, 9612, 2) * 3.99)])
            v = rng.random()
            if v < 0.32:
                bb.set(x, top + 1, z, "minecraft:light_weighted_pressure_plate")
            elif v < 0.42:
                bb.set(x, top + 1, z, f"onepiece:treasure_pile[facing={('north', 'east', 'south', 'west')[int(rng.integers(4))]}]")
    # the top: a 3x3 gold dais at y 5 and the chest at y 6, nothing loose around it
    bb.fill(px - 1, 1, pz - 1, px + 1, Hh, pz + 1, GOLD)
    bb.fill(px - 1, Hh + 1, pz - 1, px + 1, Hh + 1, pz + 1, AIR)
    bb.set(px, Hh + 1, pz, "onepiece:joy_boy_chest[facing=south,treasure=true]")
    for (x, z) in ((px - 1, pz - 1), (px + 1, pz - 1)):
        bb.set(x, Hh + 1, z, "minecraft:candle[candles=4,lit=true,waterlogged=false]")


# ------------------------------------------------------------------ outside
def rings(bb, rng):
    """Two ring walls of ancient stone round the temple: broken tops, buttresses, four gates (the south one on the
    avenue), and a courtyard of worn paving with grass and moss breaking through."""
    # courtyard paving (in noise patches with grass, never a pattern)
    r_out = RINGS[1] + 2
    pav = [("minecraft:stone_bricks", 0.34), ("minecraft:mossy_stone_bricks", 0.2), ("minecraft:cracked_stone_bricks", 0.12),
           ("minecraft:grass_block", 0.18), ("minecraft:moss_block", 0.1), ("minecraft:coarse_dirt", 0.06)]
    NT.cover(bb, TX - r_out, TZ - r_out, TX + r_out, TZ + r_out, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), pav,
             9620, mask=lambda X, Z: np.hypot(X - TX, Z - TZ) <= RINGS[0] - 1)
    for ri, R in enumerate(RINGS):
        gates = (90, 0, 180, 270) if ri == 0 else (90, 35, 160, 300)
        for a10 in range(0, 3600, 4):
            a = a10 / 10
            if any(abs((a - g + 180) % 360 - 180) < 6.5 for g in gates):
                continue
            t = math.radians(a)
            x, z = round(TX + R * math.cos(t)), round(TZ + R * math.sin(t))
            hgt = 5 + int(3 * NT.noise(x, z, 9621 + ri, 5)) - (3 if NT.noise(x, z, 9622, 9) < 0.25 else 0)
            for y in range(-2, hgt + 1):
                bb.set(x, y, z, STONES[int(NT.noise(x + y, z, 9623, 2) * 2.99)] if y % 4 else CHIS)
            if hgt >= 5:
                bb.set(x, hgt + 1, z, "minecraft:mossy_stone_brick_wall" if (a10 // 4) % 3 else "minecraft:stone_brick_wall")
        for g in gates:                                                   # gate piers with gold caps
            for s in (-1, 1):
                t = math.radians(g + s * 7.5)
                x, z = round(TX + R * math.cos(t)), round(TZ + R * math.sin(t))
                bb.fill(x - 1, -1, z - 1, x + 1, 9, z + 1, CHIS)
                bb.fill(x - 1, 10, z - 1, x + 1, 10, z + 1, "minecraft:stone_brick_slab[type=bottom]")
                bb.set(x, 10, z, GOLD)


def avenue(bb, rng):
    """The road from the cove to the temple: broken paving, a colonnade with fallen columns, the Sun Gate."""
    z0, z1 = TZ + RINGS[1] + 1, COVE[1] - COVE[3] + 6
    pav = [("minecraft:stone_bricks", 0.36), ("minecraft:mossy_stone_bricks", 0.2), ("minecraft:cracked_stone_bricks", 0.14),
           ("minecraft:gravel", 0.1), ("minecraft:grass_block", 0.14), ("minecraft:moss_block", 0.06)]
    NT.cover(bb, TX - 4, z0, TX + 4, z1, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), pav, 9630)
    bb.fill(TX - 4, 1, TZ + TIERS[0] + 2, TX + 4, 6, z1, AIR)
    for z in range(TZ + TIERS[0] + 6, z1, 6):
        for x in (TX - 7, TX + 7):
            broken = NT.noise(x, z, 9631, 3) < 0.35
            hgt = int(rng.integers(2, 4)) if broken else 8
            bb.fill(x, -1, z, x, 0, z, "minecraft:polished_andesite")
            bb.fill(x, 1, z, x, hgt, z, CHIS if hgt == 8 else "minecraft:cracked_stone_bricks")
            if hgt == 8:
                bb.set(x, 9, z, "minecraft:stone_brick_slab[type=bottom]")
            else:                                                   # the fallen drum lies beside it
                d = 1 if x > TX else -1
                for k in range(2, 6):
                    set_if_air(bb, x + d * k, 1, z, "minecraft:stone_bricks" if k % 2 else "minecraft:cracked_stone_bricks")
    # the Sun Gate of Joy Boy
    gz = GATE_Z
    for dx in (-8, 8):
        bb.fill(TX + dx - 1, -1, gz - 1, TX + dx + 1, 17, gz + 1, CHIS)
        bb.fill(TX + dx - 2, -1, gz - 2, TX + dx + 2, 1, gz + 2, "minecraft:polished_andesite")
        for y in range(3, 16, 4):
            bb.set(TX + dx, y, gz - 2, GLYPH)
            bb.set(TX + dx, y, gz + 2, GLYPH)
    bb.fill(TX - 10, 18, gz - 1, TX + 10, 20, gz + 1, "minecraft:stone_bricks")
    bb.fill(TX - 10, 21, gz - 1, TX + 10, 21, gz + 1, "minecraft:stone_brick_slab[type=bottom]")
    for x in range(TX - 9, TX + 10, 3):
        bb.set(x, 19, gz + 2, GOLD)
    sun_disc(bb, TX, 27, gz, 5, "x")


def cove(bb, rng):
    """The Roger Pirates' landing: a stone quay, the anchor stone, their cold camp on the beach."""
    qz = COVE[1] - COVE[3] + 3
    bb.fill(TX - 5, -4, qz, TX + 5, 0, qz + 9, "minecraft:stone_bricks")
    bb.mix(TX - 5, 0, qz, TX + 5, 0, qz + 9, STONES, [0.5, 0.35, 0.15])
    for (x, z) in ((TX - 5, qz + 9), (TX + 5, qz + 9), (TX - 5, qz + 4), (TX + 5, qz + 4)):
        bb.fill(x, 1, z, x, 1, z, "minecraft:andesite_wall")
    for z in range(qz + 10, qz + 14):                                 # wooden landing stage
        bb.fill(TX - 2, 0, z, TX + 2, 0, z, "minecraft:spruce_planks")
        if z % 2:
            bb.fill(TX - 2, -5, z, TX - 2, -1, z, "minecraft:spruce_log[axis=y]")
            bb.fill(TX + 2, -5, z, TX + 2, -1, z, "minecraft:spruce_log[axis=y]")
    bb.fill(TX - 7, 1, qz + 1, TX - 6, 2, qz + 2, "minecraft:mossy_cobblestone")
    bb.set(TX - 7, 3, qz + 1, "onepiece:anchor[facing=south]")
    # the old camp on the sand, east of the quay
    cx, cz = TX + 15, qz - 1
    y = max(0, hy(cx, cz))
    bb.set(cx, y + 1, cz, "minecraft:campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]")
    for (dx, dz, ax) in ((2, 0, "z"), (-2, 0, "z"), (0, 2, "x")):
        set_if_air(bb, cx + dx, y + 1, cz + dz, f"minecraft:stripped_spruce_log[axis={ax}]")
    set_if_air(bb, cx + 3, y + 1, cz - 3, "minecraft:barrel[facing=up,open=false]")
    set_if_air(bb, cx + 4, y + 1, cz - 2, "minecraft:barrel[facing=north,open=false]")
    set_if_air(bb, cx - 3, y + 1, cz - 3, "minecraft:white_carpet")
    set_if_air(bb, cx - 4, y + 1, cz - 3, "minecraft:white_carpet")


def ruin(bb, x0, z0, w, d, rng, tracker, audit, k):
    """A ruined building of the ancient city on the hillside: walls of mixed ancient stone with broken tops, a gold-
    inlaid lintel, doorway and window gaps, a footing down to the slope, half its floor overgrown."""
    base = min(hy(x, z) for x in (x0, x0 + w - 1) for z in (z0, z0 + d - 1))
    top = max(hy(x, z) for x in (x0, x0 + w - 1) for z in (z0, z0 + d - 1))
    y0 = base
    hgt = int(rng.integers(5, 10))
    bb.fill(x0, y0 - 3, z0, x0 + w - 1, y0, z0 + d - 1, "minecraft:stone_bricks")
    bb.mix(x0, y0 + 1, z0, x0 + w - 1, y0 + hgt, z0 + d - 1, STONES, [0.45, 0.35, 0.2])
    bb.fill(x0 + 1, y0 + 1, z0 + 1, x0 + w - 2, y0 + max(hgt, top - y0 + 4), z0 + d - 2, AIR)
    for x in range(x0, x0 + w):
        for z in (z0, z0 + d - 1):
            c = int(hgt * 0.7 * NT.noise(x * 3, z * 3, 9640 + k, 2))
            if c:
                bb.fill(x, y0 + hgt - c + 1, z, x, y0 + hgt, z, AIR)
    for z in range(z0, z0 + d):
        for x in (x0, x0 + w - 1):
            c = int(hgt * 0.7 * NT.noise(x * 3, z * 3, 9641 + k, 2))
            if c:
                bb.fill(x, y0 + hgt - c + 1, z, x, y0 + hgt, z, AIR)
    for x in range(x0 + 2, x0 + w - 2, 3):
        bb.fill(x, y0 + 2, z0, x, y0 + 3, z0, AIR)
        bb.fill(x, y0 + 2, z0 + d - 1, x, y0 + 3, z0 + d - 1, AIR)
    dx = x0 + w // 2
    bb.fill(dx, y0 + 1, z0 + d - 1, dx + 1, y0 + 3, z0 + d - 1, AIR)
    bb.fill(dx - 1, y0 + 4, z0 + d - 1, dx + 2, y0 + 4, z0 + d - 1, CHIS)
    bb.set(dx, y0 + 4, z0 + d - 1, GOLD) if k % 3 == 0 else None
    bb.mix(x0 + 1, y0, z0 + 1, x0 + w - 2, y0, z0 + d - 2, ["minecraft:mossy_stone_bricks", "minecraft:moss_block", "minecraft:coarse_dirt"], [0.5, 0.3, 0.2])
    kind = ["storage", "library", "workshop", "living"][k % 4]
    furnish(bb, [(x0 + 2, z0 + 2, x0 + w - 3, z0 + d - 3)], y0 + 1, 4, [kind], seed_of("ltr", k), tracker,
            doors=[(dx, z0 + d - 1)], wood="dark_oak", audit=audit)
    for _ in range(int(w * d * 0.06)):
        x, z = int(rng.integers(x0 + 1, x0 + w - 1)), int(rng.integers(z0 + 1, z0 + d - 1))
        set_if_air(bb, x, y0 + 1, z, "minecraft:moss_carpet")
    return (x0 - 3, z0 - 3, x0 + w + 3, z0 + d + 3)


def jungle(bb, rng, tracker, audit):
    taken = []
    n = 0
    for _ in range(3000):
        w, d = int(rng.integers(8, 14)), int(rng.integers(7, 12))
        x0, z0 = int(rng.integers(8, N - 22)), int(rng.integers(8, N - 22))
        corners = [(x, z) for x in (x0 - 2, x0 + w + 2) for z in (z0 - 2, z0 + d + 2)]
        X = np.array([[c[0] for c in corners]])
        Z = np.array([[c[1] for c in corners]])
        if (SHORE(X, Z) < 8).any() or in_cove(X, Z).any():
            continue
        if (np.hypot(X - TX, Z - TZ) < RINGS[1] + 4).any() or (np.abs(X - TX) < 12).any() and (Z > TZ).any():
            continue
        hs = height(X, Z)
        if hs.max() - hs.min() > 6 or hs.max() >= 15:
            continue
        box = (x0 - 3, z0 - 3, x0 + w + 3, z0 + d + 3)
        if any(box[0] <= t[2] and t[0] <= box[2] and box[1] <= t[3] and t[1] <= box[3] for t in taken):
            continue
        taken.append(ruin(bb, x0, z0, w, d, rng, tracker, audit, n))
        n += 1
        if n >= 24:
            break
    print("ruins:", n)
    # giant trees through the wilderness (not on the rings, avenue, cove or the cliff tops)
    k = 0
    for _ in range(2500):
        x, z = int(rng.integers(6, N - 6)), int(rng.integers(6, N - 6))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 8 or in_cove(X, Z)[0, 0] or flatness(X, Z)[0, 0] < 0.6:
            continue
        if any(t[0] - 2 <= x <= t[2] + 2 and t[1] - 2 <= z <= t[3] + 2 for t in taken):
            continue
        y = hy(x, z)
        big = rng.random() < 0.45
        if big:
            NT.giant_tree(bb, x, y + 1, z, int(rng.integers(16, 26)), rng)
            taken.append((x - 5, z - 5, x + 6, z + 6))
        else:
            P.tree(bb, x, y + 1, z, int(rng.integers(7, 12)), "jungle" if rng.random() < 0.7 else "oak", rng)
            taken.append((x - 3, z - 3, x + 3, z + 3))
        k += 1
        if k >= 70:
            break
    print("trees:", k)
    # boulders on the hills and below the cliffs
    for _ in range(26):
        x, z = int(rng.integers(8, N - 8)), int(rng.integers(8, N - 8))
        X, Z = np.array([[x]]), np.array([[z]])
        if SHORE(X, Z)[0, 0] < 4 or in_cove(X, Z)[0, 0] or flatness(X, Z)[0, 0] < 0.5:
            continue
        NT.boulder(bb, x, hy(x, z), z, rng.uniform(1.5, 3.2), rng)
    return taken


def design():
    bb = BigBuild(seed=967, y_min=-12, y_max=80)
    tracker = P.PropTracker(967)
    audit = []
    rng = np.random.default_rng(967)
    terrain(bb)
    rings(bb, rng)
    avenue(bb, rng)
    cove(bb, rng)
    temple(bb, tracker, audit)
    jungle(bb, rng, tracker, audit)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 9650, density=0.32, kinds=NT.PLANTS_JUNGLE,
              flowers=["minecraft:blue_orchid", "minecraft:poppy", "minecraft:allium"],
              mask=lambda X, Z: land(X, Z) & (np.hypot(X - TX, Z - TZ) > TIERS[0] + 3))
    return bb, audit


def build():
    bb, audit = design()
    for a in audit[:12]:
        print("audit:", a)
    print("audit fails:", len(audit))
    b = to_canvas(bb)
    b.npc(ROGER[0], 1, ROGER[1], "roger", False)
    b.chest(PILE[0] + 7, 1, PILE[1] - 6, "laugh_tale", "west")
    b.chest(TX - 25, 1, TZ + 3, "void_century", "east")
    b.chest(TX + 25, 1, TZ + 3, "legendary", "west")
    for (gx, gz) in ((TX + RINGS[1] + 8, TZ), (TX - RINGS[1] - 8, TZ + 6), (TX + 20, TZ + RINGS[0] - 3), (TX - 22, TZ - RINGS[0] + 4), (TX, GATE_Z + 4)):
        b.guard(gx, max(0, hy(gx, gz)) + 1, gz, "ancient_guardian")
    return b, 0
