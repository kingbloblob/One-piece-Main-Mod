"""Paints the ship-combat textures: the enemy pirate skins and the Boarding Hook icon.

Run:  PYTHONDONTWRITEBYTECODE=1 python3 gen_textures.py [path to source/] [--preview out.png]
Writes assets/onepiece/textures/entity/sea_pirate/<0-3>.png (3 = Pirate Captain)
and assets/onepiece/textures/item/boarding_hook.png.
Pirate looks use the same outfit keys as tools/skins/gen_skins.py (see tools/skins/outfits.py).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'skins'))
from PIL import Image
from outfits import build
from skinkit import preview
from gen_skins import LIGHT, TAN, BROWN, DARK, front_mark, JOLLY

SRC = next((a for a in sys.argv[1:] if not a.startswith('--') and not a.endswith('.png')),
           '/mnt/project-files/one-piece-mod/source')
ASSETS = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures')

PIRATES = {
    '0': dict(skin=TAN, hair='#2a1a10', hair_style='short', face=['stubble'],
              hat=dict(kind='bandana', color='#b02020'),
              top=dict(kind='shirt', color='#e8e0c8', pattern='stripes', patcol='#2a2a2a', sleeves='short'),
              pants=dict(color='#4a3a2a'), shoes=dict(kind='boot', color='#2a1a10'), sash=('#a02a2a', 8, 2)),
    '1': dict(skin=BROWN, hair='#1a1a1a', hair_style='buzz', face=['beard'],
              hat=dict(kind='bandana', color='#2a2a2a'),
              top=dict(kind='v', color='#5a3a2a', sleeves='short'),
              pants=dict(color='#2a2a3a', length='capri'), shoes=dict(kind='sandal', color='#5a3a20'),
              post=[front_mark('body', JOLLY, '#e8e8e8')]),
    '2': dict(skin=LIGHT, hair='#8a5a2a', hair_style='wavy', face=['stubble'],
              hat=dict(kind='cap', color='#3a3a2a'),
              top=dict(kind='shirt', color='#6a7a5a', sleeves='long'),
              pants=dict(color='#3a2a1a'), shoes=dict(kind='boot', color='#1a1a1a'), gloves='#4a3a2a'),
    '3': dict(skin=DARK, hair='#1a1a1a', hair_style='long', hair_len=4, face=['beard'],
              hat=dict(kind='top', color='#1a1a1a', color2='#e8c040'),
              top=dict(kind='suit', color='#6a1a1a', color2='#f4f4f4', color3='#e8c040'),
              coat=dict(kind='long', color='#2a1a1a', length=9),
              pants=dict(color='#1a1a1a'), shoes=dict(kind='boot', color='#3a2a1a'),
              post=[front_mark('body', JOLLY, '#f0f0f0')]),
}


def hook_icon(path):
    """A grey iron grapnel with three prongs and a rope coil, 16x16."""
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = img.load()
    iron, dark, light = (150, 156, 166, 255), (80, 84, 94, 255), (210, 214, 222, 255)
    rope, rope_dark = (196, 160, 104, 255), (140, 104, 60, 255)
    # Shaft from bottom-left to top-right.
    for i in range(3, 12):
        px[i, 15 - i] = iron
        px[i + 1, 15 - i] = dark
    # Prongs at the top right.
    for x, y in [(12, 1), (13, 1), (14, 2), (14, 3), (11, 2), (10, 1), (9, 1), (13, 5), (14, 6), (13, 4), (12, 3)]:
        px[x, y] = iron
    for x, y in [(13, 0), (8, 1), (14, 7)]:
        px[x, y] = light
    # Rope coil at the bottom left.
    for x, y in [(0, 12), (1, 11), (2, 11), (3, 12), (3, 13), (2, 14), (1, 14), (0, 13),
                 (1, 13), (2, 12), (4, 14), (5, 15), (2, 15)]:
        px[x, y] = rope if (x + y) % 2 else rope_dark
    img.save(path)


def main():
    out = os.path.join(ASSETS, 'entity', 'sea_pirate')
    os.makedirs(out, exist_ok=True)
    previews = []
    for i, (pid, spec) in enumerate(PIRATES.items()):
        img = build(spec, seed=7000 + i * 13).finish(os.path.join(out, pid + '.png'))
        previews.append(preview(img, 3))
    hook_icon(os.path.join(ASSETS, 'item', 'boarding_hook.png'))
    if '--preview' in sys.argv:
        dest = sys.argv[sys.argv.index('--preview') + 1]
        w, h = previews[0].size
        sheet = Image.new('RGBA', (len(previews) * w, h), (40, 40, 48, 255))
        for k, p in enumerate(previews):
            sheet.alpha_composite(p, (k * w, 0))
        sheet.save(dest)
    print('painted %d pirate skins and the boarding hook' % len(previews))


if __name__ == '__main__':
    main()
