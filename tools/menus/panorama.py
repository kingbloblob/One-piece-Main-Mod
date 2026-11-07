"""Original ocean panorama for the One Piece menus: open sea at golden hour, islands, a pirate ship.
Writes panorama_0..5.png (front, right, back, left, up, down) into the given folder."""
import sys, math
import numpy as np
from PIL import Image

OUT = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
rng = np.random.default_rng(7)

# value noise --------------------------------------------------------------
GRID = rng.random((256, 256))
def vnoise(x, y):
    xi = np.floor(x).astype(int); yi = np.floor(y).astype(int)
    xf = x - xi; yf = y - yi
    u = xf * xf * (3 - 2 * xf); v = yf * yf * (3 - 2 * yf)
    def g(a, b): return GRID[(a) & 255, (b) & 255]
    return (g(xi, yi) * (1 - u) * (1 - v) + g(xi + 1, yi) * u * (1 - v)
            + g(xi, yi + 1) * (1 - u) * v + g(xi + 1, yi + 1) * u * v)
def fbm(x, y, oct=5):
    s = 0; a = 0.5; f = 1
    for _ in range(oct):
        s += a * vnoise(x * f, y * f); f *= 2.03; a *= 0.5
    return s

FACES = [  # forward, right, up
    ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
    ((1, 0, 0), (0, 0, 1), (0, 1, 0)),
    ((0, 0, 1), (-1, 0, 0), (0, 1, 0)),
    ((-1, 0, 0), (0, 0, -1), (0, 1, 0)),
    ((0, 1, 0), (1, 0, 0), (0, 0, 1)),
    ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
]

SUN_AZ = math.radians(-35)   # a little left of the starting view
SUN_EL = math.radians(9)
HORIZON = -0.035             # camera sits above the water, so the horizon dips a bit

def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t

def island_profile(az):
    """Height (as elevation angle) of land along the horizon for azimuth az (radians)."""
    h = np.zeros_like(az)
    for center, width, height, seed in [(0.55, 0.32, 0.075, 1), (2.2, 0.5, 0.05, 2), (-2.4, 0.22, 0.11, 3), (3.05, 0.15, 0.035, 4)]:
        d = np.angle(np.exp(1j * (az - center))) / width
        bump = np.clip(1 - d * d, 0, None) ** 0.8
        rough = 0.75 + 0.5 * fbm(az * 9 + seed * 10, np.full_like(az, seed * 3.1), 4)
        h = np.maximum(h, height * bump * rough)
    return h

def render(face):
    f, r, u = (np.array(v, float) for v in face)
    ys, xs = np.mgrid[0:N, 0:N]
    a = (xs + 0.5) / N * 2 - 1
    b = 1 - (ys + 0.5) / N * 2
    d = f[None, None] + a[..., None] * r + b[..., None] * u
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    dx, dy, dz = d[..., 0], d[..., 1], d[..., 2]
    el = np.arcsin(np.clip(dy, -1, 1))
    az = np.arctan2(dx, -dz)  # 0 = straight ahead (north), positive = right
    sun = np.array([math.sin(SUN_AZ) * math.cos(SUN_EL), math.sin(SUN_EL), -math.cos(SUN_AZ) * math.cos(SUN_EL)])
    cs = np.clip((d * sun).sum(-1), -1, 1)

    # sky ------------------------------------------------------------------
    t = np.clip((el - HORIZON) / 1.2, 0, 1) ** 0.55
    sky = mix((255, 196, 140), (58, 112, 196), t)
    sky = mix(sky, (40, 78, 160), np.clip((el - 0.7) / 0.9, 0, 1))
    glow = np.clip((cs - 0.55) / 0.45, 0, 1) ** 2.2
    sky = mix(sky, (255, 214, 150), glow * 0.85)
    sky = mix(sky, (255, 250, 225), np.clip((cs - 0.9975) / 0.0015, 0, 1))
    # clouds on a plane above
    py = np.maximum(dy - HORIZON + 0.02, 0.02)
    cx, cz = dx / py * 0.9, dz / py * 0.9
    c = fbm(cx * 1.1 + 40, cz * 2.2 + 40, 6)
    cover = np.clip((c - 0.5) * 3.2, 0, 1) * np.clip((el - HORIZON) * 8, 0, 1)
    cshade = fbm(cx * 1.1 + 40.4, cz * 2.2 + 40.6, 6)
    cloud_col = mix((255, 236, 214), (178, 160, 182), np.clip((cshade - c) * 6 + 0.4, 0, 1))
    cloud_col = mix(cloud_col, (255, 222, 170), glow * 0.7)
    sky = mix(sky, cloud_col, cover * 0.9)

    # sea ------------------------------------------------------------------
    depth = np.clip((HORIZON - el) / 0.5, 0, 1) ** 0.6
    sea = mix((112, 158, 196), (14, 52, 98), depth)
    pd = np.maximum(HORIZON - dy + 0.002, 0.002)
    wx, wz = dx / pd, dz / pd
    w = fbm(wx * 0.9, wz * 2.6, 5)
    sea = mix(sea, (190, 220, 235), np.clip((w - 0.62) * 4, 0, 1) * (1 - depth * 0.5) * 0.55)
    sea = mix(sea, (8, 34, 70), np.clip((0.4 - w) * 3, 0, 1) * 0.5)
    # sun glitter road
    refl = np.array([sun[0], -sun[1], sun[2]])
    rc = np.clip((d * refl).sum(-1), -1, 1)
    road = np.clip((rc - 0.93) / 0.07, 0, 1) ** 1.5
    sparkle = (vnoise(wx * 6, wz * 18) > 0.62).astype(float)
    sea = mix(sea, (255, 226, 160), road * (0.35 + 0.65 * sparkle))
    # haze at the horizon
    sea = mix(sea, (230, 190, 160), np.clip(1 - (HORIZON - el) / 0.03, 0, 1) * 0.6)

    img = np.where((el > HORIZON)[..., None], sky, sea)

    # islands ----------------------------------------------------------------
    h = island_profile(az)
    land = (el > HORIZON) & (el < HORIZON + h)
    rel = np.clip((el - HORIZON) / np.maximum(h, 1e-4), 0, 1)
    tex = fbm(az * 60, el * 60, 4)
    land_col = mix((44, 92, 60), (96, 130, 92), tex * 0.6 + rel * 0.3)
    land_col = mix(land_col, (196, 170, 132), np.clip(np.abs(np.angle(np.exp(1j * (az - 3.05)))) < 0.2, 0, 1) * 0.0)
    land_col = mix(land_col, (230, 208, 160), np.clip((0.12 - rel) * 12, 0, 1) * 0.9)  # beach
    land_col = mix(land_col, (220, 170, 150), 0.25)  # atmospheric haze
    img = np.where(land[..., None], land_col, img)
    # palm trees on the near island
    for paz in (0.38, 0.47, 0.66, 0.74):
        base = HORIZON + island_profile(np.array([paz]))[0] * 0.9
        top = base + 0.045
        trunk = (np.abs(az - paz - (el - base) * 0.25) < 0.0028) & (el > base - 0.005) & (el < top)
        img = np.where(trunk[..., None], np.array([70, 56, 46.0]), img)
        for k in range(6):
            ang = k / 6 * math.pi * 2 + 0.3
            lx = paz + 0.0112 + math.cos(ang) * 0.022
            ly = top + math.sin(ang) * 0.011 - 0.006
            for s in np.linspace(0, 1, 14):
                px = paz + (top - base) * 0.25 + (lx - paz - (top - base) * 0.25) * s
                py2 = top + (ly - top) * s - 0.006 * s * s
                leaf = (az - px) ** 2 + ((el - py2) * 1.0) ** 2 < (0.0045 * (1 - s * 0.7)) ** 2
                img = np.where(leaf[..., None], np.array([34, 70, 46.0]), img)

    img = draw_ship(img, az, el)
    return np.clip(img, 0, 255).astype(np.uint8)

def draw_ship(img, az, el):
    """A small three-masted pirate ship, left of the sun, seen from the side (original design)."""
    sx, sy, s = math.radians(-12), HORIZON - 0.018, 0.2  # position and size (radians)
    x = (az - sx) / s; y = (el - sy) / s
    dark = np.array([46, 30, 26.0]); sail = np.array([236, 222, 196.0]); flag = np.array([20, 20, 22.0])
    hull = (y > 0) & (y < 0.16) & (np.abs(x) < 0.5 - (0.16 - y) * 1.0) | ((y > 0.1) & (y < 0.22) & (x > -0.58) & (x < -0.3))
    img = np.where(hull[..., None], dark, img)
    stripe = (y > 0.1) & (y < 0.125) & (np.abs(x) < 0.43)
    img = np.where(stripe[..., None], np.array([150, 60, 40.0]), img)
    for mx, mh in ((-0.25, 0.75), (0.02, 0.92), (0.28, 0.7)):
        mast = (np.abs(x - mx) < 0.012) & (y > 0.12) & (y < mh)
        img = np.where(mast[..., None], dark, img)
        for lo, hi, wd in ((0.26, 0.48, 0.14), (0.5, mh - 0.08, 0.11)):
            bulge = 0.025 * np.sin(np.clip((y - lo) / (hi - lo), 0, 1) * math.pi)
            sl = (y > lo) & (y < hi) & (np.abs(x - mx - bulge) < wd - (y - lo) * 0.08)
            img = np.where(sl[..., None], sail, img)
        fl = (x > mx) & (x < mx + 0.1) & (y > mh - 0.07) & (y < mh) & (y < mh - (x - mx) * 0.2)
        img = np.where(fl[..., None], flag, img)
    # tiny white skull dot on the main flag
    skull = ((x - 0.07) ** 2 + (y - 0.875) ** 2) < 0.012 ** 2
    img = np.where(skull[..., None], np.array([240, 240, 240.0]), img)
    bow = (y > 0.13) & (y < 0.2) & (x > 0.45) & (x < 0.62) & (y > 0.13 + (x - 0.45) * 0.3)
    img = np.where(bow[..., None], dark, img)
    return img

for i, face in enumerate(FACES):
    Image.fromarray(render(face)).save(f"{OUT}/panorama_{i}.png")
    print("face", i)
