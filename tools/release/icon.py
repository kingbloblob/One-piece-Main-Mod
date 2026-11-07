import math, sys
from PIL import Image, ImageDraw, ImageFilter
N = 1600  # supersample
img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
c = N // 2
# sea badge: radial gradient
R = int(N * 0.47)
for r in range(R, 0, -4):
    t = r / R
    col = (int(20 + 30 * (1 - t)), int(70 + 90 * (1 - t)), int(120 + 80 * (1 - t)), 255)
    d.ellipse([c - r, c - r, c + r, c + r], fill=col)
# waves at bottom
wave = Image.new("RGBA", (N, N), (0, 0, 0, 0))
wd = ImageDraw.Draw(wave)
for k, (y0, col) in enumerate([(0.70, (230, 245, 255, 200)), (0.80, (180, 220, 245, 170))]):
    pts = []
    for x in range(0, N + 1, 8):
        y = N * y0 + math.sin(x / N * math.pi * 6 + k) * N * 0.018
        pts.append((x, y))
    pts += [(N, N), (0, N)]
    wd.polygon(pts, fill=(15 + 10 * k, 60 + 10 * k, 110 + 10 * k, 255))
    wd.line(pts[:-2], fill=col, width=int(N * 0.012))
mask = Image.new("L", (N, N), 0)
ImageDraw.Draw(mask).ellipse([c - R, c - R, c + R, c + R], fill=255)
img.paste(wave, (0, 0), Image.composite(wave.split()[3], Image.new("L", (N, N), 0), mask))
# fruit body: overlapping lobes
fx, fy, fr = c, int(N * 0.50), int(N * 0.25)
fruit = Image.new("RGBA", (N, N), (0, 0, 0, 0))
fd = ImageDraw.Draw(fruit)
lobes = [(0, -0.30, 0.62), (-0.52, -0.02, 0.58), (0.52, -0.02, 0.58), (-0.28, 0.38, 0.6), (0.28, 0.38, 0.6), (0, 0.08, 0.6)]
def swirl(x, y, r, w):
    pts = []
    for i in range(140):
        a = i / 140 * math.pi * 2.4 - math.pi / 2
        rr = r * (1 - i / 150)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    fd.line(pts, fill=(78, 24, 112, 255), width=w, joint="curve")
for dx, dy, s in lobes:
    r = fr * s
    x, y = fx + dx * fr, fy + dy * fr
    fd.ellipse([x - r - 16, y - r - 16, x + r + 16, y + r + 16], fill=(40, 10, 60, 255))
    fd.ellipse([x - r, y - r, x + r, y + r], fill=(135, 55, 180, 255))
    swirl(x, y, r * 0.55, int(N * 0.017))
# highlight
fd.ellipse([fx - fr * 0.85, fy - fr * 0.40, fx - fr * 0.60, fy - fr * 0.22], fill=(220, 180, 245, 150))
img = Image.alpha_composite(img, fruit)
d = ImageDraw.Draw(img)
# stem + leaf
sx, sy = fx, fy - fr * 0.85
d.line([(sx, sy + 20), (sx + N * 0.03, sy - N * 0.09)], fill=(70, 120, 40, 255), width=int(N * 0.03))
d.ellipse([sx + N * 0.01, sy - N * 0.13, sx + N * 0.17, sy - N * 0.06], fill=(30, 70, 25, 255))
d.ellipse([sx + N * 0.02, sy - N * 0.125, sx + N * 0.16, sy - N * 0.068], fill=(90, 170, 60, 255))
# rope ring
ring = int(N * 0.035)
d.ellipse([c - R, c - R, c + R, c + R], outline=(110, 75, 30, 255), width=ring)
for i in range(72):
    a = i / 72 * 2 * math.pi
    x, y = c + math.cos(a) * (R - ring / 2), c + math.sin(a) * (R - ring / 2)
    q = ring * 0.42
    d.line([(x - q * math.cos(a + 0.9), y - q * math.sin(a + 0.9)), (x + q * math.cos(a + 0.9), y + q * math.sin(a + 0.9))], fill=(225, 185, 100, 255), width=int(ring * 0.32))
out = sys.argv[1]
img.resize((128, 128), Image.LANCZOS).save(out + "/icon.png")
img.resize((400, 400), Image.LANCZOS).save(out + "/curseforge-logo.png")
img.resize((512, 512), Image.LANCZOS).save(out + "/preview.png")
