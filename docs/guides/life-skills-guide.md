# Life Skills

Four skills that level on their own by doing the work: **Farming, Mining, Cooking and Smithing**.
Each goes from 1 to 50. Type `/skills` to see your levels and the next perk, `/skills info mining` for every perk.

## How you earn XP

| Skill | What trains it | XP |
|---|---|---|
| Farming | Breaking a fully grown crop (wheat, carrots, potatoes, beetroot, nether wart, cocoa, melons, modded crops with an age) | 3 per crop, melon 2 |
| Mining | Breaking an ore without Silk Touch | coal 2, copper/quartz/sulfur 3, iron/redstone 4, lapis 5, gold/tamahagane/wapometal 6, Shandora gold 8, seastone 10, diamond 12, emerald/kokuto 15, ancient debris 20 |
| Mining | Breaking stone, deepslate, netherrack... | 1 per 10 blocks |
| Cooking | Taking food out of a furnace or smoker, or crafting food | 2 per item |
| Cooking | Ship's Galley dishes | 6 per item |
| Smithing | Crafting tools, weapons and armour (crafting table, smithing table) | wood/leather 1, iron about 6, diamond 13 to 39, depends on durability |
| Smithing | Swordsmith's Forge, Seastone Workbench, Shipwright's Bench | at least 8 per gear item, 3 for anything else |
| Smithing | Taking smelted ingots out of a furnace | 1 per ingot |

Level 1 to 2 takes 40 XP and each level takes 10 more than the last. Level 50 takes 13,720 XP in total,
so maxing a skill is a long-term goal. Every level gained also gives **5 + level Pirate XP**.
Creative mode doesn't train skills. Silk Touch ores, pumpkins and sugar cane give nothing, so nothing can be placed and broken for free XP.

## Perks

Every skill has a small bonus that grows each level, plus milestones at 10, 25 and 50.

| Skill | Every level | 10 | 25 | 50 |
|---|---|---|---|---|
| Farming | +0.5% chance to harvest twice (25% at 50) | **Green Thumb**: crops replant themselves if you carry the seed | **Fertile Touch**: 15% chance a harvest grows nearby crops a stage | **Bumper Crop**: the double-harvest roll happens twice |
| Mining | +0.4% chance of double ore drops (20% at 50) | **Steady Pick**: Haste I for 10 s after an ore | **Hard Hat**: Haste II instead | **Prospector**: ores drop extra experience |
| Cooking | +0.5% chance of an extra portion when cooking | **Hearty Eater**: every meal fills 1 more hunger | **Warm Meal**: Regeneration I for 5 s after eating | **Master Chef**: extra portions give 2, meals fill 2 more |
| Smithing | Crafted gear gets +1% durability (shows "Forged by you" on the item) | **Field Repair**: held tool mends 1 durability every 30 s | **Smith's Mark**: 15% chance crafted gear is Fine (Unbreaking I) | **Master Smith**: durability bonus doubles (+100%), Fine gear gets Unbreaking II |

## Commands

- `/skills`: your levels, progress bars and next perk
- `/skills info <skill>`: all perks for one skill
- Operators: `/skills set <player> <skill> <level>`, `/skills addxp <player> <skill> <amount>`

## For other features (API)

Package `com.onepiecemod.lifeskill`. Everything goes through `LifeSkills`:

```java
LifeSkills.level(player, LifeSkill.MINING);                 // 1..50
LifeSkills.has(player, LifeSkill.SMITHING, 25);             // gate something
LifeSkills.require(serverPlayer, LifeSkill.FARMING, 15, "plant Sea Cherries"); // false + red message if too low
LifeSkills.addXp(serverPlayer, LifeSkill.COOKING, 20);      // quest reward, custom machine
LifeSkills.registerBlock(MY_ORE, LifeSkill.MINING, 9);       // custom XP for a block (call in your initialize())
LifeSkills.registerCraft(MY_DISH, LifeSkill.COOKING, 12);    // custom XP per crafted item
LifeSkillHooks.onStationCraft(player, "ships_galley", stack); // a new crafting station handing out a stack
```

Data only, no Java:
- Ores ending in `_ore` or in `#c:ores` count automatically (XP from the name, see the table).
  Crops that extend `CropBlock` (or have an `age` property and are in the tag) count automatically.
- Add blocks to `data/onepiece/tags/block/life_skill/farming.json` or `mining.json`,
  items to `data/onepiece/tags/item/life_skill/cooking.json` or `smithing.json`.
- Items in `data/onepiece/tags/item/life_skill/no_xp.json` never give craft XP (for craft/uncraft loops like dried kelp blocks).

Hooks in other features' files (re-apply with `python3 tools/lifeskills/hooks.py <root>`, safe to run again):
`OnePieceMod` init line, one line in `crafting/StationPayloads.craft`, the mixin config in `fabric.mod.json`.
Saved on the player as attachment `onepiece:life_skills` (kept on death).
