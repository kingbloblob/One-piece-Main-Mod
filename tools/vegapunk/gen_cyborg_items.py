"""Paints the Vegapunk parts and cyborg module icons (package com.onepiecemod.vegapunk) and writes their item models.

Run:  python3 gen_cyborg_items.py [path to source/]
Writes assets/onepiece/textures/item/<id>.png, models/item/<id>.json, items/<id>.json and the names in
assets/onepiece_cyborg/lang/en_us.json. Safe to rerun.
"""
import json
import os
import sys

from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
ASSETS = os.path.join(SRC, 'src/main/resources/assets')


def hexc(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


class Pix:
    def __init__(self):
        self.img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))

    def p(self, x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            self.img.putpixel((x, y), hexc(c) if isinstance(c, str) else c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.p(x, y, c)

    def rows(self, rows, palette, ox=0, oy=0):
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in palette:
                    self.p(ox + x, oy + y, palette[ch])

    def outline(self, color='#141418'):
        src = self.img.copy()
        for y in range(16):
            for x in range(16):
                if src.getpixel((x, y))[3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 16 and 0 <= ny < 16 and src.getpixel((nx, ny))[3] > 0:
                            self.p(x, y, color)
                            break


METAL = {'a': '#3a3e46', 'b': '#5c626c', 'c': '#8a929e', 'd': '#c4ccd6', 'y': '#e8c040', 'k': '#24262c', 'r': '#b03a2a'}


def scrap():
    s = Pix()
    s.rows([
        "      bbbb      ",
        "    bbccccb     ",
        "   bccddccbb    ",
        "  bccdccccccb   ",
        "  bcdkccccccbb  ",
        " bccccyyyccccb  ",
        " bcccyyycccccb  ",
        " bccyyycccckcb  ",
        "  bcccccccccbb  ",
        "  bbccckccccb   ",
        "   bbccccccbb   ",
        "    bbbcbbbb    ",
        "      bb b      ",
    ], METAL, 0, 1)
    s.outline()
    return s


def laser_core():
    s = Pix()
    s.rows([
        "     bbbbbb     ",
        "   bbccccccbb   ",
        "  bcc111111ccb  ",
        "  bc12222221cb  ",
        " bc1223333221cb ",
        " bc1233443321cb ",
        " bc1234444321cb ",
        " bc1234444321cb ",
        " bc1233443321cb ",
        " bc1223333221cb ",
        "  bc12222221cb  ",
        "  bcc111111ccb  ",
        "   bbccccccbb   ",
        "     bbbbbb     ",
    ], {**METAL, '1': '#c08010', '2': '#f0b020', '3': '#ffe060', '4': '#fffff0'}, 0, 1)
    s.outline()
    return s


def chip():
    s = Pix()
    s.rows([
        "  y y y y y y   ",
        " gggggggggggggg ",
        "ygGGGGGGGGGGGGgy",
        " gGkkkkkkkkkkGg ",
        "ygGk22222222kGgy",
        " gGk2pppp222kGg ",
        "ygGk2pwwp222kGgy",
        " gGk2pppp222kGg ",
        "ygGk22222222kGgy",
        " gGkkkkkkkkkkGg ",
        "ygGGyGGGGGyGGGgy",
        " gggggggggggggg ",
        "  y y y y y y   ",
    ], {'g': '#1e5a2e', 'G': '#2e8a44', 'k': '#1a1a20', '2': '#3a3a46', 'p': '#e85aa0', 'w': '#ffd0e8', 'y': '#e8c040'}, 0, 2)
    s.outline()
    return s


def feather():
    s = Pix()
    s.rows([
        "           fo   ",
        "          fFo   ",
        "         kFFo   ",
        "        kkkF    ",
        "       kkkkk    ",
        "      kkkdkk    ",
        "     kkkdkk     ",
        "    kkkdkkk     ",
        "   kkkdkkk      ",
        "   kkdkkk       ",
        "  kkdkkk        ",
        "  kdkk          ",
        " kdk            ",
        " d              ",
        "d               ",
    ], {'k': '#18161c', 'd': '#4a4652', 'f': '#ff7a20', 'F': '#ffc040', 'o': '#ff4010'}, 0, 0)
    s.outline('#08070a')
    return s


def module(icon):
    s = Pix()
    # Steel casing with Franky-blue trim and corner bolts.
    s.rect(1, 2, 14, 13, '#5c626c')
    s.rect(2, 3, 13, 12, '#8a929e')
    s.rect(1, 2, 14, 2, '#3a8ad8')
    s.rect(1, 13, 14, 13, '#2a5aa0')
    for (x, y) in ((2, 3), (13, 3), (2, 12), (13, 12)):
        s.p(x, y, '#c4ccd6')
    s.rect(4, 5, 11, 10, '#24262c')
    icon(s)
    s.outline()
    return s


def icon_frame(s):
    s.rows(["  dddd  ", " dcccc d", " dcbbcd ", " dcbbcd ", "  dccd  ", "   dd   "],
           {'d': '#e0e6ee', 'c': '#a0a8b4', 'b': '#6a7280'}, 4, 5)


def icon_arm(s):
    s.rows(["  ssss  ", " sSSSSs ", " sSSSSs ", "  sSSs  ", "  y  y  ", "   yy   "],
           {'s': '#c0c8d4', 'S': '#8a929e', 'y': '#e8c040'}, 4, 5)


def icon_cola(s):
    s.rows(["   ww   ", "   bb   ", "  bbbb  ", "  brrb  ", "  bbbb  ", "  bbbb  "],
           {'w': '#e8e8e8', 'b': '#5a2a14', 'r': '#e02020'}, 4, 5)


def icon_beam(s):
    s.rows(["   yy   ", "  yWWy  ", "yyWWWWyy", "yyWWWWyy", "  yWWy  ", "   yy   "],
           {'y': '#f0b020', 'W': '#fffff0'}, 4, 5)


def icon_vent(s):
    s.rows([" ccccc  ", "c     c ", "c  cc  c", "c c  c c", " c  cc c", "  cc   c"],
           {'c': '#c8f0ff'}, 4, 5)


def icon_lunar(s):
    s.rows(["   ff   ", "  fFFf  ", "  fFFf  ", " kkkkkk ", " kddddk ", " kkkkkk "],
           {'f': '#ff5a10', 'F': '#ffc040', 'k': '#141418', 'd': '#3a3a46'}, 4, 5)


ITEMS = {
    'pacifista_scrap': ('Pacifista Scrap', scrap),
    'laser_core': ('Pacifista Laser Core', laser_core),
    'vegapunk_chip': ('Vegapunk Control Chip', chip),
    'seraphim_feather': ('Seraphim Feather', feather),
    'iron_frame_plating': ('Iron Frame Plating', lambda: module(icon_frame)),
    'strong_right_arm': ('Strong Right Arm', lambda: module(icon_arm)),
    'cola_engine_core': ('Cola Engine Core', lambda: module(icon_cola)),
    'radical_beam_emitter': ('Radical Beam Emitter', lambda: module(icon_beam)),
    'coup_de_vent_cannon': ('Coup de Vent Cannon', lambda: module(icon_vent)),
    'lunarian_plating': ('Lunarian Plating', lambda: module(icon_lunar)),
}


def main():
    tex = os.path.join(ASSETS, 'onepiece/textures/item')
    models = os.path.join(ASSETS, 'onepiece/models/item')
    defs = os.path.join(ASSETS, 'onepiece/items')
    lang_dir = os.path.join(ASSETS, 'onepiece_cyborg/lang')
    for d in (tex, models, defs, lang_dir):
        os.makedirs(d, exist_ok=True)
    lang = {
        'itemGroup.onepiece.cyborg': 'One Piece: Cyborg Parts',
        'key.onepiece_cyborg.fire': 'Radical Beam (Sneak: Coup de Vent)',
        'key.category.onepiece_cyborg.cyborg': 'One Piece: Cyborg',
    }
    for item_id, (name, paint) in ITEMS.items():
        paint().img.save(os.path.join(tex, item_id + '.png'))
        with open(os.path.join(models, item_id + '.json'), 'w') as f:
            json.dump({'parent': 'minecraft:item/generated', 'textures': {'layer0': 'onepiece:item/' + item_id}}, f, indent=2)
        with open(os.path.join(defs, item_id + '.json'), 'w') as f:
            json.dump({'model': {'type': 'minecraft:model', 'model': 'onepiece:item/' + item_id}}, f, indent=2)
        lang['item.onepiece.' + item_id] = name
    with open(os.path.join(lang_dir, 'en_us.json'), 'w') as f:
        json.dump(lang, f, indent=2)
    print('painted %d cyborg items' % len(ITEMS))


if __name__ == '__main__':
    main()
