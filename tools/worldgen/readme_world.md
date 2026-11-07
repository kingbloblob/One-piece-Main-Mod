## The world: islands, ores and 80 structures

Everything here is in the **One Piece: World** creative tab, and it also generates by itself in survival.

### Grand Line world type (a new world every seed)

On the *Create New World* screen, click **More World Options → World Type** until it says **Grand Line**.
You get a world that is mostly sea, dotted with islands of every size. Every seed gives a different map, but the
islands always come from the One Piece world, and neighbouring islands usually have different climates, like sailing the Grand Line.
High, rugged land turns into the red **Red Line Cliffs**.

There are **20 island biomes**. Each one has its own animals and monsters, and how dangerous it is decides what spawns:
easy islands have lots of farm animals and only a few, weak monsters; deadly ones have almost no animals and spawn
wither skeletons, blazes and magma cubes in the open. *Passive* animals never attack, *neutral* ones (wolves, polar bears,
pandas, llamas, goats, dolphins) only fight back, *hostile* ones attack on sight.

| Island biome | Danger | Animals (passive and neutral) | Hostile mobs |
| --- | --- | --- | --- |
| East Blue Isle | Easy | cow, sheep, pig, chicken, horse, wolf | zombie, skeleton, spider, creeper, enderman |
| Dressrosa Fields | Easy | donkey, horse, sheep, rabbit, cow, llama | zombie, skeleton, spider, creeper, enderman |
| Zou Forest | Easy | ocelot, fox, rabbit, cat, parrot, panda, wolf | zombie, skeleton, spider, creeper, enderman |
| Sabaody Archipelago | Easy | frog, chicken, parrot | zombie, skeleton, spider, creeper, enderman, slime |
| Totto Land | Medium | sheep, pig, chicken, rabbit, goat, llama | zombie, skeleton, spider, creeper, enderman, zombie villager, slime, witch |
| Wano Country | Medium | rabbit, pig, horse, wolf | zombie, skeleton, spider, creeper, enderman, witch, zombie villager, slime |
| Drum Island | Medium | rabbit, fox, wolf, polar bear, goat | zombie, skeleton, spider, creeper, enderman, witch, zombie villager, slime, stray |
| Elbaph | Medium | sheep, cow, rabbit, wolf, goat, polar bear | zombie, skeleton, spider, creeper, enderman, witch, zombie villager, slime |
| Egghead | Medium | rabbit, fox, polar bear | zombie, skeleton, spider, creeper, enderman, witch, zombie villager, slime, stray |
| Alabasta | Medium | camel, rabbit, armadillo, llama | husk, parched, spider, creeper, zombie, enderman |
| Jaya | Medium | parrot, ocelot, chicken, panda | zombie, skeleton, spider, creeper, enderman, witch, zombie villager, slime |
| Skypiea Upper Yard | Medium | parrot, chicken, rabbit, llama | zombie, skeleton, spider, creeper, enderman, witch, zombie villager, slime |
| Fish-Man Reef | Medium | turtle | drowned, zombie, skeleton |
| Amazon Lily | Hard | parrot, ocelot, panda | spider, witch, creeper, skeleton, zombie |
| Punk Hazard (Frozen Side) | Hard | rabbit, polar bear | stray, skeleton, zombie, creeper, enderman |
| Punk Hazard (Burning Side) | Hard | armadillo | magma cube, husk, skeleton, creeper, blaze |
| Little Garden | Hard | sniffer, parrot, frog, panda | spider, cave spider, zombie, creeper, witch |
| Thriller Bark Mist | Hard | none | zombie, zombie villager, skeleton, bogged, witch, spider |
| Onigashima Wastes | Deadly | none | wither skeleton, blaze, magma cube, husk, creeper |
| Red Line Cliffs | Deadly | goat | wither skeleton, stray, enderman, creeper, skeleton |

These biomes only appear in the Grand Line world type. Find one with `/locate biome onepiece:alabasta` (ids: `east_blue`, `dressrosa`,
`zou`, `sabaody`, `whole_cake`, `wano`, `drum_island`, `elbaph`, `egghead`, `alabasta`, `jaya`, `skypiea`, `fishman_reef`, `amazon_lily`,
`punk_hazard_frozen`, `punk_hazard_burning`, `little_garden`, `thriller_bark`, `onigashima`, `red_line`).

### 80 structures: one lair for every boss, plus 58 places from the story

Every one of the 22 bosses has their own lair (Buggy's Big Top, Crocodile's Rain Dinners, Enel's Shandora, Kaido's Onigashima,
Big Mom's Whole Cake Chateau, Whitebeard's Moby Dick, Blackbeard's Hachinosu, Akainu at Marineford...). The other 58 are places
like Foosha Village, Arlong Park, the Baratie, Water 7's shipyard, Impel Down, Fish-Man Island, Mary Geoise and Laugh Tale.

| Difficulty | How many | What to expect |
| --- | --- | --- |
| Easy | 34 | Villages, bars and ruins. Friendly characters, a few weak zombies or skeletons at most. Common. |
| Medium | 22 | Pirate towns and Marine outposts. 2 to 5 guards, sometimes a weaker boss. |
| Hard | 13 | Fortresses and warships. 4 to 9 tough guards and a strong boss. Rare. |
| Legendary | 11 | Very, very hard: Marineford, Onigashima, Impel Down, Laugh Tale... Up to 16 elite guards, Admirals and Emperors. Very rare, best loot (Laugh Tale even hides a Devil Fruit). |

The full list, with who you meet in each place, is in **structures.md** next to this README.
Find one with `/locate structure onepiece:marineford` (use the id from the list).
Structures appear in normal worlds too, in matching Minecraft biomes (beaches, deserts, jungles, oceans, snowy plains...).

### Ores and materials

- **Seastone (Kairoseki)**: ore under every ocean floor, between y=-48 and y=40. Needs an iron pickaxe. Smelt Raw Seastone into Seastone Ingots.
  Devil Fruit users who hold seastone or stand on a Block of Seastone get Weakness, just like in water.
  - **Seastone Jitte** (Smoker's weapon): as strong as an iron sword, and drains any Devil Fruit user it hits for 5 seconds.
  - **Seastone Cuffs** (2 ingots and an Iron Chain, at the Seastone Workbench): right-click a Devil Fruit user, player or boss, to seal their power for 10 seconds. Used up after one go.
- **Adam wood**: from the Treasure Tree Adam, a rare giant tree in jungles (common in Skypiea, Elbaph and Little Garden). Much tougher than oak. Perfect for ships.
- **Island Cloud**: the soft white ground of the sky islands.

### Where the world files live (and how to change them)

| File or folder | What it does |
| --- | --- |
| `src/main/java/com/onepiecemod/world/` | The new blocks and items, seastone's effect, and dressing up guards (`GuardKit.java`). |
| `src/main/resources/onepiece/guards.json` | Every guard's weapon, armour and health. |
| `src/main/resources/data/onepiece/worldgen/biome/` | One file per island biome: sky colour, plants, and which mobs spawn. |
| `src/main/resources/data/onepiece/worldgen/world_preset/grand_line.json` | The Grand Line world type and which biome goes where. |
| `src/main/resources/data/onepiece/worldgen/density_function/grand_line/continents.json` | How much sea vs. land. Make `-0.3` more negative for more sea, raise `0.55` for smaller islands. |
| `src/main/resources/data/onepiece/worldgen/material_rule/grand_line.json` | The ground blocks of each island (sand in Alabasta, magma on Punk Hazard...). |
| `src/main/resources/data/onepiece/structure/` | The 80 buildings, as `.nbt` files. Load one in game with a Structure Block to edit it. |
| `src/main/resources/data/onepiece/worldgen/structure_set/` | How often each difficulty appears (`spacing` = average distance in chunks). |
| `src/main/resources/data/onepiece/tags/worldgen/biome/has_structure/` | Which biomes each structure can appear in. |
| `src/main/resources/data/onepiece/loot_table/chests/` | What's in the chests (easy, medium, hard, legendary and themed ones). |
| `src/main/resources/assets/onepiece_world/lang/en_us.json` | In-game names for the world blocks, items and biomes. |
| `tools/worldgen/` (next to the zip) | The scripts that generated all of the above, if you'd rather change a design in code. |

Tip: buildings, guards and NPCs only appear in *new* chunks, so explore somewhere you haven't been or make a new world.
