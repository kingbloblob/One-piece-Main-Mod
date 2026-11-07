# Learning from a 3D model of a Minecraft build

`scripts/mesh_analyze.py` reads a Minecraft build exported as glTF, GLB, FBX (binary) or a zip of one
(nested zips are unpacked), rebuilds the block grid and prints compact numbers. Only analyse builds the
user made or has permission to study; extract techniques and proportions, never recreate the model.

## Contents
- Run it
- What the report contains
- Reading block identities
- Turning results into a technique card
- Limits

## Run it
First check the material names (`python -c "import json;print([m['name'] for m in json.load(open('scene.gltf'))['materials']])"`).
If they are block names (Mineways style: `Block_of_Quartz`, `Wool`, `Stained_Glass`), use
`python scripts/mesh_blocks.py model.zip --out analysis` instead: exact blocks, dye colours from the
atlas, memory-mapped (models of ~500 MB work), writes `grid.npz`, `names.json`, `palette.txt`, renders.
Study `grid.npz` (z is up) with ad-hoc numpy: radial profiles around a centre for domes and towers,
per-height band counts for collars/cornices, unrolled cylinder images for facades, and
`scipy.ndimage.label` for free-floating objects (identical sizes = stamped prefabs).
Otherwise:
`python scripts/mesh_analyze.py model.zip --out analysis [--block SIZE]`
Outputs in `analysis/`: `report.txt`, `analysis.json`, `elevations.png` (top + 4 sides contact sheet),
`tiles_top.png` (most used textures, numbered), `voxels.npz` (grid, per-block texture ids).
Prefer glTF/GLB. FBX works if binary (ASCII FBX and Draco/meshopt-compressed glTF are not supported).
If the FBX has no texture links, textures are matched by file name (the diffuse atlas is chosen
over files named glow/normal/emission).

## What the report contains
Size in blocks, block size in model units, share of sub-block (partial) faces, silhouette per height
band, palette by texture with provisional block names, palette by height third, flat-wall percent per
side, facade rhythm (bay spacing), symmetry of the height map, height steps between neighbouring
columns. Then use ad-hoc scripts on `voxels.npz` for the specifics: height map profiles, spire taper by
connected components, cross-sections, tile shares per role (roof tops vs walls vs height bands).

## Reading block identities
Block size and grid origin come from the geometry. Each surface block gets the atlas tile used by most of its
faces; tiles are found from the faces' exact UV rectangles, so irregular atlases work. Names are nearest by
average colour, so look at `tiles_top.png` and name the textures yourself (stone slab vs stone bricks, copper
stages, iron bars). Record them as inferred.

## Turning results into a technique card
Write `references/techniques/<subject>.md`: overall proportions, height tiers, repeated elements with
spacing, taper schedules, roof profiles, palette roles, a reusable recipe, scaling rules. Label measured vs
inferred. Then add or adjust parts in `mcparts.py` and test with a demo under `examples/`.

## Limits
- Block identities and block states (stair direction, slab half) are guesses; about 50% of faces in
  detailed builds are sub-block geometry.
- Rotated models: only axis-aligned faces are used; the report warns if few faces are aligned.
- Very large grids (over about 4e8 cells) are refused; pass the right `--block`.
- Facade rhythm needs repeated relief; shallow windows can be missed.
