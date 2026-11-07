"""Building kit: a block canvas plus helpers (houses, towers, ships, flags...) that saves Minecraft structure .nbt files."""
import math, os
import nbt
from nbt import Byte, Int, IntList, DoubleList

DATA_VERSION = 5023  # Minecraft 26.3 (palette entries use "id" and "properties")
NEW_CHAR_TAG = "onepiece_new_character"  # WorldFeature.NEW_CHARACTER_TAG
GUARD_TAG = "onepiece_guard"             # GuardKit.GUARD_TAG
AIR = "minecraft:air"

def leaves(kind="oak"):
    return f"minecraft:{kind}_leaves[distance=7,persistent=true,waterlogged=false]"
def log(kind="oak", axis="y"):
    return f"minecraft:{kind}_log[axis={axis}]"
FENCE = "minecraft:{}_fence[east=false,north=false,south=false,west=false,waterlogged=false]"
LANTERN = "minecraft:lantern[hanging=false,waterlogged=false]"
HANG = "minecraft:lantern[hanging=true,waterlogged=false]"
SOUL_LANTERN = "minecraft:soul_lantern[hanging=false,waterlogged=false]"
BARREL = "minecraft:barrel[facing=up,open=false]"
CAMPFIRE = "minecraft:campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
SOUL_FIRE = "minecraft:soul_campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]"
CHAIN = "minecraft:iron_chain[axis=y,waterlogged=false]"
BARS = "minecraft:iron_bars[east=false,north=false,south=false,west=false,waterlogged=false]"
PANE = "minecraft:glass_pane[east=false,north=false,south=false,west=false,waterlogged=false]"
def pane(color=None):
    return PANE if not color else f"minecraft:{color}_stained_glass_pane[east=false,north=false,south=false,west=false,waterlogged=false]"
def ladder(facing="south"):
    return f"minecraft:ladder[facing={facing},waterlogged=false]"
def bed(color, x, y, z, b, facing="south"):
    dz = {"south": 1, "north": -1}.get(facing, 0); dx = {"east": 1, "west": -1}.get(facing, 0)
    b.set(x, y, z, f"minecraft:{color}_bed[facing={facing},occupied=false,part=foot]")
    b.set(x + dx, y, z + dz, f"minecraft:{color}_bed[facing={facing},occupied=false,part=head]")

class B:
    def __init__(self):
        self.blocks = {}; self.nbt = {}; self.entities = []; self.waterline = 0
    # ---- basics
    def set(self, x, y, z, s, data=None):
        x, y, z = int(x), int(y), int(z)
        self.blocks[(x, y, z)] = s
        if data: self.nbt[(x, y, z)] = data
        else: self.nbt.pop((x, y, z), None)
    def get(self, x, y, z):
        return self.blocks.get((x, y, z))
    def box(self, x0, y0, z0, x1, y1, z1, s):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, s)
    def walls(self, x0, y0, z0, x1, y1, z1, s):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, z0, s); self.set(x, y, z1, s)
            for z in range(z0, z1 + 1):
                self.set(x0, y, z, s); self.set(x1, y, z, s)
    def room(self, x0, y0, z0, x1, y1, z1, wall, floor=None, ceiling=None):
        """Hollow box: walls, floor, ceiling and air inside."""
        self.box(x0, y0, z0, x1, y1, z1, wall)
        self.box(x0 + 1, y0 + 1, z0 + 1, x1 - 1, y1 - 1, z1 - 1, AIR)
        if floor: self.box(x0 + 1, y0, z0 + 1, x1 - 1, y0, z1 - 1, floor)
        if ceiling: self.box(x0 + 1, y1, z0 + 1, x1 - 1, y1, z1 - 1, ceiling)
    def cyl(self, cx, cz, r, y0, y1, s, hollow=False):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for z in range(int(cz - r) - 1, int(cz + r) + 2):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.35 and (not hollow or d > r - 0.85):
                    for y in range(y0, y1 + 1): self.set(x, y, z, s)
                elif hollow and d <= r - 0.85:
                    for y in range(y0, y1 + 1): self.set(x, y, z, AIR)
    def disk(self, cx, y, cz, r, s):
        self.cyl(cx, cz, r, y, y, s)
    def sphere(self, cx, cy, cz, r, s, hollow=False, upper=False, ry=None):
        ry = ry or r
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                if upper and y < cy: continue
                for z in range(int(cz - r) - 1, int(cz + r) + 2):
                    d = math.sqrt(((x - cx) / r) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / r) ** 2)
                    if d <= 1.0 and (not hollow or d > 1.0 - 1.2 / max(r, ry)):
                        self.set(x, y, z, s)
                    elif hollow and d <= 1.0:
                        self.set(x, y, z, AIR)
    def roof(self, x0, z0, x1, z1, y, s, top=None):
        """Stepped pyramid roof that shrinks by one each level."""
        i = 0
        while x0 + i <= x1 - i and z0 + i <= z1 - i:
            self.walls(x0 + i, y + i, z0 + i, x1 - i, y + i, z1 - i, s)
            i += 1
        if top: self.box(x0 + i - 1, y + i - 1, z0 + i - 1, x1 - i + 1, y + i - 1, z1 - i + 1, top)
    def gable(self, x0, z0, x1, z1, y, s):
        """Roof that slopes along z (ridge runs along x)."""
        i = 0
        while z0 + i <= z1 - i:
            self.box(x0, y + i, z0 + i, x1, y + i, z0 + i, s); self.box(x0, y + i, z1 - i, x1, y + i, z1 - i, s)
            if z0 + i < z1 - i:
                for z in range(z0 + i + 1, z1 - i):
                    self.set(x0, y + i, z, s); self.set(x1, y + i, z, s)
            i += 1
    # ---- buildings
    def house(self, x0, z0, w, d, h, wall, roof, floor="minecraft:oak_planks", y=0, door="south", windows=True, corner=None, gable=False):
        x1, z1 = x0 + w - 1, z0 + d - 1
        self.room(x0, y, z0, x1, y + h + 1, z1, wall, floor=floor)
        self.box(x0 + 1, y + h + 1, z0 + 1, x1 - 1, y + h + 1, z1 - 1, AIR)
        if corner:
            for cx, cz in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
                self.box(cx, y + 1, cz, cx, y + h, cz, corner)
        mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
        doors = {"south": (mx, z1), "north": (mx, z0), "east": (x1, mz), "west": (x0, mz)}
        dx, dz = doors[door]
        self.box(dx, y + 1, dz, dx, y + 2, dz, AIR)
        if windows:
            for x in range(x0 + 2, x1 - 1, 3):
                for zz in (z0, z1):
                    if (x, zz) != (dx, dz) and self.get(x, y + 2, zz) == wall: self.set(x, y + 2, zz, PANE)
            for z in range(z0 + 2, z1 - 1, 3):
                for xx in (x0, x1):
                    if (xx, z) != (dx, dz) and self.get(xx, y + 2, z) == wall: self.set(xx, y + 2, z, PANE)
        if gable: self.gable(x0 - 1, z0 - 1, x1 + 1, z1 + 1, y + h + 1, roof)
        else: self.roof(x0 - 1, z0 - 1, x1 + 1, z1 + 1, y + h + 1, roof, top=roof)
        self.set(mx, y + h, mz, HANG)
        return (x0 + 1, y + 1, z0 + 1, x1 - 1, z1 - 1)
    def tower(self, cx, cz, r, h, wall, roof=None, y=0, windows=True, ladder_side=True, floors=None):
        self.cyl(cx, cz, r, y, y + h, wall, hollow=True)
        self.disk(cx, y, cz, r - 1, wall)
        if windows:
            for yy in range(y + 3, y + h - 1, 4):
                for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
                    self.set(cx + dx, yy, cz + dz, PANE)
        for f in (floors or []):
            self.disk(cx, y + f, cz, r - 1, wall)
        if ladder_side:
            for yy in range(y + 1, y + h + 1): self.set(cx, yy, cz - r + 1, ladder("south"))
        self.disk(cx, y + h, cz, r, wall)
        self.set(cx, y + h, cz - r + 1, ladder("south"))
        for i in range(0, 360, 30):  # battlement
            a = math.radians(i); self.set(round(cx + r * math.cos(a)), y + h + 1, round(cz + r * math.sin(a)), wall)
        if roof:
            for i in range(r + 1):
                self.cyl(cx, cz, r - i, y + h + 1 + i, y + h + 1 + i, roof, hollow=True)
    def door(self, x, y, z, h=2, w=1, axis="x"):
        for i in range(w):
            for yy in range(y, y + h):
                if axis == "x": self.set(x + i, yy, z, AIR)
                else: self.set(x, yy, z + i, AIR)
    # ---- nature
    def tree(self, x, y, z, h=6, kind="oak", r=2.5):
        for yy in range(y, y + h): self.set(x, yy, z, log(kind))
        self.sphere(x, y + h, z, r, leaves(kind), ry=r * 0.8)
        for yy in range(y, y + h): self.set(x, yy, z, log(kind))
    def palm(self, x, y, z, h=6):
        for yy in range(y, y + h): self.set(x + (1 if yy > y + h // 2 else 0), yy, z, log("jungle"))
        tx = x + 1; ty = y + h
        self.set(tx, ty, z, leaves("jungle"))
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for i in range(1, 4):
                self.set(tx + dx * i, ty - (1 if i == 3 else 0), z + dz * i, leaves("jungle"))
    def fruit_tree(self, x, y, z, fruit="minecraft:orange_wool"):
        self.tree(x, y, z, 4, "oak", 2)
        for dx, dz in ((2, 0), (-2, 1), (0, -2), (1, 2)):
            self.set(x + dx, y + 3, z + dz, fruit)
    def bones(self, x, y, z, length, axis="x", height=6):
        """Giant skeleton: a spine with ribs (bone blocks)."""
        for i in range(length):
            px, pz = (x + i, z) if axis == "x" else (x, z + i)
            self.set(px, y + 2, pz, f"minecraft:bone_block[axis={axis}]")
            if i % 3 == 0 and 2 < i < length - 3:
                for s in (-1, 1):
                    for k in range(1, height):
                        rx, rz = (px, pz + s * min(k, 3)) if axis == "x" else (px + s * min(k, 3), pz)
                        self.set(rx, y + 2 + (k if k < 3 else 2) - (k - 3 if k > 3 else 0), rz, "minecraft:bone_block[axis=y]")
        hx, hz = (x + length, z) if axis == "x" else (x, z + length)
        self.sphere(hx, y + 3, hz, 2.5, "minecraft:bone_block[axis=y]", hollow=True)
    # ---- props
    def chest(self, x, y, z, loot, facing="south"):
        self.set(x, y, z, f"minecraft:chest[facing={facing},type=single,waterlogged=false]", {"id": "minecraft:chest", "LootTable": f"onepiece:chests/{loot}"})
    def flag(self, x, y, z, h=8, colors=("minecraft:black_wool", "minecraft:white_wool"), skull=True, length=5):
        for yy in range(y, y + h): self.set(x, yy, z, FENCE.format("dark_oak"))
        top = y + h - 1
        self.box(x, top - 3, z + 1, x, top, z + length, colors[0])
        if skull:
            mz = z + 1 + length // 2
            for yy, zz in ((top - 1, mz - 1), (top - 1, mz + 1), (top - 2, mz), (top, mz), (top, mz - 1), (top, mz + 1)):
                self.set(x, yy, zz, colors[1])
        else:
            self.box(x, top - 2, z + 1, x, top - 1, z + length, colors[1])
    def stall(self, x, y, z, color):
        for dx, dz in ((0, 0), (2, 0), (0, 2), (2, 2)):
            self.box(x + dx, y + 1, z + dz, x + dx, y + 2, z + dz, FENCE.format("spruce"))
        self.box(x, y + 3, z, x + 2, y + 3, z + 2, f"minecraft:{color}_wool")
        self.set(x + 1, y + 1, z + 1, BARREL)
    def ship(self, x0, y0, z0, L, W, hull="minecraft:dark_oak_planks", deck="minecraft:spruce_planks", masts=(), sail="minecraft:white_wool",
             flag=("minecraft:black_wool", "minecraft:white_wool"), cabin=None, depth=4):
        """A ship pointing to +x. y0 = keel. Deck at y0+depth. Returns deck y."""
        cz = z0 + W // 2
        for y in range(y0, y0 + depth + 1):
            t = (y - y0) / depth
            for x in range(x0, x0 + L):
                f = (x - x0) / (L - 1)
                taper = 1.0 - max(0.0, (f - 0.7) / 0.3) ** 1.5 * 0.9 - max(0.0, (0.12 - f) / 0.12) * 0.4
                half = max(0, round((W / 2 - 0.5) * (0.45 + 0.55 * t) * taper))
                for z in range(cz - half, cz + half + 1):
                    edge = abs(z - cz) == half or y == y0
                    self.set(x, y, z, hull if (edge or y < y0 + depth) else deck)
                    if y == y0 + depth: self.set(x, y, z, deck if abs(z - cz) < half else hull)
                if y == y0 + depth:
                    for z in (cz - half, cz + half):
                        self.set(x, y + 1, z, FENCE.format("dark_oak"))
        dy = y0 + depth
        self.waterline = dy - 2  # for ships at sea: this level sits at the water's surface
        for (mx, mh) in masts:
            for y in range(dy + 1, dy + mh): self.set(x0 + mx, y, cz, log("spruce"))
            for y in range(dy + 4, dy + mh - 2):
                for z in range(cz - W // 2 + 1, cz + W // 2):
                    if z != cz: self.set(x0 + mx + 1, y, z, sail)
            if flag:
                self.box(x0 + mx, dy + mh, cz, x0 + mx, dy + mh, cz, log("spruce"))
                self.box(x0 + mx, dy + mh - 1, cz + 1, x0 + mx, dy + mh, cz + 3, flag[0])
                self.set(x0 + mx, dy + mh, cz + 2, flag[1])
        if cabin:
            cl, ch, mat = cabin
            self.room(x0 + 1, dy, cz - W // 2 + 2, x0 + cl, dy + ch, cz + W // 2 - 2, mat, floor=deck)
            self.door(x0 + cl, dy + 1, cz, axis="z")
        return dy
    # ---- people
    def npc(self, x, y, z, cid, boss=False):
        self.entities.append(("onepiece:character", x, y, z,
                              {"Character": cid, "Boss": Byte(1 if boss else 0), "PersistenceRequired": Byte(1), "Tags": [NEW_CHAR_TAG]}))
    def guard(self, x, y, z, kit):
        from kits import KITS
        k = KITS[kit]
        self.entities.append((k["entity"], x, y, z, {"PersistenceRequired": Byte(1), "Tags": [GUARD_TAG, "onepiece_kit_" + kit]}))
    def guards(self, kit, spots, y=1):
        for (x, z) in spots: self.guard(x, y, z, kit)
    # ---- save
    def save(self, path):
        xs = [p[0] for p in self.blocks]; ys = [p[1] for p in self.blocks]; zs = [p[2] for p in self.blocks]
        mx, my, mz = min(xs), min(ys), min(zs)
        palette, index, blocks = [], {}, []
        for (x, y, z), s in sorted(self.blocks.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0])):
            if s not in index:
                index[s] = len(palette)
                name, props = (s.split('[', 1) + [''])[:2]
                entry = {"id": name}
                if props: entry["properties"] = dict(p.split('=') for p in props.rstrip(']').split(','))
                palette.append(entry)
            b = {"state": Int(index[s]), "pos": IntList([x - mx, y - my, z - mz])}
            if (x, y, z) in self.nbt: b["nbt"] = self.nbt[(x, y, z)]
            blocks.append(b)
        ents = []
        for (eid, x, y, z, data) in self.entities:
            d = {"id": eid}; d.update(data)
            ents.append({"pos": DoubleList([x - mx + 0.5, float(y - my), z - mz + 0.5]),
                         "blockPos": IntList([x - mx, y - my, z - mz]), "nbt": d})
        size = [max(xs) - mx + 1, max(ys) - my + 1, max(zs) - mz + 1]
        root = {"DataVersion": Int(DATA_VERSION), "size": IntList(size), "palette": palette, "blocks": blocks, "entities": ents}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        nbt.write(path, root)
        return size, my
