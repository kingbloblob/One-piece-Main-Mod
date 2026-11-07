# Ships: notes for the first build

The ship code (`com.onepiecemod.ship`) was written without being able to compile it: the cloud sandbox
can't download Minecraft 26.3 or Fabric. These are the places most likely to need a small rename when
it is first built. If one fails, look up the new name in the Minecraft 26.3 sources (IntelliJ: Ctrl+click
a vanilla class) and adjust. Paste any error into Claude if you get stuck.

Checked on 2026-10-23 against vanilla 26.3 data (misode/mcmeta) and Fabric API's 26.3 source, and fixed:
loot tables (new `modifier` / `condition` format), recipes, tags, models, item and blockstate files, texture names,
Fabric payload registration (`clientboundPlay` / `serverboundPlay`), the GUI (`extractRenderState` + `GuiGraphicsExtractor`),
`CameraRenderState` package, block drawing on ships (`BlockModelResolver` + `BlockModelRenderState`), overlay messages
(`sendOverlayMessage`), and right-clicking ships (now through Fabric's `UseEntityCallback`).

Still unconfirmed (no source for these was reachable):

| Where | What it assumes |
| --- | --- |
| `client/FlagDrawing.java` | `RenderTypes.entityCutoutNoCull(Identifier)` (the `RenderTypes` class itself is confirmed). `new DynamicTexture(Supplier<String>, NativeImage)`. `NativeImage.setPixel(x, y, argb)`. |
| `client/FlagRenderer.java` | `BlockEntityRenderer<T, S>` method `extractRenderState(..., Vec3 cameraPos, ModelFeatureRenderer.CrumblingOverlay)`. |
| `ShipEntity.java` | `isLocalInstanceAuthoritative()`, `positionRider(Entity, MoveFunction)`, `getViewYRot(float)`. Other players see the ship move without smoothing; adding the 26.3 interpolation handler would make it glide. |
| `ShipAssembler.java` | `Block.UPDATE_SUPPRESS_DROPS`, `Clearable.tryClear`. (`saveWithFullMetadata`, `loadStatic`, `snapTo` are confirmed.) |

How it works, in one paragraph: right-clicking the Ship's Wheel flood-fills every connected non-natural block,
saves each block state (plus block-entity NBT such as chest contents) relative to the ship's centre, removes the
blocks, and spawns one `onepiece:ship` entity that carries them. The entity floats by keeping its saved waterline at the
sea surface, is steered by its first passenger like a boat (the captain's client simulates it, as vanilla does for
boats and horses), and is drawn block by block by `ShipRenderer`. Docking snaps the heading to the nearest
quarter turn, checks the space is free, and places the rotated blocks back.

Hooks for other features:
- `ShipEntity.windAt` (Level, BlockPos -> 0..1): multiplies sail speed. The Calm Belt sets it to 0.
- Ships are ridden entities, so anything that dismounts riders (Sea Kings) works on them.
- Performance: every ship block is drawn each frame. Fine for normal ships; very large ones may lower FPS.
  A later improvement is to cache the ship's mesh.
