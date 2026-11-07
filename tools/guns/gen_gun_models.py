"""
Writes the 3D in-hand models for the guns (see README.md next to this file).

Each gun is a list of boxes in model pixels, barrel pointing north (-Z), grip pointing down.
The inventory keeps the old flat icon; everything else (hands, ground, item frames) uses the 3D model.
Run from anywhere:  python3 gen_gun_models.py <path to source/src/main/resources/assets/onepiece>
"""
import json, os, random, sys, zlib
from PIL import Image

ASSETS = sys.argv[1]
TILE = 32           # texels per material tile
ATLAS = 128         # atlas size in texels -> 16 tiles, 1 UV unit = 8 texels
UV = ATLAS / 16

# ---------- materials: (base colour, kind) ----------
MATERIALS = {
    "wood":       ((138, 90, 43), "grain"),
    "dark_wood":  ((92, 58, 30), "grain"),
    "iron":       ((125, 127, 134), "metal"),
    "steel":      ((196, 199, 206), "metal"),
    "gunmetal":   ((70, 72, 80), "metal"),
    "black":      ((38, 39, 45), "metal"),
    "brass":      ((201, 161, 59), "metal"),
    "lens":       ((142, 197, 232), "lens"),
    "bore":       ((14, 14, 16), "flat"),
    "red":        ((168, 34, 30), "metal"),
    "green":      ((112, 184, 72), "metal"),
}
# Wood gets two tiles: grain along u (h) and along v (v).
TILES = {}
order = []
for name, (_, kind) in MATERIALS.items():
    if kind == "grain":
        order += [name + "/h", name + "/v"]
    else:
        order.append(name)
for i, key in enumerate(order):
    TILES[key] = ((i % 4) * TILE, (i // 4) * TILE)


def clamp(v):
    return max(0, min(255, int(v)))


def make_atlas():
    img = Image.new("RGBA", (ATLAS, ATLAS), (0, 0, 0, 0))
    rnd = random.Random(7)
    for key, (ox, oy) in TILES.items():
        name, _, axis = key.partition("/")
        (r, g, b), kind = MATERIALS[name]
        # wood grain: stripes of slightly different tone running along one axis
        stripes = [rnd.uniform(-14, 10) for _ in range(TILE)]
        for y in range(TILE):
            for x in range(TILE):
                if kind == "grain":
                    across = y if axis == "h" else x
                    along = x if axis == "h" else y
                    d = stripes[across] + rnd.uniform(-4, 4)
                    if rnd.random() < 0.03:
                        d -= 18  # a knot / dark fleck
                    _ = along
                elif kind == "metal":
                    d = rnd.uniform(-7, 7)
                    if rnd.random() < 0.05:
                        d += 14  # glint
                elif kind == "lens":
                    d = 30 if (x + y) % 9 == 0 else rnd.uniform(-6, 6)
                else:
                    d = 0
                img.putpixel((ox + x, oy + y), (clamp(r + d), clamp(g + d), clamp(b + d), 255))
    return img


# ---------- model building ----------
FACES = {  # face: (u axis, v axis) in box coordinates
    "north": ("x", "y"), "south": ("x", "y"),
    "east": ("z", "y"), "west": ("z", "y"),
    "up": ("x", "z"), "down": ("x", "z"),
}
AX = {"x": 0, "y": 1, "z": 2}


def box(frm, to, mat, rot=None, faces=None):
    """faces: optional {face: material} overrides, e.g. a dark bore on the muzzle."""
    return {"from": frm, "to": to, "mat": mat, "rot": rot, "faces": faces or {}}


def element(b, seed):
    frm, to = b["from"], b["to"]
    size = [to[i] - frm[i] for i in range(3)]
    longest = max(range(3), key=lambda i: size[i])
    faces = {}
    for face, (ua, va) in FACES.items():
        mat = b["faces"].get(face, b["mat"])
        w, h = size[AX[ua]], size[AX[va]]
        if MATERIALS[mat][1] == "grain":
            # grain runs along the box's long side
            key = mat + ("/h" if AX[ua] == longest else "/v")
        else:
            key = mat
        ox, oy = TILES[key]
        rnd = random.Random(zlib.crc32(f"{seed}{face}".encode()))
        sx = rnd.uniform(0, max(0, TILE - w - 0.01))
        sy = rnd.uniform(0, max(0, TILE - h - 0.01))
        u0, v0 = (ox + sx) / UV, (oy + sy) / UV
        faces[face] = {"uv": [round(u0, 3), round(v0, 3), round(u0 + w / UV, 3), round(v0 + h / UV, 3)], "texture": "#parts"}
    e = {"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "faces": faces}
    if b["rot"]:
        axis, angle, origin = b["rot"]
        e["rotation"] = {"angle": angle, "axis": axis, "origin": origin}
    return e


def ring(x0, y0, x1, y1, z0, z1, mat="brass", pad=0.2):
    return box([x0 - pad, y0 - pad, z0], [x1 + pad, y1 + pad, z1], mat)


# Grip centre = where the fist goes. Third person and first person transforms are worked out from it.
GUNS = {}

GUNS["flintlock_pistol"] = dict(hold="pistol", grip=(8, 6.2, 11.6), scale=0.8, boxes=[
    box([7, 9, -2], [9, 11, 9], "iron", faces={"north": "bore"}),           # barrel
    ring(7, 9, 9, 11, -2, -1),                                                # muzzle band
    box([7.1, 8, 0], [8.9, 9, 10], "wood"),                                   # stock under the barrel
    ring(7.1, 8, 8.9, 11, 4, 4.6, pad=0.15),                                  # barrel band
    box([6.6, 8.6, 7.5], [7.1, 10.6, 10.5], "iron"),                          # lock plate
    box([7.4, 11, 9.2], [8.6, 12.6, 10.4], "gunmetal"),                       # hammer
    box([7.6, 11.6, 8.4], [8.4, 12.6, 9.2], "gunmetal"),                      # flint jaw
    box([7.1, 8, 9.5], [8.9, 11, 12], "wood"),                                # wrist
    box([7.1, 3.4, 10.4], [8.9, 9, 13], "wood", rot=("x", -22.5, [8, 9, 11.5])),        # grip
    box([6.8, 2.6, 10.1], [9.2, 3.6, 13.4], "brass", rot=("x", -22.5, [8, 9, 11.5])),   # butt cap
    box([7.5, 7.3, 8], [8.5, 7.8, 10.6], "brass"),                            # trigger guard
    box([7.5, 7.3, 7.6], [8.5, 8, 8.1], "brass"),
    box([7.8, 7.8, 9.4], [8.2, 8.4, 9.8], "black"),                           # trigger
])

GUNS["marine_rifle"] = dict(hold="rifle", grip=(8, 7.6, 10.6), support=-6, scale=0.8, boxes=[
    box([7.25, 10, -14], [8.75, 11.5, 7], "iron", faces={"north": "bore"}),   # barrel
    box([7.6, 11.5, -13.6], [8.4, 12.2, -13], "brass"),                        # front sight
    box([7.8, 11.1, -16], [8.2, 11.5, -14], "steel"),                          # bayonet blade
    box([7.6, 10.6, -14.8], [8.4, 11.3, -13.5], "steel"),                      # bayonet socket
    box([7, 8.4, -11], [9, 10.3, 7], "wood"),                                  # forestock
    ring(7, 8.4, 9, 11.5, -10.5, -9.9, pad=0.15),
    ring(7, 8.4, 9, 11.5, -3, -2.4, pad=0.15),
    ring(7, 8.4, 9, 11.5, 3.5, 4.1, pad=0.15),
    box([6.6, 8.8, 5.5], [7, 10.8, 9], "iron"),                                # lock plate
    box([7.4, 11.4, 8], [8.6, 12.8, 9.2], "gunmetal"),                         # hammer
    box([7, 8, 7], [9, 11.4, 10], "wood"),                                     # receiver wood
    box([7.1, 6.6, 9.6], [8.9, 10, 12.4], "dark_wood"),                        # wrist (hand)
    box([6.8, 5, 12.2], [9.2, 10.6, 19.5], "wood"),                            # butt stock
    box([6.7, 4.8, 19.5], [9.3, 10.8, 20.1], "brass"),                         # butt plate
    box([7.5, 7.3, 6.5], [8.5, 7.8, 9.2], "brass"),                            # trigger guard
    box([7.8, 7.8, 8], [8.2, 8.4, 8.4], "black"),
])

GUNS["tommy_gun"] = dict(hold="rifle", grip=(8, 7, 11.4), support=0, scale=0.8, boxes=[
    box([7.3, 9.6, -8], [8.7, 11, 2], "gunmetal", faces={"north": "bore"}),   # barrel
    *[box([7, 9.3, z], [9, 11.3, z + 0.6], "black") for z in (-5, -3.6, -2.2, -0.8, 0.6)],  # cooling fins
    box([7.6, 11, -7.6], [8.4, 11.8, -7]  , "black"),                          # front sight
    box([7, 9, 2], [9, 12, 11], "gunmetal"),                                   # receiver
    box([7.4, 12, 6], [8.6, 12.5, 9], "black"),                                # bolt
    box([7.3, 4.6, -1.4], [8.7, 9, 0.8], "wood"),                              # front grip
    box([6.2, 4.4, 3.8], [9.8, 8.6, 8.2], "black"),                            # drum magazine
    box([6.4, 3.8, 4.4], [9.6, 9, 7.6], "black"),
    box([6.4, 4.2, 4], [9.6, 8.8, 8], "gunmetal"),
    box([7.3, 4.6, 9.8], [8.7, 9, 12.4], "wood", rot=("x", -22.5, [8, 9, 11])),   # rear grip
    box([7.6, 8, 8.6], [8.4, 9, 9.8], "black"),                                # trigger
    box([7.2, 7.6, 11], [8.8, 11.4, 20], "wood"),                              # stock
    box([7.1, 7.4, 20], [8.9, 11.6, 20.6], "black"),
])

GUNS["hand_cannon"] = dict(hold="rifle", grip=(8, 6.6, 4.6), support=-3, scale=0.75, first=(4, -2.5, 1), first_scale=0.55, boxes=[
    box([5.5, 9, -8], [10.5, 14, 14], "iron", faces={"north": "bore", "south": "bore"}),  # tube
    box([5, 8.5, -9], [11, 14.5, -7.4], "gunmetal", faces={"north": "bore"}),           # muzzle ring
    box([5, 8.5, 12.6], [11, 14.5, 14.4], "gunmetal", faces={"south": "bore"}),          # rear ring
    box([5.3, 8.8, 2], [10.7, 14.2, 3], "brass"),                                          # band
    box([7.5, 14, 0], [8.5, 15.4, 6], "gunmetal"),                                         # sight rail
    box([7.6, 15.4, 1], [8.4, 16.2, 2], "black"),
    box([7.2, 4, 3.4], [8.8, 9, 5.8], "wood"),                                             # rear grip
    box([7.6, 7.6, 5.8], [8.4, 9, 6.6], "black"),                                          # trigger
    box([7.2, 5, -4.6], [8.8, 9, -2.6], "wood"),                                           # front grip
])

GUNS["senriku"] = dict(hold="rifle", grip=(8, 7.4, 12.6), support=-4, scale=0.8, boxes=[
    box([7.4, 10, -16], [8.6, 11.2, 4], "black", faces={"north": "bore"}),     # barrel
    box([7.1, 9.7, -16], [8.9, 11.5, -13.6], "gunmetal", faces={"north": "bore"}),   # muzzle brake
    box([7.1, 8.6, -6], [8.9, 10, 4], "dark_wood"),                             # handguard
    box([7, 9, 4], [9, 11.6, 12], "black"),                                     # receiver
    box([7.25, 12, 2], [8.75, 13.5, 11], "black", faces={"north": "lens", "south": "lens"}),  # scope
    box([7.05, 11.8, 2], [8.95, 13.7, 3.2], "gunmetal", faces={"north": "lens"}),
    box([7.05, 11.8, 9.8], [8.95, 13.7, 11], "gunmetal", faces={"south": "lens"}),
    box([7.7, 11.5, 4], [8.3, 12, 5], "gunmetal"),                              # scope mounts
    box([7.7, 11.5, 8.5], [8.3, 12, 9.5], "gunmetal"),
    box([9, 10.6, 8], [9.8, 11, 9], "steel"),                                   # bolt handle
    box([7.6, 7.8, 9.2], [8.4, 9, 10], "black"),                                # trigger
    box([7.5, 7.4, 8.6], [8.5, 7.9, 11], "gunmetal"),                           # trigger guard
    box([7.2, 5.4, 11.2], [8.8, 9.6, 13.8], "dark_wood", rot=("x", -22.5, [8, 9, 12.5])),  # grip
    box([7, 6.6, 13.4], [9, 11.4, 21.6], "wood"),                               # stock
    box([7.1, 11.4, 14], [8.9, 12.2, 18], "wood"),                              # cheek rest
    box([6.9, 6.4, 21.6], [9.1, 11.6, 22.2], "black"),                          # butt pad
])


# Where the fist sits in each frame (model pixels relative to the frame origin), worked out from
# ItemInHandLayer: the origin is 1px right, 2px "up" and at the end of the arm; the fist is 1px left,
# 2px down and 2px back of it.
THIRD_FIST = (-1, -2, 2)


def display(g):
    s = g["scale"]
    gx, gy, gz = g["grip"]
    def t(target, scale):
        return [round(target[0] - scale * (gx - 8), 2), round(target[1] - scale * (gy - 8), 2), round(target[2] - scale * (gz - 8), 2)]
    first_target = g.get("first", (1.5, 1.0, -1.0))
    fs = s * g.get("first_scale", 0.65)
    return {
        "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": t(THIRD_FIST, s), "scale": [s, s, s]},
        "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": t((1, -2, 2), s), "scale": [s, s, s]},
        "firstperson_righthand": {"rotation": [0, 0, 0], "translation": t(first_target, fs), "scale": [fs, fs, fs]},
        "firstperson_lefthand": {"rotation": [0, 0, 0], "translation": t((-first_target[0], first_target[1], first_target[2]), fs), "scale": [fs, fs, fs]},
        "ground": {"rotation": [0, 90, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 90, 0], "translation": [0, 0, 0], "scale": [0.6, 0.6, 0.6]},
        "head": {"rotation": [0, 90, 0], "translation": [0, 10, 0], "scale": [0.8, 0.8, 0.8]},
        "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
    }


def main():
    tex_dir = os.path.join(ASSETS, "textures/item")
    make_atlas().save(os.path.join(tex_dir, "gun_parts.png"))
    for name, g in GUNS.items():
        model = {
            "textures": {"parts": "onepiece:item/gun_parts", "particle": f"onepiece:item/{name}"},
            "gui_light": "front",
            "display": display(g),
            "elements": [element(b, f"{name}{i}") for i, b in enumerate(g["boxes"])],
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
    # The slingshots stay flat (they are flat), but stand up in the fist instead of sticking out like a sword.
    for name in ("kabuto", "kuro_kabuto"):
        model = {
            "parent": "minecraft:item/generated",
            "textures": {"layer0": f"onepiece:item/{name}"},
            "display": {
                "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [-1, 2.5, 1.5], "scale": [0.7, 0.7, 0.7]},
                "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [1, 2.5, 1.5], "scale": [0.7, 0.7, 0.7]},
                "firstperson_righthand": {"rotation": [0, -10, 0], "translation": [3, 2, -2], "scale": [0.5, 0.5, 0.5]},
                "firstperson_lefthand": {"rotation": [0, 10, 0], "translation": [-3, 2, -2], "scale": [0.5, 0.5, 0.5]},
            },
        }
        with open(os.path.join(ASSETS, f"models/item/{name}.json"), "w") as f:
            json.dump(model, f, indent=2)
            f.write("\n")
    print("wrote", len(GUNS), "gun models + 2 slingshots")


main()
