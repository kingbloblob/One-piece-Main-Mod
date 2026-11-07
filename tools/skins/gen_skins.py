"""Paints the 64x64 skins for the story characters, crewmates and marines.

Run:  python3 gen_skins.py [path to source/] [--preview out.png]
Writes assets/onepiece/textures/entity/{character,crewmate,marine}/<id>.png.
Each skin is described in a few lines below (see outfits.py for what the keys mean),
so to change someone's look, edit their entry and run this again.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from outfits import build
from skinkit import preview, shade
from giants import GIANTS, paint_giant, write_java
from player_format import build_layers, outer_mask, to_player

SRC = next((a for a in sys.argv[1:] if not a.startswith('--') and not a.endswith('.png')),
           '/mnt/project-files/one-piece-mod/source')
TEX = os.path.join(SRC, 'src/main/resources/assets/onepiece/textures/entity')

LIGHT, FAIR, TAN, BROWN, DARK = '#f2c9a0', '#f6d6b8', '#dca478', '#b07a50', '#7a5238'
MARINE_COAT = dict(kind='cape', color='#f2f2f0', kanji=True, length=9)


# Kuma's look, shared with the Pacifista / S-Bear NPC skins (tools/npcs/gen_npc_skins.py kuma_style).
KUMA_CAP, KUMA_SPOTS = '#ece6d6', '#8a5a34'
KUMA_RING = [(2, 2), (3, 2), (4, 2), (5, 2), (1, 3), (6, 3), (1, 4), (6, 4), (1, 5), (6, 5), (1, 6), (6, 6),
             (2, 7), (3, 7), (4, 7), (5, 7), (3, 4), (4, 4), (3, 5), (4, 5), (3, 0), (4, 0), (3, 9), (4, 9),
             (0, 4), (0, 5), (7, 4), (7, 5)]


def kuma_target(s):
    for (x, y) in KUMA_RING:
        s.front('body', x, y, '#f4f4f0')


def kuma_paws(s):
    # paw prints on the trousers, and the Nikyu Nikyu paw pads on his hands (palm side + fingertips)
    for (x, y) in ((1, 9), (2, 9), (1, 10), (2, 10), (0, 8), (1, 7), (2, 7), (3, 8)):
        s.front('leg', x, y, '#f4f4f0')
    s.cap('arm', 'bottom', None, fn=lambda x, y: '#e89aa8' if (1 <= x <= 2 and 1 <= y <= 2) or (x, y) in ((0, 0), (3, 0)) else None)
    for x in (1, 2):
        s.front('arm', x, 11, '#e89aa8')


def kuma_cap_spots(s):
    s.cap('hat', 'top', None, fn=lambda x, y: KUMA_SPOTS if (x * 3 + y * 5) % 7 == 0 and 1 < x < 6 else None)
    for col in range(1, 32, 5):
        s.w('hat', col, 0, KUMA_SPOTS, 0)


def kuma_lenses(s):
    for x in (1, 2, 5, 6):
        s.front('head', x, 4, '#c8dcea')


def chest_x(color):
    """Luffy's X scar on the chest."""
    def f(s):
        for i in range(4):
            s.front('body', 2 + i, 2 + i, color)
            s.front('body', 5 - i, 2 + i, color)
    return f


def arm_mark(color, rows=(2, 3), cols=(1, 2)):
    def f(s):
        for r in rows:
            for c in cols:
                s.w('arm', c, r, color, 0)
    return f


def front_mark(part, pixels, color):
    def f(s):
        for (x, r) in pixels:
            s.front(part, x, r, color)
    return f


def back_mark(part, pixels, color):
    def f(s):
        for (x, r) in pixels:
            s.back(part, x, r, color)
    return f


JOLLY = [(3, 3), (4, 3), (2, 4), (5, 4), (3, 5), (4, 5)]          # a small skull shape
WB_MARK = [(3, 2), (4, 2), (2, 3), (3, 3), (4, 3), (5, 3), (3, 4), (4, 4), (2, 5), (5, 5)]
STAR = [(1, 7), (2, 6), (2, 7), (2, 8), (3, 7)]

CHARACTERS = {
    'luffy': dict(skin=TAN, hair='#1a1a1e', hair_style='spiky', eyes='#2a1a10',
                  face=['scar_luffy'], hat=dict(kind='straw', color='#e8c860', color2='#c82020'),
                  top=dict(kind='vest', color='#c82424'), sash=('#e8c030', 8, 2),
                  pants=dict(color='#3a62b8', length='knee'), shoes=dict(kind='sandal', color='#8a5a30'),
                  post=[chest_x('#a0503a')]),
    # Post-timeskip Zoro: long dark green coat open over a bare chest with the diagonal scar from Mihawk,
    # green haramaki under a red sash, black bandana tied on the left arm, three gold earrings.
    'zoro': dict(skin=TAN, hair='#4aa04a', hair_style='buzz', eyes='#1a1a1a', face=['scar_eye_l', 'earrings3'],
                 top=dict(kind='none'), sash=('#b02a2a', 9, 1),
                 pants=dict(color='#262a26'), shoes=dict(kind='boot', color='#1c1c1c', **{'from': 8}),
                 coat=dict(kind='long', color='#1e4a30', trim='#163a26', length=10),
                 post=[lambda s: s.band('body', 7, 9, '#3a8a3a', cols=range(4, 12)),      # haramaki
                       front_mark('body', [(2, 2), (3, 3), (4, 4), (5, 5)], '#a0503a'),     # chest scar
                       arm_mark('#202020', rows=(1, 2), cols=range(0, 16))]),
    'nami': dict(skin=LIGHT, hair='#f07a2a', hair_style='long', hair_len=7, eyes='#7a4a20', face=['blush'],
                 top=dict(kind='bikini', color='#4a90d8', pattern='hstripes', patcol='#f4f4f4'),
                 pants=dict(color='#3a5a9a'), shoes=dict(kind='shoe', color='#b06a30'),
                 post=[arm_mark('#3a6ad0', rows=(1, 2), cols=(1, 2)), lambda s: s.band('arm', 9, 10, '#3a3a3a')]),
    # Usopp: brown overalls over a bare chest, white sash, goggles pushed up, long nose (a 3D box, see giants.py).
    'usopp': dict(skin=BROWN, hair='#1a1a1a', hair_style='curly', eyes='#1a1a1a', face=['goggles', 'stubble'],
                  top=dict(kind='none'), sash=('#f0ece0', 8, 2),
                  pants=dict(color='#7a5a32', length='capri'), shoes=dict(kind='boot', color='#5a3a20', **{'from': 9}),
                  post=[lambda s: [s.front('body', x, r, '#7a5a32') for x in (1, 6) for r in range(0, 8)],   # straps
                        lambda s: [s.front('body', x, r, '#7a5a32') for x in range(1, 7) for r in (6, 7)],   # bib
                        lambda s: [s.back('body', x, r, '#7a5a32') for x in (2, 5) for r in range(0, 8)],
                        lambda s: s.front('head', 3, 5, shade(BROWN, 1.15)),
                        lambda s: s.front('head', 4, 5, shade(BROWN, 1.1))]),
    'sanji': dict(overlay_top=True, skin=FAIR, hair='#f0d860', hair_style='side', eyes='#2a3a6a', face=['cigarette', 'goatee'],
                  brow='#c0a030',
                  top=dict(kind='suit', color='#1e1e26', color2='#4a6ab0', color3='#1a1a1a', sleeves='long'),
                  pants=dict(color='#1e1e26'), shoes=dict(kind='shoe', color='#141414'),
                  post=[lambda s: (s.front('head', 1, 2, '#c0a030'), s.front('head', 0, 3, '#c0a030'))]),   # the curly brow
    'chopper': dict(skin='#8a5a38', hair='#6a4228', hair_style='curly', eyes='#1a1a1a', eye_white='#1a1a1a',
                    hat=dict(kind='top', color='#f07aa8', color2='#f07aa8'),
                    face=[('blush', '#3a6ad0')], mouth='#5a3a20',
                    top=dict(kind='none'), pants=dict(color='#8a4ab0', length='short'),
                    shoes=dict(kind='hoof', color='#3a2a1a'),
                    post=[front_mark('hat', [(2, 0), (3, 1), (4, 1), (5, 0), (2, 2), (5, 2)], '#f4f4f4'),
                          lambda s: (s.front('head', 3, 5, '#3a6ad0'), s.front('head', 4, 5, '#3a6ad0')),
                          front_mark('body', [(x, r) for x in range(2, 6) for r in range(2, 9)], '#b08060')]),
    'robin': dict(overlay_top=True, coat=dict(kind='long', color='#2e2438', trim='#3e3050', length=10), skin='#e2b48c', hair='#1a1a2a', hair_style='bangs', hair_len=8, eyes='#3a3a8a',
                  top=dict(kind='v', color='#6a3a8a', sleeves='long'),
                  pants=dict(color='#202028'), shoes=dict(kind='boot', color='#2a2020', **{'from': 9}),
                  post=[lambda s: [s.front('hat', x, 1, '#e080b0') for x in (1, 2, 5, 6)]]),
    'franky': dict(skin=TAN, hair='#3aa0e8', hair_style='pomp', eyes='#1a1a1a', face=['sunglasses'],
                   top=dict(kind='open', color='#e04848', pattern='flowers', patcol='#f0d040', sleeves='short'),
                   pants=dict(color='#2a50b0', length='brief'), shoes=dict(kind='sandal', color='#3a3a3a'),
                   post=[lambda s: [s.w('arm', c, r, '#3070d0', 0) for (c, r) in ((5, 6), (4, 7), (5, 7), (6, 7), (5, 8))],
                         lambda s: (s.front('head', 3, 5, '#a8b0b8'), s.front('head', 4, 5, '#a8b0b8'))]),
    'brook': dict(skin='#f0ece0', hair='#141414', hair_style='afro', eyes='#141414', eye_white='#141414',
                  mouth='#141414',
                  top=dict(kind='suit', color='#1c1c26', color2='#f0f0f0', color3='#e8c040', sleeves='long'),
                  pants=dict(color='#1c1c26'), shoes=dict(kind='shoe', color='#141414'),
                  post=[lambda s: [s.front('head', x, 6, '#f8f8f8' if x % 2 else '#606060') for x in range(1, 7)],
                        lambda s: [s.front('head', x, 3, '#141414') for x in (1, 2, 5, 6)],
                        lambda s: s.front('head', 3, 5, '#202020')]),
    'jinbe': dict(skin='#5a7aa0', hair='#141418', hair_style='slick', eyes='#1a1a1a', face=['tusks'],
                  mouth='#2a3a5a', brow='#141418',
                  top=dict(kind='kimono', color='#30489a', color2='#a8bcd0', pattern='dots', patcol='#4a62c0'),
                  sash=('#e08030', 8, 2), pants=dict(color='#2a3a6a'), shoes=dict(kind='geta', color='#8a6a40'),
                  post=[lambda s: [s.w('head', c, r, '#141418') for c in range(26, 30) for r in range(5, 8)],
                        front_mark('head', [(3, 1), (4, 2), (3, 2)], '#8a3a3a')]),   # the forehead scar
    'shanks': dict(skin=LIGHT, hair='#c02828', hair_style='wavy', eyes='#2a1a10', face=['scars3', 'stubble'],
                   top=dict(kind='open', color='#f4f2ea', sleeves='long'), sash=('#8a6a3a', 9, 1),
                   pants=dict(color='#7a5a3a', length='capri'), shoes=dict(kind='sandal', color='#5a3a20'),
                   coat=dict(kind='cape', color='#1a1a1c', length=10)),
    'blackbeard': dict(skin=TAN, hair='#141414', hair_style='curly', eyes='#1a1a1a', face=['beard', 'grin'],
                       hat=dict(kind='bandana', color='#8a2a2a'),
                       top=dict(kind='open', color='#e8e4d8', sleeves='short'), sash=('#6a4a2a', 9, 1),
                       pants=dict(color='#3a3028'), shoes=dict(kind='boot', color='#2a2018'),
                       coat=dict(kind='cape', color='#18181a', length=10),
                       post=[front_mark('body', [(3, 2), (4, 3), (3, 4), (4, 5)], '#2a1a14')]),
    'buggy': dict(skin='#f8e8d8', hair='#3a6ad0', hair_style='long', hair_len=4, eyes='#1a1a1a',
                  face=['big_nose_red', ('lips', '#e03030'), ('eyeshadow', '#3a6ad0')],
                  hat=dict(kind='tricorn', color='#e87a20', color2='#e8c040', skull=True),   # his orange captain's hat
                  top=dict(kind='shirt', color='#f4f4f4', pattern='stripes', patcol='#e04040'),
                  pants=dict(color='#e8e0d0', pattern='stripes', patcol='#e04040'),
                  shoes=dict(kind='boot', color='#5a2a1a'),
                  coat=dict(kind='long', color='#d84a3a', trim='#e8c040', collar='#e8c870', length=8)),
    'whitebeard': dict(skin='#d89060', hair='#e8d8a0', hair_style='buzz', eyes='#3a2a1a', face=['crescent'],
                       brow='#e8e0c0', hat=dict(kind='bandana', color='#18181a'),
                       top=dict(kind='none'), sash=('#7a4a8a', 8, 2),
                       pants=dict(color='#2a2a2e'), shoes=dict(kind='boot', color='#141414', **{'from': 8}),
                       coat=dict(kind='cape', color='#f2f0e8', length=10),
                       post=[front_mark('body', [(2, 4), (3, 5), (5, 3), (5, 6), (4, 7)], '#b06a50')]),
    'big_mom': dict(skin=LIGHT, hair='#f07aa8', hair_style='afro', eyes='#3a2a1a', face=['lips', 'grin'],
                    top=dict(kind='dress', color='#f6aac0', pattern='dots', patcol='#d8344e', sleeves='none'),
                    pants=dict(color='#f6aac0', length='short', pattern='dots', patcol='#d8344e'),
                    shoes=dict(kind='shoe', color='#c8204a')),
    'kaido': dict(skin='#d09068', hair='#1a1a20', hair_style='long', hair_len=8, eyes='#2a1a10',
                  face=['horns', 'mustache', 'beard'],
                  top=dict(kind='none'), sash=('#ece4c8', 8, 2),
                  pants=dict(color='#5a3a7a'), shoes=dict(kind='boot', color='#2a2028'),
                  coat=dict(kind='cape', color='#3a3048', length=10),
                  post=[lambda s: [s.w('arm', c, r, '#3a8a5a', 0) for c in range(4, 8) for r in range(3, 9) if (c + r) % 2]]),
    'law': dict(overlay_top=True, skin='#e0b080', hair='#141418', hair_style='short', eyes='#d0b040',
                face=['goatee', 'dark_circles', 'earring_l'],
                hat=dict(kind='fur', color='#f4f2ea', color2='#6a4a2a'),
                top=dict(kind='hoodie', color='#f0d040', color2='#1a1a1a', sleeves='long', sleeve_color='#1a1a1a'),
                pants=dict(color='#4a6a9a', pattern='spots', patcol='#2a3a5a'),
                shoes=dict(kind='shoe', color='#2a2a2a'),
                post=[lambda s: s.band('arm', 10, 12, '#202020', cols=range(4, 8))]),
    'kid': dict(skin=FAIR, hair='#d02a1a', hair_style='spiky', eyes='#7a1a1a',
                face=['goggles', ('lips', '#4a2a4a'), 'eyeshadow'],
                top=dict(kind='none'), sash=('#e0b030', 9, 1),
                pants=dict(color='#2a2a30', pattern='stripes', patcol='#3a3a44'),
                shoes=dict(kind='boot', color='#1a1a1a'),
                coat=dict(kind='cape', color='#a02020', collar='#e8e4d8', length=10)),
    'killer': dict(overlay_top=True, skin=FAIR, hair='#f0d870', hair_style='long', hair_len=10, eyes='#1a1a1a', face=['mask_killer'],
                   top=dict(kind='shirt', color='#1a1a1a', pattern='dots', patcol='#f4f4f4', sleeves='short'),
                   pants=dict(color='#3a5a8a'), shoes=dict(kind='shoe', color='#2a2a2a')),
    'hawkins': dict(skin='#f4e4d0', hair='#f0e8b0', hair_style='long', hair_len=9, eyes='#5a2a6a',
                    face=[('eyeshadow', '#5a2a6a')],
                    top=dict(kind='robe', color='#e8e4d8', sleeves='long'),
                    pants=dict(color='#3a2a4a'), shoes=dict(kind='shoe', color='#2a1a2a'),
                    coat=dict(kind='long', color='#4a2a5a', trim='#e8c040', length=10)),
    'drake': dict(skin=TAN, hair='#e07a3a', hair_style='short', eyes='#2a2a1a', face=['x_scar'],
                  hat=dict(kind='tricorn', color='#2a2a2a', color2='#a02020'),
                  top=dict(kind='v', color='#f0eee8', sleeves='long'),
                  pants=dict(color='#3a3a3a'), shoes=dict(kind='boot', color='#2a2a2a'),
                  coat=dict(kind='long', color='#3a3a4a', length=10)),
    'bonney': dict(skin=LIGHT, hair='#f080b0', hair_style='long', hair_len=6, eyes='#6a2a4a', face=['lips'],
                   hat=dict(kind='cap', color='#3a9a5a', color2='#2a6a3a'),
                   top=dict(kind='shirt', color='#f4f4f4', pattern='stripes', patcol='#3a7ad0', sleeves='short'),
                   pants=dict(color='#e08a30', length='short'), shoes=dict(kind='boot', color='#5a3a2a', **{'from': 6})),
    'mihawk': dict(skin=LIGHT, hair='#141414', hair_style='slick', eyes='#e8c020', face=['mustache', 'goatee'],
                   hat=dict(kind='cowboy', color='#1a1a1a', color2='#f4f4f4'),
                   top=dict(kind='open', color='#f0ece0', sleeves='long'),
                   pants=dict(color='#1a1a1a'), shoes=dict(kind='boot', color='#1a1a1a', **{'from': 8}),
                   coat=dict(kind='long', color='#1e1e22', trim='#8a1a1a', length=10),
                   post=[front_mark('body', [(3, 3), (4, 3), (3, 4), (2, 4), (4, 4), (3, 5)], '#e8c040')]),
    'crocodile': dict(skin='#e8c4a0', hair='#141414', hair_style='slick', eyes='#2a2a2a', face=['scar_across', 'cigar'],
                      top=dict(kind='suit', color='#4a3a2a', color2='#f0f0f0', color3='#e08a30', sleeves='long'),
                      pants=dict(color='#2a2a2e'), shoes=dict(kind='shoe', color='#141414'),
                      coat=dict(kind='long', color='#1e2a24', collar='#6a5a3a', length=10)),   # gold hook: giants.py
    'doflamingo': dict(skin=TAN, hair='#f0d860', hair_style='short', eyes='#1a1a1a',
                       face=[('sunglasses', '#f0f0f0'), 'grin'], lens='#d02060',
                       top=dict(kind='open', color='#f4f4f4', pattern='stripes', patcol='#e08a30', sleeves='short'),
                       pants=dict(color='#e8e4d8', pattern='stripes', patcol='#e0a050'),
                       shoes=dict(kind='shoe', color='#e8e0d0'),
                       coat=dict(kind='cape', color='#f070b8', collar='#ff90c8', length=10),
                       post=[lambda s: [s.w('body', c, r, '#ff90c8', 0.15) for c in range(16, 24) for r in range(12) if (c + r) % 3 == 0]]),
    # Boa Hancock (Pirate Empress outfit): red dress with a deep V neck and patterned sleeves, pink sash with a
    # gold buckle, long red skirt with green and pink flowers and a high slit, gold earrings; white cape and gold
    # epaulettes are 3D (giants.py).
    'hancock': dict(skin='#f4d4b8', hair='#141418', hair_style='bangs', hair_len=10, eyes='#2a2a5a',
                    face=['lips', ('earring_l', '#e8c040')],
                    top=dict(kind='dress', color='#b8283a', sleeves='long'),
                    pants=dict(color='#b8283a', length='long'), shoes=dict(kind='shoe', color='#e8c040'),
                    post=[lambda s: [s.front('body', x, r, '#f4d4b8') for r in range(0, 7) for x in range(3 - (6 - r) // 3, 5 + (6 - r) // 3)],
                          lambda s: s.band('body', 8, 10, '#f0b0c8'),
                          lambda s: [s.front('body', x, 8, '#e8c040') for x in (3, 4)],
                          lambda s: [s.w('arm', c, r, '#f08aa8', 0) for c in range(16) for r in range(2, 11) if (c + r) % 4 == 0],
                          lambda s: [s.w('leg', c, r, '#3a9a5a' if (c * 3 + r) % 7 == 0 else '#f0a0c0', 0)
                                     for c in range(16) for r in range(0, 11) if (c * 3 + r) % 7 in (0, 3)],
                          lambda s: [s.front('leg', 3, r, '#f4d4b8') for r in range(2, 11)]]),   # the slit
    # Kuma: same look as his Pacifista copies (tools/npcs/gen_npc_skins.py kuma_style): cream bear-eared cap with
    # brown spots, mirrored round glasses, black coat with the white crosshair, spotted navy trousers, paw-pad gloves.
    'kuma': dict(skin='#a8744e', hair='#141414', hair_style='short', hair_len=3, eyes='#2a2a2a',
                 face=[('glasses', '#e4ecf2'), ('bear_ears', KUMA_CAP)],
                 top=dict(kind='shirt', color='#1a1a1e', sleeves='long'),
                 pants=dict(color='#262a40', pattern='spots', patcol=KUMA_SPOTS),
                 shoes=dict(kind='shoe', color='#141414'), gloves='#6a4a2a',
                 coat=dict(kind='long', color='#18181c', length=10),
                 hat=dict(kind='cap', color=KUMA_CAP),
                 post=[kuma_target, kuma_paws, kuma_cap_spots, kuma_lenses]),
    # Moria: pale blue-grey skin, spiky dark purple hair, yellow eyes, wide grin with the stitched mouth corners,
    # black coat with the big orange fur collar, purple-striped trousers.
    'moria': dict(skin='#9aa8c0', hair='#3a2a5a', hair_style='spiky', eyes='#e8c020', face=['grin', 'horns'],
                  top=dict(kind='open', color='#3a2a4a', sleeves='long'),
                  pants=dict(color='#2a2030', pattern='stripes', patcol='#4a3a5a'), shoes=dict(kind='boot', color='#1a1a1a'),
                  coat=dict(kind='cape', color='#1a1420', collar='#e08030', length=10),
                  post=[lambda s: s.band('head', 7, 8, '#3a3a3a', cols=range(0, 32, 2)),
                        lambda s: [s.front('head', x, r, '#2a2a3a') for (x, r) in ((0, 5), (0, 7), (7, 5), (7, 7))]]),   # stitches
    'garp': dict(skin=TAN, hair='#a8a8a8', hair_style='buzz', eyes='#2a2a2a', face=['scar_eye_l', 'beard'],
                 top=dict(kind='robe', color='#f0f0ee', sleeves='long'),
                 pants=dict(color='#4a5a7a'), shoes=dict(kind='shoe', color='#2a2a2a'),
                 coat=MARINE_COAT),
    'sengoku': dict(skin=TAN, hair='#202020', hair_style='afro', eyes='#2a2a2a', face=['glasses', 'beard'],
                    hat=dict(kind='cap', color='#f0f0f0', color2='#2a4a9a'),
                    top=dict(kind='suit', color='#4a4a52', color2='#f0f0f0', color3='#2a2a2a'),
                    pants=dict(color='#4a4a52'), shoes=dict(kind='shoe', color='#141414'),
                    coat=MARINE_COAT,
                    post=[lambda s: s.cap('hat', 'top', None, fn=lambda x, y: '#f8f8f8' if 2 <= x <= 5 and 2 <= y <= 5 else None)]),
    'akainu': dict(skin=TAN, hair='#141414', hair_style='short', eyes='#2a1a1a',
                   hat=dict(kind='marine', color='#2a2a4a', color2='#1a1a2a'),
                   top=dict(kind='suit', color='#b02424', color2='#1a1a1a', color3='#b02424'),
                   pants=dict(color='#b02424'), shoes=dict(kind='shoe', color='#141414'),
                   coat=MARINE_COAT, post=[front_mark('body', [(1, 2), (1, 3)], '#e04870')]),
    'kizaru': dict(skin=TAN, hair='#202020', hair_style='wavy', eyes='#2a2a2a', face=['sunglasses'], lens='#c08020',
                   top=dict(kind='suit', color='#e8d040', color2='#f0f0f0', color3='#2a2a2a',
                            pattern='hstripes', patcol='#d8b830'),
                   pants=dict(color='#e8d040', pattern='stripes', patcol='#d8b830'),
                   shoes=dict(kind='shoe', color='#f0f0f0'), coat=MARINE_COAT),
    'fujitora': dict(skin=TAN, hair='#3a3030', hair_style='buzz', eyes='#2a2a2a', face=['closed_eyes', 'x_scar'],
                     top=dict(kind='kimono', color='#5a3a7a', color2='#e8e0d0'),
                     pants=dict(color='#3a2a4a'), shoes=dict(kind='geta', color='#8a6a40'),
                     coat=MARINE_COAT),
    'ryokugyu': dict(skin=TAN, hair='#2a4a2a', hair_style='long', hair_len=9, eyes='#2a2a1a', face=['stubble'],
                     top=dict(kind='none'), pants=dict(color='#2a3a2a'), shoes=dict(kind='sandal', color='#5a4a2a'),
                     coat=MARINE_COAT,
                     post=[lambda s: [s.w('arm', c, r, '#3a8a3a', 0) for c in range(4, 8) for r in range(8, 11) if (c + r) % 2]]),
    'aokiji': dict(skin=TAN, hair='#141414', hair_style='curly', eyes='#2a2a2a', face=['sleepy'],
                   top=dict(kind='suit', color='#f0f0f0', color2='#4a7ac0', color3='#4a7ac0', sleeves='long'),
                   pants=dict(color='#f0f0f0'), shoes=dict(kind='shoe', color='#2a2a2a'),
                   coat=MARINE_COAT,
                   post=[lambda s: [s.front('hat', x, 1, '#7ab0e8') for x in range(1, 7)]]),
    'smoker': dict(skin=TAN, hair='#e8e8e8', hair_style='buzz', eyes='#3a3a3a', face=['two_cigars'],
                   top=dict(kind='none'), pants=dict(color='#3a3a40'), shoes=dict(kind='boot', color='#1a1a1a'),
                   coat=dict(kind='long', color='#e8e8e8', collar='#a08a6a', length=9, kanji=True), gloves='#2a2a2a'),
    'koby': dict(coat=MARINE_COAT, skin=FAIR, hair='#f090b8', hair_style='short', eyes='#2a2a4a', face=['x_scar'],
                 top=dict(kind='shirt', color='#f4f4f4', sleeves='long', cuff='#2a4a9a'),
                 pants=dict(color='#2a3a6a'), shoes=dict(kind='shoe', color='#2a2a2a'),
                 hat=dict(kind='marine', color='#f4f4f4', color2='#2a4a9a'),
                 post=[lambda s: s.band('body', 0, 2, '#2a4a9a', cols=range(16, 24)),
                       front_mark('body', [(2, 1), (5, 1), (3, 2), (4, 2)], '#2a4a9a')]),
    'tashigi': dict(overlay_top=True, skin=FAIR, hair='#1a2a4a', hair_style='short', eyes='#3a2a1a', face=['glasses'],
                    top=dict(kind='shirt', color='#e8a0b0', pattern='flowers', patcol='#f4f4f4', sleeves='long'),
                    pants=dict(color='#3a5a8a'), shoes=dict(kind='boot', color='#2a2a2a', **{'from': 9})),
    'lucci': dict(skin=FAIR, hair='#141414', hair_style='pony', hair_len=6, eyes='#2a2a2a', face=['goatee'],
                  hat=dict(kind='top', color='#141414', color2='#f0f0f0'),
                  top=dict(kind='suit', color='#141418', color2='#f0f0f0', color3='#f0f0f0'),
                  pants=dict(color='#141418'), shoes=dict(kind='shoe', color='#0e0e0e'),
                  post=[lambda s: s.cap('arm', 'top', '#f4f4f4')]),
    'dragon': dict(skin=TAN, hair='#141414', hair_style='spiky', eyes='#2a2a2a', face=['tattoo_left'],
                   top=dict(kind='robe', color='#3a3a2a'), pants=dict(color='#2a2a2a'),
                   shoes=dict(kind='boot', color='#1a1a1a'),
                   coat=dict(kind='long', color='#2a5a2e', length=11, collar='#2a5a2e'),
                   post=[lambda s: s.band('hat', 6, 8, '#2a5a2e', cols=range(16, 32))]),
    'sabo': dict(skin=FAIR, hair='#f0d870', hair_style='wavy', eyes='#2a3a6a', face=['burn_left'],
                 hat=dict(kind='top', color='#1a1a22', color2='#3a6ad0'),
                 top=dict(kind='suit', color='#2a46a0', color2='#f4f4f4', color3='#f4f4f4'),
                 pants=dict(color='#1a1a22'), shoes=dict(kind='boot', color='#6a4a2a'),
                 post=[lambda s: [s.front('hat', x, 2, '#80c0f0') for x in (1, 2, 5, 6)]]),
    'ace': dict(skin=TAN, hair='#141414', hair_style='wavy', eyes='#2a1a10', face=['freckles'],
                hat=dict(kind='cowboy', color='#e08030', color2='#c02a2a', smile=True),
                top=dict(kind='none'), sash=('#6a4a2a', 10, 1),
                pants=dict(color='#1a1a1a', length='knee'), shoes=dict(kind='boot', color='#1a1a1a', **{'from': 7}),
                post=[lambda s: [s.w('body', c, 1, '#c82020', 0) for c in range(0, 24, 1) if c % 2],
                      lambda s: [s.w('arm', c, 3, '#1a1a1a', 0) for c in (0, 2, 3)],
                      back_mark('body', [(2, 2), (3, 2), (4, 2), (5, 2), (3, 3), (4, 3), (2, 4), (5, 4), (3, 5), (4, 5)], '#5a3aa0'),
                      front_mark('body', [(3, 10), (4, 10)], '#e8c040')]),
    'marco': dict(overlay_top=True, skin=LIGHT, hair='#f0d860', hair_style='spiky', eyes='#2a2a2a', face=['sleepy', 'stubble'],
                  top=dict(kind='open', color='#7a5ab0', sleeves='long'), sash=('#3a6ad0', 9, 1),
                  pants=dict(color='#2a2a30', length='capri'), shoes=dict(kind='sandal', color='#5a4a3a'),
                  post=[front_mark('body', WB_MARK, '#4a6ad0')]),
    'rayleigh': dict(skin=LIGHT, hair='#e8e8e8', hair_style='slick', eyes='#2a2a2a',
                     face=['glasses', 'beard', 'scar_eye_r'],
                     top=dict(kind='open', color='#e8e0c8', sleeves='long'),
                     pants=dict(color='#6a5a4a'), shoes=dict(kind='sandal', color='#5a4a3a'),
                     coat=dict(kind='cape', color='#c8c0b0', length=10)),
    'roger': dict(skin=TAN, hair='#1a1a1a', hair_style='wavy', eyes='#2a2a2a', face=['roger_stache', 'grin'],
                  hat=dict(kind='tricorn', color='#1a1a1a', color2='#e8c040'),
                  top=dict(kind='open', color='#f0f0f0', sleeves='long'), sash=('#e8c040', 9, 1),
                  pants=dict(color='#2a2a2a'), shoes=dict(kind='boot', color='#1a1a1a'),
                  coat=dict(kind='cape', color='#b02424', trim='#e8c040', length=10)),
    'oden': dict(skin=TAN, hair='#141414', hair_style='slick', eyes='#2a2a2a', face=['goatee'],
                 top=dict(kind='kimono', color='#e8742a', color2=TAN, sleeves='long'),
                 sash=('#3a2a5a', 8, 2), pants=dict(color='#e8742a', length='brief'), shoes=dict(kind='sandal', color='#c8a060'),
                 post=[lambda s: [s.front('head', x, y, '#c82020') for (x, y) in ((0, 4), (7, 4), (0, 3), (7, 3))],
                       lambda s: [s.w('body', c0 + dx, r0 + dy, '#f4d040', 0) for (c0, r0) in ((5, 4), (17, 2), (21, 5))
                                  for (dx, dy) in ((0, 0), (1, 0), (0, 1), (0, 2), (1, 2))]]),
    'yamato': dict(skin=LIGHT, hair='#f4f4f4', hair_style='short', eyes='#e07a20', brow='#2a2a2a',
                   top=dict(kind='kimono', color='#f6f6f6', color2='#f6f6f6', sleeves='none'),
                   pants=dict(color='#c42a2a'), shoes=dict(kind='sandal', color='#8a6a40'),
                   post=[lambda s: [s.w('body', c, r, '#2a3a8a' if (c * 3 + r * 5) % 7 else '#7a8ae0', 0) for c in range(24) for r in range(6, 10)],
                         lambda s: [s.w('body', c0 + dx, r, '#5a4a9a', 0) for c0 in (0, 12) for r in range(1, 6)
                                    for dx in ((1, 2) if r in (1, 5) else ((0, 3) if r == 3 else (0, 1, 2, 3)[r % 2::3]))],
                         lambda s: [s.w('body', c, 10, '#e8d8a8', 0) for c in range(24)]]),
    'katakuri': dict(skin=TAN, hair='#802040', hair_style='spiky', eyes='#2a1a1a', face=['scarf'],
                     top=dict(kind='vest', color='#2a2224'), pants=dict(color='#3a2a2a'),
                     shoes=dict(kind='boot', color='#2a1a1a'),
                     post=[lambda s: [s.w('arm', c, r, '#3a2a4a', 0) for c in range(16) for r in (2, 5, 8) if c % 3]]),
    'king': dict(skin=DARK, hair='#e8e8e8', hair_style='bald', eyes='#3a4250', face=['mask_king'],
                 top=dict(kind='shirt', color='#1e2a4a', sleeves='long'), pants=dict(color='#14161c'),
                 shoes=dict(kind='boot', color='#0e0e10'),
                 post=[lambda s: [s.front('head', x, y, c) for (x, y, c) in ((1, 3, '#3a4250'), (2, 3, '#3a4250'), (5, 3, '#3a4250'), (6, 3, '#3a4250'),
                                                                               (1, 4, '#3a4250'), (2, 4, '#5a6a80'), (5, 4, '#3a4250'), (6, 4, '#5a6a80'),
                                                                               (0, 3, '#5a5a62'), (3, 3, '#5a5a62'), (4, 3, '#5a5a62'), (7, 3, '#5a5a62'))],
                       lambda s: [s.front('body', x, r, '#e8c040') for x in (2, 5) for r in (1, 3, 5, 7, 9)],
                       lambda s: [s.front('body', x, r, '#16203a') for x in (3, 4) for r in range(0, 10)]]),
    'enel': dict(skin=TAN, hair='#f0e8b0', hair_style='buzz', eyes='#2a2a2a',
                 hat=dict(kind='bandana', color='#f4f4f4', low=True),
                 top=dict(kind='none'), sash=('#2a6ab0', 9, 1),
                 pants=dict(color='#e8a040'), shoes=dict(kind='bare'),
                 post=[lambda s: [s.side('head', w, x, r, shade(TAN, 0.9)) for w, x in (('r', 3), ('l', 4)) for r in (5, 6, 7)]]),
    'kinemon': dict(skin=TAN, hair='#141414', hair_style='slick', eyes='#2a2a2a',
                    top=dict(kind='kimono', color='#e07a30', color2='#f0e8d8'), sash=('#e8e0c8', 8, 2),
                    pants=dict(color='#34344a'), shoes=dict(kind='geta', color='#8a6a40'),
                    post=[lambda s: [s.w('body', c, r, '#1a1a1a' if (c // 2) % 2 else '#f0f0ea', 0)
                                     for c in range(8, 20) for r in range(0, 8)
                                     if not (c in (8, 9) and r < 3)],
                          lambda s: [s.front('head', 1, 3, '#f4f4f4'), s.front('head', 2, 3, '#2a2a2a'),
                                     s.front('head', 1, 2, '#141414'), s.front('head', 2, 2, '#141414')]]),
    'vegapunk': dict(skin=LIGHT, hair='#9a8ab0', hair_style='wavy', eyes='#2a2a4a', face=['beard', 'goggles'],
                     top=dict(kind='shirt', color='#3a3a4a', sleeves='long'), pants=dict(color='#2a2a30'),
                     shoes=dict(kind='shoe', color='#2a2a2a'),
                     coat=dict(kind='long', color='#f6f6f6', length=10), gloves='#e8e0c0'),
    # Added by the characters thread for the Nether/End story.
    'magellan': dict(skin='#7a5a8a', hair='#1a1a1a', hair_style='buzz', eyes='#2a1a2a', face=['horns'],
                     top=dict(kind='suit', color='#2a2a2e', sleeves='long'),
                     pants=dict(color='#2a2a2e'), shoes=dict(kind='boot', color='#1a1a1a'),
                     coat=dict(kind='cape', color='#4a2a5a', length=10)),
    # Ivankov: huge made-up face (blue eyeshadow, red lips, big cheeks), purple afro, pink top under a
    # dark Revolutionary cape, short trousers and fishnet stockings into tall pink boots.
    'ivankov': dict(skin=LIGHT, hair='#6a3a8a', hair_style='afro', eyes='#3a2a1a',
                    face=[('lips', '#d0203a'), ('eyeshadow', '#3a6ad0'), ('blush', '#f0a0a0')],
                    top=dict(kind='shirt', color='#e86a9c', sleeves='short'),
                    pants=dict(color='#3a2a4a', length='brief'), shoes=dict(kind='boot', color='#e86a9c', **{'from': 7}),
                    coat=dict(kind='cape', color='#2a2240', length=10),
                    post=[lambda s: [s.w('leg', c, r, '#3a2a3a', 0) for c in range(16) for r in range(2, 7) if (c + r) % 2 == 0],
                          lambda s: [s.front('head', x, 6, '#d0203a') for x in (2, 5)],
                          lambda s: [s.front('head', x, 2, '#1a1a1a') for x in (1, 2, 5, 6)]]),
    'xebec': dict(skin='#c99a6e', hair='#eef0f6', hair_style='spiky', eyes='#2a1a1a', brow='#3a64c8',
                  face=['grin'],
                  top=dict(kind='none'),
                  pants=dict(color='#1a1a1e'), shoes=dict(kind='boot', color='#141414'),
                  post=[lambda s: [s.front('head', x, y, '#8a3ac8') for (x, y) in ((7, 1), (7, 2), (6, 3), (7, 5), (7, 6))],
                        lambda s: [s.side('head', 'l', x, y, '#8a3ac8') for (x, y) in ((0, 2), (1, 3), (0, 4), (1, 5))],
                        lambda s: [s.w('leg', c, r, '#e8c040', 0) for c in (8, 9, 10, 11) for r in (2, 4) if (c + r) % 2]]),
    'imu': dict(skin='#b8835a', hair='#f0f0f0', hair_style='long', hair_len=10, eyes='#140808', eye_white='#e02020',
                brow='#2a1a1a', face=['sleepy'],
                top=dict(kind='robe', color='#16141a', sleeves='long'),
                pants=dict(color='#16141a'), shoes=dict(kind='shoe', color='#16141a'),
                post=[lambda s: [s.w('body', c, r, '#c8a040', 0) for c in (7, 8) for r in range(0, 12)]]),
    # Added for the Wano and Egghead story chapters (2026-11-03).
    # Queen: slicked-back black hair, sunglasses and a moustache, open white shirt over the belly, pink fur coat.
    'queen': dict(skin=TAN, hair='#1a1a1a', hair_style='slick', hair_len=8, eyes='#2a2a2a', face=['sunglasses', 'mustache'],
                  top=dict(kind='open', color='#f4f0e8', sleeves='long'),
                  pants=dict(color='#3a2a2a'), shoes=dict(kind='boot', color='#1a1a1a'),
                  coat=dict(kind='cape', color='#e0a8c4', length=10)),
    # Saint Jaygarcia Saturn: pale, bald on top with white hair and a long white beard, dark formal robe.
    'saturn': dict(skin='#e6d6c4', hair='#f0f0ee', hair_style='bald', eyes='#3a2a2a', brow='#f0f0ee', face=['beard', 'mustache'],
                   top=dict(kind='suit', color='#1a1a22', color2='#f4f4f4', sleeves='long'),
                   pants=dict(color='#1a1a22'), shoes=dict(kind='shoe', color='#141414'),
                   coat=dict(kind='long', color='#2a2a36', length=10),
                   post=[lambda s: s.front('head', 2, 1, '#6a4a3a'),
                         lambda s: [s.side('head', w, x, r, '#f0f0ee') for w in ('l', 'r') for x in range(8) for r in range(2, 7) if x < 3]]),
    # Added for the Elbaph story chapters (2026-11-06).
    # Figarland Shamrock: commander of the Holy Knights, Shanks's twin. The same red hair (longer, swept back) but no
    # scars, a clean-shaven face, a white Holy Knight's uniform with gold trim and a long dark cape.
    'shamrock': dict(skin=LIGHT, hair='#c02828', hair_style='long', hair_len=7, eyes='#2a1a10', face=[],
                     top=dict(kind='suit', color='#f2f0ea', color2='#d8b040', color3='#1a1a1c', sleeves='long'),
                     pants=dict(color='#f2f0ea'), shoes=dict(kind='boot', color='#1a1a1c'), gloves='#f2f0ea',
                     coat=dict(kind='cape', color='#1a1a28', collar='#d8b040', length=10)),
    # Added for the Fish-Man Island story chapter (2026-11-05).
    # Hody Jones: great white shark Fish-Man, blue-grey skin, black crest of hair, bloodshot red eyes from the
    # Energy Steroids, a white shark grin, dark open shirt with a pale scarf-collar.
    'hody': dict(skin='#7e9cb8', hair='#141418', hair_style='spiky', hair_len=6, eyes='#d02020', brow='#141418',
                 face=['grin', 'dark_circles'], mouth='#f4f4f4',
                 top=dict(kind='open', color='#2a2a3a', color2='#7e9cb8', sleeves='long'),
                 pants=dict(color='#e8e0d0'), shoes=dict(kind='shoe', color='#3a2a2a'),
                 coat=dict(kind='cape', color='#1a1a28', collar='#e8e0d0', length=9)),
    # Added for the Elbaph transformations (chapter 1198, 2026-11-06). Loki, the "accursed prince" of Elbaph:
    # wild long golden hair, a fierce grin, bare muscled chest, a heavy dark fur mantle, broken chains on his wrists.
    # Colours are our best guess from the black-and-white pages.
    'loki': dict(skin='#d8a878', hair='#e0b848', hair_style='spiky', hair_len=10, eyes='#c03020', brow='#a8802a',
                 face=['grin'],
                 top=dict(kind='none'),
                 pants=dict(color='#3a2e26'), shoes=dict(kind='boot', color='#2a2018'),
                 post=[lambda s: [s.w('arm', c, r, '#8a8a92', 0) for c in range(16) for r in (9, 10) if c % 2 == 0]]),
    # Added 2026-11-06 for the Elbaph story chapter (kept last so the other skins' seeds don't shift).
    # Saint Gunko of the Holy Knights: a young woman in the white-and-gold Holy Knight's uniform with a long cape.
    'gunko': dict(skin=FAIR, hair='#e8e0f0', hair_style='bangs', hair_len=7, eyes='#3a2a5a',
                  top=dict(kind='suit', color='#f2f0ea', color2='#d8b040', color3='#2a2a48', sleeves='long'),
                  pants=dict(color='#f2f0ea'), shoes=dict(kind='boot', color='#2a2a48'), gloves='#f2f0ea',
                  coat=dict(kind='cape', color='#2a2a48', collar='#d8b040', length=10)),
}

# Generic crewmates by job: plain sailors with a uniform hint for the role.
CREW = {
    'swordsman': dict(skin=TAN, hair='#2a2a2a', hair_style='short', face=['stubble'],
                      hat=dict(kind='bandana', color='#2a2a2a'),
                      top=dict(kind='kimono', color='#3a5a4a', color2=TAN), sash=('#a02a2a', 8, 2),
                      pants=dict(color='#2a2a2a'), shoes=dict(kind='boot', color='#1a1a1a')),
    'cook': dict(skin=LIGHT, hair='#c09040', hair_style='short',
                 hat=dict(kind='top', color='#f8f8f8', color2='#f8f8f8'),
                 top=dict(kind='suit', color='#f4f4f4', color2='#f4f4f4', color3='#e04040'),
                 pants=dict(color='#2a2a2a', pattern='stripes', patcol='#4a4a4a'),
                 shoes=dict(kind='shoe', color='#1a1a1a')),
    'doctor': dict(skin=FAIR, hair='#5a3a2a', hair_style='short', face=['glasses'],
                   top=dict(kind='shirt', color='#8ac0e0', sleeves='long'), pants=dict(color='#3a4a5a'),
                   shoes=dict(kind='shoe', color='#2a2a2a'), coat=dict(kind='long', color='#f6f6f6', length=9),
                   post=[front_mark('body', [(1, 3), (0, 4), (1, 4), (2, 4), (1, 5)], '#e03030')]),
    'helmsman': dict(skin=BROWN, hair='#1a1a1a', hair_style='buzz', face=['beard'],
                     hat=dict(kind='cap', color='#2a3a6a'),
                     top=dict(kind='shirt', color='#f4f4f4', pattern='stripes', patcol='#2a3a8a', sleeves='long'),
                     pants=dict(color='#2a3a6a'), shoes=dict(kind='boot', color='#3a2a1a'), gloves='#6a4a2a'),
    'musician': dict(skin=LIGHT, hair='#e8c040', hair_style='wavy',
                     hat=dict(kind='top', color='#5a2a6a', color2='#e8c040'),
                     top=dict(kind='suit', color='#5a2a6a', color2='#f4f4f4', color3='#e8c040'),
                     pants=dict(color='#2a1a2a'), shoes=dict(kind='shoe', color='#1a1a1a')),
    'navigator': dict(skin=LIGHT, hair='#d06a30', hair_style='long', hair_len=5, face=['blush'],
                      top=dict(kind='v', color='#3a8ad0', sleeves='short'), pants=dict(color='#e8e0c8', length='capri'),
                      shoes=dict(kind='sandal', color='#8a5a30'),
                      post=[lambda s: s.band('arm', 9, 10, '#3a3a3a', cols=range(0, 16))]),
    'shipwright': dict(skin=TAN, hair='#6a4a2a', hair_style='short', face=['stubble'],
                       hat=dict(kind='bandana', color='#e08030'),
                       top=dict(kind='shirt', color='#e8e0c8', sleeves='short'),
                       pants=dict(color='#5a6a8a'), shoes=dict(kind='boot', color='#4a3a2a'),
                       post=[lambda s: [s.w('body', c, r, '#6a5a3a') for c in (5, 6, 9, 10) for r in range(0, 10)],
                             lambda s: s.band('body', 9, 10, '#4a3a2a')]),
    'sniper': dict(skin=BROWN, hair='#2a2a2a', hair_style='curly', face=['goggles'],
                   top=dict(kind='shirt', color='#6a7a3a', sleeves='short'), pants=dict(color='#7a6a4a'),
                   shoes=dict(kind='boot', color='#3a2a1a'),
                   post=[front_mark('body', [(i, i + 1) for i in range(8)], '#3a2a1a')]),
    'archaeologist': dict(skin=FAIR, hair='#2a1a2a', hair_style='long', hair_len=5, face=['glasses'],
                          hat=dict(kind='cowboy', color='#b09060', color2='#6a4a2a'),
                          top=dict(kind='shirt', color='#c8b890', sleeves='long'), pants=dict(color='#6a5a3a'),
                          shoes=dict(kind='boot', color='#4a3a2a'),
                          post=[lambda s: s.band('body', 9, 10, '#4a3a2a')]),
}

# Marines by rank. Same uniform, more braid and coat as the rank goes up.
_MARINE_BASE = dict(skin=LIGHT, hair='#3a2a1a', hair_style='short',
                    top=dict(kind='shirt', color='#f4f4f4', sleeves='long', cuff='#2a4a9a'),
                    pants=dict(color='#2a3a6a'), shoes=dict(kind='shoe', color='#1a1a1a'),
                    hat=dict(kind='marine', color='#f4f4f4', color2='#2a4a9a'))


def marine(**extra):
    d = dict(_MARINE_BASE)
    d.update(extra)
    collar = [lambda s: s.band('body', 0, 2, '#2a4a9a', cols=range(16, 24)),
              front_mark('body', [(2, 1), (5, 1), (3, 2), (4, 2)], '#2a4a9a')]
    d['post'] = collar + d.get('post', [])
    return d


MARINES = {
    'recruit': marine(),
    'rifleman': marine(hair='#1a1a1a', skin=TAN, post=[front_mark('body', [(i, i + 1) for i in range(8)], '#5a3a20')]),
    'lieutenant': marine(skin=TAN, hair='#141414', face=['glasses'],
                         top=dict(kind='suit', color='#2a3a6a', color2='#f4f4f4', color3='#c02020'),
                         hat=dict(kind='marine', color='#2a3a6a', color2='#1a2a4a'), post=[]),
    'captain': marine(hair='#5a5a5a', face=['mustache'],
                      top=dict(kind='suit', color='#2a2a3a', color2='#f4f4f4', color3='#2a4a9a'),
                      pants=dict(color='#2a2a3a'), coat=dict(MARINE_COAT, epaulettes='#e8c040'),
                      hat=dict(kind='marine', color='#2a2a3a', color2='#e8c040'), post=[]),
}


# Normal-sized characters drawn with the slim (3-pixel) player arms.
SLIM = {'nami', 'robin', 'hancock', 'tashigi', 'bonney', 'gunko'}


def write_formats_java(src):
    """Tells CharacterRenderer which characters have player-layout skins, and which of those have slim arms."""
    normal = sorted(c for c in CHARACTERS if c not in GIANTS)
    fmt = lambda ids: ', '.join('"%s"' % c for c in sorted(ids))
    path = os.path.join(src, 'src/client/java/com/onepiecemod/character/client/CharacterSkinFormats.java')
    with open(path, 'w') as f:
        f.write('''package com.onepiecemod.character.client;

import java.util.Set;

/**
 * Which characters have full player-layout skins (separate left arm/leg and a 3D outer layer),
 * drawn with the player model instead of the old zombie model. GENERATED by tools/skins/gen_skins.py.
 */
public final class CharacterSkinFormats {
	/** Player-layout skins with normal 4-pixel arms. */
	public static final Set<String> WIDE = Set.of(%s);
	/** Player-layout skins with slim 3-pixel arms. */
	public static final Set<String> SLIM = Set.of(%s);

	private CharacterSkinFormats() {
	}
}
''' % (fmt(c for c in normal if c not in SLIM), fmt(c for c in normal if c in SLIM)))


def main():
    groups = (('character', CHARACTERS), ('crewmate', CREW), ('marine', MARINES))
    previews = []
    for i, (folder, table) in enumerate(groups):
        for j, (cid, spec) in enumerate(table.items()):
            path = os.path.join(TEX, folder, cid + '.png')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            seed = i * 1000 + j * 17 + 3
            if folder == 'character' and cid not in GIANTS:
                # Normal-sized characters: full player skin with a 3D outer layer (and slim arms for SLIM).
                painted, marks = build_layers(spec, seed)
                img = painted.finish(path)
                to_player(img, outer_mask(spec, marks), slim=cid in SLIM).save(path)
                previews.append(preview(img, 3))
                continue
            img = build(spec, seed=seed).finish(path)
            if folder == 'character' and cid in GIANTS:
                paint_giant(cid, img).save(path)   # 128x128 with the extra 3D boxes
            previews.append(preview(img, 3))
    write_java(SRC)
    write_formats_java(SRC)
    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        cols = 10
        w, h = previews[0].size
        rows = (len(previews) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * w, rows * h), (40, 40, 48, 255))
        for k, p in enumerate(previews):
            sheet.alpha_composite(p, ((k % cols) * w, (k // cols) * h))
        sheet.save(out)
    print('painted %d skins' % len(previews))


if __name__ == '__main__':
    main()
