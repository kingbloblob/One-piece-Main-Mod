"""Paints the extra crewmate outfits: two more kinds of recruit for every job.

Run:  python3 gen_crew_variants.py [path to source/] [--preview out.png]
Writes assets/onepiece/textures/entity/crewmate/<role>_1.png and <role>_2.png.
Kind 0 (<role>.png) is painted by gen_skins.py. The kinds are described in CrewVariant.java:
  _1 = quick and hard-hitting, _2 = a tough veteran.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from outfits import build
from skinkit import preview

SRC = next((a for a in sys.argv[1:] if not a.startswith('--') and not a.endswith('.png')),
           '/mnt/project-files/one-piece-mod/source')
TEX = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/entity/crewmate')

LIGHT, FAIR, TAN, BROWN, DARK = '#f2c9a0', '#f6d6b8', '#dca478', '#b07a50', '#7a5238'
FISHMAN = '#5a8ac8'

VARIANTS = {
    # Swordsman: Fencer (quick) and Brute (tough).
    'swordsman_1': dict(skin=FAIR, hair='#e8e0d0', hair_style='pony', face=['earring_l'],
                        top=dict(kind='shirt', color='#f4f4f4', sleeves='long'), sash=('#2a2a6a', 8, 2),
                        pants=dict(color='#2a2a3a'), shoes=dict(kind='boot', color='#3a2a1a'),
                        coat=dict(kind='long', color='#7a1a2a', length=9)),
    'swordsman_2': dict(skin=DARK, hair='#1a1a1a', hair_style='bald', face=['scar_eye_l', 'beard'],
                        top=dict(kind='kimono', color='#5a3a2a', color2=DARK), sash=('#2a2a2a', 8, 2),
                        pants=dict(color='#3a3a3a'), shoes=dict(kind='geta', color='#4a3a2a')),
    # Navigator: Sky Reader and Old Sea Dog.
    'navigator_1': dict(skin=TAN, hair='#3a6ae0', hair_style='bangs', face=['goggles'],
                        top=dict(kind='hoodie', color='#e8e8f0', sleeves='long'), pants=dict(color='#5a5a7a'),
                        shoes=dict(kind='boot', color='#3a3a4a')),
    'navigator_2': dict(skin=LIGHT, hair='#c8c8c8', hair_style='short', face=['mustache', 'glasses'],
                        hat=dict(kind='tricorn', color='#2a2a3a', color2='#e8c040'),
                        top=dict(kind='suit', color='#2a3a5a', color2='#f4f4f4', color3='#e8c040'),
                        pants=dict(color='#2a2a3a'), shoes=dict(kind='boot', color='#1a1a1a')),
    # Sniper: Trickster and Hunter.
    'sniper_1': dict(skin=LIGHT, hair='#e0a020', hair_style='spiky', face=['grin', 'big_nose_red'],
                     hat=dict(kind='bandana', color='#e03030'),
                     top=dict(kind='v', color='#e8c040', sleeves='short'), pants=dict(color='#3a6a3a', length='capri'),
                     shoes=dict(kind='sandal', color='#6a4a2a')),
    'sniper_2': dict(skin=TAN, hair='#4a3a2a', hair_style='long', hair_len=4, face=['beard'],
                     hat=dict(kind='cowboy', color='#5a4a2a', color2='#3a2a1a'),
                     top=dict(kind='shirt', color='#4a5a2a', sleeves='long'), pants=dict(color='#5a4a3a'),
                     shoes=dict(kind='boot', color='#2a1a1a'), coat=dict(kind='long', color='#6a5a3a', length=10)),
    # Cook: Kick Chef and Galley Boss.
    'cook_1': dict(skin=FAIR, hair='#f0d050', hair_style='side', face=['cigarette'],
                   top=dict(kind='suit', color='#1a1a22', color2='#f4f4f4', color3='#2a4a9a'),
                   pants=dict(color='#1a1a22'), shoes=dict(kind='shoe', color='#2a2a2a')),
    'cook_2': dict(skin=BROWN, hair='#2a2a2a', hair_style='buzz', face=['mustache'],
                   hat=dict(kind='top', color='#f8f8f8', color2='#f8f8f8'),
                   top=dict(kind='shirt', color='#f4f4f4', sleeves='short'), pants=dict(color='#5a3a2a'),
                   shoes=dict(kind='boot', color='#2a1a1a'), sash=('#c03030', 7, 3)),
    # Doctor: Field Surgeon and Old Healer.
    'doctor_1': dict(skin=TAN, hair='#1a1a1a', hair_style='short', face=['dark_circles'],
                     hat=dict(kind='fur', color='#f0f0f0', color2='#2a2a2a'),
                     top=dict(kind='hoodie', color='#e8c040', sleeves='long'), pants=dict(color='#3a3a3a'),
                     shoes=dict(kind='boot', color='#1a1a1a')),
    'doctor_2': dict(skin=FAIR, hair='#e8e8e8', hair_style='long', hair_len=6, face=['glasses', 'beard'],
                     top=dict(kind='robe', color='#6a8a5a', sleeves='long'), pants=dict(color='#4a5a3a'),
                     shoes=dict(kind='sandal', color='#6a4a2a'), coat=dict(kind='long', color='#f4f4f4', length=11)),
    # Shipwright: Tinkerer and Iron Builder.
    'shipwright_1': dict(skin=LIGHT, hair='#3ab0e0', hair_style='pomp', face=['sunglasses'],
                         top=dict(kind='shirt', color='#e04080', sleeves='short', pattern='stripes', patcol='#f0a0c0'),
                         pants=dict(color='#3a3a6a', length='capri'), shoes=dict(kind='sandal', color='#5a3a2a')),
    'shipwright_2': dict(skin=DARK, hair='#2a2a2a', hair_style='buzz', face=['goatee'],
                         hat=dict(kind='helmet', color='#8a8a8a', color2='#5a5a5a'),
                         top=dict(kind='shirt', color='#5a6a7a', sleeves='long'), pants=dict(color='#3a4a5a'),
                         shoes=dict(kind='boot', color='#2a2a2a'), gloves='#4a4a4a'),
    # Archaeologist: Treasure Hunter and Professor.
    'archaeologist_1': dict(skin=BROWN, hair='#1a1a2a', hair_style='pony', face=['earring_l'],
                            hat=dict(kind='bandana', color='#8a2a8a'),
                            top=dict(kind='v', color='#e8d8b0', sleeves='short'), pants=dict(color='#5a4a2a'),
                            shoes=dict(kind='boot', color='#3a2a1a'), sash=('#8a2a8a', 8, 1)),
    'archaeologist_2': dict(skin=LIGHT, hair='#a0a0a0', hair_style='short', face=['glasses', 'mustache'],
                            hat=dict(kind='top', color='#3a2a1a', color2='#6a4a2a'),
                            top=dict(kind='suit', color='#6a4a2a', color2='#f4f4f4', color3='#2a5a2a'),
                            pants=dict(color='#4a3a2a'), shoes=dict(kind='shoe', color='#2a1a1a')),
    # Musician: Drummer and Soul Singer.
    'musician_1': dict(skin=TAN, hair='#e03030', hair_style='spiky', face=['grin'],
                       top=dict(kind='none', color=TAN), sash=('#2a2a2a', 9, 1),
                       pants=dict(color='#2a2a3a', pattern='stripes', patcol='#e03030'),
                       shoes=dict(kind='boot', color='#1a1a1a')),
    'musician_2': dict(skin='#e8e8e0', hair='#141414', hair_style='afro', face=['sunglasses'],
                       hat=dict(kind='top', color='#141414', color2='#c02020'),
                       top=dict(kind='suit', color='#141414', color2='#f4f4f4', color3='#c02020'),
                       pants=dict(color='#141414'), shoes=dict(kind='shoe', color='#141414'),
                       coat=dict(kind='long', color='#1a1a1a', length=10)),
    # Helmsman: Fish-man Swimmer and Old Captain.
    'helmsman_1': dict(skin=FISHMAN, hair='#141414', hair_style='long', hair_len=5, eyes='#e0c040',
                       top=dict(kind='kimono', color='#e8a040', color2=FISHMAN), sash=('#2a2a2a', 8, 2),
                       pants=dict(color='#2a2a3a'), shoes=dict(kind='geta', color='#3a2a1a')),
    'helmsman_2': dict(skin=LIGHT, hair='#f0f0f0', hair_style='short', face=['beard'],
                       hat=dict(kind='cap', color='#f4f4f4'),
                       top=dict(kind='suit', color='#2a3a6a', color2='#f4f4f4', color3='#e8c040'),
                       pants=dict(color='#2a3a6a'), shoes=dict(kind='boot', color='#1a1a1a'),
                       coat=dict(kind='long', color='#2a3a6a', length=10)),
}


def main():
    os.makedirs(TEX, exist_ok=True)
    previews = []
    for j, (cid, spec) in enumerate(VARIANTS.items()):
        img = build(spec, seed=5000 + j * 31).finish(os.path.join(TEX, cid + '.png'))
        previews.append(preview(img, 3))
    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        cols = 6
        w, h = previews[0].size
        rows = (len(previews) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * w, rows * h), (40, 40, 48, 255))
        for k, p in enumerate(previews):
            sheet.alpha_composite(p, ((k % cols) * w, (k // cols) * h))
        sheet.save(out)
    print('painted %d crewmate variant skins' % len(previews))


if __name__ == '__main__':
    main()
