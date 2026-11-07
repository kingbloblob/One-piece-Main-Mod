# Furniture generator (tables, chairs, shelves, rugs, crates, ship and kitchen props)

Makes everything in com.onepiecemod.furniture plus models, textures, loot, tags, recipes, lang and the Journal entries.

    python3 gen_furniture.py /mnt/project-files/one-piece-mod/source [vanilla data/minecraft/recipe dir, to check recipe clashes]
    python3 ../journal/gen_journal.py /mnt/project-files/one-piece-mod/source
    python3 merge_descriptions.py /mnt/project-files/one-piece-mod/source
    sh /mnt/project-files/one-piece-mod/tools/build.sh && sh /mnt/project-files/one-piece-mod/tools/rebuild-zip.sh

Add a block in props.py (boxes are pixels, model drawn facing north; "mount" WALL/CEILING, "seat" height, "light", "solid", "climbable", "storage" 9 or 27 slots to open it like a chest).
FurnitureBlock.java, StorageFurnitureBlock.java, FurnitureStorageBlockEntity.java, SeatEntity.java, Furniture.java and client/FurnitureClient.java are hand-written.
Shared minecraft tag files (mineable/axe, mineable/pickaxe, climbable) are union-merged, never replaced.
