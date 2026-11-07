"""Pixel textures for the ship upgrade items, special cannon ammo and the Cola Engine block.
Usage: python3 gen_ship_items.py <resources/assets/onepiece/textures dir> <vanilla textures dir>"""
import sys, os
from PIL import Image, ImageDraw

OUT, VAN = sys.argv[1], sys.argv[2]
def van(p): return Image.open(os.path.join(VAN, p)).convert('RGBA')
def new(): return Image.new('RGBA', (16, 16), (0, 0, 0, 0))
def save(im, path):
    os.makedirs(os.path.dirname(os.path.join(OUT, path)), exist_ok=True)
    im.save(os.path.join(OUT, path))

def ball(d, cx, cy, r, base=(58, 60, 66), hi=(120, 124, 132), lo=(26, 27, 31)):
    for y in range(16):
        for x in range(16):
            dx, dy = x + .5 - cx, y + .5 - cy
            if dx * dx + dy * dy <= r * r:
                c = base
                if dx + dy < -r * .6: c = hi
                elif dx + dy > r * .7: c = lo
                d.point((x, y), fill=c + (255,))

# Chain shot: two balls joined by a chain.
im = new(); d = ImageDraw.Draw(im)
for i, (x, y) in enumerate([(5, 6), (6, 7), (7, 8), (8, 8), (9, 9), (10, 10)]):
    d.point((x, y), fill=(150, 152, 160, 255) if i % 2 == 0 else (90, 92, 100, 255))
ball(d, 4, 4, 3.6); ball(d, 12, 12, 3.6)
save(im, 'item/chain_shot.png')

# Fire shot: a cannonball wrapped in burning pitch.
im = new(); d = ImageDraw.Draw(im)
ball(d, 8, 9.5, 5.6, base=(70, 40, 30), hi=(150, 80, 40), lo=(30, 18, 14))
flame = [(6, 2, (255, 220, 90)), (9, 1, (255, 200, 70)), (11, 3, (255, 160, 40)), (4, 4, (255, 150, 40)),
         (7, 3, (255, 120, 30)), (10, 4, (240, 90, 20)), (8, 2, (255, 240, 150)), (5, 3, (250, 130, 30)), (12, 5, (230, 80, 20))]
for x, y, c in flame: d.point((x, y), fill=c + (255,))
for x in range(4, 13): d.point((x, 5), fill=(240, 100, 25, 255) if x % 2 else (255, 170, 50, 255))
save(im, 'item/fire_shot.png')

# Grapeshot: a canvas bag of iron balls tied with string.
im = new(); d = ImageDraw.Draw(im)
d.ellipse((2, 4, 13, 15), fill=(196, 178, 140, 255), outline=(120, 100, 70, 255))
d.line((6, 4, 9, 4), fill=(230, 230, 230, 255)); d.line((7, 2, 8, 3), fill=(230, 230, 230, 255))
for cx, cy in [(5.5, 8.5), (9.5, 8.5), (7.5, 11.5), (11, 12), (4.5, 12)]:
    ball(d, cx, cy, 1.6)
save(im, 'item/grapeshot.png')

# Iron Hull Plating: a riveted iron plate over planks.
im = new(); d = ImageDraw.Draw(im)
planks = van('block/oak_planks.png')
im.paste(planks.crop((0, 0, 16, 16)).resize((16, 16)), (0, 0))
d.rectangle((2, 2, 13, 13), fill=(176, 180, 186, 255), outline=(92, 96, 104, 255))
d.line((3, 3, 12, 3), fill=(220, 224, 230, 255))
for x, y in [(4, 4), (11, 4), (4, 11), (11, 11), (7, 4), (7, 11)]:
    d.point((x, y), fill=(70, 72, 80, 255))
mask = new(); ImageDraw.Draw(mask).polygon([(1, 1), (14, 1), (14, 14), (1, 14)], fill=(255, 255, 255, 255))
save(im, 'item/hull_plating.png')

# Reinforced Sailcloth: a folded white sail with stitched seams.
im = new(); d = ImageDraw.Draw(im)
d.polygon([(2, 3), (13, 2), (14, 13), (3, 14)], fill=(236, 232, 220, 255), outline=(150, 140, 120, 255))
for y in (6, 10): d.line((3, y, 13, y - 1), fill=(170, 150, 110, 255))
for x in (5, 9, 12): d.point((x, 6 if x < 10 else 5), fill=(110, 80, 50, 255)); d.point((x, 10 if x < 10 else 9), fill=(110, 80, 50, 255))
d.line((8, 2, 8, 14), fill=(214, 208, 196, 255))
save(im, 'item/reinforced_sailcloth.png')

# Heavy Gun Carriage: a black cannon barrel on a wooden carriage with wheels.
im = new(); d = ImageDraw.Draw(im)
d.rectangle((3, 8, 12, 10), fill=(120, 80, 45, 255), outline=(70, 45, 25, 255))
d.polygon([(2, 5), (13, 3), (14, 6), (3, 8)], fill=(50, 52, 58, 255), outline=(24, 25, 28, 255))
d.line((4, 5, 12, 4), fill=(110, 114, 122, 255))
for cx in (5, 11):
    d.ellipse((cx - 2, 10, cx + 2, 14), fill=(96, 62, 34, 255), outline=(50, 32, 18, 255)); d.point((cx, 12), fill=(30, 30, 30, 255))
save(im, 'item/heavy_gun_carriage.png')

# Cola Engine (block): riveted iron with a cola-red window and pressure gauge; top has a valve.
side = van('block/iron_block.png').copy(); d = ImageDraw.Draw(side)
d.rectangle((3, 3, 12, 9), fill=(40, 22, 14, 255), outline=(70, 72, 80, 255))
for y in range(5, 9): d.line((4, y, 11, y), fill=(120 + y * 8, 36, 20, 255))
d.line((4, 4, 11, 4), fill=(230, 210, 180, 255))
d.ellipse((5, 10, 10, 15), fill=(235, 235, 225, 255), outline=(60, 60, 64, 255)); d.line((7, 12, 9, 11), fill=(200, 30, 30, 255))
for x, y in [(1, 1), (14, 1), (1, 14), (14, 14)]: d.point((x, y), fill=(80, 82, 90, 255))
save(side, 'block/cola_engine_side.png')
top = van('block/iron_block.png').copy(); d = ImageDraw.Draw(top)
d.ellipse((3, 3, 12, 12), fill=(90, 92, 100, 255), outline=(50, 52, 58, 255))
d.ellipse((6, 6, 9, 9), fill=(190, 40, 30, 255)); d.line((7, 2, 8, 13), fill=(60, 62, 70, 255))
save(top, 'block/cola_engine_top.png')
print('ok')
