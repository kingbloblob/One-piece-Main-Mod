"""Build landmark structures: python3 make.py <id>... [--render-only] [--no-render] [--sheet] [--out=DIR]
--sheet also writes <id>_sheet.png, all views on one 1000 px image: look at that one instead of the separate renders.
Renders previews into /mnt/project-files/one-piece-mod/previews/landmarks/ and writes the jigsaw tiles."""
import importlib, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render, tiler, pipeline
OUT = "/mnt/project-files/one-piece-mod/previews/landmarks"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
only_render = "--render-only" in sys.argv
sheet = "--sheet" in sys.argv
SHEET_W = 1000  # px; keep it small, a bigger picture costs more tokens and shows little more


def contact_sheet(paths, dest, width=SHEET_W):
    """Tile the renders two per row into one image at most `width` px wide; returns the path."""
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths if os.path.exists(p)]
    cw = width // 2
    ims = [im.resize((cw, max(1, im.height * cw // im.width))) for im in ims]
    rows = [ims[i:i + 2] for i in range(0, len(ims), 2)]
    hs = [max(im.height for im in r) for r in rows]
    s = Image.new("RGB", (width, sum(hs)), (255, 255, 255))
    y = 0
    for r, h in zip(rows, hs):
        for i, im in enumerate(r): s.paste(im, (i * cw, y))
        y += h
    s.save(dest)
    return dest
no_render = "--no-render" in sys.argv
out = OUT
res = tiler.RES
for a in sys.argv:
    if a.startswith("--out="): out = a[6:]
    if a.startswith("--res="): res = a[6:]
for sid in args:
    t = time.time()
    m, b, ground, mode, fr = pipeline.prepare(sid, "--no-finish" not in sys.argv)
    print(sid, mode, " ".join(f"{k}={v}" for k, v in sorted(fr.items())))
    from mcb.bridge import check_ids
    bad = check_ids(b)
    if bad: print(sid, "UNKNOWN BLOCK IDS (would be missing in game):", bad)
    opts = getattr(m, "TILER", {})
    title = getattr(m, "TITLE", sid)
    blocks = b.blocks
    wy = getattr(m, "WATER_Y", None)
    if wy is not None:  # show the sea around it in the pictures only
        blocks = dict(b.blocks)
        xs = [p[0] for p in blocks]; zs = [p[2] for p in blocks]
        for x in range(min(xs) - 6, max(xs) + 7):
            for z in range(min(zs) - 6, max(zs) + 7):
                if (x, wy, z) not in blocks: blocks[(x, wy, z)] = "minecraft:water[level=0]"
    b2 = type("V", (), {})(); b2.blocks = blocks
    if not no_render: render.render(blocks, f"{out}/{sid}_se.png", "se", title=title + " (from the south-east)")
    if not no_render: render.render(blocks, f"{out}/{sid}_nw.png", "nw", title=title + " (from the north-west)")
    for cut in ([] if no_render else getattr(m, "CUTS", [])):
        render.render(blocks, f"{out}/{sid}_cut{cut}.png", "se", cut=cut, title=f"{title}: inside, cut at height {cut}")
    if sheet and not no_render:  # one small image to look at instead of 3+ big ones (each viewed image costs tokens)
        shots = [f"{out}/{sid}_se.png", f"{out}/{sid}_nw.png"] + [f"{out}/{sid}_cut{c}.png" for c in getattr(m, "CUTS", [])]
        print(sid, "sheet:", contact_sheet(shots, f"{out}/{sid}_sheet.png"))
    info = ""
    if not only_render:
        # never let the world waterlog a build: a ship's chests, ladders and lanterns below the waterline, a lamp at
        # sea level or the props inside Fish-Man Island's air bubble would turn into water sources and flood it.
        # finish.waterlog() waterlogs what really sits in water (hull planks, posts in a pool, sunken wrecks).
        liquid = "ignore_waterlogging"
        info = tiler.write(sid, b, ground, res=res, liquid=liquid, **opts)
    print(sid, len(b.blocks), "blocks", info, f"{time.time() - t:.1f}s")
