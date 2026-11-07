"""Room furnishing for the landmarks. furnish(b, x0, y, z0, x1, z1, h, kind, theme) fills the empty inside of a room
(x0..x1, z0..z1 inclusive, floor block at y-1, h free blocks of headroom) with themed furniture, lighting, wall
decoration and props. It only places into empty cells, never into walls, doors or stairs, and keeps a walking
path free in front of every doorway it finds.

Kinds: bedroom, barracks, kitchen, dining, banquet, library, study, captain, tavern, throne, treasure, armory,
storage, workshop, lab, shrine, cell, hall, bath, chapel.
Themes (palettes) are in THEMES: wood, cloth colours, light, accent block, banner colour.
"""
import math, random, zlib
from canvas import *
from nbt import Byte, Int, Float, IntList

DIR = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
PAINTINGS = ("minecraft:kebab", "minecraft:aztec", "minecraft:alban", "minecraft:bomb", "minecraft:plant", "minecraft:wasteland",
             "minecraft:wanderer", "minecraft:graham", "minecraft:sea", "minecraft:sunset", "minecraft:creebet", "minecraft:courbet",
             "minecraft:pool", "minecraft:meditative", "minecraft:prairie_ride", "minecraft:baroque", "minecraft:humble", "minecraft:tides",
             "minecraft:passage", "minecraft:changing", "minecraft:fern", "minecraft:sunflowers", "minecraft:lowmist", "minecraft:orb")
PLANTS = ("minecraft:potted_fern", "minecraft:potted_azalea_bush", "minecraft:potted_flowering_azalea_bush", "minecraft:potted_red_tulip",
          "minecraft:potted_cactus", "minecraft:potted_blue_orchid", "minecraft:potted_allium", "minecraft:potted_cherry_sapling",
          "minecraft:potted_oxeye_daisy", "minecraft:potted_bamboo", "minecraft:potted_lily_of_the_valley", "minecraft:potted_mangrove_propagule")

THEMES = {
    # wood, rug border, rug inside, bed colour, light block, accent (trim/table cloth), banner colour, candle colour
    "pirate":   dict(wood="dark_oak", rug="red", rug2="black", bed="red", light="minecraft:lantern", accent="minecraft:gold_block", banner="black", candle="white"),
    "marine":   dict(wood="birch", rug="blue", rug2="white", bed="light_blue", light="minecraft:lantern", accent="minecraft:light_blue_concrete", banner="blue", candle="white"),
    "royal":    dict(wood="dark_oak", rug="red", rug2="yellow", bed="red", light="minecraft:lantern", accent="minecraft:gold_block", banner="red", candle="yellow"),
    "desert":   dict(wood="jungle", rug="orange", rug2="yellow", bed="orange", light="minecraft:lantern", accent="minecraft:cut_sandstone", banner="yellow", candle="orange"),
    "wano":     dict(wood="spruce", rug="red", rug2="black", bed="red", light="onepiece:paper_lantern[hanging=true]", accent="onepiece:wano_lacquer_planks", banner="red", candle="red"),
    "candy":    dict(wood="cherry", rug="pink", rug2="white", bed="pink", light="minecraft:pearlescent_froglight[axis=y]", accent="onepiece:frosting_block", banner="pink", candle="pink"),
    "gloom":    dict(wood="dark_oak", rug="purple", rug2="black", bed="purple", light="minecraft:soul_lantern", accent="minecraft:crying_obsidian", banner="purple", candle="purple"),
    "sea":      dict(wood="mangrove", rug="cyan", rug2="light_blue", bed="cyan", light="onepiece:bubble_lamp[hanging=true]", accent="onepiece:pearl_block", banner="cyan", candle="cyan"),
    "shipyard": dict(wood="spruce", rug="brown", rug2="orange", bed="brown", light="minecraft:lantern", accent="minecraft:copper_block", banner="orange", candle="orange"),
    "justice":  dict(wood="dark_oak", rug="black", rug2="gray", bed="black", light="minecraft:lantern", accent="minecraft:polished_deepslate", banner="black", candle="black"),
    "kaido":    dict(wood="dark_oak", rug="purple", rug2="black", bed="purple", light="onepiece:paper_lantern[hanging=true]", accent="onepiece:wano_lacquer_planks", banner="purple", candle="purple"),
}


class Room:
    def __init__(self, b, x0, y, z0, x1, z1, h, theme, rnd):
        self.b, self.x0, self.y, self.z0, self.x1, self.z1, self.h = b, min(x0, x1), y, min(z0, z1), max(x0, x1), max(z0, z1), h
        self.t = THEMES[theme] if isinstance(theme, str) else theme
        self.rnd = rnd
        self.cx, self.cz = (self.x0 + self.x1) // 2, (self.z0 + self.z1) // 2
        self.keep = set()
        # doorways: an empty cell just outside the room at foot height -> keep a 2-deep path in front of it
        for (x, z, f) in self.edge():
            dx, dz = DIR[f]
            ox, oz = x - dx, z - dz
            if self.free(ox, y, oz) and self.free(ox, y + 1, oz):
                for k in range(3):
                    for s in (-1, 0, 1):
                        px, pz = (x + dx * k + (s if dz else 0), z + dz * k + (s if dx else 0))
                        self.keep.add((px, pz))

        # keep clear: cells over holes in the floor (stair and ladder wells) and next to ladders, stairs and doors
        for x in range(self.x0 - 1, self.x1 + 2):
            for z in range(self.z0 - 1, self.z1 + 2):
                here = b.get(x, y, z) or ""
                below = b.get(x, y - 1, z)
                inside = self.x0 <= x <= self.x1 and self.z0 <= z <= self.z1
                hole = inside and below in (None, AIR, "minecraft:cave_air")
                if hole or "ladder" in here or "_stairs" in here or "door" in here or "trapdoor" in here and "open=true" in here:
                    for dx in (-1, 0, 1):
                        for dz in (-1, 0, 1): self.keep.add((x + dx, z + dz))

    def free(self, x, y, z):
        return self.b.get(x, y, z) in (None, AIR, "minecraft:cave_air")

    def ok(self, x, y, z):
        return (x, z) not in self.keep and self.free(x, y, z) and not self.free(x, y - 1, z) and self.x0 <= x <= self.x1 and self.z0 <= z <= self.z1

    def put(self, x, y, z, s, data=None):
        if self.ok(x, y, z): self.b.set(x, y, z, s, data); return True
        return False

    def edge(self):
        """Cells along the inside of each wall, with the direction pointing into the room."""
        out = []
        for x in range(self.x0, self.x1 + 1): out += [(x, self.z0, "south"), (x, self.z1, "north")]
        for z in range(self.z0 + 1, self.z1): out += [(self.x0, z, "east"), (self.x1, z, "west")]
        return out

    def wall_is_solid(self, x, z, f, y=None):
        dx, dz = DIR[f]
        return not self.free(x - dx, self.y if y is None else y, z - dz)

    # ---------------- common pieces
    def rug(self, inset=1, c1=None, c2=None):
        c1 = c1 or self.t["rug"]; c2 = c2 or self.t["rug2"]
        x0, x1, z0, z1 = self.x0 + inset, self.x1 - inset, self.z0 + inset, self.z1 - inset
        if x1 - x0 < 2 or z1 - z0 < 2: return
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                border = x in (x0, x1) or z in (z0, z1)
                diamond = (abs(x - self.cx) + abs(z - self.cz)) % 4 == 0
                c = c1 if border else (c1 if diamond else c2)
                if self.free(x, self.y, z): self.b.set(x, self.y, z, f"minecraft:{c}_carpet")

    def chandelier(self, x=None, z=None, drop=2, ring=2):
        x = self.cx if x is None else x; z = self.cz if z is None else z
        top = self.y + self.h - 1
        if self.h < 5: self.b.set(x, top, z, self.t["light"] if "hanging" in self.t["light"] else lantern(True)); return
        for yy in range(top, top - drop, -1): self.b.set(x, yy, z, "minecraft:iron_chain[axis=y]")
        cy = top - drop
        self.b.set(x, cy, z, "minecraft:gold_block" if self.t["accent"] == "minecraft:gold_block" else "minecraft:dark_oak_planks")
        for (dx, dz) in ((ring, 0), (-ring, 0), (0, ring), (0, -ring)):
            self.b.set(x + dx // 2 if ring > 1 else x + dx, cy, z + dz // 2 if ring > 1 else z + dz, "minecraft:dark_oak_fence")
            self.b.set(x + dx, cy, z + dz, "minecraft:dark_oak_fence")
            self.b.set(x + dx, cy - 1, z + dz, lantern(True, soul="soul" in self.t["light"]))

    def lights(self, every=5):
        for x in range(self.x0 + 2, self.x1 - 1, every):
            for z in range(self.z0 + 2, self.z1 - 1, every):
                top = self.y + self.h - 1
                if self.free(x, top, z) and not self.free(x, top + 1, z):
                    l = self.t["light"]
                    self.b.set(x, top, z, l if ("hanging" in l or "froglight" in l) else lantern(True, soul="soul" in l))

    def wall_banners(self, every=4, y_off=2):
        for (x, z, f) in self.edge():
            if (x + z) % every or (x, z) in self.keep or not self.wall_is_solid(x, z, f, self.y + y_off): continue
            if self.free(x, self.y + y_off, z) and self.free(x, self.y + y_off - 1, z):
                self.b.set(x, self.y + y_off, z, f"minecraft:{self.t['banner']}_wall_banner[facing={f}]")

    def paintings(self, n=2):
        cells = [c for c in self.edge() if self.wall_is_solid(c[0], c[2] if False else c[1], c[2], self.y + 2)]
        self.rnd.shuffle(cells)
        face = {"south": 0, "west": 1, "north": 2, "east": 3}
        for (x, z, f) in cells[:n]:
            if self.free(x, self.y + 2, z):
                self.b.entities.append(("minecraft:painting", x, self.y + 2, z,
                                        {"variant": self.rnd.choice(PAINTINGS), "facing": Byte(face[f]), "block_pos": IntList([x, self.y + 2, z])}))

    def plants(self, n=2):
        corners = [(self.x0, self.z0), (self.x1, self.z0), (self.x0, self.z1), (self.x1, self.z1)]
        self.rnd.shuffle(corners)
        for (x, z) in corners[:n]:
            if self.put(x, self.y, z, "minecraft:spruce_trapdoor[facing=north,half=top,open=false]" if False else "minecraft:decorated_pot" if self.rnd.random() < 0.3 else self.rnd.choice(PLANTS)):
                pass

    def shelves_run(self, f_filter=None, height=2, books=False, every=1):
        for (x, z, f) in self.edge():
            if f_filter and f not in f_filter: continue
            if (x, z) in self.keep or not self.wall_is_solid(x, z, f): continue
            for k in range(height):
                yy = self.y + k
                if not self.free(x, yy, z): break
                if books:
                    self.b.set(x, yy, z, "minecraft:bookshelf" if (x + z + k) % 5 else f"minecraft:chiseled_bookshelf[facing={f},slot_0_occupied=true,slot_1_occupied=true,slot_2_occupied=false,slot_3_occupied=true,slot_4_occupied=true,slot_5_occupied=false]")
                else:
                    self.b.set(x, yy, z, f"minecraft:{self.t['wood']}_shelf[facing={f}]" if k else "minecraft:barrel[facing=up,open=false]")

    def table(self, x, z, cloth=True, candle=True, chairs=True):
        w = self.t["wood"]
        if not self.ok(x, self.y, z): return
        self.b.set(x, self.y, z, f"minecraft:{w}_fence")
        self.b.set(x, self.y + 1, z, f"minecraft:{self.t['rug']}_carpet" if cloth else f"minecraft:{w}_pressure_plate[powered=false]")
        if candle and self.free(x, self.y + 2, z) and self.rnd.random() < 0.6:
            self.b.set(x, self.y + 1, z, f"minecraft:{w}_slab[type=bottom,waterlogged=false]")
            self.b.set(x, self.y + 2, z, candle_str(self.t["candle"], self.rnd.randint(1, 3)))
        if chairs:
            for f, (dx, dz) in DIR.items():
                self.put(x + dx, self.y, z + dz, stairs(f"minecraft:{w}_stairs", f))

    def long_table(self, x0, x1, z, candles=True, food=True):
        w = self.t["wood"]
        for x in range(x0, x1 + 1):
            if not self.ok(x, self.y, z): continue
            self.b.set(x, self.y, z, f"minecraft:stripped_{w}_log[axis=x]" if w not in ("bamboo",) else "minecraft:bamboo_block[axis=x]")
            top = self.y + 1
            if (x - x0) % 3 == 1 and candles: self.b.set(x, top, z, candle_str(self.t["candle"], 3))
            elif food and self.rnd.random() < 0.5: self.b.set(x, top, z, self.rnd.choice(("minecraft:cake", "onepiece:feast_table[facing=north]", "minecraft:decorated_pot", "minecraft:flower_pot")))
            for dz in (-1, 1): self.put(x, self.y, z + dz, stairs(f"minecraft:{w}_stairs", "north" if dz < 0 else "south"))

    def bed(self, x, z, f, color=None):
        """Bed with its head against the wall in direction f's opposite (f points into the room)."""
        dx, dz = DIR[f]
        c = color or self.t["bed"]
        if self.ok(x, self.y, z) and self.ok(x + dx, self.y, z + dz):
            head_facing = {"north": "south", "south": "north", "east": "west", "west": "east"}[f]
            self.b.set(x, self.y, z, f"minecraft:{c}_bed[facing={head_facing},occupied=false,part=head]")
            self.b.set(x + dx, self.y, z + dz, f"minecraft:{c}_bed[facing={head_facing},occupied=false,part=foot]")
            return True
        return False

    def armor_stand(self, x, z, kit="iron", yaw=0.0):
        if not self.ok(x, self.y, z): return
        sets = {"iron": ("iron_helmet", "iron_chestplate", "iron_leggings", "iron_boots", "iron_sword"),
                "gold": ("golden_helmet", "golden_chestplate", "golden_leggings", "golden_boots", "golden_sword"),
                "chain": ("chainmail_helmet", "chainmail_chestplate", "chainmail_leggings", "chainmail_boots", "iron_axe"),
                "leather": ("leather_helmet", "leather_chestplate", "leather_leggings", "leather_boots", "trident"),
                "diamond": ("diamond_helmet", "diamond_chestplate", "diamond_leggings", "diamond_boots", "diamond_sword")}[kit]
        eq = {"head": {"id": "minecraft:" + sets[0], "count": Int(1)}, "chest": {"id": "minecraft:" + sets[1], "count": Int(1)},
              "legs": {"id": "minecraft:" + sets[2], "count": Int(1)}, "feet": {"id": "minecraft:" + sets[3], "count": Int(1)},
              "mainhand": {"id": "minecraft:" + sets[4], "count": Int(1)}}
        self.b.entities.append(("minecraft:armor_stand", x, self.y, z, {"equipment": eq, "ShowArms": Byte(1), "Invulnerable": Byte(1),
                                                                     "PersistenceRequired": Byte(1), "Rotation": [Float(yaw), Float(0.0)]}))
        self.keep.add((x, z))

    def scatter(self, blocks, n, wall=False):
        cells = [(x, z) for x in range(self.x0, self.x1 + 1) for z in range(self.z0, self.z1 + 1)]
        if wall: cells = [(x, z) for (x, z, f) in self.edge()]
        self.rnd.shuffle(cells)
        k = 0
        for (x, z) in cells:
            if k >= n: break
            if self.put(x, self.y, z, self.rnd.choice(blocks)): k += 1


def candle_str(color, n=1):
    return f"minecraft:{color}_candle[candles={n},lit=true,waterlogged=false]" if color else f"minecraft:candle[candles={n},lit=true,waterlogged=false]"


def furnish(b, x0, y, z0, x1, z1, h, kind, theme="pirate", seed=None, lit=True):
    rnd = random.Random(seed if seed is not None else zlib.crc32(repr((x0, y, z0, kind)).encode()))
    r = Room(b, x0, y, z0, x1, z1, h, theme, rnd)
    w = r.t["wood"]
    W, D = r.x1 - r.x0 + 1, r.z1 - r.z0 + 1
    big = W * D > 120
    if kind == "bedroom":
        cells = sorted((c for c in r.edge() if r.wall_is_solid(*c)), key=lambda c: (c[2] not in ("north", "south"), abs(c[0] - r.cx) + abs(c[1] - r.cz)))
        x, z, f = cells[0] if cells else (r.cx, r.z0, "south")
        for (x, z, f) in cells:
            if r.bed(x, z, f):
                px, pz = (1, 0) if f in ("north", "south") else (0, 1)
                r.bed(x + px, z + pz, f)
                break
        side = (1, 0) if f in ("north", "south") else (0, 1)
        r.put(x - side[0], r.y, z - side[1], "minecraft:barrel[facing=up,open=false]"); r.put(x - side[0], r.y + 1, z - side[1], candle_str(r.t["candle"], 2))
        r.put(x + 2 * side[0], r.y, z + 2 * side[1], f"minecraft:{w}_shelf[facing={f}]")
        r.shelves_run(("north",), 2)
        r.rug(1); r.paintings(2); r.plants(2)
        r.put(r.x1, r.y, r.cz, "minecraft:lectern[facing=west,has_book=false,powered=false]")
        r.scatter(("minecraft:chest[facing=east,type=single,waterlogged=false]",), 1, wall=True)
    elif kind == "barracks":
        for (x, z, f) in r.edge():
            if f in ("east", "west") and (z - r.z0) % 3 == 1: r.bed(x, z, f)
        for x in range(r.x0 + 3, r.x1 - 2, 4): r.armor_stand(x, r.cz, rnd.choice(("iron", "chain")))
        r.scatter(("minecraft:barrel[facing=up,open=false]", "onepiece:training_post[facing=north]", "minecraft:chest[facing=north,type=single,waterlogged=false]"), max(2, W * D // 30))
        r.wall_banners(5)
    elif kind == "kitchen":
        for (x, z, f) in r.edge():
            if not r.wall_is_solid(x, z, f): continue
            k = (x + z) % 7
            s = ("minecraft:smoker[facing={f},lit=true]", "minecraft:furnace[facing={f},lit=true]", "onepiece:ships_galley[facing={f}]",
                 "minecraft:water_cauldron[level=3]", "minecraft:barrel[facing=up,open=false]", f"minecraft:{w}_shelf[facing={{f}}]", "minecraft:crafting_table")[k]
            r.put(x, r.y, z, s.format(f=f))
            if k in (4, 5): r.put(x, r.y + 1, z, f"minecraft:{w}_shelf[facing={f}]")
            if k in (0, 1) and r.free(x, r.y + 1, z): r.put(x, r.y + 1, z, "minecraft:iron_chain[axis=y]")
        for x in range(r.x0 + 2, r.x1 - 1, 3):
            r.put(x, r.y, r.cz, "minecraft:smooth_stone_slab[type=double,waterlogged=false]")
            r.put(x, r.y + 1, r.cz, rnd.choice(("minecraft:cake", "minecraft:decorated_pot", "onepiece:feast_table[facing=north]", "minecraft:flower_pot")))
        r.scatter(("onepiece:mikan_crate[axis=y]", "onepiece:cola_crate[axis=y]", "onepiece:sake_barrel[axis=y]", "minecraft:hay_block[axis=y]"), max(2, W * D // 25))
        r.lights(4)
    elif kind in ("dining", "banquet"):
        n = max(1, (D - 2) // 4)
        for i in range(n):
            z = r.z0 + 2 + i * 4
            if z <= r.z1 - 2: r.long_table(r.x0 + 2, r.x1 - 2, z)
        r.wall_banners(4); r.paintings(3); r.plants(4)
        for x in range(r.x0 + W // 4, r.x1, max(4, W // 3)): r.chandelier(x, r.cz)
    elif kind == "library":
        r.shelves_run(None, min(r.h - 1, 4), books=True)
        for x in range(r.x0 + 2, r.x1 - 1, 4):
            for z in range(r.z0 + 2, r.z1 - 1, 4): r.table(x, z, cloth=False)
        r.put(r.cx, r.y, r.cz, "minecraft:lectern[facing=south,has_book=false,powered=false]")
        r.rug(2, "brown", r.t["rug"]); r.lights(4); r.plants(2)
    elif kind in ("study", "captain"):
        r.put(r.cx, r.y, r.z0 + 1, "onepiece:navigators_desk[facing=south]")
        r.put(r.cx + 1, r.y, r.z0 + 1, "minecraft:cartography_table"); r.put(r.cx - 1, r.y, r.z0 + 1, "minecraft:lectern[facing=south,has_book=false,powered=false]")
        r.put(r.cx, r.y, r.z0 + 2, stairs(f"minecraft:{w}_stairs", "north"))
        r.shelves_run(("east", "west"), 3, books=True)
        r.put(r.x0, r.y, r.z1, "onepiece:den_den_relay[facing=east]" if kind == "study" else "onepiece:ships_wheel[facing=east]")
        r.put(r.x1, r.y, r.z1, "minecraft:chest[facing=west,type=single,waterlogged=false]")
        r.rug(1); r.paintings(2); r.chandelier(); r.plants(2)
        r.scatter(("onepiece:rope_coil[facing=north]", "minecraft:decorated_pot", "onepiece:sake_barrel[axis=y]"), 2, wall=True)
    elif kind == "tavern":
        # bar counter along the back wall with bottles and barrels behind it
        zc = r.z1 - 2
        for x in range(r.x0 + 1, r.x1):
            r.put(x, r.y, zc, stairs(f"minecraft:{w}_stairs", "north", "top"))
            if (x % 3) == 0: r.put(x, r.y + 1, zc, rnd.choice(("minecraft:brewing_stand", candle_str(r.t["candle"], 2), "minecraft:flower_pot")))
            r.put(x, r.y, r.z1, "onepiece:sake_barrel[axis=x]" if x % 2 else "minecraft:barrel[facing=north,open=false]")
            r.put(x, r.y + 1, r.z1, f"minecraft:{w}_shelf[facing=north]")
            r.put(x, r.y, zc - 1, f"minecraft:{w}_trapdoor[facing=north,half=top,open=false,powered=false,waterlogged=false]" if x % 2 else AIR)
        for x in range(r.x0 + 2, r.x1 - 1, 4):
            for z in range(r.z0 + 2, zc - 2, 4): r.table(x, z)
        r.put(r.x0, r.y, r.z0, "minecraft:jukebox"); r.put(r.x1, r.y + 1, r.z0, "onepiece:recruitment_board[facing=south]")
        r.paintings(2); r.lights(4)
    elif kind == "throne":
        for z in range(r.z0, r.z1 + 1):
            for x in (r.cx - 1, r.cx, r.cx + 1): r.put(x, r.y, z, f"minecraft:{r.t['rug']}_carpet")
        for z in range(r.z0 + 2, r.z1 - 1, 4):
            for x in (r.x0 + 1, r.x1 - 1):
                if r.ok(x, r.y, z):
                    for yy in range(r.y, r.y + min(r.h - 1, 5)): b.set(x, yy, z, "minecraft:quartz_pillar[axis=y]")
                    b.set(x, r.y + min(r.h - 1, 5), z, r.t["accent"])
                    r.keep.add((x, z))
        r.wall_banners(3); r.lights(6); r.plants(4)
    elif kind == "treasure":
        piles = ("minecraft:gold_block", "minecraft:raw_gold_block", "onepiece:berry_block", "minecraft:emerald_block", "minecraft:diamond_block")
        for i in range(max(3, W * D // 12)):
            x = rnd.randint(r.x0, r.x1); z = rnd.randint(r.z0, r.z1)
            hgt = rnd.choice((1, 1, 2))
            for k in range(hgt): r.put(x, r.y + k, z, rnd.choice(piles[:3]) if k == 0 else rnd.choice(piles))
        r.scatter(("minecraft:decorated_pot", "onepiece:treasure_vault[facing=north]", candle_str("yellow", 4), "minecraft:chest[facing=south,type=single,waterlogged=false]"), max(3, W * D // 15))
        for x in range(r.x0 + 1, r.x1, 3): r.armor_stand(x, r.z1, "gold", 180.0)
        r.lights(4)
    elif kind == "armory":
        for (x, z, f) in r.edge():
            if not r.wall_is_solid(x, z, f): continue
            k = (x + 2 * z) % 6
            if k == 0: r.armor_stand(x, z, rnd.choice(("iron", "chain", "diamond")))
            else: r.put(x, r.y, z, ("minecraft:anvil[facing=north]", "minecraft:grindstone[face=floor,facing=north]", "minecraft:smithing_table",
                                   f"onepiece:swordsmith_forge[facing={f}]", "minecraft:barrel[facing=up,open=false]")[k - 1])
        r.put(r.cx, r.y, r.cz, "onepiece:cannon[facing=south]")
        r.scatter(("onepiece:training_post[facing=north]", "minecraft:target", "minecraft:chest[facing=north,type=single,waterlogged=false]"), 3)
        r.wall_banners(4); r.lights(4)
    elif kind == "storage":
        for x in range(r.x0, r.x1 + 1):
            for z in range(r.z0, r.z1 + 1):
                if (x - r.x0) % 3 == 2 or (z - r.z0) % 4 == 3: continue
                hgt = rnd.randint(1, 3)
                for k in range(hgt):
                    r.put(x, r.y + k, z, rnd.choice(("minecraft:barrel[facing=up,open=false]", "onepiece:mikan_crate[axis=y]", "onepiece:cola_crate[axis=y]",
                                                     "minecraft:hay_block[axis=y]", "onepiece:sake_barrel[axis=y]", "onepiece:rope_coil[facing=north]")))
        r.lights(5)
    elif kind == "workshop":
        for (x, z, f) in r.edge():
            if not r.wall_is_solid(x, z, f): continue
            k = (x + z) % 6
            r.put(x, r.y, z, (f"onepiece:shipwright_bench[facing={f}]", "minecraft:crafting_table", f"minecraft:loom[facing={f}]",
                             "minecraft:anvil[facing=north]", "onepiece:rope_coil[facing=north]", "minecraft:fletching_table")[k])
            if k in (1, 5): r.put(x, r.y + 1, z, f"minecraft:{w}_shelf[facing={f}]")
        r.scatter(("minecraft:stripped_spruce_log[axis=x]", "minecraft:spruce_planks", "onepiece:anchor[facing=north]", "minecraft:chain[axis=y]" if False else "minecraft:iron_chain[axis=y]"), 4)
        r.lights(4)
    elif kind == "lab":
        for (x, z, f) in r.edge():
            if not r.wall_is_solid(x, z, f): continue
            k = (x + z) % 5
            r.put(x, r.y, z, ("onepiece:lab_panel", "minecraft:brewing_stand", "minecraft:water_cauldron[level=2]", "minecraft:crafter[crafting=false,orientation=north_up,triggered=false]", "minecraft:copper_bulb[lit=true,powered=false]")[k])
        for x in range(r.x0 + 2, r.x1 - 1, 4):
            r.put(x, r.y, r.cz, "minecraft:iron_block"); r.put(x, r.y + 1, r.cz, "minecraft:brewing_stand")
        top = r.y + r.h - 1
        for x in range(r.x0 + 1, r.x1, 3):
            for z in range(r.z0 + 1, r.z1, 3):
                if r.free(x, top, z): b.set(x, top, z, "onepiece:lab_light")
    elif kind == "shrine":
        for x in range(r.x0, r.x1 + 1):
            for z in range(r.z0, r.z1 + 1):
                if b.get(x, r.y - 1, z) not in (None, AIR): b.set(x, r.y - 1, z, "onepiece:tatami")
        r.put(r.cx, r.y, r.z1, "onepiece:sake_barrel[axis=y]"); r.put(r.cx - 1, r.y, r.z1, candle_str("red", 3)); r.put(r.cx + 1, r.y, r.z1, candle_str("red", 3))
        r.put(r.cx, r.y + 1, r.z1, "minecraft:bell[attachment=floor,facing=north,powered=false]")
        r.scatter(("minecraft:potted_bamboo", "minecraft:potted_cherry_sapling", "onepiece:paper_lantern[hanging=false]"), 4, wall=True)
        r.lights(4)
    elif kind == "cell":
        r.put(r.x0, r.y, r.z0, "minecraft:white_bed[facing=north,occupied=false,part=foot]")
        r.put(r.x1, r.y, r.z1, "minecraft:cauldron"); r.scatter(("minecraft:cobweb", "minecraft:skeleton_skull[rotation=3]", "minecraft:iron_chain[axis=y]"), 2)
    elif kind == "bath":
        # a pool sunk into the floor only where there is solid ground under it; on an upper floor (one block of floor
        # over the room below) the water would pour through, so build a raised tub with a stone rim instead
        cells = [(x, z) for x in range(r.cx - 2, r.cx + 3) for z in range(r.cz - 2, r.cz + 3)]
        solid = lambda x, y, z: b.get(x, y, z) not in (None, AIR) and "water" not in (b.get(x, y, z) or "")
        if all(solid(x, r.y - 1, z) and solid(x, r.y - 2, z) for (x, z) in cells):
            for (x, z) in cells: b.set(x, r.y - 1, z, WATER); r.keep.add((x, z))
        elif all(solid(x, r.y - 1, z) for (x, z) in cells):
            for (x, z) in cells:
                rim = abs(x - r.cx) == 2 or abs(z - r.cz) == 2
                b.set(x, r.y, z, "minecraft:smooth_quartz" if rim else WATER); r.keep.add((x, z))
        r.scatter(("minecraft:potted_fern", "minecraft:barrel[facing=up,open=false]", candle_str(r.t["candle"], 2)), 4, wall=True)
        r.lights(4)
    elif kind == "chapel":
        for z in range(r.z0 + 2, r.z1 - 2, 2):
            for x in list(range(r.x0 + 1, r.cx - 1)) + list(range(r.cx + 2, r.x1)): r.put(x, r.y, z, stairs(f"minecraft:{w}_stairs", "south"))
        r.put(r.cx, r.y, r.z1, "minecraft:lectern[facing=north,has_book=false,powered=false]")
        r.wall_banners(3); r.lights(4)
    else:  # hall
        for z in range(r.z0 + 2, r.z1 - 1, 5):
            for x in (r.x0 + 1, r.x1 - 1):
                if r.ok(x, r.y, z):
                    b.set(x, r.y, z, "minecraft:polished_andesite"); b.set(x, r.y + 1, z, rnd.choice(PLANTS)); r.keep.add((x, z))
        r.wall_banners(5); r.paintings(2 if big else 1); r.plants(4)
        if big: r.rug(2)
    if lit and kind not in ("lab",): r.lights(6)
    return r


def subdivide(b, x0, y, z0, x1, z1, h, wall_block, kinds, theme="pirate", cell=12, corridor=3, keepout=(), seed=0, door=None):
    """Split a big open floor into rooms on both sides of a corridor running along x through the middle.
    Each room gets a doorway onto the corridor and is furnished with the next kind from `kinds`.
    keepout: boxes (x0, z0, x1, z1) where no partition is built (stair wells etc.)."""
    rnd = random.Random(seed)
    cz = (z0 + z1) // 2
    c0, c1 = cz - corridor // 2, cz - corridor // 2 + corridor - 1
    def blocked(x, z):
        return any(a <= x <= c and bz <= z <= d for (a, bz, c, d) in keepout)
    def wset(x, z):
        if blocked(x, z): return
        for yy in range(y, y + h):
            if b.get(x, yy, z) in (None, AIR): b.set(x, yy, z, wall_block)
    # corridor walls
    for x in range(x0, x1 + 1):
        wset(x, c0 - 1); wset(x, c1 + 1)
    # room splits
    n = max(1, (x1 - x0 + 1) // cell)
    xs = [x0 + round(i * (x1 - x0 + 1) / n) for i in range(1, n)]
    for xw in xs:
        for z in list(range(z0, c0 - 1)) + list(range(c1 + 2, z1 + 1)): wset(xw, z)
    bounds = [x0] + [xw + 1 for xw in xs]
    ends = [xw - 1 for xw in xs] + [x1]
    k = 0
    rooms = []
    for (rx0, rx1) in zip(bounds, ends):
        for (rz0, rz1, dz) in ((z0, c0 - 2, c0 - 1), (c1 + 2, z1, c1 + 1)):
            if rx1 - rx0 < 2 or rz1 - rz0 < 2: continue
            mx = (rx0 + rx1) // 2
            for xx in (mx, mx + 1):
                for yy in (y, y + 1, y + 2):
                    if not blocked(xx, dz): b.set(xx, yy, dz, AIR)
            b.set(mx, y + 3, dz, lantern(False)) if h > 4 and not blocked(mx, dz) else None
            rooms.append((rx0, rz0, rx1, rz1))
    for (rx0, rz0, rx1, rz1) in rooms:
        furnish(b, rx0, y, rz0, rx1, rz1, h, kinds[k % len(kinds)], theme, seed=rnd.randint(0, 99999)); k += 1
    # corridor: runner carpet and lamps
    t = THEMES[theme] if isinstance(theme, str) else theme
    for x in range(x0, x1 + 1):
        for z in range(c0, c1 + 1):
            if b.get(x, y, z) in (None, AIR) and b.get(x, y - 1, z) not in (None, AIR): b.set(x, y, z, f"minecraft:{t['rug']}_carpet" if z == cz else f"minecraft:{t['rug2']}_carpet")
        if (x - x0) % 6 == 3 and b.get(x, y + h - 1, cz) in (None, AIR): b.set(x, y + h - 1, cz, lantern(True))
    return rooms
