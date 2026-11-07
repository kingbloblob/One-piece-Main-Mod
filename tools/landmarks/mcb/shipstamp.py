"""Put the mod's show-accurate ship templates (tools/ships -> data/onepiece/structure/ships/<id>.nbt) into a build,
so harbours and battles use the real Going Merry / Marine warship / Red Force models instead of a quick hull
(ryan's batch 4 feedback: no basic ships).

    from mcb.shipstamp import stamp_ship
    stamp_ship(bb, "marine_warship", x, z, water_y=0, rot=1)   # bow east by default; rot = 90 deg clockwise turns

The template is read straight from the .nbt (gzip NBT, palette + blocks). Its waterline (from ships/<id>.json) is set
on water_y. Chests become barrels (template chests carry loot NBT the landmark pipeline can't copy)."""
import gzip
import json
import os
import struct

from mcbig import BigBuild, transform_block

RES = os.environ.get("SHIP_RES", "/mnt/project-files/one-piece-mod/source/src/main/resources/data/onepiece")
_CACHE = {}


def _read_nbt(path):
    data = gzip.open(path).read()
    pos = [0]

    def rd(fmt):
        v = struct.unpack_from(">" + fmt, data, pos[0])
        pos[0] += struct.calcsize(">" + fmt)
        return v[0]

    def rstr():
        n = rd("H")
        s = data[pos[0]:pos[0] + n].decode("utf-8", "replace")
        pos[0] += n
        return s

    def payload(t):
        if t == 1: return rd("b")
        if t == 2: return rd("h")
        if t == 3: return rd("i")
        if t == 4: return rd("q")
        if t == 5: return rd("f")
        if t == 6: return rd("d")
        if t == 7:
            n = rd("i"); v = data[pos[0]:pos[0] + n]; pos[0] += n; return v
        if t == 8: return rstr()
        if t == 9:
            et = rd("b"); n = rd("i"); return [payload(et) for _ in range(n)]
        if t == 10:
            d = {}
            while True:
                tt = rd("b")
                if tt == 0: return d
                k = rstr(); d[k] = payload(tt)
        if t == 11:
            n = rd("i"); return [rd("i") for _ in range(n)]
        if t == 12:
            n = rd("i"); return [rd("q") for _ in range(n)]
        raise ValueError(f"nbt tag {t}")
    t = rd("b"); rstr()
    return payload(t)


def load(sid, res=RES):
    """(blocks {(x, y, z): state}, size, waterline) of a ship template; bow = +x."""
    if sid in _CACHE:
        return _CACHE[sid]
    nbt = _read_nbt(os.path.join(res, "structure", "ships", sid + ".nbt"))
    meta = json.load(open(os.path.join(res, "ships", sid + ".json")))
    pal = []
    for p in nbt["palette"]:
        name = p.get("Name") or p.get("id")
        props = p.get("Properties") or p.get("properties") or {}
        pal.append(name + ("[" + ",".join(f"{k}={v}" for k, v in sorted(props.items())) + "]" if props else ""))
    blocks = {}
    for b in nbt["blocks"]:
        s = pal[b["state"]]
        if s.startswith(("minecraft:air", "minecraft:structure_void")):
            continue
        if s.startswith("minecraft:chest") or s.startswith("minecraft:trapped_chest"):
            s = "minecraft:barrel[facing=up,open=false]"
        blocks[tuple(b["pos"])] = s
    out = (blocks, nbt["size"], float(meta.get("waterline", 2)), meta.get("bow", "east"))
    _CACHE[sid] = out
    return out


def stamp_ship(bb, sid, x, z, water_y=0, rot=0, res=RES):
    """Stamp ship `sid` with its hull centre at (x, z) and its waterline at water_y. rot turns it clockwise (seen from
    above) in 90 degree steps from bow-east. Returns the footprint (x1, z1, x2, z2)."""
    blocks, size, wl, bow = load(sid, res)
    sx, sy, sz = size
    m = BigBuild(seed=1, y_min=-2, y_max=sy + 2)
    for (bx, by, bz), s in blocks.items():
        m.set(bx, by, bz, s)
    # the template's waterline is `wl` blocks above its y 0; the centre of its footprint lands on (x, z)
    y0 = water_y - int(round(wl)) + 1
    cx, cz = (sx - 1) / 2, (sz - 1) / 2
    corners = []
    for (px, pz) in ((0, 0), (sx - 1, 0), (0, sz - 1), (sx - 1, sz - 1)):
        rx, rz = px - cx, pz - cz
        for _ in range(rot % 4):
            rx, rz = -rz, rx
        corners.append((rx, rz))
    mx, mz = min(c[0] for c in corners), min(c[1] for c in corners)
    ox, oz = int(round(x + mx)), int(round(z + mz))
    # stamp() rotates around the source origin; shift so the rotated box starts at (ox, oz)
    rc = []
    for (px, pz) in ((0, 0), (sx - 1, 0), (0, sz - 1), (sx - 1, sz - 1)):
        for _ in range(rot % 4):
            px, pz = -pz, px
        rc.append((px, pz))
    bb.stamp(m, ox - min(c[0] for c in rc), y0, oz - min(c[1] for c in rc), rot=rot % 4, include_air=False)
    w, d = (sx, sz) if rot % 2 == 0 else (sz, sx)
    return (ox, oz, ox + w - 1, oz + d - 1)
