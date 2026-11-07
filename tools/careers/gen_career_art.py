"""Paints the art for careers (package com.onepiecemod.career).

Run:  PYTHONDONTWRITEBYTECODE=1 python3 gen_career_art.py [path to source/] [--preview out.png]
Writes:
  assets/onepiece/textures/entity/career/rev_soldier_<n>.png, rev_officer_<n>.png  (Revolutionary backup soldiers)
  assets/onepiece/textures/item/navy_den_den_mushi.png, revolutionary_den_den_mushi.png, revolutionary_invitation.png
  assets/onepiece/items/<item>.json and models/item/<item>.json
Skin counts must match REV_SOLDIER_SKINS / REV_OFFICER_SKINS in career/CareerSquads.java.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'skins'))
sys.path.insert(0, os.path.join(HERE, '..', 'npcs'))
from PIL import Image
from outfits import build
from skinkit import preview
import gen_npc_skins as npc

SRC = next((a for a in sys.argv[1:] if not a.startswith('--') and not a.endswith('.png')),
           '/mnt/project-files/one-piece-mod/source')
ASSETS = os.path.join(SRC, 'src/main/resources/assets/onepiece')

# Revolutionary Army colours: field greens, browns and dusty blues, like Sabo's and Koala's outfits.
REV_COATS = ['#3a4a2a', '#4a3a2a', '#2a3a4a', '#5a4a30', '#2e4a3a', '#3a2e2a', '#4a5a3a']
REV_SHIRTS = ['#d8cfb8', '#c8b898', '#e8e0d0', '#a89878', '#7a8a6a', '#5a6a7a']
REV_SCARVES = ['#a03020', '#c0a040', '#2a6a5a', '#e0e0e0', '#7a2a2a']
GOGGLES = '#c09040'


def rev_soldier(r):
    d = npc.head(r, hair_pool=npc.HAIR, face_pool=['stubble', 'scar_eye_l', 'goatee', 'freckles', 'scar_across', 'glasses', 'beard'])
    coat = r.choice(REV_COATS)
    d.update(top=dict(kind=r.choice(['shirt', 'v', 'shirt']), color=r.choice(REV_SHIRTS), sleeves=r.choice(['long', 'elbow'])),
             pants=dict(color=r.choice(['#3a3a2a', '#4a3a2a', '#2a2a2a', coat])),
             shoes=dict(kind='boot', color=r.choice(['#2a1a10', '#1a1a1a', '#3a2a1a'])),
             coat=dict(kind='jacket', color=coat),
             sash=(r.choice(['#2a1a10', '#3a2a1a']), 9, 1),
             post=[npc.bandolier(r.choice(['#5a3a20', '#3a2a1a']))] if r.random() < 0.5 else [])
    hat = r.random()
    if hat < 0.4:
        d['hat'] = dict(kind='cap', color=coat)
    elif hat < 0.7:
        d['hat'] = dict(kind='bandana', color=r.choice(REV_SCARVES))
    return d


def rev_officer(r):
    """Sabo-style: long coat, cravat, top hat or goggles."""
    d = npc.head(r, hair_pool=npc.HAIR + ['#e8d070', '#f0e0a0'], face_pool=['scar_eye_l', 'stubble', 'glasses', 'mustache'], most=1)
    coat = r.choice(['#1e2a4a', '#2a2a3a', '#3a2a2a', '#2a3a2a', '#1a1a2a'])
    d.update(top=dict(kind='suit', color=r.choice(['#e8e0d0', '#d0c8b0']), color2='#f4f4f4', color3=r.choice(REV_SCARVES)),
             pants=dict(color=r.choice(['#2a2a2a', '#3a3a2a', coat])),
             shoes=dict(kind='boot', color='#1a1a1a'),
             coat=dict(kind='long', color=coat, trim=r.choice(['#c0a040', None]), length=r.choice([9, 10]),
                       collar=r.choice(['#2a2a2a', None])),
             hat=dict(kind='top', color=r.choice(['#1a1a1a', coat]), color2=GOGGLES if r.random() < 0.6 else None))
    return d


GROUPS = {'rev_soldier': (rev_soldier, 12), 'rev_officer': (rev_officer, 6)}


def recolor(src, dst, mapping):
    im = Image.open(src).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if c[:3] in mapping:
                px[x, y] = mapping[c[:3]] + (c[3],)
    im.save(dst)


def invitation(dst):
    """A folded letter with a red wax seal stamped with the Revolutionary Army mark."""
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = im.load()
    paper, shade, edge = (236, 222, 186, 255), (210, 192, 150, 255), (120, 96, 60, 255)
    for x in range(1, 15):
        for y in range(3, 13):
            px[x, y] = paper
    for x in range(1, 15):
        px[x, 3] = edge
        px[x, 12] = edge
    for y in range(3, 13):
        px[1, y] = edge
        px[14, y] = edge
    # envelope flap
    for i in range(7):
        px[2 + i, 4 + i // 2 + (i % 2 == 0 and 0 or 0)] = shade
        px[13 - i, 4 + i // 2] = shade
    # wax seal
    red, dark = (170, 30, 30, 255), (110, 15, 15, 255)
    for (x, y) in [(7, 7), (8, 7), (6, 8), (7, 8), (8, 8), (9, 8), (7, 9), (8, 9), (6, 9), (9, 9), (7, 10), (8, 10)]:
        px[x, y] = red
    px[7, 8] = dark
    px[8, 9] = dark
    # green ribbon tail
    green = (50, 110, 60, 255)
    px[9, 11] = green
    px[10, 12] = green
    px[10, 13] = green
    im.save(dst)


def item_json(name):
    with open(os.path.join(ASSETS, 'items', name + '.json'), 'w') as f:
        json.dump({'model': {'type': 'minecraft:model', 'model': 'onepiece:item/' + name}}, f, indent=2)
        f.write('\n')
    with open(os.path.join(ASSETS, 'models/item', name + '.json'), 'w') as f:
        json.dump({'parent': 'minecraft:item/generated', 'textures': {'layer0': 'onepiece:item/' + name}}, f, indent=2)
        f.write('\n')


def main():
    tex = os.path.join(ASSETS, 'textures/entity/career')
    os.makedirs(tex, exist_ok=True)
    previews = []
    for gi, (group, (recipe, n)) in enumerate(GROUPS.items()):
        for i in range(n):
            r = random.Random(f'{group}-{i}')
            spec = {k: v for k, v in recipe(r).items() if v is not None}
            spec['post'] = [f for f in spec.get('post', []) if f]
            img = build(spec, seed=7700 + gi * 101 + i).finish(os.path.join(tex, f'{group}_{i}.png'))
            previews.append(preview(img, 3))

    items = os.path.join(ASSETS, 'textures/item')
    base = os.path.join(items, 'den_den_mushi.png')
    # Navy: blue-and-white shell. Revolution: green shell.
    recolor(base, os.path.join(items, 'navy_den_den_mushi.png'),
            {(120, 60, 25): (30, 50, 120), (200, 110, 50): (70, 120, 210), (170, 135, 80): (220, 225, 235)})
    recolor(base, os.path.join(items, 'revolutionary_den_den_mushi.png'),
            {(120, 60, 25): (35, 70, 40), (200, 110, 50): (80, 140, 75), (170, 135, 80): (160, 120, 70)})
    invitation(os.path.join(items, 'revolutionary_invitation.png'))
    for name in ('navy_den_den_mushi', 'revolutionary_den_den_mushi', 'revolutionary_invitation'):
        item_json(name)

    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        w, h = previews[0].size
        cols = 9
        rows = (len(previews) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * w, rows * h), (40, 40, 48, 255))
        for k, p in enumerate(previews):
            sheet.alpha_composite(p, ((k % cols) * w, (k // cols) * h))
        sheet.save(out)
    print('painted %d Revolutionary skins and 3 items' % len(previews))


if __name__ == '__main__':
    main()
