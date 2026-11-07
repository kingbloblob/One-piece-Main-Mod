"""Writes the Cannon block models (assets/onepiece/models/block/): full-size ship cannons on wheeled carriages.

cannon.json (mounted=false, placed by players): the block is the carriage; the barrel runs one block forward and
  the cascabel knob sticks out a few pixels behind. About 2.3 blocks long.
cannon_mounted.json (mounted=true, ship gunports): the block is the hull wall with a dark gunport; the barrel pokes
  out almost a block over the sea and the carriage stands on the deck behind. About 2.9 blocks long.
Model space is -16..32, so nothing reaches further. Facing north = muzzle toward -z; the blockstate rotates it.
Usage: python3 gen_cannon_model.py <models/block dir>
"""
import json, os, sys
TEX = {
    "wood": "minecraft:block/dark_oak_planks",
    "iron": "minecraft:block/polished_blackstone",
    "band": "minecraft:block/netherite_block",
    "wheel": "minecraft:block/dark_oak_log_top",
    "tread": "minecraft:block/dark_oak_log",
    "bore": "minecraft:block/black_concrete",
    "port": "minecraft:block/black_concrete",
    "particle": "minecraft:block/polished_blackstone",
}

def uv(a, b):
    """UV rect for a face spanning model coords a..b on two axes, kept inside one 16x16 texture."""
    (u0, u1), (v0, v1) = a, b
    w, h = min(16, u1 - u0), min(16, v1 - v0)
    su = (u0 % 16) if (u0 % 16) + w <= 16 else 16 - w
    sv = (v0 % 16) if (v0 % 16) + h <= 16 else 16 - h
    return [round(su, 3), round(sv, 3), round(su + w, 3), round(sv + h, 3)]

def box(f, t, tex, side_tex=None, faces=None, only=None):
    (x0, y0, z0), (x1, y1, z1) = f, t
    flip = lambda r: [r[0], 16 - r[3], r[2], 16 - r[1]]  # v grows downward
    spans = {
        "north": ((16 - x1, 16 - x0), (16 - y1, 16 - y0)),
        "south": ((x0, x1), (16 - y1, 16 - y0)),
        "east": ((16 - z1, 16 - z0), (16 - y1, 16 - y0)),
        "west": ((z0, z1), (16 - y1, 16 - y0)),
        "up": ((x0, x1), (z0, z1)),
        "down": ((x0, x1), (16 - z1, 16 - z0)),
    }
    out = {}
    for name, (a, b) in spans.items():
        if only and name not in only:
            continue
        t_ = (faces or {}).get(name, side_tex if (side_tex and name in ("up", "down", "north", "south")) else tex)
        out[name] = {"uv": uv(a, b), "texture": "#" + t_}
    return {"from": list(f), "to": list(t), "faces": out}

def free_cannon():
    E = []
    # Carriage: bed, two stepped cheeks, axles, four truck wheels.
    E.append(box((3, 2, 0), (13, 4, 16), "wood"))
    for x0 in (3, 11):
        E.append(box((x0, 4, 1), (x0 + 2, 10, 9), "wood"))
        E.append(box((x0, 4, 9), (x0 + 2, 7.5, 16), "wood"))
    for z0 in (2.5, 11.5):
        E.append(box((1.5, 1.5, z0), (14.5, 3.5, z0 + 2), "band"))
    for x0 in (0.5, 13.5):
        for z0 in (0.5, 9.5):
            E.append(box((x0, 0, z0), (x0 + 2, 6, z0 + 6), "tread", faces={"east": "wheel", "west": "wheel"}))
    # Trunnions resting on the cheeks.
    E.append(box((2.5, 9, 5), (13.5, 11, 7), "band"))
    # Barrel, breech to muzzle, with reinforcing bands.
    E.append(box((4.5, 6.5, 4), (11.5, 13.5, 15.75), "iron"))     # breech (ends inside the base ring: no z-fight)
    E.append(box((4, 6, 13), (12, 14, 16), "band"))               # base ring
    E.append(box((5, 7, -6), (11, 13, 4), "iron"))                # reinforce
    E.append(box((4.5, 6.5, -1.5), (11.5, 13.5, 0.5), "band"))    # reinforce ring
    E.append(box((5.5, 7.5, -13.5), (10.5, 12.5, -6), "iron"))    # chase
    E.append(box((4.75, 6.75, -15.9), (11.25, 13.25, -13.5), "band"))  # muzzle swell
    E.append(box((6.5, 8.5, -15.95), (9.5, 11.5, -15.9), "bore", only=["north"]))  # dark bore
    # Cascabel knob behind the breech.
    E.append(box((7, 9, 16), (9, 11, 18), "iron"))
    E.append(box((6.5, 8.5, 18), (9.5, 11.5, 20.5), "band"))

    return E


def mounted_cannon():
    E = []
    # Gunport frame filling the hull-wall block around the barrel.
    E.append(box((0, 0, 0), (16, 6.5, 16), "port"))
    E.append(box((0, 13.5, 0), (16, 16, 16), "port"))
    E.append(box((0, 6.5, 0), (4.5, 13.5, 16), "port"))
    E.append(box((11.5, 6.5, 0), (16, 13.5, 16), "port"))
    # Barrel: muzzle out over the sea, through the port, breech on the deck behind.
    E.append(box((4.75, 6.75, -14), (11.25, 13.25, -11.5), "band"))   # muzzle swell
    E.append(box((6.5, 8.5, -14.05), (9.5, 11.5, -14), "bore", only=["north"]))
    E.append(box((5.5, 7.5, -11.5), (10.5, 12.5, 0), "iron"))         # chase
    E.append(box((4.5, 6.5, 0), (11.5, 13.5, 16), "iron"))            # through the port
    E.append(box((4.5, 6.5, 16), (11.5, 13.5, 18), "band"))           # ring
    E.append(box((5, 7, 18), (11, 13, 21), "iron"))                   # reinforce
    E.append(box((4.5, 6.5, 21), (11.5, 13.5, 28.75), "iron"))        # breech
    E.append(box((4, 6, 26), (12, 14, 29), "band"))                   # base ring
    E.append(box((7, 9, 29), (9, 11, 30.5), "iron"))
    E.append(box((6.5, 8.5, 30.5), (9.5, 11.5, 32), "band"))          # cascabel
    # Carriage on the deck behind the wall.
    E.append(box((3, 2, 16.5), (13, 4, 32), "wood"))
    for x0 in (3, 11):
        E.append(box((x0, 4, 16.5), (x0 + 2, 10, 24), "wood"))
        E.append(box((x0, 4, 24), (x0 + 2, 7.5, 32), "wood"))
    for z0 in (18.5, 27.5):
        E.append(box((1.5, 1.5, z0), (14.5, 3.5, z0 + 2), "band"))
    for x0 in (0.5, 13.5):
        for z0 in (16.5, 25.5):
            E.append(box((x0, 0, z0), (x0 + 2, 6, z0 + 6), "tread", faces={"east": "wheel", "west": "wheel"}))
    E.append(box((2.5, 9, 19), (13.5, 11, 21), "band"))               # trunnions
    return E

model = {
    "parent": "minecraft:block/block",
    "ambientocclusion": False,
    "textures": TEX,
    "display": {
        "gui": {"rotation": [30, 135, 0], "translation": [0.6, 0, 0], "scale": [0.42, 0.42, 0.42]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.2, 0.2, 0.2]},
        "fixed": {"rotation": [0, 90, 0], "translation": [0, 0, 0], "scale": [0.4, 0.4, 0.4]},
        "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.25, 0.25, 0.25]},
        "thirdperson_lefthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0], "scale": [0.25, 0.25, 0.25]},
        "firstperson_righthand": {"rotation": [0, 135, 0], "translation": [0, 0, 0], "scale": [0.3, 0.3, 0.3]},
        "firstperson_lefthand": {"rotation": [0, 135, 0], "translation": [0, 0, 0], "scale": [0.3, 0.3, 0.3]},
    },
    "elements": None,
}
out = sys.argv[1]
for name, elements in (("cannon", free_cannon()), ("cannon_mounted", mounted_cannon())):
    for e in elements:
        for c in e["from"] + e["to"]:
            assert -16 <= c <= 32, e
    m = dict(model, elements=elements)
    if name == "cannon_mounted":
        m.pop("display")  # The item uses the free-standing model.
    json.dump(m, open(os.path.join(out, name + ".json"), "w"), indent=1)
    print(name, len(elements), "elements")
