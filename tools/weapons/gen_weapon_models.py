"""
Writes life-size 3D in-hand models for the melee weapons, named swords and slingshots
(the guns have their own script, tools/guns/gen_gun_models.py).

Every weapon is a list of boxes in model pixels. 1 pixel = 1/16 block = about 6 cm, and the player is about
29 pixels tall, so a katana (about 1 m) is 16 pixels long and Whitebeard's bisento about 40.
Blades and poles point up (+Y) in the model, with the cutting edge toward -Z; the hand holds the `grip` point.
The inventory keeps the old flat icon; hands, the ground and item frames use the 3D model.

Run from anywhere:  python3 -I gen_weapon_models.py <path to source/src/main/resources/assets/onepiece>
"""
import json, math, os, random, sys, zlib
from PIL import Image

ASSETS = sys.argv[1]
TILE = 32           # texels per material tile
ATLAS = 256         # atlas size in texels -> 8x8 tiles; 1 texel per model pixel
UV = ATLAS / 16     # texels per UV unit

# ---------- materials: (base colour, kind) ----------
MATERIALS = {
    "steel":       ((206, 210, 218), "metal"),
    "hamon":       ((236, 238, 242), "metal"),
    "black_steel": ((40, 40, 48), "metal"),
    "black_edge":  ((88, 88, 104), "metal"),
    "iron":        ((120, 122, 130), "metal"),
    "dark_iron":   ((66, 66, 74), "metal"),
    "gold":        ((226, 182, 56), "metal"),
    "brass":       ((186, 146, 58), "metal"),
    "silver":      ((176, 180, 190), "metal"),
    "wrap_white":  ((226, 222, 210), "wrap"),
    "wrap_black":  ((36, 34, 40), "wrap"),
    "wrap_red":    ((150, 28, 34), "wrap"),
    "wrap_purple": ((96, 46, 138), "wrap"),
    "wrap_blue":   ((44, 70, 140), "wrap"),
    "wrap_brown":  ((112, 72, 40), "wrap"),
    "lacquer_black": ((24, 22, 26), "lacquer"),
    "lacquer_red": ((150, 22, 26), "lacquer"),
    "wood":        ((138, 90, 43), "grain"),
    "dark_wood":   ((86, 54, 30), "grain"),
    "blue":        ((60, 110, 200), "lacquer"),
    "light_blue":  ((140, 200, 236), "lacquer"),
    "white":       ((236, 236, 232), "lacquer"),
    "red":         ((196, 36, 36), "lacquer"),
    "pink":        ((236, 164, 190), "lacquer"),
    "green_gem":   ((40, 190, 110), "gem"),
    "red_gem":     ((220, 30, 50), "gem"),
    "blue_gem":    ((60, 120, 230), "gem"),
    "leather":     ((110, 70, 42), "leather"),
    "black_leather": ((44, 38, 36), "leather"),
    "fur":         ((236, 232, 222), "fur"),
    "rope":        ((196, 160, 104), "wrap"),
    "bone":        ((226, 218, 196), "lacquer"),
    "poison":      ((120, 60, 150), "metal"),
    "yellow":      ((246, 200, 48), "lacquer"),   # keep new materials at the end so older models' UVs stay put
}
TILES = {}
order = []
for name, (_, kind) in MATERIALS.items():
    if kind == "grain":
        order += [name + "/h", name + "/v"]
    else:
        order.append(name)
assert len(order) <= (ATLAS // TILE) ** 2, len(order)
for i, key in enumerate(order):
    TILES[key] = ((i % (ATLAS // TILE)) * TILE, (i // (ATLAS // TILE)) * TILE)


def clamp(v):
    return max(0, min(255, int(v)))


def make_atlas():
    img = Image.new("RGBA", (ATLAS, ATLAS), (0, 0, 0, 0))
    rnd = random.Random(11)
    for key, (ox, oy) in TILES.items():
        name, _, axis = key.partition("/")
        (r, g, b), kind = MATERIALS[name]
        stripes = [rnd.uniform(-14, 10) for _ in range(TILE)]
        for y in range(TILE):
            for x in range(TILE):
                if kind == "grain":
                    across = y if axis == "h" else x
                    d = stripes[across] + rnd.uniform(-4, 4)
                    if rnd.random() < 0.03:
                        d -= 18
                elif kind == "metal":
                    d = rnd.uniform(-6, 6)
                    if rnd.random() < 0.05:
                        d += 16
                elif kind == "wrap":
                    # tsuka-ito: criss-cross cord with light diamonds showing through
                    a, c = (x + y) % 4, (x - y) % 4
                    d = 10 if (a == 0 or c == 0) else -18 if (a == 2 and c == 2) else -4
                    d += rnd.uniform(-3, 3)
                elif kind == "lacquer":
                    d = rnd.uniform(-3, 3) + (10 if (x + 2 * y) % 13 == 0 else 0)
                elif kind == "gem":
                    d = 40 if (x + y) % 5 == 0 else rnd.uniform(-10, 10)
                elif kind == "leather":
                    d = rnd.uniform(-10, 6)
                elif kind == "fur":
                    d = rnd.uniform(-22, 6)
                else:
                    d = 0
                img.putpixel((ox + x, oy + y), (clamp(r + d), clamp(g + d), clamp(b + d), 255))
    return img


# ---------- model building ----------
FACES = {"north": ("x", "y"), "south": ("x", "y"), "east": ("z", "y"), "west": ("z", "y"), "up": ("x", "z"), "down": ("x", "z")}
AX = {"x": 0, "y": 1, "z": 2}


def box(frm, to, mat, rot=None, faces=None):
    """rot: (axis, angle, origin). Angles must be -45, -22.5, 0, 22.5 or 45."""
    lo = [min(a, b) for a, b in zip(frm, to)]
    hi = [max(a, b) for a, b in zip(frm, to)]
    return {"from": lo, "to": hi, "mat": mat, "rot": rot, "faces": faces or {}}


def element(b, seed):
    frm, to = b["from"], b["to"]
    for i in range(3):
        assert -16 <= frm[i] <= 32 and -16 <= to[i] <= 32, (seed, frm, to)
        assert to[i] > frm[i], (seed, frm, to)
    size = [to[i] - frm[i] for i in range(3)]
    longest = max(range(3), key=lambda i: size[i])
    faces = {}
    for face, (ua, va) in FACES.items():
        mat = b["faces"].get(face, b["mat"])
        w, h = min(size[AX[ua]], TILE), min(size[AX[va]], TILE)
        key = mat + ("/h" if AX[ua] == longest else "/v") if MATERIALS[mat][1] == "grain" else mat
        ox, oy = TILES[key]
        rnd = random.Random(zlib.crc32(f"{seed}{face}".encode()))
        sx = rnd.uniform(0, max(0, TILE - w - 0.01))
        sy = rnd.uniform(0, max(0, TILE - h - 0.01))
        u0, v0 = (ox + sx) / UV, (oy + sy) / UV
        faces[face] = {"uv": [round(u0, 3), round(v0, 3), round(u0 + w / UV, 3), round(v0 + h / UV, 3)], "texture": "#parts"}
    e = {"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "faces": faces}
    if b["rot"]:
        axis, angle, origin = b["rot"]
        assert angle in (-45, -22.5, 0, 22.5, 45), angle
        e["rotation"] = {"angle": angle, "axis": axis, "origin": list(origin)}
    return e


def col(x0, x1, y0, y1, z0, z1, mat, **kw):
    return box([x0, y0, z0], [x1, y1, z1], mat, **kw)


def rod(y0, y1, w, mat, cx=8.0, cz=8.0, **kw):
    """A square bar standing up, w pixels thick."""
    h = w / 2
    return box([cx - h, y0, cz - h], [cx + h, y1, cz + h], mat, **kw)


def plate(y0, y1, wx, wz, mat, cz=8.0, **kw):
    return box([8 - wx / 2, y0, cz - wz / 2], [8 + wx / 2, y1, cz + wz / 2], mat, **kw)


def blade(y0, y1, width, thick, mat, edge, curve=0.0, segments=4, cz=8.0, tip=1.6, edge_w=0.35):
    """A sword blade from y0 up to y1. curve: how far (px) the tip bends back toward +Z.
    The edge (hamon) is a thin lighter strip on the -Z side. The tip is a short wedge."""
    out = []
    body = (y1 - tip) - y0
    for i in range(segments):
        a, b = y0 + body * i / segments, y0 + body * (i + 1) / segments
        t = (i + 0.5) / segments
        off = curve * t * t
        z0 = cz - width / 2 + off
        out.append(box([8 - thick / 2, a, z0 + edge_w], [8 + thick / 2, b, z0 + width], mat))
        out.append(box([8 - thick / 2 + 0.05, a, z0], [8 + thick / 2 - 0.05, b, z0 + edge_w], edge))
    off = curve
    z0 = cz - width / 2 + off
    # tip: the back slopes down to the edge (kissaki)
    out.append(box([8 - thick / 2 + 0.05, y1 - tip, z0], [8 + thick / 2 - 0.05, y1, z0 + width * 0.55], edge))
    out.append(box([8 - thick / 2, y1 - tip, z0 + width * 0.55], [8 + thick / 2, y1 - tip * 0.45, z0 + width], mat))
    return out


def katana(handle, blade_len, wrap, tsuba, blade_mat="steel", edge="hamon", tsuba_size=2.6, tsuba_shape="round",
           width=1.3, thick=0.7, curve=0.5, kashira="dark_iron", habaki="gold", y0=-2.0):
    """Japanese sword: pommel cap, wrapped handle, guard, collar, slightly curved blade."""
    hb = y0 + handle
    parts = [
        rod(y0 - 0.5, y0, 1.25, kashira),
        plate(y0, hb, 1.1, 1.3, wrap),
        plate(y0 + handle * 0.35, y0 + handle * 0.55, 1.2, 0.6, habaki, cz=8.0),  # menuki ornament
    ]
    if tsuba_shape == "round":
        parts += [plate(hb, hb + 0.45, tsuba_size, tsuba_size, tsuba), plate(hb, hb + 0.45, tsuba_size * 0.7, tsuba_size * 1.2, tsuba)]
    elif tsuba_shape == "cross":   # Shusui: four-leaf guard
        parts += [plate(hb, hb + 0.45, tsuba_size, 1.0, tsuba), plate(hb, hb + 0.45, 1.0, tsuba_size, tsuba),
                  plate(hb, hb + 0.45, tsuba_size * 0.7, tsuba_size * 0.7, tsuba)]
    elif tsuba_shape == "square":
        parts += [plate(hb, hb + 0.45, tsuba_size, tsuba_size, tsuba)]
    parts.append(plate(hb + 0.45, hb + 1.0, thick + 0.3, width + 0.2, habaki))
    parts += blade(hb + 1.0, hb + 1.0 + blade_len, width, thick, blade_mat, edge, curve=curve)
    return parts, (8, y0 + handle * 0.45, 8)


W = {}   # name -> dict(boxes, grip, scale, kind)


def add(name, parts_grip, kind="sword", scale=1.0, **extra):
    parts, grip = parts_grip
    W[name] = dict(boxes=parts, grip=grip, scale=scale, kind=kind, **extra)


# ---- Named swords (Zoro and friends): about 1 m ----
add("wado_ichimonji", katana(4.6, 11.0, "wrap_white", "gold", tsuba_size=2.4, curve=0.4))
add("sandai_kitetsu", katana(4.6, 11.0, "wrap_red", "dark_iron", tsuba_size=2.5, tsuba_shape="square", curve=0.6, habaki="brass"))
add("shusui", katana(4.8, 11.4, "wrap_red", "gold", blade_mat="black_steel", edge="black_edge", tsuba_size=3.0, tsuba_shape="cross"))
add("enma", katana(4.8, 12.0, "wrap_purple", "gold", tsuba_size=2.8, curve=0.5))
add("shigure", katana(4.4, 10.6, "wrap_blue", "silver", tsuba_size=2.2, curve=0.4, habaki="silver"))
add("tamahagane_katana", katana(4.4, 10.6, "wrap_black", "dark_iron", tsuba_size=2.3, curve=0.5, habaki="brass"))
add("kokuto_blade", katana(4.6, 11.0, "wrap_black", "dark_iron", blade_mat="black_steel", edge="black_edge", tsuba_size=2.4, curve=0.5))
add("shodai_kitetsu", katana(4.8, 11.6, "wrap_red", "dark_iron", blade_mat="black_steel", edge="black_edge", tsuba_size=2.7,
                            tsuba_shape="square", curve=0.6, habaki="brass"))
add("ame_no_habakiri", katana(4.8, 12.0, "wrap_blue", "gold", tsuba_size=2.8, curve=0.5))


def ace_sword():
    # Roger's sword Ace: a curved sabre with a gold guard and knuckle bow, red grip.
    p = [
        rod(-2.6, -2.0, 1.2, "gold"),
        plate(-2.0, 2.0, 1.0, 1.2, "wrap_red"),
        plate(2.0, 2.5, 1.6, 3.6, "gold"),
        box([7.5, -2.4, 5.8], [8.5, 2.5, 6.3], "gold"),
        box([7.5, -2.6, 5.8], [8.5, -2.0, 7.6], "gold"),
        box([7.6, 2.5, 9.5], [8.4, 3.4, 10.1], "gold"),
        plate(0.5, 1.5, 1.2, 0.5, "red_gem", cz=8.0),
    ]
    p += blade(2.5, 15.5, 1.4, 0.6, "steel", "hamon", curve=1.2, segments=5)
    return p, (8, 0.0, 8)


add("ace", ace_sword())


def kikoku():
    # Law's nodachi: very long, white cord with black diamonds, cross-pattern guard, red tassel.
    parts, grip = katana(7.0, 19.0, "wrap_white", "dark_iron", tsuba_size=2.8, tsuba_shape="cross", curve=0.9, y0=-8.0, habaki="silver")
    parts.append(box([7.6, -8.8, 7.6], [8.4, -7.6, 8.4], "red"))       # tassel knot under the pommel
    parts.append(box([7.7, -11.0, 7.7], [8.3, -8.8, 8.3], "red"))
    return parts, (8, -2.2, 8)


add("kikoku", kikoku())


def yoru():
    # Mihawk's black blade: a huge cross-shaped sword, black, gold-trimmed cross guard with green jewels.
    p = [
        rod(-8.6, -8.0, 1.6, "gold"),                     # pommel
        box([7.6, -9.6, 7.6], [8.4, -8.6, 8.4], "green_gem"),
        plate(-8.0, -0.6, 1.2, 1.2, "wrap_black"),          # long handle
        plate(-5.0, -4.4, 1.5, 1.5, "gold"),
        plate(-0.6, 0.4, 2.2, 2.2, "gold"),                 # guard centre
        plate(-0.3, 0.3, 1.0, 9.0, "black_steel"),          # cross arms (along Z)
        plate(-0.5, 0.5, 1.2, 1.2, "green_gem", cz=3.6),
        plate(-0.5, 0.5, 1.2, 1.2, "green_gem", cz=12.4),
        box([7.4, -0.8, 3.0], [8.6, 0.8, 3.6], "gold"),     # arm tips curl up
        box([7.4, -0.8, 12.4], [8.6, 0.8, 13.0], "gold"),
        plate(0.4, 2.4, 1.3, 1.6, "black_steel"),           # ricasso with gold inlay
        plate(0.6, 2.2, 1.35, 0.4, "gold"),
    ]
    p += blade(2.4, 24.0, 2.2, 0.8, "black_steel", "black_edge", curve=0.0, segments=4, tip=2.6, edge_w=0.4)
    # Yoru is straight and double-edged: an edge on the back too
    p.append(box([7.65, 2.4, 9.05], [8.35, 21.4, 9.3], "black_edge"))
    return p, (8, -4.4, 8)


add("yoru", yoru(), scale=1.0)


def gryphon():
    # Shanks's saber: curved single-edged blade, gold basket guard with a knuckle bow.
    p = [
        rod(-2.6, -2.0, 1.2, "gold"),
        plate(-2.0, 2.0, 1.0, 1.2, "black_leather"),
        plate(2.0, 2.5, 1.4, 3.2, "gold"),                   # cross guard
        box([7.5, -2.4, 6.0], [8.5, 2.5, 6.5], "gold"),      # knuckle bow (front)
        box([7.5, -2.6, 6.0], [8.5, -2.0, 7.6], "gold"),
        box([7.6, 2.5, 9.3], [8.4, 3.2, 9.9], "gold"),       # quillon tip
    ]
    p += blade(2.5, 14.5, 1.3, 0.6, "steel", "hamon", curve=1.4, segments=5)
    return p, (8, 0.0, 8)


add("gryphon", gryphon())


def soul_solid():
    # Brook's cane sword: slim straight blade; the handle is a cane with a curved crook and a ring.
    p = [
        plate(-3.0, 2.0, 0.9, 0.9, "dark_wood"),
        box([7.55, 2.0, 7.55], [8.45, 2.5, 8.45], "silver"),        # ring
        box([7.55, -3.6, 7.55], [8.45, -3.0, 10.2], "dark_wood"),   # crook going back
        box([7.55, -3.6, 9.4], [8.45, -1.6, 10.2], "dark_wood"),    # and down
        box([7.5, -1.8, 9.35], [8.5, -1.4, 10.25], "silver"),
    ]
    p += blade(2.5, 13.5, 0.7, 0.45, "steel", "hamon", curve=0.0, segments=3, tip=1.2, edge_w=0.2)
    return p, (8, -0.5, 8)


add("soul_solid", soul_solid())


def kiribachi():
    # Arlong's saw-sword: long and wide, with big saw teeth on the front edge.
    p = [
        rod(-4.6, -4.0, 1.4, "iron"),
        plate(-4.0, 0.0, 1.1, 1.2, "wrap_brown"),
        plate(0.0, 0.6, 1.6, 2.6, "iron"),
        plate(0.6, 18.0, 0.7, 3.0, "iron", cz=8.6),                 # wide flat blade
        box([7.7, 0.6, 9.9], [8.3, 18.0, 10.2], "dark_iron"),       # back spine
    ]
    for i in range(9):   # saw teeth
        y = 1.4 + i * 1.85
        p.append(box([7.75, y, 6.3], [8.25, y + 1.1, 7.2], "steel", rot=("x", 45, [8, y + 0.55, 7.1])))
    p.append(box([7.7, 18.0, 7.6], [8.3, 19.4, 9.6], "iron", rot=("x", 22.5, [8, 18, 8.6])))
    return p, (8, -2.0, 8)


add("kiribachi", kiribachi())


def hassaikai():
    # Kaido's kanabo: a long octagonal iron club, studded with spikes, red-wrapped grip.
    p = [
        rod(-8.6, -8.0, 2.0, "dark_iron"),
        rod(-8.0, -1.0, 1.6, "wrap_red"),
        rod(-1.0, 0.0, 2.4, "gold"),
        rod(0.0, 20.0, 3.4, "dark_iron"),            # club body
        rod(1.0, 19.0, 3.8, "iron", cx=8, cz=8),      # slightly wider middle (octagon feel)
        rod(19.6, 20.6, 2.6, "dark_iron"),
    ]
    p[-2] = box([6.3, 1.0, 6.3], [9.7, 19.0, 9.7], "dark_iron", rot=("y", 45, [8, 10, 8]))
    for row in range(6):
        y = 2.6 + row * 3.0
        for k, (dx, dz) in enumerate([(2.2, 0), (-2.2, 0), (0, 2.2), (0, -2.2)]):
            if (row + k) % 2:
                continue
            cx, cz = 8 + dx, 8 + dz
            p.append(box([cx - 0.45, y, cz - 0.45], [cx + 0.45, y + 0.9, cz + 0.45], "steel"))
        for dx, dz in [(1.6, 1.6), (-1.6, 1.6), (1.6, -1.6), (-1.6, -1.6)]:
            if row % 2:
                cx, cz = 8 + dx, 8 + dz
                p.append(box([cx - 0.4, y + 1.2, cz - 0.4], [cx + 0.4, y + 2.0, cz + 0.4], "steel"))
    return p, (8, -4.5, 8)


add("hassaikai", hassaikai(), kind="heavy")


def murakumogiri():
    # Whitebeard's bisento: a long black pole with a gold ring and a big curved blade on top.
    p = [
        rod(-15.0, -14.2, 1.4, "gold"),
        rod(-14.2, 22.0, 1.1, "lacquer_black"),
        rod(-2.0, -1.4, 1.4, "gold"),
        rod(4.0, 4.6, 1.4, "gold"),
        rod(21.6, 22.8, 1.8, "gold"),                         # collar
        plate(22.8, 23.6, 1.0, 3.4, "gold", cz=8.6),          # guard
    ]
    # the broad blade: edge forward (-Z), back curving
    p.append(box([7.65, 23.6, 6.4], [8.35, 30.0, 10.2], "steel"))
    p.append(box([7.7, 23.6, 6.1], [8.3, 30.0, 6.4], "hamon"))
    p.append(box([7.65, 29.0, 6.6], [8.35, 31.6, 9.0], "steel", rot=("x", -22.5, [8, 30, 8])))
    p.append(box([7.7, 29.0, 6.3], [8.3, 31.6, 6.6], "hamon", rot=("x", -22.5, [8, 30, 8])))
    p.append(box([7.6, 24.2, 9.6], [8.4, 26.6, 10.6], "gold"))   # gold back spike
    return p, (8, 0.6, 8)


add("murakumogiri", murakumogiri(), kind="polearm")


def mogura():
    # Katakuri's trident: thick pole, a wide three-pronged head with barbed side prongs.
    p = [
        rod(-14.0, -13.2, 1.6, "dark_iron"),
        rod(-13.2, 20.0, 1.2, "dark_wood"),
        rod(-1.6, -1.0, 1.5, "iron"),
        rod(4.0, 4.6, 1.5, "iron"),
        rod(20.0, 21.4, 2.0, "dark_iron"),
        plate(21.4, 22.4, 1.2, 6.4, "dark_iron"),                # crossbar
        plate(22.4, 30.0, 1.0, 1.2, "steel"),                     # middle prong
        box([7.6, 30.0, 7.5], [8.4, 31.4, 8.5], "steel", rot=("x", 45, [8, 30, 8])),
        box([7.55, 22.4, 4.8], [8.45, 28.0, 5.8], "steel"),       # side prongs
        box([7.55, 22.4, 10.2], [8.45, 28.0, 11.2], "steel"),
        box([7.6, 26.4, 5.6], [8.4, 27.2, 6.6], "steel"),         # barbs
        box([7.6, 26.4, 9.4], [8.4, 27.2, 10.4], "steel"),
        box([7.6, 28.0, 4.9], [8.4, 29.0, 5.7], "steel", rot=("x", -22.5, [8, 28, 5.3])),
        box([7.6, 28.0, 10.3], [8.4, 29.0, 11.1], "steel", rot=("x", 22.5, [8, 28, 10.7])),
    ]
    return p, (8, 1.4, 8)


add("mogura", mogura(), kind="polearm")


def nonosama_bo():
    # Enel's golden staff: a plain gold pole with round knobs at both ends.
    p = [
        rod(-12.0, 15.0, 0.9, "gold"),
        rod(-12.8, -12.0, 1.4, "gold"),
        rod(15.0, 16.2, 1.6, "gold"),
        rod(16.2, 16.8, 1.0, "gold"),
        rod(-1.0, -0.6, 1.15, "brass"),
        rod(3.0, 3.4, 1.15, "brass"),
    ]
    return p, (8, 1.2, 8)


add("nonosama_bo", nonosama_bo(), kind="polearm")


def clima_tact():
    # Nami's Sorcery Clima-Tact: a blue segmented rod with gold joints and the three weather balls at the tip.
    p = [rod(-5.0, 9.0, 0.8, "blue")]
    for y in (-5.2, -1.0, 3.0, 7.0):
        p.append(rod(y, y + 0.5, 1.05, "gold"))
    p.append(rod(9.0, 10.0, 1.1, "gold"))
    p.append(rod(10.0, 11.4, 1.6, "light_blue"))      # Heat / Cool / Thunder balls
    p.append(rod(11.4, 12.8, 1.6, "white"))
    p.append(rod(12.8, 14.2, 1.6, "blue_gem"))
    p.append(rod(14.2, 14.7, 0.9, "gold"))
    return p, (8, 1.0, 8)


add("sorcery_clima_tact", clima_tact(), kind="polearm")


def golden_hook():
    # Crocodile's golden hook: a gold cuff with a big curved hook (the poison hook hides inside).
    p = [
        plate(-2.5, 1.0, 2.0, 2.0, "gold"),
        plate(0.5, 1.0, 2.4, 2.4, "gold"),
        rod(1.0, 4.5, 0.9, "gold"),
        box([7.55, 4.5, 7.55], [8.45, 6.6, 8.45], "gold", rot=("x", -22.5, [8, 4.5, 8])),
        box([7.55, 6.2, 5.6], [8.45, 7.1, 8.2], "gold"),
        box([7.55, 5.0, 5.4], [8.45, 6.4, 6.3], "gold", rot=("x", 22.5, [8, 6.4, 5.8])),
        box([7.7, 4.6, 5.5], [8.3, 5.2, 6.0], "poison"),
    ]
    return p, (8, -1.0, 8)


add("golden_hook", golden_hook(), kind="hand")


def punisher():
    # Killer's Punisher: a gauntlet with two crescent scythe blades that spin.
    p = [
        plate(-3.0, 2.0, 1.8, 2.0, "dark_iron"),
        plate(1.6, 2.6, 2.2, 2.2, "silver"),
        rod(2.6, 3.4, 0.8, "silver"),
    ]
    for side in (-1, 1):
        cz = 8 + side * 2.0
        p.append(box([7.7, 1.0, cz - 0.5], [8.3, 7.0, cz + 0.5], "steel"))
        p.append(box([7.72, 6.2, cz - 0.4 + side * 0.4], [8.28, 8.0, cz + 0.4 + side * 0.4], "steel", rot=("x", side * 22.5, [8, 6.2, cz])))
        p.append(box([7.72, 0.2, cz - 0.4 + side * 0.6], [8.28, 1.6, cz + 0.4 + side * 0.6], "steel", rot=("x", -side * 22.5, [8, 1.6, cz])))
        p.append(box([7.66, 2.6, 8 + side * 0.4 - 0.3], [8.34, 3.2, cz], "silver"))
    return p, (8, -0.5, 8)


add("punisher", punisher(), kind="hand")


def neko_no_te():
    # Kuro's "Cat's Claws": a black glove with five long thin blades, one per finger.
    p = [
        plate(-2.0, 1.6, 2.0, 2.0, "black_leather"),
        plate(1.6, 2.6, 2.2, 2.0, "dark_iron"),
    ]
    for k in range(5):
        x = 6.8 + k * 0.6
        top = 11.5 - abs(k - 2) * 0.8
        p.append(box([x, 2.6, 7.75], [x + 0.3, top, 8.25], "steel"))
        p.append(box([x, top, 7.85], [x + 0.3, top + 0.8, 8.15], "steel", rot=("x", -22.5, [x, top, 8])))
    return p, (8, 0.0, 8)


add("neko_no_te", neko_no_te(), kind="hand")


def buggy_knife():
    # Buggy's throwing knife: a short broad blade with a red-and-white handle.
    p = [
        plate(-1.6, 1.0, 0.8, 0.9, "red"),
        plate(-0.4, 0.2, 0.85, 0.95, "white"),
        plate(1.0, 1.3, 0.9, 1.8, "silver"),
    ]
    p += blade(1.3, 5.6, 1.1, 0.35, "steel", "hamon", curve=0.0, segments=2, tip=1.2, edge_w=0.2)
    return p, (8, -0.3, 8)


add("buggy_knife", buggy_knife(), kind="knife")


def homie_umbrella():
    # Big Mom's little umbrella homie: a round yellow canopy with a smiling face and black drips round the rim,
    # on a pale shaft with a hooked handle.
    p = [
        rod(-1.0, 10.0, 0.7, "bone"),
        box([7.6, -2.4, 7.6], [8.4, -1.0, 8.4], "yellow"),             # handle
        box([7.6, -3.1, 7.6], [8.4, -2.4, 10.0], "yellow"),            # the hook
        box([7.6, -2.4, 9.3], [8.4, -1.4, 10.0], "yellow"),
        plate(10.0, 11.0, 11.0, 11.0, "yellow"),                        # canopy, in rings
        plate(11.0, 12.6, 10.0, 10.0, "yellow"),
        plate(12.6, 14.0, 8.0, 8.0, "yellow"),
        plate(14.0, 14.9, 5.0, 5.0, "yellow"),
        rod(14.9, 16.2, 0.6, "dark_iron"),                              # tip
        # the face, on the front (-Z)
        box([6.0, 12.9, 3.7], [6.9, 13.8, 4.0], "lacquer_black"),
        box([9.1, 12.9, 3.7], [10.0, 13.8, 4.0], "lacquer_black"),
        box([6.0, 11.3, 2.7], [10.0, 11.9, 3.0], "red"),                # big grin
        box([5.6, 11.6, 2.7], [6.0, 12.2, 3.0], "red"),
        box([10.0, 11.6, 2.7], [10.4, 12.2, 3.0], "red"),
    ]
    # black drips hanging under the rim
    for k, x in enumerate((3.0, 5.2, 7.4, 9.6, 11.8)):
        ln = (1.6, 0.9, 1.3)[k % 3]
        p.append(box([x, 10.0 - ln, 2.4], [x + 1.0, 10.0, 2.9], "lacquer_black"))
        p.append(box([x + 0.4, 10.0 - (2.4 - ln), 13.1], [x + 1.4, 10.0, 13.6], "lacquer_black"))
    for k, z in enumerate((4.0, 7.0, 10.0)):
        ln = (1.2, 1.7, 0.9)[k]
        p.append(box([2.4, 10.0 - ln, z], [2.9, 10.0, z + 1.0], "lacquer_black"))
        p.append(box([13.1, 10.0 - (2.6 - ln), z], [13.6, 10.0, z + 1.0], "lacquer_black"))
    return p, (8, -1.7, 8)


add("homie_umbrella", homie_umbrella(), kind="sword", third_rot=90)   # held up like a parasol


def slingshot(name, frame, accent, height, fork_w):
    # Usopp's slingshots: a long staff with a wide fork on top and a band between the prongs.
    p = [
        rod(-height * 0.45, height * 0.4, 1.1, frame),
        rod(-height * 0.45 - 0.6, -height * 0.45, 1.4, accent),
        plate(-1.8, 1.8, 1.25, 1.25, "black_leather"),             # hand grip
        plate(height * 0.4, height * 0.4 + 1.2, 1.2, fork_w, frame),  # fork bridge
    ]
    top = height * 0.4 + 1.2
    for side in (-1, 1):
        cz = 8 + side * (fork_w / 2 - 0.6)
        p.append(box([7.4, top, cz - 0.6], [8.6, top + 4.5, cz + 0.6], frame))
        p.append(box([7.35, top + 4.5, cz - 0.65], [8.65, top + 5.2, cz + 0.65], accent))
    p.append(box([7.85, top + 3.6, 8 - fork_w / 2 + 0.6], [8.15, top + 4.0, 8 + fork_w / 2 - 0.6], "black_leather"))  # band
    return p, (8, 0.0, 8)


add("kabuto", slingshot("kabuto", "dark_wood", "red", 20.0, 6.4), kind="slingshot")
add("kuro_kabuto", slingshot("kuro_kabuto", "lacquer_black", "red", 16.0, 6.0), kind="slingshot")


# ---------- how they sit in the hand ----------
# Third person: the hand's frame (worked out for the guns, see tools/guns/README.md) points model -Z along the arm,
# so with no rotation a blade standing on +Y points forward when the arm hangs down, like Minecraft's own swords.
THIRD_FIST = (-1, -2, 2)


def display(w):
    s = w["scale"]
    gx, gy, gz = w["grip"]

    def t(target, scale):
        return [round(target[0] - scale * (gx - 8), 2), round(target[1] - scale * (gy - 8), 2), round(target[2] - scale * (gz - 8), 2)]

    # First person: tilt the blade up and away like Minecraft's swords, and shrink long weapons so they fit the screen.
    length = max(b["to"][1] for b in w["boxes"]) - min(b["from"][1] for b in w["boxes"])
    fs = s * min({"sword": 0.55, "heavy": 0.42, "polearm": 0.36, "hand": 0.45, "knife": 0.55, "slingshot": 0.5}[w["kind"]], 15.0 / length)
    first_rot = {"sword": [-15, 0, 18], "heavy": [-15, 0, 15], "polearm": [-10, 0, 15], "hand": [-30, 0, 10], "knife": [-20, 0, 18], "slingshot": [0, 0, 5]}[w["kind"]]
    first_target = (2.0, 2.0, -1.5)
    def rotated(target, scale, ax):
        # a weapon tipped over in the hand (rotation about X): move it so the grip still lands in the fist
        a = math.radians(ax)
        oy, oz = scale * (gy - 8), scale * (gz - 8)
        ry, rz = oy * math.cos(a) - oz * math.sin(a), oy * math.sin(a) + oz * math.cos(a)
        return [round(target[0] - scale * (gx - 8), 2), round(target[1] - ry, 2), round(target[2] - rz, 2)]

    ax = w.get("third_rot", 0)
    d = {
        "thirdperson_righthand": {"rotation": [ax, 0, 0], "translation": rotated(THIRD_FIST, s, ax), "scale": [s, s, s]},
        "thirdperson_lefthand": {"rotation": [ax, 0, 0], "translation": rotated((1, -2, 2), s, ax), "scale": [s, s, s]},
        "firstperson_righthand": {"rotation": first_rot, "translation": t(first_target, fs), "scale": [fs, fs, fs]},
        "firstperson_lefthand": {"rotation": first_rot, "translation": t((-first_target[0], first_target[1], first_target[2]), fs), "scale": [fs, fs, fs]},
        "ground": {"rotation": [90, 0, 0], "translation": [0, 1, 0], "scale": [0.4, 0.4, 0.4]},
        "fixed": {"rotation": [0, 90, 45], "translation": [0, 0, 0], "scale": [0.45, 0.45, 0.45]},
        "head": {"rotation": [0, 90, 0], "translation": [0, 10, 0], "scale": [0.6, 0.6, 0.6]},
        "gui": {"rotation": [0, 90, 45], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
    }
    for key in ("thirdperson_righthand", "thirdperson_lefthand", "firstperson_righthand", "firstperson_lefthand"):
        tr = d[key]["translation"]
        d[key]["translation"] = [max(-80, min(80, v)) for v in tr]
    return d


def main():
    only = sys.argv[2:] or list(W)
    make_atlas().save(os.path.join(ASSETS, "textures/item/weapon_parts.png"))
    for name in only:
        w = W[name]
        model = {
            "textures": {"parts": "onepiece:item/weapon_parts", "particle": f"onepiece:item/{name}"},
            "gui_light": "front",
            "display": display(w),
            "elements": [element(b, f"{name}{i}") for i, b in enumerate(w["boxes"])],
        }
        with open(os.path.join(ASSETS, f"models/item/{name}_held.json"), "w") as f:
            json.dump(model, f, indent=1)
        item = {"model": {
            "type": "minecraft:select",
            "property": "minecraft:display_context",
            "cases": [{"when": "gui", "model": {"type": "minecraft:model", "model": f"onepiece:item/{name}"}}],
            "fallback": {"type": "minecraft:model", "model": f"onepiece:item/{name}_held"},
        }}
        with open(os.path.join(ASSETS, f"items/{name}.json"), "w") as f:
            json.dump(item, f, indent=2)
            f.write("\n")
    print("wrote", len(only), "weapon models")


main()
