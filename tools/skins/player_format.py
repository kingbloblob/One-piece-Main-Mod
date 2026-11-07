"""Turns a classic zombie-layout skin into a full player-layout skin with a 3D outer layer.

Used by gen_skins.py for the normal-sized story characters (the giants have their own models).
The game draws these with the player model (CharacterRenderer, "wide" or "slim" arms), which has:
  - separate left arm and left leg textures (the zombie model just mirrored the right ones),
  - an outer layer (jacket, sleeves, pants, hat) drawn slightly bigger than the body, for depth.

What goes on the outer layer is worked out from what each painting step changed:
coats and capes, long hair over the back, boots, and (with overlay_top=True) the shirt, suit or dress.
"""
from PIL import Image

import outfits
from skinkit import Skin, PARTS

# Box sizes (w, h, d) and texture origins in the player layout.
BOXES = {
    'body': ((8, 12, 4), (16, 16), (16, 32)),
    'right_arm': ((4, 12, 4), (40, 16), (40, 32)),
    'left_arm': ((4, 12, 4), (32, 48), (48, 48)),
    'right_leg': ((4, 12, 4), (0, 16), (0, 32)),
    'left_leg': ((4, 12, 4), (16, 48), (0, 48)),
}
# Painter part -> (base box, outer box name) for the parts the painter knows.
PAINTED = {'body': 'body', 'arm': 'right_arm', 'leg': 'right_leg'}


def build_layers(spec, seed):
    """Same as outfits.build, but also returns which pixels each step painted (for the outer layer)."""
    s = Skin(seed)
    skin = spec['skin']
    for part in ('body', 'arm', 'leg'):
        s.fill(part, skin, 0.03)
    outfits.paint_face(s, spec)
    marks = {}

    def step(name, fn):
        before = s.img.copy()
        fn(s, spec)
        marks[name] = changed(before, s.img)

    step('top', outfits.paint_top)
    outfits.paint_pants(s, spec)
    outfits.paint_sash(s, spec)
    step('shoes', outfits.paint_shoes)
    step('coat', outfits.paint_coat)
    outfits.paint_hands(s, spec)
    step('hair', outfits.paint_hair)
    outfits.paint_face_extras(s, spec)
    outfits.paint_hat(s, spec)
    post = spec.get('post', [])
    for fn in post if isinstance(post, list) else [post]:
        fn(s)
    return s, marks


def changed(a, b):
    return {(x, y) for y in range(64) for x in range(64) if a.getpixel((x, y)) != b.getpixel((x, y))}


def outer_mask(spec, marks):
    """Pixels (in the zombie layout) that should also be drawn on the outer layer."""
    mask = set(marks['coat'])
    if spec.get('overlay_top'):
        mask |= marks['top']
    # Long hair hanging down the back.
    bx, by, bw, bh = PARTS['body'][:4]
    mask |= {(x, y) for (x, y) in marks['hair'] if bx <= x < bx + bw and by <= y < by + bh}
    # Boots: only the lower part of the leg, so the shin has some depth.
    lx, ly = PARTS['leg'][:2]
    mask |= {(x, y) for (x, y) in marks['shoes'] if y >= ly + 7}
    return mask


def box_regions(w, h, d, ox, oy):
    """Each face of a box as (name, x, y, width, height) in the texture."""
    return [
        ('top', ox + d, oy, w, d), ('bottom', ox + d + w, oy, w, d),
        ('side0', ox, oy + d, d, h), ('front', ox + d, oy + d, w, h),
        ('side1', ox + d + w, oy + d, d, h), ('back', ox + 2 * d + w, oy + d, w, h),
    ]


def copy_box(src, dst, size, sorigin, dorigin, mirror=False, mask=None):
    """Copies one box's texture. mirror=True does what the zombie model's .mirror() did for the left limbs:
    every face flipped left-right and the two side faces swapped."""
    w, h, d = size
    sreg = {n: r for n, *r in box_regions(w, h, d, *sorigin)}
    dreg = {n: r for n, *r in box_regions(w, h, d, *dorigin)}
    for name, (dx, dy, fw, fh) in dreg.items():
        sname = {'side0': 'side1', 'side1': 'side0'}.get(name, name) if mirror else name
        sx, sy = sreg[sname][:2]
        for y in range(fh):
            for x in range(fw):
                fx = fw - 1 - x if mirror else x
                if mask is not None and (sx + fx, sy + y) not in mask:
                    continue
                dst.putpixel((dx + x, dy + y), src.getpixel((sx + fx, sy + y)))


def to_player(img, mask, slim=False):
    """img: the finished 64x64 zombie-layout skin. Returns the 64x64 player-layout skin."""
    out = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    # Head and hat are in the same place in both layouts.
    out.paste(img.crop((0, 0, 64, 16)), (0, 0))
    src = {'body': (16, 16), 'arm': (40, 16), 'leg': (0, 16)}
    for part, (size, base, outer) in BOXES.items():
        kind = 'body' if part == 'body' else part.split('_')[1]
        mirror = part.startswith('left')
        copy_box(img, out, size, src[kind], base, mirror)
        copy_box(img, out, size, src[kind], outer, mirror, mask)
    if slim:
        out = slim_arms(out)
    return out


def slim_arms(img):
    """Squeezes the 4-pixel arms to the 3-pixel "Alex" arms: drops the inner column of the front, back,
    top and bottom faces."""
    out = img.copy()
    for ox, oy in ((40, 16), (40, 32), (32, 48), (48, 48)):
        # Clear the old 4-wide arm area (16 x 16 including the top row).
        for y in range(oy, oy + 16):
            for x in range(ox, ox + 16):
                out.putpixel((x, y), (0, 0, 0, 0))
        wide = {n: r for n, *r in box_regions(4, 12, 4, ox, oy)}
        thin = {n: r for n, *r in box_regions(3, 12, 4, ox, oy)}
        for name, (dx, dy, fw, fh) in thin.items():
            sx, sy, sw, _ = wide[name]
            cols = list(range(sw)) if fw == sw else [0, 1, 3]
            for y in range(fh):
                for x, c in enumerate(cols):
                    out.putpixel((dx + x, dy + y), img.getpixel((sx + c, sy + y)))
    return out
