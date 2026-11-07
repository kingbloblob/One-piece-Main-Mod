# Deco generator (building blocks, wood sets, plants)

Makes everything in com.onepiecemod.deco plus its models, textures, loot, tags, recipes and tree/flower worldgen.

    curl the 26.3 client.jar from piston-data.mojang.com and unzip it to VANILLA (only JSON templates are used)
    python3 gen_deco.py VANILLA /tmp/decoout
    python3 install.py /tmp/decoout /mnt/project-files/one-piece-mod/source
    sh /mnt/project-files/one-piece-mod/tools/build.sh && sh /mnt/project-files/one-piece-mod/tools/rebuild-zip.sh

install.py replaces our own files and union-merges shared data/minecraft/tags files.
DecoItems.java, DecoFlowerBlock.java and MikanBushBlock.java are hand-written (not generated).
Where plants grow: data/onepiece/tags/worldgen/biome/has_deco_*.json.
