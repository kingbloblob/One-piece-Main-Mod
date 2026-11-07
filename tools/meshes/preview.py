"""Quick still pictures of a meshkit.Mesh (rest pose), to check shapes before trying them in the game.
Painter's algorithm with simple lighting; good enough to judge silhouettes and colours."""
import math

import numpy as np
from PIL import Image, ImageDraw

from meshkit import rot_matrix


def render(mesh, yaw=0.0, pitch=8.0, size=700, bg=(235, 235, 240), box=None):
    quads = []
    for name, q in mesh.quads.items():
        quads.extend(q)
    if not quads:
        return Image.new('RGB', (size, size), bg)
    P = np.array([[c[0] for c in q] for q in quads], dtype=float)       # n,4,3
    Nn = np.array([[c[1] for c in q] for q in quads], dtype=float)
    C = np.array([[c[2][:3] for c in q] for q in quads], dtype=float)
    G = np.array([[1.0 if len(c[2]) > 3 and c[2][3] else 0.0 for c in q] for q in quads])
    # camera looks at the model's front (-z) from yaw degrees round to the model's right
    R = rot_matrix(-pitch, 0, 0) @ rot_matrix(0, yaw, 0)
    Pc = P @ R.T
    Nc = Nn @ R.T
    lo, hi = P.reshape(-1, 3).min(0), P.reshape(-1, 3).max(0)
    if box:
        lo, hi = np.array(box[0], dtype=float), np.array(box[1], dtype=float)
    span = max(hi[1] - lo[1], (hi[0] - lo[0]), 1e-3) * 1.08
    cy = (lo[1] + hi[1]) / 2
    sc = size / span
    sx = size / 2 + Pc[:, :, 0] * sc * -1.0  # model +x (its right) shows on the viewer's left when facing us
    sy = size / 2 - (Pc[:, :, 1] - (cy * math.cos(math.radians(pitch)))) * sc
    depth = Pc[:, :, 2].mean(1)  # camera at -z: smaller z is nearer
    L = np.array([0.35, 0.75, -0.55]); L /= np.linalg.norm(L)
    lam = np.clip((Nc * L).sum(2), -1, 1)
    # double-sided: flip normals facing away from camera
    lam = np.where(Nc[:, :, 2] > 0, np.clip((-Nc * L).sum(2), -1, 1), lam)
    lit = 0.45 + 0.55 * np.clip(lam, 0, 1)
    lit = np.where(G > 0, 1.0, lit)
    col = (C * lit[:, :, None]).mean(1).clip(0, 255).astype(int)
    img = Image.new('RGB', (size, size), bg)
    d = ImageDraw.Draw(img)
    for i in np.argsort(-depth):
        pts = [(sx[i, k], sy[i, k]) for k in range(4)]
        d.polygon(pts, fill=tuple(col[i]))
    return img


def sheet(mesh, path, size=600):
    views = [render(mesh, 0, 6, size), render(mesh, -35, 10, size), render(mesh, 90, 4, size), render(mesh, 180, 8, size)]
    out = Image.new('RGB', (size * len(views), size), (255, 255, 255))
    for i, v in enumerate(views):
        out.paste(v, (i * size, 0))
    out.save(path)


def head(mesh, path, center, r, size=500):
    box = ([center[0] - r, center[1] - r, 0], [center[0] + r, center[1] + r, 0])
    views = [render(mesh, 0, 4, size, box=box), render(mesh, -35, 6, size, box=box)]
    out = Image.new('RGB', (size * 2, size), (255, 255, 255))
    for i, v in enumerate(views):
        out.paste(v, (i * size, 0))
    out.save(path)
