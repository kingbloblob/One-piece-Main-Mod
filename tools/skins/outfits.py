"""Turns a short outfit description into a painted skin. Used by gen_skins.py.

A character spec is a dict:
  skin, hair, hair_style, eyes        colours / style name
  top     = dict(kind, color, color2, color3, sleeves, pattern, patcol)
  pants   = dict(color, length, pattern, patcol)
  shoes   = dict(kind, color)
  sash    = (color, first_row, rows)          a band around the waist
  coat    = dict(kind, color, trim, collar, kanji)
  hat     = dict(kind, color, color2)
  face    = list of extra names (scar_l, freckles, beard, ...) or (name, colour)
  post    = function(skin) for anything special
"""
from skinkit import Skin, hexc, shade, mix, FRONT, BACK

# ---------------- head ----------------

FRINGES = {
    'short': [2, 1, 1, 1, 1, 1, 1, 2],
    'spiky': [3, 1, 2, 1, 2, 1, 2, 3],
    'long': [3, 2, 1, 1, 1, 1, 2, 3],
    'bangs': [3, 3, 2, 2, 2, 2, 3, 3],
    'slick': [1, 1, 1, 1, 1, 1, 1, 1],
    'buzz': [1, 1, 1, 1, 1, 1, 1, 1],
    'afro': [2, 1, 1, 1, 1, 1, 1, 2],
    'pomp': [2, 2, 2, 2, 2, 2, 2, 2],
    'wavy': [2, 2, 1, 2, 1, 2, 2, 2],
    'pony': [2, 1, 1, 1, 1, 1, 1, 2],
    'curly': [2, 2, 1, 2, 2, 1, 2, 2],
    'bald': [0] * 8,
    'side': [2, 1, 1, 1, 3, 4, 5, 5],   # hair over the left eye (viewer's right)
}


def paint_face(s, sp):
    skin = sp['skin']
    eyes = sp.get('eyes', '#3a2a1a')
    white = sp.get('eye_white', '#f4f4f4')
    # whole head in skin first, with a slightly darker jaw
    s.fill('head', skin, 0.03)
    s.band('head', 7, 8, shade(skin, 0.94), noise=0.02)
    if sp.get('no_face'):
        return
    # eyes: white on the outside, iris inside
    s.front('head', 1, 4, white)
    s.front('head', 2, 4, eyes)
    s.front('head', 5, 4, eyes)
    s.front('head', 6, 4, white)
    # brows in hair colour (or brow colour)
    brow = sp.get('brow', shade(sp.get('hair', '#202020'), 0.8))
    for x in (1, 2, 5, 6):
        s.front('head', x, 3, brow)
    # nose shadow and mouth
    s.front('head', 3, 5, shade(skin, 0.88))
    s.front('head', 4, 5, shade(skin, 0.92))
    mouth = sp.get('mouth', shade(skin, 0.62))
    s.front('head', 3, 6, mouth)
    s.front('head', 4, 6, mouth)
    # ears
    s.side('head', 'r', 3, 4, shade(skin, 0.86))
    s.side('head', 'l', 4, 4, shade(skin, 0.86))


def hair_px(s, part, col, row, base):
    """Hair pixel with a strand pattern."""
    f = 1.0 + (0.1 if (col * 3 + row) % 5 == 0 else 0) - (0.12 if (col + row * 2) % 7 == 0 else 0)
    s.w(part, col, row, shade(base, f), 0.05)


def paint_hair(s, sp):
    style = sp.get('hair_style', 'short')
    hc = sp.get('hair')
    if style == 'bald' or hc is None:
        return
    fr = FRINGES.get(style, FRINGES['short'])
    s.cap('head', 'top', None, fn=lambda x, y: shade(hc, 1.0 + 0.1 * ((x + y) % 3 == 0)))
    back_rows = {'short': 5, 'spiky': 5, 'slick': 6, 'buzz': 3, 'long': 8, 'bangs': 8, 'afro': 6,
                 'pomp': 4, 'wavy': 7, 'pony': 6, 'curly': 6, 'side': 5}.get(style, 5)
    side_rows = {'long': 8, 'bangs': 8, 'wavy': 6, 'afro': 5, 'buzz': 1, 'curly': 4}.get(style, 3)
    for col in range(32):
        if col in FRONT['head']:
            n = fr[col - 8]
        elif col in BACK['head']:
            n = back_rows
        else:
            # sides: longer towards the back
            k = col if col < 8 else 23 - col
            n = side_rows if style in ('long', 'bangs', 'wavy') else max(side_rows, side_rows + (k <= 2) * 2)
            if style not in ('long', 'bangs', 'wavy', 'afro') and k >= 5:
                n = max(1, side_rows - 1)
        for r in range(n):
            hair_px(s, 'head', col, r, hc)
    if style in ('long', 'bangs'):
        # strands framing the face and hair down the back
        for r in range(2, 8):
            hair_px(s, 'head', 8, r, hc)
            hair_px(s, 'head', 15, r, hc)
        rows = sp.get('hair_len', 6)
        for col in range(16, 24):
            for r in range(rows - (1 if col in (16, 23) else 0)):
                hair_px(s, 'body', col, r, hc)
        for col in (0, 3, 12, 15):   # over the shoulders a little
            hair_px(s, 'body', col, 0, hc)
    if style == 'pony':
        for col in (27, 28):
            for r in range(5, 8):
                hair_px(s, 'head', col, r, hc)
        for col in (19, 20):
            for r in range(0, sp.get('hair_len', 4)):
                hair_px(s, 'body', col, r, hc)
    # volume on the outer layer
    if style in ('spiky', 'afro', 'pomp', 'curly', 'wavy'):
        s.cap('hat', 'top', None, fn=lambda x, y: shade(hc, 1.05) if (style != 'spiky' or (x + y) % 2 == 0 or y > 1) else None)
        for col in range(32):
            if style == 'afro':
                rows = range(0, 6) if col not in FRONT['hat'] else range(0, 1)
            elif style == 'pomp':
                rows = range(0, 2) if col in FRONT['hat'] else range(0, 1)
            elif style == 'spiky':
                rows = range(0, 2 if col % 2 == 0 else 1)
            elif style == 'wavy':
                rows = range(0, 1) if col in FRONT['hat'] else range(0, 3 if col % 3 else 2)
            else:  # curly
                rows = range(0, 2) if (col % 2 == 0 and col not in FRONT['hat']) else range(0, 1)
            for r in rows:
                hair_px(s, 'hat', col, r, shade(hc, 1.06))
    if style == 'side':
        for r in range(2, 6):
            hair_px(s, 'hat', 13, r, hc)
            hair_px(s, 'hat', 14, r, hc)


def paint_hat(s, sp):
    h = sp.get('hat')
    if not h:
        return
    k = h['kind']
    c = h.get('color', '#202020')
    c2 = h.get('color2')
    if k == 'straw':
        s.cap('hat', 'top', None, fn=lambda x, y: shade(c, 1.0 + 0.1 * ((x + 2 * y) % 3 == 0)))
        s.band('hat', 0, 2, c, noise=0.08)
        s.band('hat', 2, 3, c2 or '#c02020')
        s.band('hat', 3, 4, c, cols=[x for x in range(32) if x not in FRONT['hat']], noise=0.08)
    elif k in ('cap', 'marine'):
        s.cap('hat', 'top', c)
        s.band('hat', 0, 2, c)
        if c2:
            s.band('hat', 2, 3, c2)
        if k == 'marine':
            s.front('hat', 3, 0, '#2a4a9a')
            s.front('hat', 4, 0, '#2a4a9a')
            s.front('hat', 3, 1, '#2a4a9a')
            s.front('hat', 4, 1, '#2a4a9a')
            s.band('hat', 2, 3, c2 or '#1a2a5a', cols=list(FRONT['hat']))
    elif k == 'top':
        s.cap('hat', 'top', c)
        s.band('hat', 0, 2, c)
        s.band('hat', 2, 3, c2 or '#a02020')
    elif k == 'cowboy':
        s.cap('hat', 'top', c)
        s.band('hat', 0, 2, c, noise=0.05)
        s.band('hat', 2, 3, c2 or '#c03030')
        s.band('hat', 3, 4, shade(c, 0.85), cols=[x for x in range(32) if x not in FRONT['hat']])
        if h.get('smile'):
            s.front('hat', 2, 1, '#f0e040')
            s.front('hat', 5, 1, '#3060c0')
    elif k == 'bandana':
        s.cap('hat', 'top', c)
        s.band('hat', 0, 2 if not h.get('low') else 3, c, noise=0.06)
        if c2:
            for col in range(0, 32, 3):
                s.w('hat', col, 0, c2, 0)
        s.back('hat', 3, 2, c)
        s.back('hat', 4, 2, c)
        s.back('hat', 4, 3, c)
    elif k == 'tricorn':
        s.cap('hat', 'top', c)
        s.band('hat', 0, 3, c, noise=0.04)
        if c2:
            s.band('hat', 2, 3, c2)
        if h.get('skull'):
            s.front('hat', 3, 0, '#f0f0f0')
            s.front('hat', 4, 0, '#f0f0f0')
            s.front('hat', 3, 1, '#f0f0f0')
            s.front('hat', 4, 1, '#f0f0f0')
    elif k == 'fur':      # Law's spotted fur hat
        s.cap('hat', 'top', None, fn=lambda x, y: c2 if (x * 3 + y * 5) % 7 == 0 else c)
        for col in range(32):
            for r in range(3):
                s.w('hat', col, r, c2 if (col * 3 + r * 5) % 7 == 0 else c, 0.05)
    elif k == 'helmet':
        s.cap('hat', 'top', c)
        s.band('hat', 0, 8, c, cols=[x for x in range(32) if x not in FRONT['hat']], noise=0.03)
        s.band('hat', 0, 2, c, cols=list(FRONT['hat']))


def paint_face_extras(s, sp):
    skin = sp['skin']
    hc = sp.get('hair', '#202020')
    for e in sp.get('face', []):
        name, col = (e if isinstance(e, tuple) else (e, None))
        if name == 'scar_luffy':        # stitched scar under the left eye
            s.front('head', 5, 5, col or '#9a3a2a')
            s.front('head', 6, 5, col or '#9a3a2a')
        elif name == 'scar_eye_l':      # vertical scar over the left eye, eye shut
            c = col or shade(skin, 0.6)
            for r in (2, 3, 5):
                s.front('head', 6, r, c)
            s.front('head', 5, 4, shade(skin, 0.7))
            s.front('head', 6, 4, c)
        elif name == 'scar_eye_r':
            c = col or shade(skin, 0.6)
            for r in (2, 3, 5):
                s.front('head', 1, r, c)
        elif name == 'scars3':          # Shanks
            c = col or '#8a2a2a'
            s.front('head', 5, 2, c)
            s.front('head', 6, 3, c)
            s.front('head', 7, 3, c)
            s.front('head', 5, 5, c)
            s.front('head', 6, 5, c)
        elif name == 'scar_across':      # Crocodile
            c = col or shade(skin, 0.65)
            for x in range(0, 8):
                if x not in (2, 5):
                    s.front('head', x, 5, c)
            s.front('head', 2, 5, shade(skin, 0.75))
        elif name == 'x_scar':
            c = col or shade(skin, 0.6)
            for i in range(4):
                s.front('head', 2 + i, 2 + i, c)
                s.front('head', 5 - i, 2 + i, c)
        elif name == 'freckles':
            for x in (1, 2, 5, 6):
                if x in (1, 6) or True:
                    s.front('head', x, 5, shade(skin, 0.78))
        elif name == 'beard':
            c = col or hc
            for x in range(8):
                s.front('head', x, 7, c, 0.06)
                if x not in (3, 4):
                    s.front('head', x, 6, c, 0.06)
            s.front('head', 0, 5, c)
            s.front('head', 7, 5, c)
            s.side('head', 'r', 6, 6, c); s.side('head', 'r', 6, 7, c); s.side('head', 'r', 7, 5, c)
            s.side('head', 'l', 0, 6, c); s.side('head', 'l', 0, 7, c); s.side('head', 'l', 1, 5, c)
            s.side('head', 'r', 7, 6, c); s.side('head', 'r', 7, 7, c)
            s.side('head', 'l', 0, 5, c)
        elif name == 'goatee':
            c = col or hc
            s.front('head', 3, 7, c)
            s.front('head', 4, 7, c)
        elif name == 'stubble':
            c = col or mix(skin, hc, 0.45)
            for x in range(8):
                s.front('head', x, 7, c, 0.05)
        elif name == 'mustache':
            c = col or hc
            for x in (1, 2, 3, 4, 5, 6):
                s.front('head', x, 5, c)
            s.front('head', 3, 6, shade(skin, 0.6))
        elif name == 'crescent':        # Whitebeard
            c = col or '#f4f4f0'
            for x in range(1, 7):
                s.front('head', x, 5, c)
            s.front('head', 0, 4, c)
            s.front('head', 7, 4, c)
            s.front('head', 0, 3, c)
            s.front('head', 7, 3, c)
        elif name == 'roger_stache':
            c = col or hc
            for x in range(1, 7):
                s.front('head', x, 5, c)
            s.front('head', 0, 6, c)
            s.front('head', 7, 6, c)
            s.front('head', 0, 7, c)
            s.front('head', 7, 7, c)
        elif name == 'sunglasses':
            c = col or '#151515'
            for x in range(0, 8):
                s.front('head', x, 4, c if x in (0, 3, 4, 7) else col2(e, '#252530'))
            for x in (1, 2, 5, 6):
                s.front('head', x, 4, sp.get('lens', '#202028'))
            s.side('head', 'r', 7, 4, c)
            s.side('head', 'l', 0, 4, c)
        elif name == 'glasses':
            c = col or '#202020'
            for x in (0, 3, 4, 7):
                s.front('head', x, 4, c)
            s.front('head', 1, 3, c); s.front('head', 2, 3, c); s.front('head', 5, 3, c); s.front('head', 6, 3, c)
        elif name == 'cigarette':
            s.front('head', 5, 6, '#f4f4f4')
            s.front('head', 6, 6, '#e06020')
        elif name == 'cigar':
            s.front('head', 5, 6, '#6a4020')
            s.front('head', 6, 6, '#6a4020')
            s.front('head', 7, 6, '#e05020')
        elif name == 'two_cigars':
            for x in (1, 6):
                s.front('head', x, 6, '#7a5030')
            s.front('head', 0, 6, '#e06020')
            s.front('head', 7, 6, '#e06020')
        elif name == 'grin':
            for x in range(1, 7):
                s.front('head', x, 6, '#f4f4f4')
            s.front('head', 1, 6, shade(skin, 0.6))
            s.front('head', 6, 6, shade(skin, 0.6))
        elif name == 'lips':
            s.front('head', 3, 6, col or '#c02040')
            s.front('head', 4, 6, col or '#c02040')
        elif name == 'eyeshadow':
            s.front('head', 1, 3, col or '#202020')
            s.front('head', 2, 3, col or '#202020')
            s.front('head', 5, 3, col or '#202020')
            s.front('head', 6, 3, col or '#202020')
        elif name == 'dark_circles':
            s.front('head', 1, 5, shade(skin, 0.75))
            s.front('head', 6, 5, shade(skin, 0.75))
        elif name == 'earring_l':
            s.side('head', 'l', 4, 5, col or '#e8c040')
            s.side('head', 'l', 4, 6, col or '#e8c040')
        elif name == 'earrings3':
            for r in (5, 6):
                s.side('head', 'l', 3, r, '#e8c040')
                s.side('head', 'l', 5, r, '#e8c040')
            s.side('head', 'l', 4, 6, '#e8c040')
        elif name == 'closed_eyes':
            for x in (1, 2, 5, 6):
                s.front('head', x, 4, shade(skin, 0.6))
        elif name == 'sleepy':
            for x in (1, 2, 5, 6):
                s.front('head', x, 3, shade(skin, 0.75))
        elif name == 'big_nose_red':
            s.front('head', 3, 5, '#e02020')
            s.front('head', 4, 5, '#e02020')
            s.front('head', 3, 4, '#ff4040')
            s.front('head', 4, 4, '#c01818')
        elif name == 'tattoo_left':     # Dragon's face tattoo
            c = col or '#b02020'
            for (x, r) in ((6, 2), (7, 2), (7, 3), (7, 5), (6, 5), (6, 6), (7, 6), (5, 7)):
                s.front('head', x, r, c)
            s.side('head', 'l', 0, 3, c); s.side('head', 'l', 0, 5, c)
        elif name == 'burn_left':        # Sabo
            c = col or '#c06a60'
            for (x, r) in ((5, 3), (6, 3), (7, 3), (7, 4), (7, 5), (6, 5), (5, 5)):
                s.front('head', x, r, c)
        elif name == 'scarf':
            c = col or '#7a7060'
            for x in range(8):
                for r in (5, 6, 7):
                    s.front('head', x, r, c, 0.06)
            s.band('head', 6, 8, c, noise=0.06)
        elif name == 'mask_killer':
            for x in range(8):
                for r in range(1, 8):
                    s.front('head', x, r, '#ecece8' if (r % 2 or x in (0, 7)) else '#4060a0')
        elif name == 'mask_cp0':        # CP0's white masks: smooth white face, black eye slits, a red line
            for x in range(8):
                for r in range(0, 8):
                    s.front('head', x, r, '#f4f2ee', 0.02)
            for x in (1, 2, 5, 6):
                s.front('head', x, 4, '#141414')
            s.front('head', 3, 1, col or '#8a1a1a'); s.front('head', 4, 1, col or '#8a1a1a')
            s.front('head', 3, 6, '#d8d4cc'); s.front('head', 4, 6, '#d8d4cc')
        elif name == 'bear_ears':       # Kuma / Pacifista hat ears
            c = col or '#2a2a2a'
            s.cap('hat', 'top', None, fn=lambda x, y: c if (y < 2 and x in (0, 1, 6, 7)) else None)
            for r in (0, 1):
                s.side('hat', 'r', 6, r, c); s.side('hat', 'r', 7, r, c)
                s.side('hat', 'l', 0, r, c); s.side('hat', 'l', 1, r, c)
        elif name == 'mask_king':
            for x in range(8):
                for r in range(0, 8):
                    s.front('head', x, r, '#1a1a1e', 0.03)
            s.front('head', 2, 4, '#e02020')
            s.front('head', 5, 4, '#e02020')
        elif name == 'tusks':
            s.front('head', 1, 6, '#f8f8f0')
            s.front('head', 6, 6, '#f8f8f0')
            s.front('head', 1, 5, '#f8f8f0')
            s.front('head', 6, 5, '#f8f8f0')
        elif name == 'horns':
            c = col or '#e8e0d0'
            s.cap('hat', 'top', None, fn=lambda x, y: c if (y in (2, 3) and x in (0, 7)) else None)
            for r in (0, 1):
                s.side('hat', 'r', 6, r, c)
                s.side('hat', 'l', 1, r, c)
        elif name == 'goggles':
            c = col or '#e8c040'
            s.band('hat', 1, 2, '#3a3020')
            for x in (1, 2, 5, 6):
                s.front('hat', x, 1, c)
            s.front('hat', 1, 1, c)
        elif name == 'blush':
            s.front('head', 1, 5, col or '#f0a0a0')
            s.front('head', 6, 5, col or '#f0a0a0')


def col2(e, default):
    return e[2] if isinstance(e, tuple) and len(e) > 2 else default


# ---------------- body ----------------

def paint_top(s, sp):
    t = sp.get('top', {'kind': 'none'})
    skin = sp['skin']
    k = t['kind']
    c = t.get('color', '#e0e0e0')
    c2 = t.get('color2')
    sleeves = t.get('sleeves', 'none' if k in ('vest', 'none', 'bikini') else 'long')
    pat = t.get('pattern')
    pc = t.get('patcol', '#ffffff')

    def cloth(col, row):
        if pat == 'stripes' and row % 3 == 1:
            return pc
        if pat == 'hstripes' and col % 2 == 0:
            return pc
        if pat == 'dots' and (col * 2 + row * 3) % 7 == 0:
            return pc
        if pat == 'checker' and ((col // 2) + (row // 2)) % 2 == 0:
            return pc
        if pat == 'flowers' and (col * 5 + row * 3) % 11 == 0:
            return pc
        if pat == 'stars' and (col * 3 + row * 7) % 13 == 0:
            return pc
        return c

    if k == 'none':
        # bare chest: shading for the chest and stomach
        for x in (3, 4):
            for r in (3, 5, 7):
                s.front('body', x, r, shade(skin, 0.9))
        s.front('body', 2, 3, shade(skin, 0.9))
        s.front('body', 5, 3, shade(skin, 0.9))
    elif k == 'bikini':
        for col in range(24):
            s.w('body', col, 3, cloth(col, 3))
        for x in (1, 2, 5, 6):
            for r in (2, 3, 4):
                s.front('body', x, r, cloth(x, r))
    else:
        rows = 10 if k != 'dress' else 12
        for col in range(24):
            for r in range(rows):
                s.w('body', col, r, cloth(col, r))
        s.cap('body', 'top', c)
        if k in ('open', 'vest'):
            for r in range(0, 9):
                half = 2 if r < 3 else 1
                for x in range(4 - half, 4 + half):
                    s.front('body', x, r, skin)
            s.front('body', 2, 0, shade(c, 0.85)); s.front('body', 5, 0, shade(c, 0.85))
        elif k == 'v':        # shirt with a v neck
            for (x, r) in ((3, 0), (4, 0), (3, 1), (4, 1), (2, 0), (5, 0)):
                s.front('body', x, r, skin)
        elif k == 'suit':
            sh = c2 or '#f0f0f0'
            tie = t.get('color3', '#202020')
            for r in range(0, 7):
                s.front('body', 3, r, sh if r < 1 else tie)
                s.front('body', 4, r, sh if r < 1 else tie)
                if r < 4:
                    s.front('body', 2, r, sh)
                    s.front('body', 5, r, sh)
            s.front('body', 3, 0, sh); s.front('body', 4, 0, sh)
            s.front('body', 1, 8, shade(c, 0.7))
            s.front('body', 1, 5, shade(c, 0.7))
        elif k == 'kimono':
            inner = c2 or skin
            for r in range(0, 5):
                for x in range(3 - min(r, 0), 5):
                    pass
            for (x, r) in ((2, 0), (3, 0), (4, 0), (5, 0), (3, 1), (4, 1), (4, 2), (3, 2), (4, 3)):
                s.front('body', x, r, inner)
            edge = t.get('color3', shade(c, 0.75))
            for (x, r) in ((1, 0), (2, 1), (2, 2), (3, 3), (3, 4), (4, 5), (5, 6), (5, 7)):
                s.front('body', x, r, edge)
        elif k == 'hoodie':
            for r in range(3, 6):
                for x in (2, 3, 4, 5):
                    if (x, r) in ((3, 4), (4, 4), (2, 3), (5, 3), (2, 5), (5, 5)):
                        s.front('body', x, r, c2 or '#202020')
            for col in range(16, 24):
                s.w('body', col, 0, shade(c, 0.85))
                s.w('body', col, 1, shade(c, 0.85))
        elif k == 'robe':     # a shirt that opens a little at the neck
            s.front('body', 3, 0, skin); s.front('body', 4, 0, skin); s.front('body', 3, 1, skin)
    # sleeves
    n = {'none': 0, 'short': 4, 'elbow': 6, 'long': 10, 'full': 12, 'wide': 11}[sleeves]
    sc = t.get('sleeve_color', c)
    for col in range(16):
        for r in range(n):
            s.w('arm', col, r, sc if not pat or k == 'hoodie' else cloth(col, r))
    if n:
        s.cap('arm', 'top', sc)
    if sleeves in ('long', 'wide') and t.get('cuff'):
        s.band('arm', n - 1, n, t['cuff'])


def paint_pants(s, sp):
    p = sp.get('pants')
    if not p:
        return
    c = p['color']
    n = {'long': 12, 'knee': 7, 'short': 5, 'brief': 2, 'capri': 9}[p.get('length', 'long')]
    pat = p.get('pattern')
    pc = p.get('patcol', '#ffffff')

    def cloth(col, r):
        if pat == 'stripes' and col % 2 == 0:
            return pc
        if pat == 'spots' and (col * 3 + r * 5) % 9 == 0:
            return pc
        if pat == 'hstripes' and r % 2 == 0:
            return pc
        if pat == 'dots' and (col * 2 + r * 3) % 7 == 0:
            return pc
        return c

    for col in range(16):
        for r in range(n):
            s.w('leg', col, r, cloth(col, r))
    s.cap('leg', 'top', c)
    if n < 12:
        s.band('leg', n - 1, n, shade(c, 0.8))
    if not sp.get('top', {}).get('kind') == 'dress':
        s.band('body', 10, 12, c)
        s.cap('body', 'bottom', c)
    # a fold between the legs in front
    s.front('leg', 3, 1, shade(c, 0.85))


def paint_shoes(s, sp):
    sh = sp.get('shoes', {'kind': 'sandal'})
    k = sh['kind']
    c = sh.get('color', '#6a4a2a')
    if k == 'sandal':
        s.band('leg', 11, 12, c)
        s.front('leg', 1, 10, c)
        s.front('leg', 2, 10, c)
        s.cap('leg', 'bottom', c)
    elif k == 'geta':
        s.band('leg', 11, 12, c)
        s.front('leg', 1, 10, '#c02020')
        s.front('leg', 2, 10, '#c02020')
        s.cap('leg', 'bottom', c)
    elif k == 'boot':
        s.band('leg', sh.get('from', 7), 12, c)
        s.band('leg', sh.get('from', 7), sh.get('from', 7) + 1, shade(c, 1.2))
        s.cap('leg', 'bottom', shade(c, 0.6))
    elif k == 'shoe':
        s.band('leg', 10, 12, c)
        s.front('leg', 1, 10, shade(c, 1.3))
        s.cap('leg', 'bottom', shade(c, 0.6))
    elif k == 'hoof':
        s.band('leg', 10, 12, c)
        s.cap('leg', 'bottom', c)
    elif k == 'bare':
        s.cap('leg', 'bottom', shade(sp['skin'], 0.8))


def paint_sash(s, sp):
    sa = sp.get('sash')
    if not sa:
        return
    c, r0, n = sa
    s.band('body', r0, r0 + n, c)
    s.front('body', 1, r0 + n, c)   # knot hanging down
    if r0 + n < 12:
        s.front('body', 1, r0 + n, shade(c, 0.85))


def paint_coat(s, sp):
    co = sp.get('coat')
    if not co:
        return
    k = co['kind']
    c = co['color']
    trim = co.get('trim')
    if k == 'cape':
        # draped over the shoulders, sleeves hang empty
        for col in list(range(0, 4)) + list(range(12, 24)):
            for r in range(12):
                s.w('body', col, r, c)
        for r in range(12):
            s.front('body', 0, r, c)
            s.front('body', 7, r, c)
        s.cap('body', 'top', None, fn=lambda x, y: c if y in (0, 3) or x in (0, 7) else None)
        for col in list(range(0, 4)) + list(range(12, 16)):
            for r in range(0, 11):
                s.w('arm', col, r, c)
        s.cap('arm', 'top', c)
        for col in list(range(0, 4)) + list(range(12, 16)):
            for r in range(co.get('length', 9)):
                s.w('leg', col, r, c)
        if trim:
            s.band('arm', 0, 1, trim, cols=range(0, 4))
            for r in range(12):
                s.front('body', 0, r, trim if co.get('trim_front', False) else c)
    elif k in ('long', 'jacket'):
        rows = 12 if k == 'long' else 10
        for col in range(24):
            for r in range(rows):
                if col in FRONT['body'] and 2 <= col - 4 <= 5:
                    continue
                s.w('body', col, r, c)
        s.cap('body', 'top', c)
        n = 11 if co.get('sleeves', True) else 0
        for col in range(16):
            for r in range(n):
                s.w('arm', col, r, c)
        if n:
            s.cap('arm', 'top', c)
            if trim:
                s.band('arm', n - 1, n, trim)
        if k == 'long':
            for col in list(range(0, 4)) + list(range(12, 16)):
                for r in range(co.get('length', 9)):
                    s.w('leg', col, r, c)
        if trim:
            for r in range(rows):
                s.front('body', 1, r, trim)
                s.front('body', 6, r, trim)
    if co.get('collar'):
        cc = co['collar']
        s.band('body', 0, 1, cc, noise=0.1)
        s.cap('body', 'top', cc, noise=0.1)
        s.band('arm', 0, 1, cc, noise=0.1)
        s.front('body', 1, 1, cc, 0.1); s.front('body', 6, 1, cc, 0.1)
    if co.get('kanji'):     # "JUSTICE" on the back, as a block of black marks
        kc = '#1a1a1a'
        marks = ['.##.##.', '#..#..#', '.#####.', '#.#.#.#', '.##.##.', '#.#.#.#']
        for r, line in enumerate(marks):
            for x, ch in enumerate(line):
                if ch == '#':
                    s.back('body', x, 2 + r, kc)
    if co.get('epaulettes'):
        s.cap('arm', 'top', co['epaulettes'])
        s.band('arm', 0, 1, co['epaulettes'])


def paint_hands(s, sp):
    # gloves or markings on the hands
    g = sp.get('gloves')
    if g:
        s.band('arm', 10, 12, g)
        s.cap('arm', 'bottom', g)
    else:
        s.cap('arm', 'bottom', shade(sp['skin'], 0.9))


def build(sp, seed):
    s = Skin(seed)
    skin = sp['skin']
    for part in ('body', 'arm', 'leg'):
        s.fill(part, skin, 0.03)
    paint_face(s, sp)
    paint_top(s, sp)
    paint_pants(s, sp)
    paint_sash(s, sp)
    paint_shoes(s, sp)
    paint_coat(s, sp)
    paint_hands(s, sp)
    paint_hair(s, sp)
    paint_face_extras(s, sp)
    paint_hat(s, sp)
    for fn in sp.get('post', []) if isinstance(sp.get('post'), list) else ([sp['post']] if sp.get('post') else []):
        fn(s)
    return s
