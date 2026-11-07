"""Original pirate-ship GUI sprites: wooden buttons, brass sliders, deck-plank menu backgrounds, rope separators.
Usage: widgets.py <pack assets/minecraft/textures/gui folder>"""
import sys, os
import numpy as np
from PIL import Image

OUT = sys.argv[1]
rng = np.random.default_rng(11)
W = os.path.join(OUT, "sprites/widget")
os.makedirs(W, exist_ok=True)

def save(img, path):
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, path))

def grain(h, w, base, amount=18, seed=0):
    r = np.random.default_rng(seed)
    rows = r.normal(0, 1, (h, 1)) * 0.6 + np.cumsum(r.normal(0, 0.35, (h, w)), axis=1) * 0.05
    streak = np.sin(np.arange(w)[None, :] / (6 + r.random() * 6) + r.random((h, 1)) * 6) * 0.4
    n = rows + streak + r.normal(0, 0.35, (h, w))
    img = np.zeros((h, w, 4))
    img[..., :3] = np.asarray(base, float)[None, None] + n[..., None] * amount * np.array([1, 0.75, 0.5])
    img[..., 3] = 255
    return img

def frame(img, outer, light=None, shadow=None):
    img[0, :, :3] = outer; img[-1, :, :3] = outer; img[:, 0, :3] = outer; img[:, -1, :3] = outer
    if light is not None:
        img[1, 1:-1, :3] = light; img[1:-1, 1, :3] = light
    if shadow is not None:
        img[-2, 1:-1, :3] = shadow; img[1:-1, -2, :3] = shadow
    return img

# --- buttons (200x20, nine slice border 3) ---------------------------------
def plank_button(base, outer, light, shadow, seed):
    b = grain(20, 200, base, 16, seed)
    b[9:11, 2:-2, :3] *= 0.9           # seam between two boards
    return frame(b, outer, light, shadow)

save(plank_button((122, 80, 46), (38, 22, 12), (168, 120, 74), (82, 50, 28), 1), "sprites/widget/button.png")
hi = plank_button((150, 102, 58), (255, 210, 80), (214, 168, 104), (104, 66, 36), 1)
hi[1, 1:-1, :3] = (255, 236, 160)
save(hi, "sprites/widget/button_highlighted.png")
dis = plank_button((70, 62, 56), (24, 20, 18), (92, 84, 76), (50, 44, 40), 2)
save(dis, "sprites/widget/button_disabled.png")

# --- slider track (200x20, border 1) and brass handle (8x20) -----------------
tr = grain(20, 200, (64, 40, 24), 10, 3)
frame(tr, (30, 18, 10), None, None)
save(tr, "sprites/widget/slider.png")
trh = tr.copy(); frame(trh, (255, 210, 80)); save(trh, "sprites/widget/slider_highlighted.png")
def handle(col, outer):
    h = np.zeros((20, 8, 4)); h[..., 3] = 255
    shade = np.linspace(1.25, 0.7, 8)[None, :, None]
    h[..., :3] = np.asarray(col, float) * shade
    h[2::4, 2:6, :3] *= 0.8            # knurled grip
    return frame(h, outer, None, None)
save(handle((196, 150, 60), (40, 26, 10)), "sprites/widget/slider_handle.png")
save(handle((240, 196, 96), (255, 240, 170)), "sprites/widget/slider_handle_highlighted.png")

# --- text fields (200x20, border 1): dark sea-blue with brass rim -----------
tf = np.zeros((20, 200, 4)); tf[..., :3] = (10, 22, 38); tf[..., 3] = 255
save(frame(tf.copy(), (150, 116, 60)), "sprites/widget/text_field.png")
save(frame(tf.copy(), (255, 214, 96)), "sprites/widget/text_field_highlighted.png")

# --- tabs (130x24, borders 2,2,2,0) ---------------------------------------
def tab(base, outer, light, alpha=255, seed=4):
    t = grain(24, 130, base, 14, seed); t[..., 3] = alpha
    t[0, :, :3] = outer; t[:, 0, :3] = outer; t[:, -1, :3] = outer
    t[1, 1:-1, :3] = light; t[1:, 1, :3] = light
    return t
save(tab((96, 62, 36), (38, 22, 12), (130, 90, 54), 230), "sprites/widget/tab.png")
save(tab((124, 84, 48), (255, 210, 80), (170, 124, 76), 240), "sprites/widget/tab_highlighted.png")
save(tab((150, 102, 58), (38, 22, 12), (214, 168, 104)), "sprites/widget/tab_selected.png")
save(tab((166, 116, 66), (255, 210, 80), (232, 190, 120)), "sprites/widget/tab_selected_highlighted.png")

# --- checkboxes (20x20): a little crate; selected ones get a red X ----------
def crate(sel, hl):
    c = grain(20, 20, (126, 84, 48), 12, 5)
    c[6:8, 2:-2, :3] *= 0.8; c[12:14, 2:-2, :3] *= 0.8
    frame(c, (255, 210, 80) if hl else (38, 22, 12), (170, 124, 76), (82, 50, 28))
    if sel:
        for i in range(4, 16):
            for j in (i, 19 - i):
                c[i, j - 1:j + 2, :3] = (200, 30, 26)
                c[i, j - 1, :3] = (120, 16, 14)
    return c
save(crate(False, False), "sprites/widget/checkbox.png")
save(crate(False, True), "sprites/widget/checkbox_highlighted.png")
save(crate(True, False), "sprites/widget/checkbox_selected.png")
save(crate(True, True), "sprites/widget/checkbox_selected_highlighted.png")

# --- scroll bar (6x32, border 1): brass bar in a dark slot ---------------
sc = np.zeros((32, 6, 4)); sc[..., 3] = 255
sc[..., :3] = np.array([210, 164, 70]) * np.linspace(1.15, 0.75, 6)[None, :, None]
save(frame(sc, (60, 38, 14)), "sprites/widget/scroller.png")
sb = np.zeros((32, 6, 4)); sb[..., :3] = (20, 12, 8); sb[..., 3] = 200
save(sb, "sprites/widget/scroller_background.png")

# --- menu backgrounds (tiled, 32 GUI units per tile): ship deck planks -----
def deck(alpha, dark, seed):
    n = 64
    t = np.zeros((n, n, 4))
    r = np.random.default_rng(seed)
    for row in range(4):                      # 4 boards per tile
        y0 = row * 16
        board = grain(16, n * 2, (112, 70, 36), 16, seed * 10 + row)
        off = r.integers(0, n)
        t[y0:y0 + 16] = np.roll(board, -off, axis=1)[:, :n]
        t[y0, :, :3] *= 0.55                  # gap between boards
        t[y0 + 1, :, :3] *= 1.1
        seam = (row * 23 + 11) % n            # board ends, staggered per row
        t[y0:y0 + 16, seam, :3] *= 0.55
        for nx in (seam - 3, seam + 3):       # nails
            t[y0 + 4, nx % n, :3] = (40, 34, 30); t[y0 + 11, nx % n, :3] = (40, 34, 30)
    t[..., :3] *= dark
    t[..., 3] = alpha
    return t
save(deck(205, 0.68, 1), "menu_background.png")
save(deck(225, 0.5, 2), "menu_list_background.png")
save(deck(160, 0.62, 1), "inworld_menu_background.png")
save(deck(185, 0.48, 2), "inworld_menu_list_background.png")
save(deck(235, 0.62, 3), "tab_header_background.png")

# --- header/footer separators (32x2): a twisted rope ----------------------
def rope(alpha=255):
    s = np.zeros((2, 32, 4))
    for x in range(32):
        for y in range(2):
            s[y, x, :3] = (214, 176, 112) if (x + y) % 4 < 2 else (120, 88, 48)
    s[..., 3] = alpha
    return s
for name in ("header_separator", "footer_separator", "inworld_header_separator", "inworld_footer_separator"):
    save(rope(), name + ".png")
# --- tooltips (100x100 nine slice; content starts 9 px in, like vanilla's layout) ---
os.makedirs(os.path.join(OUT, "sprites/tooltip"), exist_ok=True)
bg = np.zeros((100, 100, 4))
bg[8:92, 9:91] = (34, 20, 12, 242); bg[9:91, 8:92] = (34, 20, 12, 242)
save(bg, "sprites/tooltip/background.png")
fr = np.zeros((100, 100, 4))
for y in range(9, 91):
    t = (y - 9) / 81
    col = np.array([236, 190, 84]) * (1 - t) + np.array([150, 96, 40]) * t
    fr[y, 9] = (*col, 255); fr[y, 90] = (*col, 255)
fr[9, 10:90] = (236, 190, 84, 255); fr[90, 10:90] = (150, 96, 40, 255)
fr[9, 9, 3] = fr[9, 90, 3] = fr[90, 9, 3] = fr[90, 90, 3] = 0
save(fr, "sprites/tooltip/frame.png")

# --- popup box (236x34, border 6): dark wood with a brass rim ---------------
pp = grain(34, 236, (52, 32, 18), 10, 9)
pp[0, :, 3] = 0; pp[-1, :, 3] = 0; pp[:, 0, 3] = 0; pp[:, -1, 3] = 0
pp[1, 1:-1, :3] = (200, 156, 70); pp[-2, 1:-1, :3] = (120, 80, 34); pp[1:-1, 1, :3] = (200, 156, 70); pp[1:-1, -2, :3] = (120, 80, 34)
pp[2, 2:-2, :3] = (20, 12, 6); pp[-3, 2:-2, :3] = (20, 12, 6); pp[2:-2, 2, :3] = (20, 12, 6); pp[2:-2, -3, :3] = (20, 12, 6)
os.makedirs(os.path.join(OUT, "sprites/popup"), exist_ok=True)
save(pp, "sprites/popup/background.png")
print("widgets done")
