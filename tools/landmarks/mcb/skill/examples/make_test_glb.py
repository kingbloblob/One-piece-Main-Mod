"""Create a synthetic Minecraft-style GLB from a BigBuild, to test mesh_analyze.py.
Faces on exposed voxel sides only, one 16x16 texture tile per block, with optional
rotation / scale / translation applied through the glTF node hierarchy."""
import io, json, struct, sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from photo_tools import BLOCKS

def export_glb(b, path, scale=1.0, rot_y90=0, translate=(0, 0, 0)):
    lo, hi = b.bounds()
    reg = b.get_region(*lo, *hi)
    solid = reg > 1
    pad = np.pad(solid, 1)
    ids = sorted(set(int(v) for v in np.unique(reg[solid])))
    tile_of = {v: i for i, v in enumerate(ids)}
    rng = np.random.default_rng(1)
    atlas = np.zeros((16 * 8, 16 * 8, 3), np.uint8)
    for v, t in tile_of.items():
        name = b.names[v].split(":")[1].split("[")[0]
        col = np.array(BLOCKS.get(name, (150, 150, 150)), float)
        tile = np.clip(col + rng.normal(0, 4, (16, 16, 1)), 0, 255)
        r, c = divmod(t, 8)
        atlas[r * 16:(r + 1) * 16, c * 16:(c + 1) * 16] = tile
    P, N, UV, I = [], [], [], []
    for axis in range(3):
        for sign in (1, -1):
            sh = np.roll(pad, -sign, axis=axis)[1:-1, 1:-1, 1:-1]
            m = solid & ~sh
            cells = np.argwhere(m)
            if not len(cells): continue
            t1, t2 = {0: (1, 2), 1: (2, 0), 2: (0, 1)}[axis]
            if sign < 0: t1, t2 = t2, t1
            base = cells.astype(np.float64)
            if sign > 0: base[:, axis] += 1
            e1 = np.zeros(3); e1[t1] = 1; e2 = np.zeros(3); e2[t2] = 1
            quad = np.stack([base, base + e1, base + e1 + e2, base + e2], axis=1)   # (n,4,3)
            n = len(cells)
            tiles = np.array([tile_of[int(reg[tuple(c)])] for c in cells])
            r, c = tiles // 8, tiles % 8
            u0 = (c * 16 + 1) / 128.0; v0 = (r * 16 + 1) / 128.0; d = 14 / 128.0
            uv = np.stack([np.stack([u0, v0], 1), np.stack([u0 + d, v0], 1),
                           np.stack([u0 + d, v0 + d], 1), np.stack([u0, v0 + d], 1)], axis=1)
            nrm = np.zeros((n, 4, 3)); nrm[:, :, axis] = sign
            off = sum(len(p) for p in P) * 1
            P.append(quad.reshape(-1, 3)); N.append(nrm.reshape(-1, 3)); UV.append(uv.reshape(-1, 2))
            k = (np.arange(n) * 4 + off)[:, None]
            I.append(np.concatenate([k + [0, 1, 2], k + [0, 2, 3]], axis=1).reshape(-1, 3).ravel())
    P = np.concatenate(P).astype(np.float32); N = np.concatenate(N).astype(np.float32)
    UV = np.concatenate(UV).astype(np.float32); I = np.concatenate(I).astype(np.uint32)
    png = io.BytesIO(); Image.fromarray(atlas).save(png, format="PNG"); png = png.getvalue()
    blobs = [P.tobytes(), N.tobytes(), UV.tobytes(), I.tobytes(), png]
    views, off = [], 0
    for bl in blobs:
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(bl)})
        off += len(bl) + (-len(bl)) % 4
    binchunk = b"".join(bl + b"\0" * ((-len(bl)) % 4) for bl in blobs)
    acc = [
        {"bufferView": 0, "componentType": 5126, "count": len(P), "type": "VEC3", "min": P.min(0).tolist(), "max": P.max(0).tolist()},
        {"bufferView": 1, "componentType": 5126, "count": len(N), "type": "VEC3"},
        {"bufferView": 2, "componentType": 5126, "count": len(UV), "type": "VEC2"},
        {"bufferView": 3, "componentType": 5125, "count": len(I), "type": "SCALAR"}]
    q = [0, np.sin(np.pi * rot_y90 / 4), 0, np.cos(np.pi * rot_y90 / 4)]
    g = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}],
         "nodes": [{"children": [1], "scale": [scale, scale, scale], "translation": list(translate)},
                   {"mesh": 0, "rotation": q}],
         "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0}]}],
         "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
         "textures": [{"source": 0}], "images": [{"bufferView": 4, "mimeType": "image/png"}],
         "accessors": acc, "bufferViews": views, "buffers": [{"byteLength": len(binchunk)}]}
    js = json.dumps(g).encode(); js += b" " * ((-len(js)) % 4)
    with open(path, "wb") as f:
        total = 12 + 8 + len(js) + 8 + len(binchunk)
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(binchunk), 0x004E4942) + binchunk)
    return solid.sum(), lo, hi

if __name__ == "__main__":
    from mcbig import BigBuild
    import mcparts as P
    b = BigBuild(y_min=0, y_max=60, seed=3)
    S, D, T, R, F = "minecraft:stone_bricks", "minecraft:deepslate_bricks", "minecraft:polished_andesite", "minecraft:dark_oak_planks", "minecraft:oak_planks"
    b.box(0, 0, 0, 44, 1, 36, "minecraft:andesite")                         # base
    b.hollow_box(4, 2, 4, 40, 14, 32, S)                                    # curtain/keep shell
    b.box(16, 2, 14, 28, 20, 22, S)                                         # thick solid keep (hidden interior)
    for x, z in [(4, 4), (40, 4), (4, 32), (40, 32)]:                        # corner towers
        b.cylinder(x, 2, z, 4, 20, D, hollow=True); b.tapered_cylinder(x, 21, z, 29, 5, 0, R)
    for x in range(8, 40, 6):                                                # buttresses along the south wall
        b.box(x, 2, 33, x + 1, 9, 34, T)
    for x in range(7, 39, 5):                                                # arched windows (air)
        b.clear(x, 6, 4, x + 1, 9, 4)
    b.fill(4, 15, 4, 40, 15, 32, F)
    for i in range(10):                                                      # stepped roof of full blocks
        b.fill(4 + i, 16 + i, 4, 40 - i, 16 + i, 32, R) if False else b.fill(4, 16 + i, 4 + i, 40, 16 + i, 32 - i, R)
    solid, lo, hi = export_glb(b, "/tmp/test_castle.glb", scale=0.37, rot_y90=1, translate=(5, -3, 2))
    print("test model:", int(solid), "solid voxels, bounds", lo, hi)
    export_glb(b, "/tmp/test_castle_plain.glb")
    np.save("/tmp/test_castle_truth.npy", (b.get_region(*lo, *hi) > 1))
