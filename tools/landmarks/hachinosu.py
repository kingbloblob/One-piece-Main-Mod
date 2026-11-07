"""Hachinosu, the pirate island ruled by Blackbeard. A huge skull-shaped crag looms over a lawless harbour town of
ramshackle shacks, taverns and stalls built up the rocks, with piers and two moored pirate ships. Inside the skull
is Blackbeard's den: the mouth-cave tavern hall where the Titanic Captains drink, a fighting pit, the bunks,
and up the stairs Blackbeard's throne room behind the eyes and the treasure vault in the cranium. ~112 x 112.
Ground = y 0, the skull faces south (+z)."""
import math, random
from canvas import *
import interiors as I

SID = "hachinosu"
TITLE = "Hachinosu (Blackbeard's island)"
CUTS = [4, 18]
TILER = dict(heightmap="WORLD_SURFACE_WG", terrain="beard_thin")

N = 112
CX, SZ = 56, 40           # skull centre (x, z)
RX, RY, RZ, YC = 24, 24, 22, 22
ROCK = ("minecraft:stone", "minecraft:andesite", "minecraft:tuff", "minecraft:stone", "minecraft:cobblestone", "minecraft:deepslate")
SEA_Z = 92                # sea south of this z
BB = dict(wood="dark_oak", rug="black", rug2="gray", bed="black", light="minecraft:lantern", accent="minecraft:obsidian",
          banner="black", candle="black")
PIRATE = I.THEMES["pirate"]


def in_skull(x, y, z):
    if y < 0: return False
    dx, dz = x - CX, z - SZ
    if (dx / RX) ** 2 + ((y - YC) / RY) ** 2 + (dz / RZ) ** 2 <= 1: return True
    return y <= 14 and (dx / 17) ** 2 + ((dz - 6) / 20) ** 2 <= 1  # jaw


def shack(b, x0, z0, w, d, y, rnd, kind):
    wall = rnd.choice(("minecraft:spruce_planks", "minecraft:oak_planks", "minecraft:dark_oak_planks", "minecraft:stripped_spruce_log[axis=y]"))
    h = 4
    b.box(x0, y, z0, x0 + w - 1, y, z0 + d - 1, "minecraft:spruce_planks")
    for x in range(x0, x0 + w):  # stilts down to the rock
        for z in (z0, z0 + d - 1):
            if x in (x0, x0 + w - 1):
                for yy in range(y - 1, y - 8, -1):
                    if b.get(x, yy, z) not in (None, AIR, WATER): break
                    b.set(x, yy, z, "minecraft:spruce_log[axis=y]")
    b.walls(x0, y + 1, z0, x0 + w - 1, y + h, z0 + d - 1, wall)
    b.box(x0 + 1, y + 1, z0 + 1, x0 + w - 2, y + h, z0 + d - 2, AIR)
    for x in range(x0 + 1, x0 + w - 1, 3): b.set(x, y + 2, z0 + d - 1, "minecraft:glass_pane" if rnd.random() < 0.5 else "minecraft:spruce_trapdoor[facing=south,half=top,open=true,powered=false,waterlogged=false]")
    mx = x0 + w // 2
    b.set(mx, y + 1, z0 + d - 1, AIR); b.set(mx, y + 2, z0 + d - 1, AIR)
    I.furnish(b, x0 + 1, y + 1, z0 + 1, x0 + w - 2, z0 + d - 2, h - 1, kind, PIRATE, seed=rnd.randint(0, 9999))
    roof = rnd.choice(("minecraft:spruce", "minecraft:dark_oak", "minecraft:mangrove"))
    b.gable_roof(x0, z0, x0 + w - 1, z0 + d - 1, y + h + 1, f"{roof}_stairs", f"{roof}_planks")
    if rnd.random() < 0.4: b.set(mx + 1, y + 3, z0 + d, lantern())


def build():
    rnd = random.Random(73)
    b = B()
    # ---------------- island rock and the harbour
    for x in range(N):
        for z in range(N):
            d = math.hypot(x - CX, (z - SZ) * 0.9)
            if z >= SEA_Z + 3 * math.sin(x * 0.2):
                depth = min(6, int((z - SEA_Z) / 2) + 1)
                for y in range(-depth, 1): b.set(x, y, z, WATER)
                b.set(x, -depth - 1, z, "minecraft:gravel" if (x + z) % 2 else "minecraft:stone")
                for y in range(-depth - 3, -depth - 1): b.set(x, y, z, "minecraft:stone")
                continue
            # terraces of rock rising towards the skull
            h = max(0, int(10 - d / 5)) if d < 50 else 0
            for y in range(-3, h + 1): b.set(x, y, z, rnd.choice(ROCK) if y < h else rnd.choice(("minecraft:coarse_dirt", "minecraft:gravel", "minecraft:stone", "minecraft:andesite", "minecraft:tuff", "minecraft:packed_mud", "minecraft:coarse_dirt")))
            if h == 0 and rnd.random() < 0.02: b.set(x, 1, z, "minecraft:dead_bush")
    # ---------------- the skull
    def mat(x, y, z):
        return "minecraft:bone_block[axis=y]" if (x * 3 + y * 7 + z * 5) % 13 == 0 else ("minecraft:calcite" if y > 30 or (x + z) % 4 else "minecraft:diorite")
    b.shape(in_skull, CX - RX - 1, 0, SZ - RZ - 1, CX + RX + 1, YC + RY, SZ + RZ + 21, mat, interior=None)
    # hollow inside
    def inner(x, y, z):
        dx, dz = x - CX, z - SZ
        return 1 <= y and ((dx / (RX - 3)) ** 2 + ((y - YC) / (RY - 3)) ** 2 + (dz / (RZ - 3)) ** 2 <= 1 or (y <= 11 and (dx / 14) ** 2 + ((dz - 6) / 17) ** 2 <= 1))
    for x in range(CX - RX, CX + RX + 1):
        for y in range(1, YC + RY):
            for z in range(SZ - RZ, SZ + RZ + 21):
                if inner(x, y, z): b.set(x, y, z, AIR)
    # eye sockets and the nose, carved through the front, lit red from inside
    def front(dx, y):
        for z in range(SZ + RZ + 21, SZ - 1, -1):
            if b.get(CX + dx, y, z) not in (None, AIR): return z
        return None
    for ex in (-10, 10):
        for dx in range(-6, 7):
            for dy in range(-5, 6):
                if (dx / 6) ** 2 + (dy / 5) ** 2 <= 1:
                    y = 28 + dy; fz = front(ex + dx, y)
                    if fz is None: continue
                    for z in range(fz + 1, fz - 2, -1): b.set(CX + ex + dx, y, z, AIR)
                    for z in (fz - 2, fz - 3): b.set(CX + ex + dx, y, z, "minecraft:red_stained_glass" if abs(dx) < 3 and abs(dy) < 2 else "minecraft:black_concrete")
    for dy in range(0, 7):
        for dx in range(-(dy // 2) - 1, dy // 2 + 2):
            y = 20 - dy; fz = front(dx, y)
            if fz is not None:
                for z in range(fz + 1, fz - 3, -1): b.set(CX + dx, y, z, AIR)
                b.set(CX + dx, y, fz - 3, "minecraft:black_concrete")
    for dx in range(-18, 19):  # brow ridge over the sockets, cheekbones under them
        for (y, out) in ((34, 2), (35, 1), (21, 1)):
            if y == 21 and abs(dx) < 5: continue
            fz = front(dx, y)
            if fz is not None:
                for k in range(1, out + 1): b.set(CX + dx, y, fz + k, "minecraft:calcite")
    # mouth: the cave entrance with teeth
    MZ = None
    for z in range(SZ + RZ + 21, SZ, -1):
        if b.get(CX, 6, z) not in (None, AIR): MZ = z; break
    for dx in range(-11, 12):
        for y in range(1, 10):
            fz = front(dx, y)
            if fz is None: continue
            for z in range(fz, fz - 4, -1): b.set(CX + dx, y, z, AIR)
        if dx % 3 == 0:  # teeth top and bottom
            fz = front(dx, 10) or MZ
            if fz: b.set(CX + dx, 9, fz - 1, "minecraft:bone_block[axis=y]"); b.set(CX + dx, 8, fz - 1, "minecraft:bone_block[axis=y]")
            if fz and abs(dx) < 10: b.set(CX + dx, 1, fz - 1, "minecraft:bone_block[axis=y]")
    # ---------------- inside: the tavern hall (y1), stairs up, throne room (y 22) and vault (y 34)
    for x in range(CX - 15, CX + 16):
        for z in range(SZ - 16, SZ + 24):
            if inner(x, 1, z): b.set(x, 0, z, "minecraft:spruce_planks" if (x + z) % 5 else "minecraft:dark_oak_planks")
    r = I.furnish(b, CX - 13, 1, SZ - 10, CX + 13, SZ + 18, 9, "tavern", BB)
    r.chandelier(CX, SZ, 3, 3); r.chandelier(CX, SZ + 12, 3, 2)
    # bar counter along the west wall
    for z in range(SZ - 6, SZ + 10):
        b.set(CX - 11, 1, z, "minecraft:dark_oak_planks"); b.set(CX - 11, 2, z, "minecraft:dark_oak_slab[type=bottom,waterlogged=false]")
        if z % 2: b.set(CX - 13, 1, z, "onepiece:sake_barrel[axis=y]"); b.set(CX - 13, 2, z, "onepiece:sake_barrel[axis=y]")
    # fighting pit in the middle
    for x in range(CX - 4, CX + 5):
        for z in range(SZ - 4, SZ + 5):
            if math.hypot(x - CX, z - SZ) <= 4.5: b.set(x, 0, z, "minecraft:sand"); b.set(x, 1, z, AIR)
            if 4.5 < math.hypot(x - CX, z - SZ) <= 5.5: b.set(x, 1, z, fence("dark_oak"))
    # floors inside the cranium
    FT, FV = 21, 33
    for (fy, ry) in ((FT, 18), (FV, 13)):
        for x in range(CX - ry, CX + ry + 1):
            for z in range(SZ - ry, SZ + ry + 1):
                if inner(x, fy, z) and not inner(x, fy - 1, z) is False: b.set(x, fy - 1, z, "minecraft:dark_oak_planks")
    for x in range(CX - 3, CX + 4):  # stairwell holes
        for z in range(SZ - 14, SZ - 11): b.set(x, FT - 1, z, AIR)
    for i in range(FT - 1):  # big switchback stairs from the hall
        z = SZ - 12 + (i % 10) * 0
        x = CX - 9 + i if i < 10 else CX + 1 + (i - 10)
        for w in (0, 1, 2): b.set(x, 1 + i, SZ - 14 + w, stairs("minecraft:dark_oak_stairs", "east"))
        for w in (0, 1, 2):
            for k in (1, 2, 3): b.set(x, 1 + i + k, SZ - 14 + w, AIR)
    for x in range(CX - 9, CX + 12):
        for z in range(SZ - 14, SZ - 11): b.set(x, FT - 1, z, AIR) if x > CX - 9 + 10 - 12 else None
    r = I.furnish(b, CX - 14, FT, SZ - 9, CX + 14, SZ + 14, 10, "throne", BB)
    b.box(CX - 3, FT, SZ + 4, CX + 3, FT, SZ + 7, "minecraft:obsidian")
    b.set(CX, FT + 1, SZ + 5, stairs("minecraft:blackstone_stairs", "north")); b.set(CX - 1, FT + 1, SZ + 5, "minecraft:obsidian"); b.set(CX + 1, FT + 1, SZ + 5, "minecraft:obsidian")
    b.set(CX, FT + 2, SZ + 6, "minecraft:obsidian"); b.set(CX, FT + 3, SZ + 6, "minecraft:crying_obsidian")
    for k in range(FV - FT):  # ladder up to the vault
        b.set(CX + 12, FT + k, SZ, "minecraft:ladder[facing=west,waterlogged=false]")
    b.set(CX + 12, FV - 1, SZ, "minecraft:ladder[facing=west,waterlogged=false]")
    for k in range(FV - FT): b.set(CX + 13, FT + k, SZ, "minecraft:stone") if b.get(CX + 13, FT + k, SZ) in (None, AIR) else None
    I.furnish(b, CX - 9, FV, SZ - 8, CX + 9, SZ + 8, 7, "treasure", BB)
    # ---------------- harbour town on the slopes and the shore
    rx = random.Random(5)
    spots = [(8, 62), (20, 66), (32, 70), (74, 70), (86, 66), (98, 62), (10, 78), (24, 80), (80, 80), (94, 78), (6, 46), (100, 46),
             (14, 30), (92, 30), (44, 78), (62, 80)]
    kinds = ("tavern", "bedroom", "storage", "kitchen", "tavern", "workshop", "bedroom", "dining", "armory", "storage", "bedroom", "tavern",
             "bedroom", "workshop", "dining", "tavern")
    for i, (x0, z0) in enumerate(spots):
        w, d = rx.randint(6, 9), rx.randint(6, 8)
        if any(in_skull(x, 3, z) for x in (x0, x0 + w) for z in (z0, z0 + d)): continue
        gy = 0
        for x in range(x0, x0 + w):
            for z in range(z0, z0 + d):
                for y in range(14, -1, -1):
                    if b.get(x, y, z) not in (None, AIR, WATER): gy = max(gy, y); break
        shack(b, x0, z0, w, d, gy + 1, rx, kinds[i])
    # piers and the two moored ships
    for (px, pl) in ((20, 16), (70, 16)):
        for z in range(SEA_Z - 2, SEA_Z + pl):
            for x in range(px, px + 3): b.set(x, 1, z, "minecraft:spruce_planks")
            if z % 4 == 0:
                for x in (px - 1, px + 3): b.column(x, z, -5, 2, "minecraft:spruce_log[axis=y]")
    b.ship(px - 40 + 30, -3, SEA_Z + 4, 26, 9, masts=((10, 14), (18, 11)), sail="minecraft:black_wool", flag=("minecraft:black_wool", "minecraft:white_wool"), cabin=(5, 3, "minecraft:dark_oak_planks"))
    b.ship(px + 6, -3, SEA_Z + 6, 30, 10, masts=((12, 16), (21, 12)), sail="minecraft:gray_wool", cabin=(6, 3, "minecraft:dark_oak_planks"))
    # Blackbeard's flag on a crag pole above the skull
    for y in range(YC + RY, YC + RY + 10): b.set(CX, y, SZ, "minecraft:dark_oak_fence")
    b.jolly_roger(CX, YC + RY + 9, SZ + 1, 9, 6, axis="z")
    # lanterns up the path to the mouth
    for z in range(SZ + 22, SEA_Z, 3):
        for x in (CX - 4, CX + 4):
            for y in range(14, -1, -1):
                if b.get(x, y, z) not in (None, AIR, WATER): b.set(x, y + 1, z, fence("dark_oak")); b.set(x, y + 2, z, lantern()); break
    # ---------------- people and loot
    b.npc(CX, FT + 1, SZ + 3, "blackbeard", True)
    b.chest(CX - 4, FV, SZ - 6, "legendary", "south"); b.chest(CX + 4, FV, SZ - 6, "legendary", "south"); b.chest(CX - 12, 1, SZ + 14, "treasure", "east")
    b.guards("blackbeard_pirate", ((CX - 6, SZ + 8), (CX + 6, SZ + 8), (CX - 8, SZ - 4), (CX + 8, SZ - 4)))
    b.guards("blackbeard_pirate", ((CX - 8, SZ + 10), (CX + 8, SZ + 10)), y=FT)
    b.guards("pirate_gunner", ((30, 72), (80, 72)), y=4)
    b.guards("war_beast", ((CX, SZ + 30),), y=4)
    return b, 0
