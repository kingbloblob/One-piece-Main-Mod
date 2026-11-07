"""Writes the textures, model, blockstate and item definition for onepiece:joy_boy_chest.
Usage: python3 gen_joy_boy_chest.py <source root>"""
import json, os, random, sys
from PIL import Image

root = sys.argv[1]
A = os.path.join(root, 'src/main/resources/assets/onepiece')
T = os.path.join(A, 'textures/block')
random.seed(14)

def tex(name, fn):
    im = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16):
            im.putpixel((x, y), fn(x, y))
    im.save(os.path.join(T, name + '.png'))

def j(c, n=10):
    return tuple(max(0, min(255, v + random.randint(-n, n))) for v in c) + (255,)

RED, RED_D, RED_L = (128, 22, 30), (82, 12, 20), (164, 38, 42)
GOLD, GOLD_D, GOLD_L = (232, 178, 40), (168, 112, 20), (255, 230, 120)

def lacquer(x, y):
    # Lacquered planks: a dark seam every 5 rows, a soft highlight on top of each plank.
    if y % 5 == 4:
        return j(RED_D, 4)
    if y % 5 == 0:
        return j(RED_L, 6)
    return j(RED, 8)

def border(x, y, inner):
    edge = x in (0, 15) or y in (0, 15)
    if edge:
        return j(GOLD_D if (x + y) % 2 else GOLD, 6)
    if x in (1, 14) or y in (1, 14):
        return j(GOLD_L if (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)) else GOLD, 6)
    return inner(x, y)

def side(x, y):
    return border(x, y, lacquer)

def front(x, y):
    return border(x, y, lacquer)

def top(x, y):
    # Lid top: a golden sun (Joy Boy / Nika) in the middle.
    dx, dy = x - 7.5, y - 7.5
    r = (dx * dx + dy * dy) ** 0.5
    if r < 2.2:
        return j(GOLD_L, 6)
    if r < 3.4:
        return j(GOLD, 6)
    if r < 5.6 and (abs(dx) < 0.8 or abs(dy) < 0.8 or abs(abs(dx) - abs(dy)) < 0.8):
        return j(GOLD_D, 6)
    return border(x, y, lacquer)

def gold(x, y):
    shade = GOLD_L if y < 3 else GOLD_D if y > 12 else GOLD
    if (x + 2 * y) % 7 == 0:
        shade = GOLD_L
    return j(shade, 8)

def gem(x, y):
    dx, dy = x - 7.5, y - 7.5
    if dx + dy < -3:
        return j((150, 255, 230), 6)
    if dx + dy > 5:
        return j((10, 90, 80), 6)
    return j((30, 190, 160), 10)

def inside(x, y):
    return j((40, 18, 14), 6)

tex('joy_boy_chest_side', side)
tex('joy_boy_chest_front', front)
tex('joy_boy_chest_top', top)
tex('joy_boy_chest_gold', gold)
tex('joy_boy_chest_gem', gem)
tex('joy_boy_chest_bottom', inside)

def box(fr, to, faces):
    return {'from': fr, 'to': to, 'faces': {f: {'texture': '#' + t} for f, t in faces.items()}}

ALL = ['north', 'south', 'east', 'west', 'up', 'down']
def every(t):
    return {f: t for f in ALL}

model = {
    'parent': 'minecraft:block/block',
    'textures': {
        'particle': 'onepiece:block/joy_boy_chest_gold',
        'side': 'onepiece:block/joy_boy_chest_side', 'front': 'onepiece:block/joy_boy_chest_front',
        'top': 'onepiece:block/joy_boy_chest_top', 'gold': 'onepiece:block/joy_boy_chest_gold',
        'gem': 'onepiece:block/joy_boy_chest_gem', 'bottom': 'onepiece:block/joy_boy_chest_bottom',
    },
    'elements': [
        # Body and lid (front faces north; the blockstate turns it).
        box([1, 1, 1], [15, 9, 15], {'north': 'front', 'south': 'side', 'east': 'side', 'west': 'side', 'down': 'bottom'}),
        box([1, 9.5, 1], [15, 13, 15], {'north': 'front', 'south': 'side', 'east': 'side', 'west': 'side', 'up': 'top'}),
        # Gold plinth, lid rim and crown moulding.
        box([0.5, 0, 0.5], [15.5, 1.5, 15.5], every('gold')),
        box([0.5, 8.5, 0.5], [15.5, 9.75, 15.5], every('gold')),
        box([2, 13, 2], [14, 14, 14], {'north': 'gold', 'south': 'gold', 'east': 'gold', 'west': 'gold', 'up': 'top'}),
        # Two gold straps over the lid and down the sides.
        box([3, 1.5, 0.75], [4.5, 13.25, 15.25], {f: 'gold' for f in ['north', 'south', 'up', 'east', 'west']}),
        box([11.5, 1.5, 0.75], [13, 13.25, 15.25], {f: 'gold' for f in ['north', 'south', 'up', 'east', 'west']}),
        # Corner posts.
        box([0.5, 1.5, 0.5], [2, 12.5, 2], every('gold')),
        box([14, 1.5, 0.5], [15.5, 12.5, 2], every('gold')),
        box([0.5, 1.5, 14], [2, 12.5, 15.5], every('gold')),
        box([14, 1.5, 14], [15.5, 12.5, 15.5], every('gold')),
        # The lock with its gem, and a gem on the crown.
        box([6, 5.5, 0.25], [10, 11, 1], every('gold')),
        box([7, 7, -0.25], [9, 9.5, 0.25], every('gem')),
        box([7, 14, 7], [9, 15, 9], every('gem')),
    ],
}
os.makedirs(os.path.join(A, 'models/block'), exist_ok=True)
json.dump(model, open(os.path.join(A, 'models/block/joy_boy_chest.json'), 'w'), indent=2)
json.dump({'variants': {f'facing={f}': ({'model': 'onepiece:block/joy_boy_chest', 'y': y} if y else {'model': 'onepiece:block/joy_boy_chest'})
                        for f, y in [('north', 0), ('east', 90), ('south', 180), ('west', 270)]}},
          open(os.path.join(A, 'blockstates/joy_boy_chest.json'), 'w'), indent=2)
json.dump({'model': {'type': 'minecraft:model', 'model': 'onepiece:block/joy_boy_chest'}},
          open(os.path.join(A, 'items/joy_boy_chest.json'), 'w'), indent=2)
print('ok')
