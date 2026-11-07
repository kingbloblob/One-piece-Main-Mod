"""Ruins of the Ancient Kingdom v2, redesigned with the Minecraft Builder skill: a Void Century city buried 800 years
ago and found again in a vast cavern deep in the rock (the Void Century's lost kingdom, Poneglyph script, Shandora's
ruined city and Joy Boy's era in Egghead's records).

Silhouette first: a huge domed cavern; in the middle a stepped temple of five tiers rising almost to the roof with a
glyph shrine and a Poneglyph on top, lit by sea prism crystals; a processional avenue of tall broken columns with
fallen drums leads up to it from a giant ruined gateway; the cavern walls carved into the Ancient script.

Around it: ruined houses (roofless rooms, broken walls, collapsed roofs), a dry canal with two arched bridges, fallen
arches, a toppled colossal head of a statue, roots and dripstone hanging from the roof, glowing lichen, moss creeping
over the stones, Stone Sentinels of the old kingdom still on guard. Tunnels out to the caves.
Canvas y 0 = the cavern floor (world y -42). 128 x 112. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, steady
from mcb.bridge import to_canvas
from mcb import nature as NT
from canvas import Byte

SID = "ancient_ruins"
TITLE = "Ruins of the Ancient Kingdom"
CUTS = [6, 14, 24]
TILER = dict(terrain="none", sky_y=-42)

NX, NZ = 128, 112
CX, CZ = 70, 56                      # temple centre
RUIN = "onepiece:shandian_ruin_stone"
GLYPH = "onepiece:ancient_glyph_stone"
RSLAB = "onepiece:shandian_ruin_stone_slab"
RSTAIR = "onepiece:shandian_ruin_stone_stairs"
RWALL = "onepiece:shandian_ruin_stone_wall"
ROCK = ["minecraft:deepslate", "minecraft:tuff", "minecraft:cobbled_deepslate", "minecraft:deepslate"]
DOME_H = 34
BLOBS = [(64, 56, 58, 50, DOME_H), (24, 30, 22, 18, 18), (104, 84, 20, 18, 16)]


def cavern(X, y, Z, grow=0.0):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    best = np.full(np.broadcast(X, Z, y).shape, 9.0)
    for (cx, cz, rx, rz, h) in BLOBS:
        v = ((X - cx) / (rx + grow)) ** 2 + ((Z - cz) / (rz + grow)) ** 2 + (np.maximum(0, y) / (h + grow)) ** 2
        best = np.minimum(best, v)
    n = 1 + 0.1 * np.sin(X * 0.31 + Z * 0.17 + y * 0.23) * np.cos(Z * 0.27 - X * 0.11 + y * 0.19)
    return best / n


def rock_and_cave(bb):
    bb.fill_where(0, -4, 0, NX - 1, DOME_H + 4, NZ - 1, lambda X, y, Z: cavern(X, y, Z, 4) < 1, "minecraft:deepslate")
    for k, blk in enumerate(ROCK[1:3]):
        bb.fill_where(0, -4, 0, NX - 1, DOME_H + 4, NZ - 1,
                      lambda X, y, Z, k=k: (cavern(X, y, Z, 4) < 1) & (NT.noise(X + y * 3, Z, 4100 + k, 5) > 0.7), blk)
    bb.fill_where(0, 1, 0, NX - 1, DOME_H + 1, NZ - 1, lambda X, y, Z: cavern(X, y, Z) < 1, AIR)
    # floor: packed dirt, gravel, moss, ruin rubble
    floor = [("minecraft:packed_mud", 0.25), ("minecraft:coarse_dirt", 0.2), ("minecraft:moss_block", 0.2), ("minecraft:gravel", 0.1),
             ("minecraft:tuff", 0.15), ("onepiece:ruin_moss", 0.1)]
    NT.cover(bb, 0, 0, NX - 1, NZ - 1, lambda X, Z: np.zeros(np.broadcast(X, Z).shape), floor, 4101,
             mask=lambda X, Z: cavern(X, 1, Z) < 1, under="minecraft:deepslate", base=-3)
    # the walls carved with the Ancient script: glyph stone in bands where the cave wall meets the air
    bb.fill_where(0, 2, 0, NX - 1, 20, NZ - 1,
                  lambda X, y, Z: (cavern(X, y, Z) >= 1) & (cavern(X, y, Z, -1.2) < 1.0) & (cavern(X, y, Z, 1.2) < 1) & (y % 6 < 3)
                  & (NT.noise(X, Z + y, 4102, 6) > 0.4), GLYPH)


def temple(bb):
    """Five stepped tiers, each smaller and set back, stairs up the south face, glyph frieze bands, a shrine on top
    with a Poneglyph and sea prism crystals."""
    y = 0
    tiers = [(26, 22, 5), (21, 17, 5), (16, 13, 5), (12, 9, 4), (8, 6, 4)]
    for k, (hx, hz, h) in enumerate(tiers):
        bb.fill(CX - hx, y + 1, CZ - hz, CX + hx, y + h, CZ + hz, RUIN)
        bb.fill(CX - hx, y + h, CZ - hz, CX + hx, y + h, CZ + hz, "minecraft:chiseled_tuff_bricks" if k % 2 else "minecraft:polished_tuff")
        bb.fill(CX - hx, y + 2, CZ - hz, CX + hx, y + 2, CZ - hz, GLYPH)
        bb.fill(CX - hx, y + 2, CZ + hz, CX + hx, y + 2, CZ + hz, GLYPH)
        bb.fill(CX - hx, y + 2, CZ - hz, CX - hx, y + 2, CZ + hz, GLYPH)
        bb.fill(CX + hx, y + 2, CZ - hz, CX + hx, y + 2, CZ + hz, GLYPH)
        for x in range(CX - hx, CX + hx + 1, 4):                       # buttresses
            for z in (CZ - hz - 1, CZ + hz + 1):
                bb.fill(x, y + 1, z, x, y + h - 1, z, "minecraft:tuff_bricks")
        # damage: chunks fallen off the corners
        for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            bb.fill_where(CX + sx * hx - 3, y + h - 2, CZ + sz * hz - 3, CX + sx * hx + 3, y + h, CZ + sz * hz + 3,
                          lambda X, yy, Z, sx=sx, sz=sz: (np.abs(X - CX - sx * hx) + np.abs(Z - CZ - sz * hz) + (y + h - yy) < 3.5)
                          & (NT.noise(X, Z, 4103 + k, 2) > 0.3), AIR)
        y += h
    # grand stair up the south face, the full height, with ramp walls
    top = y
    for k in range(top):
        z = CZ + 22 + 3 - k
        bb.fill(CX - 3, k + 1, z, CX + 3, k + 1, z, f"{RSTAIR}[facing=north,half=bottom,shape=straight,waterlogged=false]")
        bb.fill(CX - 3, k + 2, z, CX + 3, k + 5, z, AIR)
        bb.fill(CX - 4, 1, z, CX - 4, k + 1, z, "minecraft:tuff_bricks"); bb.fill(CX + 4, 1, z, CX + 4, k + 1, z, "minecraft:tuff_bricks")
        bb.fill(CX - 3, 1, z, CX + 3, k, z, RUIN)
    # shrine on top: four glyph columns, a lintel ring, the Poneglyph, crystals
    for (dx, dz) in ((-4, -3), (4, -3), (-4, 3), (4, 3)):
        bb.fill(CX + dx, top + 1, CZ + dz, CX + dx, top + 6, CZ + dz, "minecraft:chiseled_tuff")
    bb.fill(CX - 5, top + 7, CZ - 4, CX + 5, top + 7, CZ + 4, RUIN)
    bb.fill(CX - 4, top + 7, CZ - 3, CX + 4, top + 7, CZ + 3, AIR)
    bb.fill(CX - 5, top + 8, CZ - 4, CX + 5, top + 8, CZ - 4, f"{RSLAB}[type=bottom,waterlogged=false]")
    bb.fill(CX - 5, top + 8, CZ + 4, CX + 5, top + 8, CZ + 4, f"{RSLAB}[type=bottom,waterlogged=false]")
    bb.fill(CX - 1, top + 1, CZ - 2, CX + 1, top + 4, CZ - 2, "onepiece:poneglyph")
    for (dx, dz) in ((-3, 0), (3, 0), (-2, 2), (2, 2)):
        bb.set(CX + dx, top + 1, CZ + dz, "onepiece:sea_prism_crystal")
    return top


def column(bb, x, z, h, rng, broken=True):
    bb.fill(x - 1, 0, z - 1, x + 1, 1, z + 1, "minecraft:chiseled_tuff_bricks")
    for y in range(2, h + 1):
        bb.set(x, y, z, GLYPH if y % 4 == 0 else RUIN)
    if not broken:
        bb.fill(x - 1, h + 1, z - 1, x + 1, h + 1, z + 1, "minecraft:chiseled_tuff_bricks")
    else:
        bb.set(x, h + 1, z, f"{RSLAB}[type=bottom,waterlogged=false]")


def avenue(bb, rng):
    """Processional avenue south of the temple: paired tall columns (some broken short, a few fallen across the way),
    a giant ruined gateway at the south end."""
    z0, z1 = CZ + 28, NZ - 10
    for z in range(z0, z1):
        bb.fill(CX - 4, 0, z, CX + 4, 0, z, "minecraft:polished_tuff" if (z % 3) else "minecraft:tuff_bricks")
    for k, z in enumerate(range(z0 + 2, z1 - 4, 6)):
        for s in (-1, 1):
            h = int(rng.integers(6, 16)) if rng.random() < 0.6 else 18
            column(bb, CX + s * 7, z, h, rng, broken=h < 18)
    for (z, s) in ((z0 + 9, 1), (z0 + 21, -1)):                       # fallen columns lying across
        for k in range(10):
            bb.set(CX + s * (6 - k), 1, z + k // 4, RUIN if k % 4 else GLYPH)
    # gateway: two massive piers and a broken lintel
    gz = z1 - 2
    for s in (-1, 1):
        bb.fill(CX + s * 7 - 2, 0, gz - 2, CX + s * 7 + 2, 20, gz + 2, "minecraft:tuff_bricks")
        bb.fill(CX + s * 7 - 2, 4, gz + 2, CX + s * 7 + 2, 16, gz + 2, GLYPH)
    bb.fill(CX - 9, 21, gz - 2, CX + 2, 23, gz + 2, RUIN)                 # lintel broken off on the east
    bb.fill(CX + 6, 0, gz - 6, CX + 11, 3, gz - 3, RUIN)                   # its fallen piece


def house(bb, x0, z0, w, d, rng):
    """A ruined house: walls of varying height with gaps, a doorway, a collapsed roof slab inside, rubble."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    bb.fill(x0, 0, z0, x1, 0, z1, "minecraft:tuff_bricks")
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            h = int(2 + 4 * NT.noise(np.array(float(x)), np.array(float(z)), 4104, 3))
            bb.fill(x, 1, z, x, h, z, RUIN if (x + h) % 5 else GLYPH)
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            h = int(2 + 4 * NT.noise(np.array(float(x)), np.array(float(z)), 4105, 3))
            bb.fill(x, 1, z, x, h, z, RUIN)
    bb.fill((x0 + x1) // 2, 1, z1, (x0 + x1) // 2, 3, z1, AIR)
    for k in range(int(rng.integers(3, 7))):
        x, z = int(rng.integers(x0 + 1, x1)), int(rng.integers(z0 + 1, z1))
        bb.set(x, 1, z, [f"{RSLAB}[type=bottom,waterlogged=false]", "minecraft:cobblestone", "onepiece:ruin_moss",
                         "minecraft:decorated_pot", "minecraft:moss_carpet"][k % 5])
    if rng.random() < 0.5:                                              # roof slab collapsed at an angle
        for k in range(w - 2):
            bb.set(x0 + 1 + k, 1 + k // 3, z0 + 1, RUIN)


def canal(bb):
    """A dry canal west of the temple (sunk 3, cut stone walls), two arched bridges, a fallen arch."""
    x1, x2 = 22, 28
    for z in range(10, NZ - 12):
        bb.fill(x1, -3, z, x2, 0, z, AIR)
        bb.fill(x1, -4, z, x2, -4, z, "minecraft:gravel")
        bb.fill(x1 - 1, -4, z, x1 - 1, 0, z, "minecraft:tuff_bricks"); bb.fill(x2 + 1, -4, z, x2 + 1, 0, z, "minecraft:tuff_bricks")
    for bz in (40, 74):
        for x in range(x1 - 2, x2 + 3):
            t = (x - (x1 + x2) / 2) / 5.5
            bb.fill(x, -1 + int(round(2 * (1 - t * t))), bz - 2, x, 1 + int(round(2 * (1 - t * t))), bz + 2, RUIN)
            bb.fill(x, int(round(2 * (1 - t * t))) - 3, bz - 2, x, -2 + int(round(2 * (1 - t * t))), bz + 2, AIR) if abs(t) < 0.75 else None
    # a fallen arch: a broken semicircle leaning on the canal edge
    for a in range(0, 150, 8):
        t = math.radians(a)
        bb.set(36 + int(round(7 * math.cos(t))), int(round(7 * math.sin(t))) + 1, 90, RUIN)


def colossus_head(bb):
    """A toppled giant stone head lying on its side by the east wall: face, brow, nose, a crack."""
    hx, hz = 104, 40
    bb.fill_where(hx - 8, 0, hz - 8, hx + 8, 12, hz + 8,
                  lambda X, y, Z: ((X - hx) / 7) ** 2 + ((y - 5) / 6.5) ** 2 + ((Z - hz) / 6) ** 2 <= 1, RUIN)
    for (dy, dz) in ((7, -2), (7, 2)):
        bb.fill(hx - 7, 5 + dy - 5, hz + dz, hx - 6, 6 + dy - 5, hz + dz, "minecraft:black_concrete")
    bb.fill(hx - 8, 4, hz - 1, hx - 7, 5, hz + 1, RUIN)                  # nose
    bb.fill(hx - 7, 2, hz - 2, hx - 7, 2, hz + 2, "minecraft:tuff_bricks")   # mouth line
    for y in range(1, 11):
        bb.set(hx - 2 + y % 2, y, hz + 4 - y // 3, AIR)                  # crack


def roof_life(bb, rng):
    """Roots and dripstone hang from the roof, glow lichen and moss on the walls."""
    for _ in range(260):
        x, z = int(rng.integers(4, NX - 4)), int(rng.integers(4, NZ - 4))
        col = bb.get_region(x, 1, z, x, DOME_H + 2, z)[0, :, 0]
        air = np.nonzero(col == 1)[0]
        if len(air) == 0:
            continue
        top = int(air[-1]) + 1
        if col[min(top, len(col) - 1)] <= 1:
            continue
        p = rng.random()
        if p < 0.4:
            L = int(rng.integers(2, 5))
            for k in range(L):
                th = "tip" if k == L - 1 else "frustum" if k < L - 2 else "middle"
                bb.set(x, top - 1 - k, z, f"minecraft:pointed_dripstone[thickness={th},vertical_direction=down,waterlogged=false]")
        elif p < 0.75:
            L = int(rng.integers(3, 10))
            for k in range(L):
                bb.set(x, top - 1 - k, z, "minecraft:hanging_roots" if k == L - 1 else "minecraft:hanging_roots")
        else:
            bb.set(x, top - 1, z, "minecraft:glow_lichen[down=false,east=false,north=false,south=false,up=true,waterlogged=false,west=false]")
    # sea prism crystals on the floor here and there, giving light
    for _ in range(18):
        x, z = int(rng.integers(8, NX - 8)), int(rng.integers(8, NZ - 8))
        if bb.get_region(x, 1, z, x, 1, z)[0, 0, 0] == 1 and bb.get_region(x, 0, z, x, 0, z)[0, 0, 0] > 1:
            bb.set(x, 1, z, "onepiece:sea_prism_crystal")


def design():
    bb = BigBuild(seed=4100, y_min=-8, y_max=DOME_H + 6)
    rng = np.random.default_rng(4106)
    rock_and_cave(bb)
    canal(bb)
    top = temple(bb)
    avenue(bb, rng)
    colossus_head(bb)
    spots = [(8, 22, 9, 8), (12, 52, 8, 7), (8, 76, 9, 8), (34, 20, 8, 7), (38, 64, 7, 8), (98, 62, 9, 7), (104, 22, 8, 7),
             (96, 86, 8, 7), (40, 96, 9, 7), (106, 96, 7, 7)]
    for (x, z, w, d) in spots:
        if cavern(np.array(float(x)), 4, np.array(float(z))) < 0.85 and cavern(np.array(float(x + w)), 4, np.array(float(z + d))) < 0.85:
            house(bb, x, z, w, d, rng)
    roof_life(bb, rng)
    # tunnels out to the caves
    for (a, b, c) in (((14, 3, 30), (0, 8, 22), 2), ((116, 3, 84), (NX - 1, 10, 96), 2)):
        n = abs(b[0] - a[0])
        for k in range(n + 1):
            t = k / max(n, 1)
            x, y, z = (int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))
            bb.fill(x, y, z - c, x, y + 3, z + c, AIR)
    return bb, [], top


def build():
    bb, audit, top = design()
    b = to_canvas(bb)
    b.chest(CX + 2, top + 1, CZ - 2, "underground_ruins", "west")
    b.chest(CX + 2, top + 1, CZ + 2, "void_century", "west")
    for (x, z) in ((CX - 10, CZ + 30), (CX + 10, CZ + 30), (CX - 28, CZ), (CX + 28, CZ)):
        b.entities.append(("onepiece:ancient_sentinel", x, 1, z, {"PersistenceRequired": Byte(1)}))
    return b, 0
