"""verify.py: cheap numeric checks of a BigBuild against research targets.

Use these BEFORE viewing preview images: a few printed numbers cost a fraction of an
image's tokens.

    from verify import measure, silhouette, count_openings, report
    print(measure(b))                         # size, height/width ratio, solid blocks
    print(silhouette(b, bands=10))            # footprint width per height band
    print(count_openings(b, "x", fixed=1, y=2, start=60, end=90))   # arches/windows on a line
    print(report(b, {"size_y": (110, 125), "height_to_width": (0.25, 0.32)}))
"""
import numpy as np


def measure(b):
    lo, hi = b.bounds()
    size = tuple(int(h - l + 1) for l, h in zip(lo, hi))
    return {"size_x": size[0], "size_y": size[1], "size_z": size[2],
            "height_to_width": round(size[1] / max(size[0], size[2]), 3),
            "solid_blocks": int(sum(n for _, n in b.materials()))}


def silhouette(b, bands=10):
    """[(y_from, y_to, width_x, width_z, columns_occupied)] per height band."""
    lo, hi = b.bounds()
    ys = np.linspace(lo[1], hi[1] + 1, bands + 1).astype(int)
    rows = []
    for i in range(bands):
        ya, yb = int(ys[i]), int(max(ys[i + 1] - 1, ys[i]))
        occ = (b.get_region(lo[0], ya, lo[2], hi[0], yb, hi[2]) > 1).any(axis=1)
        if occ.any():
            xs = np.nonzero(occ.any(axis=1))[0]; zs = np.nonzero(occ.any(axis=0))[0]
            rows.append((ya, yb, int(xs[-1] - xs[0] + 1), int(zs[-1] - zs[0] + 1), int(occ.sum())))
        else:
            rows.append((ya, yb, 0, 0, 0))
    return rows


def count_openings(b, axis, fixed, y, start, end):
    """Number of gaps (windows, arches, gates) bounded by solid blocks on both sides
    along a line at height y. axis 'x': line (start..end, y, fixed); 'z': (fixed, y, start..end)."""
    if axis == "x":
        line = b.get_region(start, y, fixed, end, y, fixed)[:, 0, 0]
    else:
        line = b.get_region(fixed, y, start, fixed, y, end)[0, 0, :]
    solid = line > 1
    n, i, runs = len(solid), 0, 0
    while i < n:
        if not solid[i]:
            j = i
            while j < n and not solid[j]:
                j += 1
            if i > 0 and j < n:
                runs += 1
            i = j
        else:
            i += 1
    return runs


def report(b, targets):
    """targets: {metric: value or (min, max)}; metrics are keys of measure(). A bare
    number allows +-10%. Returns a compact PASS/FAIL table."""
    m = measure(b)
    out = []
    for k, t in targets.items():
        lo, hi = (t if isinstance(t, tuple) else (t * 0.9, t * 1.1))
        v = m[k]
        out.append(f"{'PASS' if lo <= v <= hi else 'FAIL'}  {k}: {v} (want {lo:g}..{hi:g})")
    return "\n".join(out)


def flatness(b, patch=6):
    """Percent of each side's visible wall area that is a flat, single-material patch
    (patch x patch blocks of identical depth and block). High numbers mean blank walls:
    above ~35% on a facade people will see, add relief, trim, windows or a module."""
    res = {}
    for name, (ids, hit, depth) in b.elevation_maps().items():
        h, w = hit.shape
        flat = total = 0
        for i in range(0, h - patch + 1, patch):
            for j in range(0, w - patch + 1, patch):
                hh = hit[i:i + patch, j:j + patch]
                if hh.mean() < 0.9:
                    continue
                total += 1
                d = depth[i:i + patch, j:j + patch]; t = ids[i:i + patch, j:j + patch]
                if d.min() == d.max() and (t == t.flat[0]).all():
                    flat += 1
        res[name] = round(100 * flat / total, 1) if total else 0.0
    return res
