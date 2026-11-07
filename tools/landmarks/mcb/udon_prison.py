"""Udon Prisoner Mine v2, redesigned with the Minecraft Builder skill: Kaido's labour camp in the barren Udon region
of Wano (manga ch. 925-947, anime 925+): prisoners dig, are fed red-bean soup only if they behave, and fight in
Queen's Sumo Inferno.

Silhouette first: on a grey, dead wasteland a huge square of stone walls with white-and-black Wano corner towers,
the main gate under a giant horned Beast Pirates skull; inside, a vast terraced pit dug deep into the rock, and
beside it the tall black-roofed warden's tower from which Queen and the headliners watch.

Inside the walls: the pit (six terraces of barred prisoner cells cut into the rock, timber walkways with rails,
ladders and a switchback ramp, rails and mine carts into side tunnels past ore veins, the Sumo Inferno ring at the
very bottom with Queen's viewing box over it); the warden's tower (guard room, armoury, Babanuki's office, Queen's
viewing hall on top); the soup kitchen with the giant red-bean cauldron; two long prisoner barracks; the weapons
workshop; stockpiles of ore and timber. 152 x 152, y 0 = ground outside the walls. (v2)"""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR, seed_of, st, set_if_air, tier, cornice, lamp_post, steady
from mcb.kit_interiors import furnish_kit, bench, wall_lights
from mcb.bridge import to_canvas
from mcb import nature as NT
import mcasian as A  # noqa: E402  (skill folder is on sys.path once mcb.kit is imported)

SID = "udon_prison"
TITLE = "Udon Prisoner Mine"
CUTS = [2, -10, -20]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")
EDGE_REACH = 6

N = 152
GY = 2                              # yard level inside the walls
W1, W2 = 22, 130                    # the square wall (x and z from W1 to W2)
PCX, PCZ = 66, 62                   # pit centre
PRX, PRZ = 30, 24                   # pit top half-sizes
TER = 6                             # terraces
TH = 5                              # terrace step height
BOTTOM = GY - TER * TH              # pit floor
_LAND = NT.outline(76, 76, 74, 6601, wobble=0.14)
WASTE = [("minecraft:coarse_dirt", 0.3), ("minecraft:gravel", 0.0), ("minecraft:tuff", 0.18), ("minecraft:andesite", 0.12),
         ("minecraft:packed_mud", 0.1), ("minecraft:dirt", 0.12), ("minecraft:stone", 0.12), ("minecraft:podzol", 0.06)]
YARD = [("minecraft:coarse_dirt", 0.35), ("minecraft:packed_mud", 0.25), ("minecraft:dirt_path", 0.15), ("minecraft:gravel", 0.0),
        ("minecraft:tuff", 0.25)]
WALL = ["minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:andesite", "minecraft:tuff_bricks", "minecraft:mossy_stone_bricks"]
WALL_W = [0.45, 0.15, 0.15, 0.15, 0.1]
WANO = dict(column="minecraft:stripped_dark_oak_log", beam="minecraft:dark_oak_planks", soffit="minecraft:dark_oak_planks",
            panel="minecraft:white_wool", lattice="minecraft:dark_oak_planks", wall_low="minecraft:white_terracotta",
            floor="minecraft:dark_oak_planks", ornament="minecraft:dark_oak_planks", bracket="minecraft:stripped_dark_oak_log",
            bracket_stairs="minecraft:dark_oak_stairs")
BARS = "onepiece:prison_bars"


def _height(X, Z):
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    d = _LAND(X, Z)
    h = GY + 1 + NT.fbm(X, Z, 6602, 22) * 6
    inside = (X >= W1 - 3) & (X <= W2 + 3) & (Z >= W1 - 3) & (Z <= W2 + 3)
    h = np.where(inside, GY, h)
    h = np.where(d < 18, 1 + (h - 1) * np.clip(d / 18.0, 0, 1) ** 1.2, h)
    return np.round(h)


X_, Z_ = np.arange(N)[:, None].astype(float), np.arange(N)[None, :].astype(float)
HMAP = _height(X_, Z_).astype(int)


def _ix(X, Z):
    return np.clip(np.asarray(X).astype(int), 0, N - 1), np.clip(np.asarray(Z).astype(int), 0, N - 1)


def height(X, Z):
    return HMAP[_ix(X, Z)]


def hy(x, z):
    return int(HMAP[min(max(int(x), 0), N - 1), min(max(int(z), 0), N - 1)])


def pit_level(X, Z):
    """Terrace index at (X, Z): 0 = rim (outside the pit) .. TER = floor."""
    e = np.sqrt(((X - PCX) / PRX) ** 2 + ((Z - PCZ) / PRZ) ** 2)
    k = np.floor((1 - e) * (TER + 1.6)).astype(int)
    return np.clip(k, 0, TER)


def terrain(bb):
    inside = lambda X, Z: (X >= W1) & (X <= W2) & (Z >= W1) & (Z <= W2)
    land = lambda X, Z: (height(X, Z) >= 1) & (_LAND(X, Z) > 0)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, WASTE, 6603, mask=lambda X, Z: land(X, Z) & ~inside(X, Z), core="minecraft:stone", base=-8)
    NT.cover(bb, 0, 0, N - 1, N - 1, height, YARD, 6604, mask=lambda X, Z: inside(X, Z), core="minecraft:stone", base=BOTTOM - 6)
    NT.plants(bb, 0, 0, N - 1, N - 1, height, 6605, density=0.06, kinds=["minecraft:dead_bush", "minecraft:short_dry_grass" if False else "minecraft:dead_bush"],
              mask=lambda X, Z: land(X, Z) & ~inside(X, Z), ground=("coarse_dirt", "dirt", "podzol", "packed_mud"))
    # a few dead trees and boulders on the wasteland
    rng = np.random.default_rng(6606)
    for _ in range(14):
        x, z = int(rng.integers(8, N - 8)), int(rng.integers(8, N - 8))
        if W1 - 6 <= x <= W2 + 6 and W1 - 6 <= z <= W2 + 6 or hy(x, z) < 1 or _LAND(np.array(float(x)), np.array(float(z))) < 3:
            continue
        if rng.random() < 0.5:
            NT.boulder(bb, x, hy(x, z), z, int(rng.integers(2, 4)), rng, blocks=("minecraft:tuff", "minecraft:andesite", "minecraft:stone"))
        else:
            y = hy(x, z)
            bb.fill(x, y + 1, z, x, y + 5, z, "minecraft:stripped_dark_oak_log[axis=y]")
            bb.fill(x - 2, y + 5, z, x + 2, y + 5, z, "minecraft:dark_oak_fence")
            bb.fill(x, y + 6, z - 1, x, y + 7, z + 1, "minecraft:dark_oak_fence")


def pit(bb):
    """Dig the terraced pit, cut barred cells into each terrace wall, timber walkway rails, ladders, a ramp, tunnels."""
    x1, x2, z1, z2 = PCX - PRX - 1, PCX + PRX + 1, PCZ - PRZ - 1, PCZ + PRZ + 1
    lev = lambda X, Z: pit_level(X, Z)
    for y in range(BOTTOM, GY + 1):
        # air above each terrace's floor, rock (mixed) below
        bb.fill_where(x1, y, z1, x2, y, z2, lambda X, yy, Z: (lev(X, Z) > 0) & (yy > GY - lev(X, Z) * TH), AIR)
        bb.fill_where(x1, y, z1, x2, y, z2, lambda X, yy, Z: (lev(X, Z) > 0) & (yy == GY - lev(X, Z) * TH), "minecraft:packed_mud")
    for y in range(BOTTOM, GY + 1):
        bb.fill_where(x1 - 1, y, z1 - 1, x2 + 1, y, z2 + 1, lambda X, yy, Z: (lev(X, Z) < TER) & (yy <= GY - lev(X, Z) * TH) &
                      (NT.noise(X, yy * 3 + Z, 6610, 4) > 0.86), "minecraft:iron_ore")
    # walls of each terrace: cells every 5 blocks along the inner edge where a level steps down
    rng = np.random.default_rng(6611)
    cells = 0
    for k in range(TER):
        fy = GY - k * TH                       # floor of level k (k=0 = yard)
        for a in range(0, 360, 6):
            t = math.radians(a)
            # a point just inside the edge of level k+1 (the wall face of level k's rim)
            e = 1 - (k + 1) / (TER + 1.6)
            px = PCX + int(round(PRX * e * math.cos(t))); pz = PCZ + int(round(PRZ * e * math.sin(t)))
            if pit_level(np.array(px), np.array(pz)) != k + 1:
                continue
            ox, oz = -math.cos(t), -math.sin(t)      # into the rock (outwards)
            if (a // 6) % 3 == 0 and k < TER - 1:
                cy = fy - TH + 1                      # cell floor = floor of level k+1
                for dd in range(1, 5):
                    cx_, cz_ = px + int(round(ox * dd)), pz + int(round(oz * dd))
                    bb.fill(cx_ - 1, cy, cz_ - 1, cx_ + 1, cy + 2, cz_ + 1, AIR)
                bb.fill(px - 1, cy, pz - 1, px + 1, cy + 2, pz + 1, BARS)
                bb.set(px, cy, pz, AIR); bb.set(px, cy + 1, pz, BARS)
                bx, bz = px + int(round(ox * 3)), pz + int(round(oz * 3))
                bb.set(bx, cy, bz, "minecraft:hay_block" if cells % 2 else "minecraft:brown_carpet")
                cells += 1
            elif (a // 6) % 3 == 1:
                # timber posts and the walkway rail along the terrace edge above
                bb.set(px, fy + 1, pz, "minecraft:dark_oak_fence") if pit_level(np.array(px), np.array(pz)) else None
    # rails along every terrace edge (one block in from the drop), torches on posts
    for k in range(1, TER):
        fy = GY - k * TH
        e = 1 - (k + 0.15) / (TER + 1.6)
        for a in range(0, 360, 2):
            t = math.radians(a)
            px = PCX + int(round(PRX * e * math.cos(t))); pz = PCZ + int(round(PRZ * e * math.sin(t)))
            if pit_level(np.array(px), np.array(pz)) == k:
                bb.set(px, fy + 1, pz, "minecraft:dark_oak_fence")
                if a % 30 == 0:
                    bb.set(px, fy + 2, pz, "minecraft:torch")
    # a switchback ramp of stairs down the south side and ladders on the north
    for k in range(TER):
        fy = GY - k * TH
        e = 1 - (k + 1) / (TER + 1.6)
        sx = PCX + (8 if k % 2 else -8)
        sz = PCZ + int(round(PRZ * e)) + 1
        for s in range(TH + 1):
            bb.fill(sx - (s if k % 2 else -s), fy - s, sz - 1, sx - (s if k % 2 else -s), fy - s, sz + 1,
                    f"minecraft:dark_oak_stairs[facing={'east' if k % 2 else 'west'}]")
            bb.fill(sx - (s if k % 2 else -s), fy - s + 1, sz - 1, sx - (s if k % 2 else -s), fy - s + 4, sz + 1, AIR)
        lz = PCZ - int(round(PRZ * e)) - 1
        bb.fill(PCX, fy - TH + 1, lz + 1, PCX, fy, lz + 1, "minecraft:ladder[facing=south]")
    # mine tunnels from the bottom: east and west, rails, carts, ore, props of timber sets
    for sgn in (-1, 1):
        x0 = PCX + sgn * int(PRX * (1 - TER / (TER + 1.6)))
        for i in range(30):
            x = x0 + sgn * i
            bb.fill(x, BOTTOM + 1, PCZ - 2, x, BOTTOM + 4, PCZ + 2, AIR)
            bb.fill(x, BOTTOM, PCZ - 2, x, BOTTOM, PCZ + 2, "minecraft:gravel" if False else "minecraft:tuff")
            bb.set(x, BOTTOM + 1, PCZ, "minecraft:rail[shape=east_west]")
            if i % 4 == 0:
                bb.fill(x, BOTTOM + 1, PCZ - 2, x, BOTTOM + 3, PCZ - 2, "minecraft:dark_oak_fence")
                bb.fill(x, BOTTOM + 1, PCZ + 2, x, BOTTOM + 3, PCZ + 2, "minecraft:dark_oak_fence")
                bb.fill(x, BOTTOM + 4, PCZ - 2, x, BOTTOM + 4, PCZ + 2, "minecraft:stripped_dark_oak_log[axis=z]")
                bb.set(x, BOTTOM + 3, PCZ + 1, "minecraft:lantern[hanging=true]")
            if i % 7 == 3:
                bb.set(x, BOTTOM + 2, PCZ + 2, "minecraft:iron_ore"); bb.set(x, BOTTOM + 3, PCZ - 2, "minecraft:coal_ore")
                bb.set(x, BOTTOM + 1, PCZ - 1, "minecraft:iron_pickaxe" if False else "minecraft:barrel[facing=up]")
        bb.fill(x0 + sgn * 31, BOTTOM + 1, PCZ - 2, x0 + sgn * 31, BOTTOM + 4, PCZ + 2, "minecraft:tuff")


def sumo_ring(bb):
    """The Sumo Inferno ring on the pit floor: a raised clay dohyo with a straw rope ring, posts and a hanging roof,
    and Queen's viewing box jutting out from the first terrace over it."""
    y = BOTTOM
    bb.cylinder(PCX, y + 1, PCZ, 9, y + 1, "minecraft:packed_mud")
    bb.cylinder(PCX, y + 2, PCZ, 7, y + 2, "minecraft:terracotta")
    bb.ring(PCX, y + 2, PCZ, 5, 6, y + 2, "minecraft:hay_block[axis=y]")
    bb.ring(PCX, y + 2, PCZ, 4, 5, y + 2, "minecraft:terracotta")
    for (dx, dz) in ((-1, -2), (1, -2), (-1, 2), (1, 2)):
        bb.set(PCX + dx, y + 2, PCZ + dz, "minecraft:white_terracotta")
    # four coloured corner posts and the suspended roof (tsuriyane) on chains
    for (dx, dz, c) in ((-8, -8, "black"), (8, -8, "green"), (-8, 8, "white"), (8, 8, "red")):
        bb.fill(PCX + dx, y + 1, PCZ + dz, PCX + dx, y + 12, PCZ + dz, f"minecraft:{c}_concrete")
    A.curved_roof(bb, PCX - 10, PCZ - 10, PCX + 10, PCZ + 10, y + 14, 4, style="irimoya", pal=WANO)
    for x in range(PCX - 10, PCX + 11, 4):
        bb.fill(x, y + 13, PCZ - 10, x, y + 13, PCZ - 10, "minecraft:purple_wool")
        bb.fill(x, y + 13, PCZ + 10, x, y + 13, PCZ + 10, "minecraft:purple_wool")
    # stands of log benches on the pit floor round the ring
    for a in range(0, 360, 20):
        t = math.radians(a)
        bx, bz = PCX + int(round(12 * math.cos(t))), PCZ + int(round(11 * math.sin(t)))
        if pit_level(np.array(bx), np.array(bz)) == TER:
            bb.set(bx, y + 1, bz, f"minecraft:stripped_spruce_log[axis={'x' if abs(math.sin(t)) > 0.7 else 'z'}]")


def warden_tower(bb):
    """The warden's tower east of the pit: a battered stone base and three Wano storeys with curved roofs; Queen's
    viewing hall on top with a balcony toward the pit."""
    x1, z1, x2, z2 = 102, 46, 122, 70
    y = GY
    bb.mix(x1 - 2, y - 2, z1 - 2, x2 + 2, y + 6, z2 + 2, WALL, WALL_W)
    bb.fill(x1 - 1, y + 7, z1 - 1, x2 + 1, y + 7, z2 + 1, "minecraft:dark_oak_planks")
    bb.fill(x1 - 1, y + 1, z1 - 1, x2 + 1, y + 6, z2 + 1, AIR)
    for x in range(x1 - 2, x2 + 3, 4):
        bb.fill(x, y + 1, z1 - 2, x, y + 6, z1 - 2, "minecraft:stone_bricks"); bb.fill(x, y + 1, z2 + 2, x, y + 6, z2 + 2, "minecraft:stone_bricks")
    for z in range(z1 - 2, z2 + 3, 4):
        bb.fill(x1 - 2, y + 1, z, x1 - 2, y + 6, z, "minecraft:stone_bricks"); bb.fill(x2 + 2, y + 1, z, x2 + 2, y + 6, z, "minecraft:stone_bricks")
    bb.fill(x1 - 2, y + 2, z1 + 4, x1 - 2, y + 4, z2 - 4, "minecraft:iron_bars")
    furnish_kit(bb, (x1 - 1, z1 - 1, x2 + 1, z2 + 1), y + 1, 5, "armory", wood="dark_oak", seed=6620, doors=[(x1 - 1, (z1 + z2) // 2)], accent="purple")
    bb.fill(x1 - 2, y + 1, (z1 + z2) // 2 - 1, x1 - 2, y + 3, (z1 + z2) // 2 + 1, AIR)
    levels = [(y + 8, 6, "office", 0), (y + 15, 6, "barracks", 2), (y + 22, 7, "captain", 4)]
    for (fy, h, kind, inset) in levels:
        a1, b1, a2, b2 = x1 + inset, z1 + inset, x2 - inset, z2 - inset
        bb.fill(a1, fy - 1, b1, a2, fy - 1, b2, "minecraft:dark_oak_planks")
        bb.fill(a1, fy, b1, a2, fy + h - 1, b2, "minecraft:white_terracotta")
        bb.fill(a1 + 1, fy, b1 + 1, a2 - 1, fy + h - 1, b2 - 1, AIR)
        for x in range(a1, a2 + 1, 3):
            bb.fill(x, fy, b1, x, fy + h - 1, b1, "minecraft:stripped_dark_oak_log[axis=y]")
            bb.fill(x, fy, b2, x, fy + h - 1, b2, "minecraft:stripped_dark_oak_log[axis=y]")
            if x + 2 <= a2:
                bb.fill(x + 1, fy + 2, b1, x + 2, fy + 3, b1, "minecraft:dark_oak_trapdoor[facing=north,half=bottom,open=true]")
        for z in range(b1, b2 + 1, 3):
            bb.fill(a1, fy, z, a1, fy + h - 1, z, "minecraft:stripped_dark_oak_log[axis=y]")
            bb.fill(a2, fy, z, a2, fy + h - 1, z, "minecraft:stripped_dark_oak_log[axis=y]")
            if z + 2 <= b2:
                bb.fill(a1, fy + 2, z + 1, a1, fy + 3, z + 2, "minecraft:glass_pane")
        furnish_kit(bb, (a1 + 1, b1 + 1, a2 - 1, b2 - 1), fy, h - 1, kind, wood="dark_oak", seed=6621 + fy, doors=[(a1 + 1, b1 + 1)], accent="purple")
        bb.fill(a1 + 1, fy - 8, b1 + 1, a1 + 1, fy + h - 1, b1 + 1, "minecraft:ladder[facing=east]")
        A.curved_roof(bb, a1 - 3, b1 - 3, a2 + 3, b2 + 3, fy + h, 3 if inset < 4 else 7, style="irimoya" if inset == 4 else "hip", pal=WANO)
    # Queen's balcony on the west side of the top hall, toward the pit
    fy = y + 22
    bb.fill(x1 + 4, fy - 1, z1 + 8, x1, fy - 1, z2 - 8, "minecraft:dark_oak_planks")
    bb.fill(x1, fy - 1, z1 + 8, x1 - 3, fy - 1, z2 - 8, "minecraft:dark_oak_planks")
    bb.fill(x1 - 3, fy, z1 + 8, x1 - 3, fy, z2 - 8, "minecraft:dark_oak_fence")
    bb.fill(x1 + 4, fy, z1 + 10, x1 + 4, fy + 2, z2 - 10, AIR)
    bb.set(x1 - 1, fy, (z1 + z2) // 2, "minecraft:dark_oak_stairs[facing=east]")
    return y + 22


def gate_and_walls(bb):
    """The square curtain wall with a walk, corner towers (yagura) and the skull gate in the south wall."""
    t = 4
    for (a, b, c, d) in ((W1, W1, W2, W1 + t - 1), (W1, W2 - t + 1, W2, W2), (W1, W1, W1 + t - 1, W2), (W2 - t + 1, W1, W2, W2)):
        bb.mix(a, GY - 4, b, c, GY + 8, d, WALL, WALL_W)
        bb.fill(a, GY + 9, b, c, GY + 13, d, "minecraft:white_terracotta")
        bb.fill(a, GY + 9, b, c, GY + 9, d, "minecraft:dark_oak_planks")
        bb.fill(a, GY + 14, b, c, GY + 14, d, "minecraft:deepslate_tiles")
    for x in range(W1, W2 + 1, 2):
        bb.set(x, GY + 15, W1, "minecraft:stone_brick_wall"); bb.set(x, GY + 15, W2, "minecraft:stone_brick_wall")
    for z in range(W1, W2 + 1, 2):
        bb.set(W1, GY + 15, z, "minecraft:stone_brick_wall"); bb.set(W2, GY + 15, z, "minecraft:stone_brick_wall")
    for x in range(W1 - 1, W2 + 2):
        bb.set(x, GY + 14, W1 - 1, "minecraft:deepslate_tile_stairs[facing=south,half=bottom]")
        bb.set(x, GY + 14, W2 + 1, "minecraft:deepslate_tile_stairs[facing=north,half=bottom]")
    for z in range(W1 - 1, W2 + 2):
        bb.set(W1 - 1, GY + 14, z, "minecraft:deepslate_tile_stairs[facing=east,half=bottom]")
        bb.set(W2 + 1, GY + 14, z, "minecraft:deepslate_tile_stairs[facing=west,half=bottom]")
    for k in range(W1 + 2, W2 - 1, 3):
        for (x, z) in ((k, W1), (k, W2), (W1, k), (W2, k)):
            bb.fill(x, GY + 10, z, x, GY + 13, z, "minecraft:stripped_dark_oak_log[axis=y]")
        for (x, z) in ((k + 1, W1), (k + 1, W2), (W1, k + 1), (W2, k + 1)):
            bb.set(x, GY + 11, z, "minecraft:iron_bars")
    # buttresses outside every 9
    for k in range(W1 + 4, W2 - 3, 9):
        for (x, z, dx, dz) in ((k, W1 - 1, 0, -1), (k, W2 + 1, 0, 1), (W1 - 1, k, -1, 0), (W2 + 1, k, 1, 0)):
            bb.fill(x, GY - 4, z, x + abs(dz), GY + 11, z + abs(dx), "minecraft:stone_bricks")
            bb.fill(x + dx, GY - 4, z + dz, x + dx + abs(dz), GY + 5, z + dz + abs(dx), "minecraft:stone_bricks")
    # corner yagura: white walls, black curved roofs, two storeys
    for (cx, cz) in ((W1 + 3, W1 + 3), (W2 - 3, W1 + 3), (W1 + 3, W2 - 3), (W2 - 3, W2 - 3)):
        bb.mix(cx - 6, GY - 4, cz - 6, cx + 6, GY + 16, cz + 6, WALL, WALL_W)
        for (fy, r) in ((GY + 17, 5), (GY + 24, 3)):
            bb.fill(cx - r, fy, cz - r, cx + r, fy + 4, cz + r, "minecraft:white_terracotta")
            bb.fill(cx - r + 1, fy, cz - r + 1, cx + r - 1, fy + 4, cz + r - 1, AIR)
            for k in range(-r, r + 1, 2):
                for (x, z) in ((cx + k, cz - r), (cx + k, cz + r), (cx - r, cz + k), (cx + r, cz + k)):
                    bb.set(x, fy + 2, z, "minecraft:dark_oak_trapdoor[facing=north,half=bottom,open=true]" if False else "minecraft:iron_bars")
            bb.fill(cx - r, fy - 1, cz - r, cx + r, fy - 1, cz + r, "minecraft:dark_oak_planks")
            A.curved_roof(bb, cx - r - 2, cz - r - 2, cx + r + 2, cz + r + 2, fy + 5, 3 if r == 5 else 4, style="hip" if r == 5 else "irimoya", pal=WANO)
        bb.set(cx, GY + 18, cz, "minecraft:lantern[hanging=false]") if False else bb.set(cx, GY + 21, cz, "minecraft:lantern[hanging=true]")
        bb.fill(cx + 2, GY + 1, cz, cx + 2, GY + 24, cz, "minecraft:ladder[facing=east]")
        bb.fill(cx + 1, GY + 1, cz, cx + 1, GY + 16, cz, AIR)
        bb.fill(cx - 5, GY + 1, cz - 5, cx + 5, GY + 16, cz + 5, AIR) if False else None
    # the gate in the south wall: a big wooden gatehouse with doors open, and the horned Beast Pirates skull above
    gx = 76
    bb.fill(gx - 5, GY + 1, W2 - 3, gx + 5, GY + 9, W2, AIR)
    bb.fill(gx - 9, GY - 2, W2 - 5, gx + 9, GY + 18, W2 + 2, "minecraft:dark_oak_planks")
    bb.fill(gx - 5, GY + 1, W2 - 5, gx + 5, GY + 10, W2 + 2, AIR)
    for x in (gx - 9, gx - 6, gx + 6, gx + 9):
        bb.fill(x, GY - 2, W2 + 3, x, GY + 18, W2 + 3, "minecraft:stripped_dark_oak_log[axis=y]")
    for k in range(-5, 6):
        bb.set(gx + k, GY + 10, W2 + 3, "minecraft:dark_oak_slab[type=top]")
    for (dx, rot) in ((-5, "east"), (5, "west")):
        bb.fill(gx + dx, GY + 1, W2 - 4, gx + dx, GY + 9, W2 - 1, "minecraft:spruce_planks")
    A.curved_roof(bb, gx - 11, W2 - 7, gx + 11, W2 + 4, GY + 19, 5, style="irimoya", pal=WANO)
    # the skull: white bone face with two curved horns, painted on a black board on the gatehouse front
    sx, sy, sz = gx, GY + 14, W2 + 4
    bb.fill(sx - 7, sy - 4, sz, sx + 7, sy + 4, sz, "minecraft:black_concrete")
    for u in range(-4, 5):
        for v in range(-3, 4):
            if u * u / 16.0 + v * v / 10.0 <= 1:
                bb.set(sx + u, sy + v, sz + 1, "minecraft:bone_block[axis=y]")
    for u in (-2, 2):
        bb.set(sx + u, sy, sz + 1, "minecraft:black_concrete"); bb.set(sx + u, sy + 1, sz + 1, "minecraft:black_concrete")
    bb.fill(sx - 2, sy - 3, sz + 1, sx + 2, sy - 3, sz + 1, "minecraft:quartz_block")
    for k in range(6):
        bb.set(sx - 5 - k // 2, sy + 2 + k, sz + 1, "minecraft:quartz_block"); bb.set(sx + 5 + k // 2, sy + 2 + k, sz + 1, "minecraft:quartz_block")


def kitchen(bb):
    """The soup kitchen west of the pit: an open-sided Wano shed with the giant red-bean cauldron and serving tables."""
    x1, z1, x2, z2 = 28, 98, 52, 118
    y = GY
    bb.fill(x1, y, z1, x2, y, z2, "minecraft:dark_oak_planks")
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            bb.fill(x, y + 1, z, x, y + 6, z, "minecraft:stripped_dark_oak_log[axis=y]")
    for z in range(z1, z2 + 1, 4):
        for x in (x1, x2):
            bb.fill(x, y + 1, z, x, y + 6, z, "minecraft:stripped_dark_oak_log[axis=y]")
    bb.fill(x1, y + 1, z1, x1, y + 2, z2, "minecraft:white_terracotta"); bb.fill(x2, y + 1, z1, x2, y + 2, z2, "minecraft:white_terracotta")
    A.curved_roof(bb, x1 - 2, z1 - 2, x2 + 2, z2 + 2, y + 7, 4, style="gable", pal=WANO)
    # the cauldron: a dark iron bowl 7 across on a fire pit, full of red-bean soup (red terracotta + mud)
    cx, cz = x1 + 8, (z1 + z2) // 2
    bb.cylinder(cx, y + 1, cz, 4, y + 1, "minecraft:magma_block")
    bb.cylinder(cx, y + 2, cz, 4, y + 4, "minecraft:polished_blackstone", hollow=True)
    bb.cylinder(cx, y + 2, cz, 3, y + 2, "minecraft:polished_blackstone")
    bb.cylinder(cx, y + 3, cz, 3, y + 3, "minecraft:brown_terracotta")
    bb.set(cx, y + 4, cz, "minecraft:red_carpet")
    bb.fill(cx - 6, y + 1, cz - 6, cx - 6, y + 6, cz - 6, "minecraft:dark_oak_fence")
    for z in range(z1 + 2, z2 - 1, 4):
        for x in range(x1 + 15, x2 - 1, 5):
            bb.fill(x, y + 1, z, x + 2, y + 1, z, "minecraft:dark_oak_slab[type=top]")
            bb.set(x, y + 2, z, "minecraft:bowl" if False else "minecraft:flower_pot")
            for xx in range(x, x + 3):
                bb.set(xx, y + 1, z - 1, "minecraft:dark_oak_stairs[facing=south]") if (xx + z) % 2 else None
    for x in range(x1 + 4, x2, 6):
        bb.set(x, y + 6, (z1 + z2) // 2, "onepiece:paper_lantern[hanging=true]")


def barracks(bb):
    """Two long prisoner barracks south-east (barred windows, bunks) and the weapons workshop north."""
    for (x1, z1, x2, z2, kind) in ((88, 96, 124, 106, "barracks"), (88, 110, 124, 120, "barracks"), (28, 28, 60, 40, "workshop")):
        y = GY
        bb.fill(x1, y, z1, x2, y, z2, "minecraft:dark_oak_planks")
        bb.mix(x1, y + 1, z1, x2, y + 5, z2, ["minecraft:dark_oak_planks", "minecraft:spruce_planks", "minecraft:stripped_dark_oak_wood"], [0.5, 0.3, 0.2])
        bb.fill(x1 + 1, y + 1, z1 + 1, x2 - 1, y + 5, z2 - 1, AIR)
        for x in range(x1, x2 + 1, 4):
            bb.fill(x, y + 1, z1, x, y + 5, z1, "minecraft:stripped_dark_oak_log[axis=y]"); bb.fill(x, y + 1, z2, x, y + 5, z2, "minecraft:stripped_dark_oak_log[axis=y]")
            if x + 2 < x2:
                bb.fill(x + 1, y + 3, z1, x + 2, y + 3, z1, BARS); bb.fill(x + 1, y + 3, z2, x + 2, y + 3, z2, BARS)
        A.curved_roof(bb, x1 - 2, z1 - 2, x2 + 2, z2 + 2, y + 6, 4, style="gable", pal=WANO)
        mid = (x1 + x2) // 2
        furnish_kit(bb, (x1 + 1, z1 + 1, mid - 1, z2 - 1), y + 1, 4, kind, wood="dark_oak", seed=6630 + x1 + z1, doors=[(mid, (z1 + z2) // 2)], accent="brown")
        furnish_kit(bb, (mid + 1, z1 + 1, x2 - 1, z2 - 1), y + 1, 4, kind if kind != "workshop" else "storeroom", wood="dark_oak",
                    seed=6631 + x1 + z1, doors=[(mid, (z1 + z2) // 2)], accent="brown")
        bb.fill(mid, y + 1, z1 + 1, mid, y + 5, z2 - 1, "minecraft:stripped_dark_oak_log[axis=y]")
        bb.fill(mid, y + 1, (z1 + z2) // 2, mid, y + 2, (z1 + z2) // 2, AIR)
        bb.fill(x1, y + 1, (z1 + z2) // 2, x1, y + 2, (z1 + z2) // 2, AIR)
    # stockpiles: ore heaps and stacked timber in the yard
    rng = np.random.default_rng(6640)
    for (x, z) in ((96, 30), (104, 34), (112, 28), (40, 80), (30, 64)):
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                h = max(0, 3 - abs(dx) - abs(dz) + int(rng.integers(0, 2)))
                bb.fill(x + dx, GY + 1, z + dz, x + dx, GY + h, z + dz, "minecraft:raw_iron_block" if (dx + dz) % 3 else "minecraft:coal_block") if h else None
    for z in range(76, 92, 3):
        bb.fill(26, GY + 1, z, 34, GY + 2, z + 1, "minecraft:stripped_spruce_log[axis=x]")
    for x in range(30, 126, 12):
        lamp_post(bb, x, GY + 1, 92, post="minecraft:dark_oak_fence", light="onepiece:paper_lantern[hanging=false]")


def design():
    bb = BigBuild(seed=6600, y_min=BOTTOM - 8, y_max=80)
    terrain(bb)
    pit(bb)
    sumo_ring(bb)
    gate_and_walls(bb)
    top = warden_tower(bb)
    kitchen(bb)
    barracks(bb)
    return bb, [], top


def build():
    bb, audit, top = design()
    b = to_canvas(bb)
    steady(b)
    b.chest(110, GY + 23, 52, "hard", "south")
    b.chest(PCX + 4, BOTTOM + 3, PCZ + 4, "hard", "north")
    b.chest(30, GY + 1, 100, "wano", "east")
    for (x, z) in ((70, 92), (90, 80), (44, 90), (76, 120), (110, 86)):
        b.guard(x, GY + 1, z, "gifter")
    b.guard(PCX - 10, BOTTOM + 1, PCZ, "headliner")
    b.guard(108, GY + 23, 58, "headliner")
    b.guard(96, GY + 1, 58, "jailer")
    return b, 0
