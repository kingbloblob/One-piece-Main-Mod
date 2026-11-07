"""photo_tools: cheap ways to mine reference photos.

CLI:
  python photo_tools.py crop    photo.png out.png --box 0.4 0.2 0.7 0.5 [--max-side 512]
  python photo_tools.py palette photo.png [--box x0 y0 x1 y1] [--k 6] [--top 3]

crop    zooms into a region (box as fractions 0-1 or pixels) so one detail can be
        inspected at a few hundred tokens instead of re-viewing the whole photo.
palette finds the dominant colours of a photo or region and lists the nearest Minecraft
        blocks for each (approximate average block colours; always sanity-check by eye).
"""
import argparse

from PIL import Image

# Approximate average RGB of common blocks (rough; for matching, not exact).
BLOCKS = {
    "stone": (125, 125, 125), "cobblestone": (127, 127, 127), "stone_bricks": (122, 121, 122),
    "mossy_stone_bricks": (115, 121, 105), "andesite": (136, 136, 136),
    "polished_andesite": (132, 134, 133), "diorite": (188, 188, 188),
    "polished_diorite": (193, 193, 195), "granite": (149, 103, 85),
    "polished_granite": (154, 106, 89), "smooth_stone": (158, 158, 158),
    "deepslate": (80, 80, 83), "deepslate_bricks": (70, 70, 71), "deepslate_tiles": (54, 54, 55),
    "blackstone": (42, 36, 41), "polished_blackstone_bricks": (48, 43, 50),
    "tuff": (108, 109, 102), "basalt": (73, 72, 77), "calcite": (223, 224, 220),
    "sandstone": (216, 203, 155), "smooth_sandstone": (223, 214, 170),
    "red_sandstone": (181, 98, 31), "bricks": (150, 97, 83), "mud_bricks": (137, 104, 79),
    "red_nether_bricks": (69, 7, 9), "nether_bricks": (44, 21, 26),
    "quartz_block": (236, 230, 223), "smooth_quartz": (235, 229, 222),
    "end_stone_bricks": (218, 224, 162), "purpur_block": (169, 125, 169),
    "white_concrete": (207, 213, 214), "light_gray_concrete": (125, 125, 115),
    "gray_concrete": (54, 57, 61), "black_concrete": (8, 10, 15), "brown_concrete": (96, 60, 32),
    "red_concrete": (142, 33, 33), "orange_concrete": (224, 97, 0), "yellow_concrete": (240, 175, 21),
    "lime_concrete": (94, 168, 24), "green_concrete": (73, 91, 36), "cyan_concrete": (21, 119, 136),
    "light_blue_concrete": (36, 137, 199), "blue_concrete": (44, 46, 143),
    "purple_concrete": (100, 31, 156), "magenta_concrete": (169, 48, 159), "pink_concrete": (213, 101, 142),
    "white_terracotta": (209, 178, 161), "orange_terracotta": (161, 83, 37), "terracotta": (152, 94, 67),
    "red_terracotta": (143, 61, 46), "brown_terracotta": (77, 51, 36), "yellow_terracotta": (186, 133, 35),
    "light_blue_terracotta": (113, 108, 137), "cyan_terracotta": (86, 91, 91),
    "blue_terracotta": (74, 60, 91), "gray_terracotta": (57, 42, 35), "light_gray_terracotta": (135, 106, 97),
    "oak_planks": (162, 130, 78), "spruce_planks": (114, 84, 48), "birch_planks": (192, 175, 121),
    "dark_oak_planks": (66, 43, 20), "acacia_planks": (168, 90, 50), "jungle_planks": (160, 115, 81),
    "cherry_planks": (226, 178, 172), "mangrove_planks": (117, 54, 48), "bamboo_planks": (193, 173, 80),
    "copper_block": (192, 107, 80), "exposed_copper": (161, 125, 103),
    "weathered_copper": (108, 153, 110), "oxidized_copper": (82, 162, 132),
    "prismarine": (99, 171, 158), "dark_prismarine": (51, 91, 75), "warped_planks": (43, 104, 99),
    "water": (50, 100, 205), "ice": (145, 183, 253), "blue_ice": (116, 167, 253),
    "packed_ice": (141, 180, 250), "snow_block": (249, 254, 254), "lapis_block": (31, 67, 140),
    "grass_block": (115, 150, 70), "moss_block": (89, 109, 45), "dirt": (134, 96, 67),
    "sand": (219, 207, 163), "gravel": (131, 127, 126), "mud": (60, 57, 60),
    "iron_block": (220, 220, 220), "gold_block": (249, 236, 79), "hay_block": (166, 139, 12),
    "glowstone": (171, 131, 84), "sea_lantern": (172, 199, 190), "shroomlight": (240, 144, 70),
}


def _box_px(img, box):
    if not box:
        return (0, 0, img.width, img.height)
    x0, y0, x1, y1 = box
    if max(box) <= 1.0:
        x0, x1 = x0 * img.width, x1 * img.width
        y0, y1 = y0 * img.height, y1 * img.height
    return tuple(int(v) for v in (x0, y0, x1, y1))


def crop(src, out, box, max_side=512):
    im = Image.open(src).convert("RGB").crop(_box_px(Image.open(src), box))
    s = max_side / max(im.size)
    if s != 1:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    im.save(out)
    return out


def nearest_blocks(rgb, top=3):
    r, g, b = rgb
    # weighted distance (eyes are more sensitive to green)
    d = sorted(BLOCKS.items(), key=lambda kv: 2 * (kv[1][0] - r) ** 2 + 4 * (kv[1][1] - g) ** 2 + 3 * (kv[1][2] - b) ** 2)
    return [k for k, _ in d[:top]]


def palette(src, box=None, k=6, top=3):
    img = Image.open(src).convert("RGB")
    img = img.crop(_box_px(img, box))
    img.thumbnail((200, 200))
    q = img.quantize(colors=k, method=Image.MEDIANCUT)
    pal = q.getpalette()[: 3 * k]
    counts = sorted(q.getcolors(), reverse=True)
    total = sum(c for c, _ in counts)
    rows = []
    for c, idx in counts:
        rgb = tuple(pal[3 * idx: 3 * idx + 3])
        rows.append(("#%02x%02x%02x" % rgb, round(100 * c / total), nearest_blocks(rgb, top)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crop"); c.add_argument("src"); c.add_argument("out")
    c.add_argument("--box", nargs=4, type=float, required=True); c.add_argument("--max-side", type=int, default=512)
    p = sub.add_parser("palette"); p.add_argument("src")
    p.add_argument("--box", nargs=4, type=float); p.add_argument("--k", type=int, default=6)
    p.add_argument("--top", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "crop":
        print(crop(a.src, a.out, a.box, a.max_side))
    else:
        for hexc, pct, blocks in palette(a.src, a.box, a.k, a.top):
            print(f"{hexc}  {pct:3d}%  " + ", ".join(blocks))


if __name__ == "__main__":
    main()
