"""Shared parts for the v2 (Minecraft Builder) landmark designs, so each landmark file only holds its own layout.

    from mcb.kit import *          # BigBuild, P (mcparts), seed_of, wing_floor, house_module, place_house, ...

Everything paints into a mcbig.BigBuild. Coordinates: x east+, y up+, z south+. Stair `facing` = the way it climbs."""
import math
import zlib

import numpy as np

from mcb.bridge import BigBuild, P

AIR = "minecraft:air"
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
DIRS = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}


def seed_of(*a):
    """Stable seed from any values (never hash(): it changes between Python runs)."""
    return zlib.crc32(repr(a).encode())


def is_air(bb, x, y, z):
    return bb.get_region(x, y, z, x, y, z)[0, 0, 0] in (0, 1)


def set_if_air(bb, x, y, z, s):
    if is_air(bb, x, y, z):
        bb.set(x, y, z, s)


def st(block, facing, half="bottom"):
    return f"{block}[facing={facing},half={half}]"


# ------------------------------------------------------------------ interiors
def furnish(bb, rooms, y, h, kinds, seed, tracker, doors=(), wood="spruce", audit=None, kit=False):
    """Furnish a list of rooms, cycling through `kinds`, and collect audit FAIL lines into `audit`. kit=True uses the
    shape-block room kit (kit_interiors: kinds mess, barracks, kitchen, office, armory, infirmary, ...)."""
    if kit:
        from mcb.kit_interiors import furnish_kit
        for i, r in enumerate(rooms):
            furnish_kit(bb, r, y, h, kinds[i % len(kinds)], wood=wood, seed=seed + i, doors=list(doors))
        return
    for i, r in enumerate(rooms):
        P.furnish_room(bb, r, y, kind=kinds[i % len(kinds)], height=h, seed=seed + i, wood=wood, tracker=tracker,
                       doors=list(doors))
        if audit is not None:
            txt, ok = P.audit_props(bb, [r], y, h)
            if not ok:
                audit.append(txt)


def wing_floor(bb, x1, z1, x2, z2, y, h, wall, seed, tracker, kinds, corridor="x", cw=3, carpet=None,
               keep=(), wood="spruce", audit=None, max_room=11, min_room=5, lamp="minecraft:lantern[hanging=true]", kit=False):
    """One office/barracks floor: a corridor `cw` wide down the middle (along x or z), rooms either side split with
    bsp_rooms, a door from every room that touches the corridor, everything furnished. (x1..x2, z1..z2) is the
    interior floor area, y the first air layer, h the clear height. keep = [(x1, z1, x2, z2)] areas left untouched
    (stair wells). Returns the rooms."""
    rooms, doors = [], []
    if corridor == "x":
        c1 = (z1 + z2) // 2 - cw // 2
        c2 = c1 + cw - 1
        halves = [(x1, z1, x2, c1 - 2, c1 - 1), (x1, c2 + 2, x2, z2, c2 + 1)]
        for (a1, b1, a2, b2, wz) in halves:
            if b2 - b1 < min_room - 1:
                continue
            bb.fill(a1, y, wz, a2, y + h - 1, wz, wall)
            rs, ds = P.bsp_rooms(bb, a1, b1, a2, b2, y, h, wall, min_room=min_room, seed=seed + wz, max_room=max_room)
            doors += ds
            for r in rs:
                if (wz == c1 - 1 and r[3] == b2) or (wz == c2 + 1 and r[1] == b1):
                    dx = (r[0] + r[2]) // 2
                    bb.fill(dx, y, wz, dx, y + 1, wz, AIR)
                    doors.append((dx, wz))
            rooms += rs
        if carpet and carpet[0]:
            bb.fill(x1, y - 1, c1, x2, y - 1, c2, carpet[0])
        if carpet:
            if carpet[1]:
                bb.fill(x1, y, c1 + cw // 2, x2, y, c1 + cw // 2, carpet[1])
        for x in range(x1 + 3, x2, 7):
            bb.set(x, y + h - 1, c1 + cw // 2, lamp)
    else:
        c1 = (x1 + x2) // 2 - cw // 2
        c2 = c1 + cw - 1
        halves = [(x1, z1, c1 - 2, z2, c1 - 1), (c2 + 2, z1, x2, z2, c2 + 1)]
        for (a1, b1, a2, b2, wx) in halves:
            if a2 - a1 < min_room - 1:
                continue
            bb.fill(wx, y, b1, wx, y + h - 1, b2, wall)
            rs, ds = P.bsp_rooms(bb, a1, b1, a2, b2, y, h, wall, min_room=min_room, seed=seed + wx, max_room=max_room)
            doors += ds
            for r in rs:
                if (wx == c1 - 1 and r[2] == a2) or (wx == c2 + 1 and r[0] == a1):
                    dz = (r[1] + r[3]) // 2
                    bb.fill(wx, y, dz, wx, y + 1, dz, AIR)
                    doors.append((wx, dz))
            rooms += rs
        if carpet and carpet[0]:
            bb.fill(c1, y - 1, z1, c2, y - 1, z2, carpet[0])
        if carpet:
            if carpet[1]:
                bb.fill(c1 + cw // 2, y, z1, c1 + cw // 2, y, z2, carpet[1])
        for z in range(z1 + 3, z2, 7):
            bb.set(c1 + cw // 2, y + h - 1, z, lamp)
    rooms = [r for r in rooms if not any(r[0] <= k[2] and k[0] <= r[2] and r[1] <= k[3] and k[1] <= r[3] for k in keep)]
    furnish(bb, rooms, y, h, kinds, seed, tracker, doors=doors, wood=wood, audit=audit, kit=kit)
    return rooms


# ------------------------------------------------------------------ houses (modules, stamped with rotation)
KIT_KIND = {"living": "dining", "storage": "storeroom", "kitchen": "kitchen", "bedroom": "bedroom", "workshop": "workshop"}
TOWN = dict(walls=["minecraft:calcite", "minecraft:white_concrete_powder", "minecraft:white_terracotta"],
            frame="minecraft:stripped_spruce_log", base=["minecraft:cobblestone", "minecraft:stone_bricks",
                                                         "minecraft:mossy_cobblestone"],
            floor="minecraft:spruce_planks", wood="spruce", chimney="minecraft:bricks")


def house_module(seed, w, d, floors, roof, tracker, kinds, pal=TOWN, fh=5, chimney=True, timber=True, jetty=True, kit=False):
    """A town house, door on the south (+z) face, footprint x 0..w-1, z 0..d-1, floor at y 0. Optional timber frame
    (posts every 3) with infill, a stone plinth 1 wider, framed windows with sills, flower boxes upstairs, a jettied
    upper floor, a gable roof with overhang, a chimney, a ladder up the west wall, every floor furnished (wider houses
    split into rooms). pal: walls (3 blocks), frame, base (3), floor, wood, chimney. Returns (module, top y, audit)."""
    rng = np.random.default_rng(seed)
    W3, FR0, ST3, wood = pal["walls"], pal["frame"], pal["base"], pal["wood"]
    axial = any(k in FR0 for k in ("log", "wood", "pillar", "stem", "hyphae", "basalt", "bamboo_block"))
    FR = FR0 if axial else None

    def fr(axis):
        return f"{FR0}[axis={axis}]" if axial else FR0
    m = BigBuild(seed=seed, y_min=-6, y_max=60)
    m.fill(0, -6, 0, w - 1, -1, d - 1, ST3[1])
    m.fill(-1, -6, -1, w, 0, d, ST3[0])
    m.mix(-1, -1, -1, w, 0, d, ST3, [0.6, 0.25, 0.15])
    m.fill(0, 0, 0, w - 1, 0, d - 1, pal["floor"])
    top = 0
    for f in range(floors):
        y0 = 1 + f * (fh + 1)
        jet = 1 if (f > 0 and jetty) else 0
        z1, z2 = -jet, d - 1 + jet
        for (x, y, z) in [(x, y, z) for x in range(w) for y in range(y0, y0 + fh) for z in (z1, z2)] + \
                         [(x, y, z) for x in (0, w - 1) for y in range(y0, y0 + fh) for z in range(z1, z2 + 1)]:
            v = rng.random()
            m.set(x, y, z, W3[0] if v < 0.6 else W3[1] if v < 0.9 else W3[2])
        m.fill(1, y0, z1 + 1, w - 2, y0 + fh - 1, z2 - 1, AIR)
        posts_x = sorted(set([0, w - 1] + list(range(3, w - 1, 3))))
        posts_z = sorted(set([z1, z2] + list(range(z1 + 3, z2, 3))))
        if timber:
            for x in posts_x:
                for z in (z1, z2):
                    m.fill(x, y0, z, x, y0 + fh - 1, z, fr("y"))
            for z in posts_z:
                for x in (0, w - 1):
                    m.fill(x, y0, z, x, y0 + fh - 1, z, fr("y"))
        else:
            for (x, z) in ((0, z1), (w - 1, z1), (0, z2), (w - 1, z2)):
                m.fill(x, y0, z, x, y0 + fh - 1, z, fr("y"))
        by = y0 + fh
        m.fill(0, by, z1, w - 1, by, z1, fr("x")); m.fill(0, by, z2, w - 1, by, z2, fr("x"))
        m.fill(0, by, z1, 0, by, z2, fr("z")); m.fill(w - 1, by, z1, w - 1, by, z2, fr("z"))
        m.fill(1, by, z1 + 1, w - 2, by, z2 - 1, pal["floor"])
        if jet:
            m.fill(0, y0 - 1, z1, w - 1, y0 - 1, z1, st(f"minecraft:{wood}_stairs", "south", "top"))
            m.fill(0, y0 - 1, z2, w - 1, y0 - 1, z2, st(f"minecraft:{wood}_stairs", "north", "top"))
        for z, out in ((z1, -1), (z2, 1)):
            face = "north" if out < 0 else "south"
            for i in range(len(posts_x) - 1):
                xc = (posts_x[i] + posts_x[i + 1]) // 2
                if f == 0 and z == z2 and abs(xc - w // 2) <= 1:
                    continue
                if rng.random() < 0.12:
                    continue
                m.fill(xc, y0 + 1, z, xc, y0 + 2, z, "minecraft:glass_pane")
                if rng.random() < 0.3:
                    m.set(xc, y0 + 3, z, f"minecraft:{wood}_trapdoor[facing={face},half=top,open=true]")
                m.set(xc, y0, z + out, st(f"minecraft:{wood}_stairs", "south" if out < 0 else "north", "top"))
                if f > 0:
                    m.set(xc, y0, z + out, f"onepiece:flower_box[facing={face}]")
        for x, out in ((0, -1), (w - 1, 1)):
            for zc in range(z1 + 2, z2 - 1, 4):
                m.fill(x, y0 + 1, zc, x, y0 + 2, zc, "minecraft:glass_pane")
                m.set(x + out, y0, zc, st(f"minecraft:{wood}_stairs", "east" if out < 0 else "west", "top"))
        top = by
    if floors > 1:
        m.fill(1, 1, 2, 1, top - fh, 2, "minecraft:ladder[facing=east]")
        for f in range(1, floors):
            m.set(1, f * (fh + 1), 2, "minecraft:ladder[facing=east]")
    dx = w // 2
    m.set(dx, 1, d - 1, f"minecraft:{wood}_door[facing=south,half=lower,hinge=left,open=false]")
    m.set(dx, 2, d - 1, f"minecraft:{wood}_door[facing=south,half=upper,hinge=left,open=false]")
    m.set(dx, 0, d, "minecraft:stone_brick_stairs[facing=north,half=bottom]")
    m.fill(dx - 1, 4, d, dx + 1, 4, d, f"minecraft:{wood}_slab[type=top]")
    m.set(dx + 1, 3, d, "onepiece:wall_lamp[facing=south]")
    audit = []
    for f in range(floors):
        fy = 1 + f * (fh + 1)
        jet = 1 if (f > 0 and jetty) else 0
        rm = (2, 1 - jet, w - 2, d - 2 + jet)
        doors = [(dx, d - 1)] if f == 0 else []
        doors += [(1, 2)]
        kind = kinds[min(f, len(kinds) - 1)]
        if w >= 11:
            rms, pdoors = P.bsp_rooms(m, *rm, fy, fh - 1, pal["floor"], min_room=4, seed=seed + f, max_room=8)
            doors += list(pdoors)
            alt = {"kitchen": "living", "bedroom": "bedroom", "living": "kitchen", "workshop": "storage"}
        else:
            rms, alt = [rm], {}
        for i, r in enumerate(rms):
            k = kind if i == 0 else alt.get(kind, kind)
            if kit:
                from mcb.kit_interiors import furnish_kit
                furnish_kit(m, r, fy, fh - 1, KIT_KIND.get(k, k), wood=wood, seed=seed + 10 * f + i, doors=doors)
                continue
            P.furnish_room(m, r, fy, kind=k, height=fh - 1, seed=seed + 10 * f + i, wood=wood, tracker=tracker,
                           doors=doors)
            txt, ok = P.audit_props(m, [r], fy, fh - 1)
            if not ok:
                audit.append(txt)
        if f == 0:
            m.fill(dx, 1, d - 2, dx, 2, d - 2, AIR)
    jet = 1 if (floors > 1 and jetty) else 0
    if roof is None or roof.startswith("flat:"):
        # flat roof terrace (desert towns): crenellated parapet, a hatch with a ladder, a striped awning at the door
        color = roof[5:] if roof else "white"
        par = pal.get("parapet", W3[0])
        for x in range(w):
            for z in (0, d - 1):
                m.set(x, top + 1, z, par)
                if (x + z) % 2 == 0:
                    m.set(x, top + 2, z, par)
        for z in range(d):
            for x in (0, w - 1):
                m.set(x, top + 1, z, par)
                if (x + z) % 2 == 0:
                    m.set(x, top + 2, z, par)
        m.set(w - 2, top, 1, f"minecraft:{wood}_trapdoor[facing=south,half=top,open=false]")
        m.fill(w - 2, top - fh, 1, w - 2, top - 1, 1, "minecraft:ladder[facing=south]")
        if rng.random() < 0.6:
            m.set(2, top + 1, d - 3, "minecraft:potted_dead_bush" if rng.random() < 0.5 else "minecraft:potted_cactus")
        if rng.random() < 0.5:
            m.fill(3, top + 1, 2, min(w - 4, 6), top + 1, 3, f"minecraft:{color}_carpet")
        for x in range(dx - 2, dx + 3):
            for z in (d, d + 1):
                m.set(x, 4, z, f"minecraft:{color if (x - dx) % 2 == 0 else 'white'}_wool")
        for x in (dx - 2, dx + 2):
            m.fill(x, 1, d + 1, x, 3, d + 1, f"minecraft:{wood}_fence")
        return m, top, audit
    P.gable_roof(m, -1, -1 - jet, w, d + jet, top + 1, roof, gable_fill=W3[0], overhang=1, ends_overhang=0)
    m.fill(-1, top, -1 - jet - 1, w, top, -1 - jet - 1, AIR)
    for x in (0, w - 1):
        m.set(x, top + 2, d // 2, "minecraft:glass_pane")
    if chimney:
        cx = w - 2 if rng.random() < 0.5 else 1
        h = top + (d + 2 * jet) // 2 + 3
        m.fill(cx, 1, -1 - jet, cx, h, -1 - jet, pal["chimney"])
        m.set(cx, h + 1, -1 - jet, "minecraft:campfire[lit=true,signal_fire=false,facing=north]")
    return m, top, audit


def place_house(bb, mod, w, d, x0, y, z0, rot):
    """Stamp a module so its footprint's minimum corner lands on (x0, z0) whatever the rotation
    (rot 0 = door south, 1 = door west, 2 = door north, 3 = door east)."""
    rc = []
    for (cx, cz) in [(0, 0), (w - 1, 0), (0, d - 1), (w - 1, d - 1)]:
        for _ in range(rot % 4):
            cx, cz = -cz, cx
        rc.append((cx, cz))
    mx, mz = min(c[0] for c in rc), min(c[1] for c in rc)
    bb.stamp(mod, x0 - mx, y, z0 - mz, rot=rot, include_air=True)
    return (w, d) if rot % 2 == 0 else (d, w)


# ------------------------------------------------------------------ small props
def lamp_post(bb, x, y, z, post="minecraft:dark_oak_fence", h=3, light="minecraft:lantern[hanging=false]"):
    bb.fill(x, y, z, x, y + h - 1, z, post)
    bb.set(x, y + h, z, light)


def table(bb, x, y, z, cloth="minecraft:white_carpet", wood="spruce", skip=None):
    """Round table: fence leg + cloth, a stair chair on each side (one left out now and then)."""
    bb.set(x, y, z, "minecraft:dark_oak_fence")
    bb.set(x, y + 1, z, cloth)
    for i, (dx, dz, f) in enumerate(((1, 0, "west"), (-1, 0, "east"), (0, 1, "north"), (0, -1, "south"))):
        if i != skip:
            set_if_air(bb, x + dx, y, z + dz, f"minecraft:{wood}_stairs[facing={f},half=bottom]")


def glyph(bb, rows, x, y, z, s, axis="x", step=1):
    """A pixel picture ('#' = block) on a wall plane. (x, y) = top-left; axis x draws along x on plane z."""
    for r, bits in enumerate(rows):
        for c, ch in enumerate(bits):
            if ch == "#":
                if axis == "x":
                    bb.set(x + c * step, y - r, z, s)
                else:
                    bb.set(x, y - r, z + c * step, s)


def castle_eave(bb, x1, z1, x2, z2, top, stairs, full, depth=3, bracket=None):
    """Japanese castle eave all round a tier whose wall top is y=top: a tiled lip over the wall top, `depth` rings
    of stairs stepping out and down, corners turned up at the tips, and brackets under the eave line."""
    for d in range(depth + 1):
        y = top + 1 - d
        a1, a2, c1, c2 = x1 - d, x2 + d, z1 - d, z2 + d
        if d == 0:
            bb.fill(a1, y, c1, a2, y, c1, full); bb.fill(a1, y, c2, a2, y, c2, full)
            bb.fill(a1, y, c1, a1, y, c2, full); bb.fill(a2, y, c1, a2, y, c2, full)
            continue
        bb.fill(a1 + 1, y, c1, a2 - 1, y, c1, st(stairs, "south")); bb.fill(a1 + 1, y, c2, a2 - 1, y, c2, st(stairs, "north"))
        bb.fill(a1, y, c1 + 1, a1, y, c2 - 1, st(stairs, "east")); bb.fill(a2, y, c1 + 1, a2, y, c2 - 1, st(stairs, "west"))
        for (cx, cz) in ((a1, c1), (a2, c1), (a1, c2), (a2, c2)):
            bb.set(cx, y, cz, full)
    y = top + 1 - depth
    slab = P.slab_of(stairs) + "[type=bottom]"
    for (cx, cz) in ((x1 - depth, z1 - depth), (x2 + depth, z1 - depth), (x1 - depth, z2 + depth), (x2 + depth, z2 + depth)):
        bb.set(cx, y + 1, cz, slab)
    if bracket:
        for x in range(x1, x2 + 1, 4):
            bb.set(x, top - 1, z1 - 1, st(bracket, "south", "top")); bb.set(x, top - 1, z2 + 1, st(bracket, "north", "top"))
        for z in range(z1, z2 + 1, 4):
            bb.set(x1 - 1, top - 1, z, st(bracket, "east", "top")); bb.set(x2 + 1, top - 1, z, st(bracket, "west", "top"))


def window_grid(bb, x1, x2, z, y0, top, fh, glass, every=3, h=2, sill=None, out=1, axis="x"):
    """Rows of windows (1 wide, h tall) on one face: along x on plane z (axis x) or along z on plane x (axis z), one
    row per storey starting y0, storeys fh apart, up to top. sill: stair block placed outside (out = +1/-1)."""
    for y in range(y0, top - h + 1, fh):
        for p in range(x1, x2 + 1, every):
            if axis == "x":
                bb.fill(p, y, z, p, y + h - 1, z, glass)
                if sill:
                    bb.set(p, y - 1, z + out, st(sill, "north" if out > 0 else "south", "top"))
            else:
                bb.fill(z, y, p, z, y + h - 1, p, glass)
                if sill:
                    bb.set(z + out, y - 1, p, st(sill, "west" if out > 0 else "east", "top"))


def marine_battleship(bb, x, y, z, L=46, beam=13, rot=0):
    """A Marine warship (white hull, blue stripe, two masts with white sails and the blue gull flag, cannon decks,
    a sterncastle and a gull figurehead), stamped with rot (0 = bow +x). (x, y, z) = stern keel centre; the water
    line sits about 5 above y."""
    m = BigBuild(seed=seed_of("mbs", L), y_min=-2, y_max=60)
    hw = beam // 2
    deck = 7
    for i in range(L):
        t = i / (L - 1)
        p = math.sqrt(max(0.0, 1 - abs(2 * t - 1) ** 3)) if t > 0.5 else 1.0
        for yy in range(0, deck + 1):
            frac = 0.5 + 0.5 * yy / deck
            h = max(1, int(round(hw * p * frac)))
            mat = "minecraft:blue_concrete" if yy == deck - 2 else ("minecraft:white_concrete" if yy > 2 else "minecraft:light_gray_concrete")
            m.fill(i, yy, -h, i, yy, h, mat)
            if yy >= 1:
                m.fill(i, yy, -h + 1, i, yy, h - 1, AIR)
        h = max(1, int(round(hw * p)))
        m.fill(i, deck, -h + 1, i, deck, h - 1, "minecraft:spruce_planks")
        if h > 2:
            m.fill(i, 1, -h + 2, i, 1, h - 2, "minecraft:spruce_planks")
        m.set(i, deck + 1, -h, "minecraft:white_concrete"); m.set(i, deck + 1, h, "minecraft:white_concrete")
        if i % 4 == 2 and 4 < i < L - 6:
            m.set(i, deck - 3, -h, "minecraft:black_concrete")       # gun ports
            m.set(i, deck - 3, h, "minecraft:black_concrete")
    # gun deck below the main deck
    m.fill(2, 4, -hw + 2, L - 6, 4, hw - 2, "minecraft:spruce_planks")
    for i in range(6, L - 8, 6):
        m.set(i, 5, -hw + 3, "onepiece:cannon[facing=north]"); m.set(i, 5, hw - 3, "onepiece:cannon[facing=south]")
    m.set(L // 2, 5, 0, "minecraft:lantern[hanging=false]")
    # sterncastle with the captain's cabin
    m.fill(0, deck + 1, -hw + 1, 9, deck + 6, hw - 1, "minecraft:white_concrete")
    m.fill(1, deck + 1, -hw + 2, 8, deck + 5, hw - 2, AIR)
    m.fill(0, deck + 6, -hw + 1, 9, deck + 6, hw - 1, "minecraft:spruce_planks")
    for k in range(-hw + 3, hw - 2, 2):
        m.set(0, deck + 3, k, "minecraft:light_blue_stained_glass_pane")
    m.fill(9, deck + 1, 0, 9, deck + 2, 0, AIR)
    m.set(5, deck + 1, 0, "onepiece:navigators_desk[facing=east]")
    m.fill(0, deck + 7, -hw + 1, 0, deck + 7, hw - 1, "minecraft:dark_oak_fence")
    m.set(5, deck + 7, 0, "minecraft:spruce_trapdoor[facing=south,half=bottom,open=false]")
    m.fill(5, deck + 1, 1, 5, deck + 6, 1, "minecraft:ladder[facing=north]")
    # masts, yards and sails
    for (mx, mh) in ((int(L * 0.4), 30), (int(L * 0.7), 27)):
        m.fill(mx, 1, 0, mx, deck + mh, 0, "minecraft:stripped_birch_log[axis=y]")
        for (sy, half) in ((deck + mh - 4, hw - 2), (deck + mh - 13, hw)):
            m.fill(mx, sy + 1, -half, mx, sy + 1, half, "minecraft:stripped_spruce_log[axis=z]")
            for dy in range(1, 8):
                bulge = 1 if 2 < dy < 6 else 0
                m.fill(mx + bulge, sy + 1 - dy, -half + 1, mx + bulge, sy + 1 - dy, half - 1, "minecraft:white_wool")
            m.fill(mx + 1, sy - 3, -1, mx + 1, sy - 3, 1, "minecraft:blue_wool")
        m.fill(mx, deck + mh - 9, -1, mx, deck + mh - 9, 1, "minecraft:spruce_slab[type=top]")
        top = deck + mh
        m.fill(mx, top + 1, 0, mx, top + 2, 0, "minecraft:dark_oak_fence")
        m.fill(mx - 4, top, 0, mx - 1, top + 2, 0, "minecraft:white_wool")
        m.fill(mx - 3, top + 1, 0, mx - 2, top + 1, 0, "minecraft:blue_wool")
    # bowsprit and the gull figurehead
    m.fill(L, deck, 0, L + 6, deck + 3, 0, AIR)
    for k in range(7):
        m.set(L - 1 + k, deck + k // 2, 0, "minecraft:stripped_birch_log[axis=x]")
    m.fill(L - 1, deck - 2, -1, L, deck, 1, "minecraft:white_concrete")
    m.set(L + 1, deck - 1, 0, "minecraft:white_concrete"); m.set(L, deck - 1, -2, "minecraft:white_concrete")
    m.set(L, deck - 1, 2, "minecraft:white_concrete"); m.set(L + 1, deck - 2, 0, "minecraft:blue_concrete")
    # deck clutter
    for (dx, dz) in ((14, -3), (15, -3), (14, 3), (L - 10, 2)):
        m.set(dx, deck + 1, dz, "minecraft:barrel[facing=up]")
    m.set(L // 2 + 2, deck + 1, 0, "minecraft:spruce_trapdoor[facing=south,half=bottom,open=false]")
    for yy in range(5, deck + 1):
        m.set(L // 2 + 2, yy, 1, "minecraft:ladder[facing=north]")
    bb.stamp(m, x, y, z, rot=rot, include_air=True)
    return m


# ------------------------------------------------------------------ towers: stair cores and ring floors
def stair_core(bb, x, z, size, y1, y2, floors, wall, stairs, newel=None, slit="minecraft:glass"):
    """A walled stair well: a size x size square spiral from y1 to y2 (its last step sits in the y2 floor plate, so
    you walk straight out on top), a 1-thick wall ring round it, opened beside the step that arrives at each floor in
    `floors` (first air layers)."""
    bb.fill(x - 1, y1, z - 1, x + size, y2 + 3, z + size, wall)
    bb.fill(x, y1, z, x + size - 1, y2 + 3, z + size - 1, AIR)
    P.square_spiral_stair(bb, x, y1, z, size, y2, stairs, core=newel or wall, headroom=3)
    x2, z2 = x + size - 1, z + size - 1
    cells = [(xx, z) for xx in range(x, x2)] + [(x2, zz) for zz in range(z, z2)] \
        + [(xx, z2) for xx in range(x2, x, -1)] + [(x, zz) for zz in range(z2, z, -1)]
    for fy in floors:
        n = fy - 1 - y1
        if n < 0 or fy - 1 > y2:
            continue
        cx, cz = cells[n % len(cells)]
        for (ox, oz) in ((cx - 1, cz), (cx + 1, cz), (cx, cz - 1), (cx, cz + 1)):
            if ox in (x - 1, x + size) or oz in (z - 1, z + size):
                bb.fill(ox, fy, oz, ox, fy + 2, oz, AIR)
                bb.set(ox, fy - 1, oz, wall)
    if slit:
        for y in range(y1 + 3, y2, 5):
            bb.set(x + size // 2, y, z - 1, slit)
    return cells


def ring_floor(bb, x1, z1, x2, z2, y, h, core, wall, seed, tracker, kinds, cw=2, audit=None, wood="spruce",
               min_room=4, max_room=9, floor=None, kit=False):
    """A floor round a central core box (cx1, cz1, cx2, cz2 incl. its wall): a corridor ring cw wide round the core,
    then rooms in four bands (north, south, west, east) split with bsp_rooms, every room on the ring gets a door,
    all furnished. Returns the rooms."""
    cx1, cz1, cx2, cz2 = core
    r1, s1, r2, s2 = cx1 - cw, cz1 - cw, cx2 + cw, cz2 + cw          # ring outer edge (inclusive)
    bands = [  # (a1, b1, a2, b2, wall line, side) side = where the ring is
        (x1, z1, x2, s1 - 2, ("z", s1 - 1)),
        (x1, s2 + 2, x2, z2, ("z", s2 + 1)),
        (x1, s1, r1 - 2, s2, ("x", r1 - 1)),
        (r2 + 2, s1, x2, s2, ("x", r2 + 1)),
    ]
    rooms, doors = [], []
    if floor:
        bb.fill(r1, y - 1, s1, r2, y - 1, s2, floor)
    for (a1, b1, a2, b2, (ax, line)) in bands:
        if a2 - a1 < min_room - 1 or b2 - b1 < min_room - 1:
            continue
        if ax == "z":
            bb.fill(a1, y, line, a2, y + h - 1, line, wall)
        else:
            bb.fill(line, y, b1, line, y + h - 1, b2, wall)
        rs, ds = P.bsp_rooms(bb, a1, b1, a2, b2, y, h, wall, min_room=min_room, seed=seed + line, max_room=max_room)
        doors += ds
        for r in rs:
            if ax == "z" and (r[1] == line + 1 or r[3] == line - 1):
                lo, hi = max(r[0], r1), min(r[2], r2)
                if lo <= hi:
                    d = (lo + hi) // 2
                    bb.fill(d, y, line, d, y + 1, line, AIR); doors.append((d, line))
            if ax == "x" and (r[0] == line + 1 or r[2] == line - 1):
                lo, hi = max(r[1], s1), min(r[3], s2)
                if lo <= hi:
                    d = (lo + hi) // 2
                    bb.fill(line, y, d, line, y + 1, d, AIR); doors.append((line, d))
        rooms += rs
    # the band corners outside the ring (where north/south bands overhang west/east bands) are fine: bsp covered them
    furnish(bb, rooms, y, h, kinds, seed, tracker, doors=doors, wood=wood, audit=audit, kit=kit)
    for (lx, lz) in ((r1, s1), (r2, s1), (r1, s2), (r2, s2)):
        bb.set(lx, y + h - 1, lz, "minecraft:lantern[hanging=true]")
    return rooms


def tier(bb, x1, z1, x2, z2, y0, n, fh, wall, glass, sill, pilaster=None, band=None, plate="minecraft:smooth_stone",
         top_plate=None, weights=None, every=3, pil_every=8, win_h=2):
    """A storeyed block: solid walls (wall = block or list mixed by weights), windows on every storey, floor plates
    every fh, coloured bands at the plates, pilasters standing proud every pil_every. Returns the top plate y."""
    top = y0 + fh * n
    bb.fill(x1, y0, z1, x2, y0, z2, top_plate or plate)
    if isinstance(wall, (list, tuple)):
        bb.mix(x1, y0 + 1, z1, x2, top - 1, z2, list(wall), weights)
    else:
        bb.fill(x1, y0 + 1, z1, x2, top - 1, z2, wall)
    bb.fill(x1 + 1, y0 + 1, z1 + 1, x2 - 1, top - 1, z2 - 1, AIR)
    for k in range(1, n + 1):
        bb.fill(x1 + 1, y0 + fh * k, z1 + 1, x2 - 1, y0 + fh * k, z2 - 1, plate if k < n else (top_plate or plate))
        if band and k < n:
            yb = y0 + fh * k
            bb.fill(x1, yb, z1, x2, yb, z1, band); bb.fill(x1, yb, z2, x2, yb, z2, band)
            bb.fill(x1, yb, z1, x1, yb, z2, band); bb.fill(x2, yb, z1, x2, yb, z2, band)
    if top_plate:
        bb.fill(x1, top, z1, x2, top, z2, top_plate)
    for k in range(n):
        wy = y0 + fh * k + 2
        for x in range(x1 + 2, x2 - 1, every):
            if pilaster and (x - x1) % pil_every == 0:
                continue
            for z, out in ((z1, -1), (z2, 1)):
                bb.fill(x, wy, z, x, wy + win_h - 1, z, glass)
                if sill:
                    bb.set(x, wy - 1, z + out, st(sill, "south" if out < 0 else "north", "top"))
        for z in range(z1 + 2, z2 - 1, every):
            if pilaster and (z - z1) % pil_every == 0:
                continue
            for x, out in ((x1, -1), (x2, 1)):
                bb.fill(x, wy, z, x, wy + win_h - 1, z, glass)
                if sill:
                    bb.set(x + out, wy - 1, z, st(sill, "east" if out < 0 else "west", "top"))
    if pilaster:
        for x in range(x1, x2 + 1, pil_every):
            bb.fill(x, y0 + 1, z1 - 1, x, top - 1, z1 - 1, pilaster); bb.fill(x, y0 + 1, z2 + 1, x, top - 1, z2 + 1, pilaster)
        for z in range(z1, z2 + 1, pil_every):
            bb.fill(x1 - 1, y0 + 1, z, x1 - 1, top - 1, z, pilaster); bb.fill(x2 + 1, y0 + 1, z, x2 + 1, top - 1, z, pilaster)
    return top


def cornice(bb, x1, z1, x2, z2, y, stairs, parapet=None, merlons=None):
    """Upside-down stair cornice round a block at height y, with an optional parapet wall (or merlons every 2)."""
    bb.fill(x1 - 1, y, z1 - 1, x2 + 1, y, z1 - 1, st(stairs, "south", "top"))
    bb.fill(x1 - 1, y, z2 + 1, x2 + 1, y, z2 + 1, st(stairs, "north", "top"))
    bb.fill(x1 - 1, y, z1, x1 - 1, y, z2, st(stairs, "east", "top"))
    bb.fill(x2 + 1, y, z1, x2 + 1, y, z2, st(stairs, "west", "top"))
    if parapet:
        for (a, b, c, d) in ((x1 - 1, z1 - 1, x2 + 1, z1 - 1), (x1 - 1, z2 + 1, x2 + 1, z2 + 1),
                             (x1 - 1, z1 - 1, x1 - 1, z2 + 1), (x2 + 1, z1 - 1, x2 + 1, z2 + 1)):
            bb.fill(a, y + 1, b, c, y + 1, d, parapet)
            if merlons:
                for p in range((a if a != c else b), (c if a != c else d) + 1, 2):
                    if a != c:
                        bb.set(p, y + 2, b, merlons)
                    else:
                        bb.set(a, y + 2, p, merlons)


def wg_emblem(bb, cu, cy, plane, s, k=1.0, axis="x"):
    """The World Government emblem: five linked rings, one in the middle and four round it in a cross.
    axis x: drawn on the plane z=plane centred on x=cu; axis z: on the plane x=plane centred on z=cu."""
    rc, rs, d = 2.4 * k, 1.7 * k, 3.6 * k
    R = int(d + rs + 2)
    for u in range(-R, R + 1):
        for v in range(-R, R + 1):
            on = abs(math.hypot(u, v) - rc) <= 0.55
            for (a, c) in ((d, 0), (-d, 0), (0, d), (0, -d)):
                if abs(math.hypot(u - a, v - c) - rs) <= 0.55:
                    on = True
            if on:
                if axis == "x":
                    bb.set(cu + u, cy + v, plane, s)
                else:
                    bb.set(plane, cy + v, cu + u, s)


def wg_flag(bb, x, y, z, w=13, h=9, axis="x"):
    """World Government flag: blue cloth with the white emblem. (x, y, z) = top corner next to the pole; the cloth
    runs +x (axis x, plane z) or +z (axis z, plane x)."""
    for i in range(w):
        for j in range(h):
            if axis == "x":
                bb.set(x + i, y - j, z, "minecraft:blue_wool")
            else:
                bb.set(x, y - j, z + i, "minecraft:blue_wool")
    k = min(w, h) / 12.0
    if axis == "x":
        wg_emblem(bb, x + w // 2, y - h // 2, z, "minecraft:white_wool", k=k, axis="x")
    else:
        wg_emblem(bb, z + w // 2, y - h // 2, x, "minecraft:white_wool", k=k, axis="z")


def palm(bb, x, y, z, h, lean=(1, 0)):
    """Curving palm: palm log trunk leaning one way, a crown of drooping fronds. y = first trunk block."""
    px, pz = x, z
    for k in range(h):
        if k > h // 3 and k % 3 == 0:
            px += lean[0]; pz += lean[1]
        bb.set(px, y + k, pz, "onepiece:palm_log[axis=y]")
    top = y + h
    leaf = "onepiece:palm_leaves[distance=1,persistent=true,waterlogged=false]"
    bb.set(px, top, pz, leaf)
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        for k in range(1, 6 if dx * dz == 0 else 4):
            yy = top - (1 if k >= 3 else 0) - (1 if k >= 5 else 0)
            bb.set(px + dx * k, yy, pz + dz * k, leaf)


def onion_dome(bb, cx, y, cz, r, block, tip="minecraft:gold_block"):
    """Onion dome sitting on y: bulges out to r a little above its base, then tapers to a point with a gold finial."""
    h = int(r * 2.2)
    for k in range(h):
        t = k / h
        rr = r * (1.0 + 0.25 * math.sin(math.pi * min(1, t / 0.45))) * (1 - t) ** 0.8 if t > 0.0 else r
        if rr < 0.6:
            bb.set(cx, y + k, cz, block)
            continue
        bb.fill_where(int(cx - rr - 1), y + k, int(cz - rr - 1), int(cx + rr + 1), y + k, int(cz + rr + 1),
                      lambda X, yy, Z, rr=rr: np.hypot(X - cx, Z - cz) <= rr, block)
    bb.fill(cx, y + h, cz, cx, y + h + 2, cz, tip)
    return y + h + 2


def steady(b):
    """Sand, gravel and concrete powder with nothing solid under it would fall (and break into items) when the build
    generates: swap them for a solid look-alike. Call on the canvas after to_canvas()."""
    import render
    for (x, y, z), s in list(b.blocks.items()):
        n = s.split("[")[0]
        if n.endswith(("gravel", "sand", "concrete_powder")) and "sandstone" not in n:
            below = b.blocks.get((x, y - 1, z))
            if below is None or render.shape_of(below) != "full":
                b.blocks[(x, y, z)] = "minecraft:coarse_dirt" if "gravel" in n else "minecraft:smooth_sandstone" if "sand" in n else \
                    n.replace("concrete_powder", "concrete")
