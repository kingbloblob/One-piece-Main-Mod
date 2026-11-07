package com.onepiecemod.creature;

import java.util.List;

import net.minecraft.world.entity.MobCategory;

/**
 * Everything that makes one kind of One Piece creature different from the others: how it behaves,
 * how big and strong it is, where it lives, what it eats and how it sounds.
 * All creatures share one entity class (CreatureEntity) that reads these settings.
 *
 * To add a creature: add an entry to ALL, add its shape in tools/creatures/creatures_more.py and run
 * tools/creatures/gen_creatures.py.
 */
public record CreatureSpecies(
		String id,
		Behavior behavior,
		boolean swims, // lives in water only, like a fish
		float width, float height, // hitbox in blocks
		float renderScale, // how much bigger than its model it is drawn
		double health, double damage, double speed, double armor, double knockback,
		int poisonSeconds, // poisons whoever it bites, 0 = no poison
		int fireSeconds, // sets whoever it bites on fire, 0 = no fire
		boolean leaps, // pounces at its target like a wolf
		boolean dayActive, // hostile creatures only: also spawns in daylight, not just in the dark
		int xp,
		String ambientSound, String hurtSound, String deathSound, // vanilla sound ids, "" = silent
		int spawnWeight, int minGroup, int maxGroup,
		String food, // item id it loves: tempts it, heals it, and tames it if it can be tamed. "" = none
		boolean tameable, // feed it to make it your companion (follows you, sneak + right-click to make it stay)
		boolean rideable, // once tamed, right-click it with an empty hand to ride it
		boolean herd, // stays close to others of its kind
		boolean sleepsAtNight, // lies still at night instead of wandering
		String harvestTool, String harvestDrop, int harvestCount, // e.g. shears give sugar, once in a while
		int caveMinY, int caveMaxY) { // cave creatures only spawn underground between these heights (see underground())

	public enum Behavior {
		/** Never fights. Runs away when hit. */
		PASSIVE,
		/** Leaves you alone until you hit it, then fights back. */
		NEUTRAL,
		/** Hunts players on sight. */
		HOSTILE
	}

	/** Lives in caves: spawns only underground (no sky above) between caveMinY and caveMaxY. */
	public boolean underground() {
		return caveMinY <= caveMaxY;
	}

	/**
	 * Flying mounts: ridden, they take off with Space and fly where you look (see CreatureEntity.travel).
	 * Value = flying speed (about 11 times this in blocks per tick at full speed).
	 */
	private static final java.util.Map<String, Float> FLIERS = java.util.Map.of(
			"fuzza", 0.06f, // Shura's giant birds of Skypiea
			"punk_hazard_dragon", 0.07f); // Vegapunk's dragon, beaten and tamed

	public boolean flies() {
		return FLIERS.containsKey(id);
	}

	public float flySpeed() {
		return FLIERS.getOrDefault(id, 0.05f);
	}

	public boolean fights() {
		return behavior != Behavior.PASSIVE;
	}

	/** Which spawning group Minecraft counts it in. Hostiles count as monsters, so they don't spawn on Peaceful. */
	public MobCategory category() {
		if (behavior == Behavior.HOSTILE) {
			return MobCategory.MONSTER;
		}
		if (underground()) {
			return MobCategory.AMBIENT; // like bats: the cave's own wildlife, so surface animals don't crowd it out
		}
		return swims ? MobCategory.WATER_CREATURE : MobCategory.CREATURE;
	}

	private static Builder passive(String id) {
		return new Builder(id, Behavior.PASSIVE);
	}

	private static Builder neutral(String id) {
		return new Builder(id, Behavior.NEUTRAL);
	}

	private static Builder hostile(String id) {
		return new Builder(id, Behavior.HOSTILE);
	}

	/** Every creature. Spawn biomes are in data/onepiece/tags/worldgen/biome/spawns/<id>.json. */
	public static final List<CreatureSpecies> ALL = List.of(
			// ================= Passive: harmless wildlife =================
			// The South Bird of Jaya always turns to face south when it stands still. Use it as a compass!
			passive("south_bird").size(0.5f, 0.75f).health(8).speed(0.25).sound("parrot").spawn(10, 2, 4)
					.food("minecraft:wheat_seeds").tameable().herd().sleeps().build(),
			// Carue's kind: big, fast desert ducks from Alabasta. Tame one and ride it.
			passive("spot_billed_duck").size(0.9f, 1.9f).health(16).speed(0.32).sound("chicken").spawn(8, 1, 3)
					.food("minecraft:wheat_seeds").rideable().herd().sleeps().build(),
			// A huge fish with an elephant's trunk and ears, from Whole Cake Island's seas.
			passive("elephant_tuna").swims().size(2.2f, 1.8f).scale(2.0f).health(24).speed(1.0).sound("cod").spawn(3, 1, 2)
					.food("minecraft:kelp").herd().build(),
			// Fluffy pink lambs from Totto Land. Shear them for sugar.
			passive("cotton_candy_lamb").size(0.9f, 1.2f).health(10).speed(0.23).sound("sheep").spawn(10, 2, 4)
					.food("minecraft:sugar").tameable().herd().sleeps().harvest("minecraft:shears", "minecraft:sugar", 3).build(),
			// Laboon's kind: whales as big as islands that sing in the deep sea. Feed one cod and ride it like a ship.
			passive("island_whale").swims().size(4.0f, 3.5f).scale(3.0f).health(80).speed(0.8).sound("dolphin").spawn(1, 1, 1)
					.food("minecraft:cod").rideable().xp(10).build(),
			// Wild baby Den Den Mushi crawling around beaches and swamps. Feed it and it follows you.
			passive("wild_den_den_mushi").size(0.4f, 0.5f).health(4).speed(0.1).voice("snail").spawn(6, 1, 3)
					.food("minecraft:kelp").tameable().build(),
			// Chopper's homeland reindeer. Tame one and ride it through the snow.
			passive("drum_reindeer").size(0.9f, 1.7f).health(16).speed(0.3).voice("deer").spawn(8, 2, 4)
					.food("minecraft:wheat").rideable().herd().sleeps().build(),
			// A gentle giant from Little Garden. Tame it and ride on its back.
			passive("sauropod").size(2.6f, 3.8f).scale(1.5f).health(100).speed(0.2).voice("giant").spawn(2, 1, 2)
					.food("minecraft:melon_slice").rideable().herd().sleeps().xp(10).build(),
			// The giant birds of Skypiea that Shura rode. Tame one and fly it (Space to take off, look where you want to go).
			passive("fuzza").size(1.0f, 2.0f).health(20).speed(0.35).voice("bird").spawn(5, 1, 3)
					.food("minecraft:wheat_seeds").rideable().herd().build(),
			// Drum Island's polite bear that bows to climbers. Feed it berries to make a friend.
			passive("hiking_bear").size(1.0f, 1.9f).health(30).speed(0.25).voice("bear").spawn(5, 1, 2)
					.food("minecraft:sweet_berries").tameable().sleeps().build(),
			// From Long Ring Long Land, where everything is extra long. Tame and ride.
			passive("long_horse").size(1.1f, 2.3f).health(25).speed(0.35).voice("horse").spawn(6, 2, 4)
					.food("minecraft:apple").rideable().herd().sleeps().build(),

			// ================= Neutral: fight back when you hit them =================
			// Turtle-shelled seals from Alabasta that train in martial arts. A tamed one fights for you, and you can ride it.
			neutral("kung_fu_dugong").size(0.7f, 1.3f).health(24).attack(5).speed(0.3).armor(2).knockback(1.0).leaps()
					.xp(6).voice("seal").spawn(6, 2, 4).food("minecraft:cod").rideable().herd().build(),
			// The sea horses of Water 7. Tame one and ride it across the water.
			neutral("yagara_bull").swims().size(1.3f, 1.3f).scale(1.4f).health(24).attack(4).speed(1.0).knockback(0.5)
					.xp(5).voice("bull").spawn(4, 1, 3).food("minecraft:kelp").rideable().herd().build(),
			// The horned bulls of Dressrosa's arena. A charge sends you flying. Feed one wheat and ride it.
			neutral("fighting_bull").size(1.6f, 1.8f).scale(1.3f).health(40).attack(8).speed(0.28).armor(4).knockback(2.0)
					.xp(10).voice("bull").spawn(5, 1, 2).food("minecraft:wheat").rideable().herd().build(),
			// Little Garden's three-horned giants. Tame one and ride it into battle.
			neutral("triceratops").size(1.8f, 2.2f).scale(1.4f).health(60).attack(9).speed(0.25).armor(6).knockback(2.0)
					.xp(15).voice("giant").spawn(4, 1, 3).food("minecraft:melon_slice").rideable().herd().build(),
			// Momoo, Arlong's giant sea cow. Treat it better than Arlong did: feed it cod and it'll pull you across the sea.
			neutral("momoo").swims().size(2.4f, 2.0f).scale(2.0f).health(50).attack(8).speed(0.9).armor(2).knockback(1.0)
					.xp(12).voice("bull").spawn(2, 1, 1).food("minecraft:cod").rideable().build(),
			// Richie, Mohji's circus lion. Tame one as a guard.
			neutral("circus_lion").size(1.2f, 1.5f).scale(1.2f).health(30).attack(7).speed(0.32).knockback(0.5)
					.xp(8).voice("cat").spawn(4, 1, 2).food("minecraft:beef").tameable().sleeps().build(),
			// Wano's lion-dogs. Loyal and rideable once tamed.
			neutral("komainu").size(1.0f, 1.4f).scale(1.2f).health(30).attack(6).speed(0.32)
					.xp(8).voice("wolf").spawn(4, 1, 2).food("minecraft:beef").rideable().build(),
			// Big white wolves of Wano, like Komachiyo that Okiku rides.
			neutral("wano_wolf").size(1.0f, 1.4f).scale(1.3f).health(30).attack(6).speed(0.35).leaps()
					.xp(8).voice("wolf").spawn(6, 2, 4).food("minecraft:mutton").rideable().herd().build(),
			// The Kuja pirates' snakes from Amazon Lily. A tamed one guards you.
			neutral("battle_snake").size(0.8f, 0.5f).health(16).attack(4).speed(0.25).poison(4)
					.xp(6).voice("snake").spawn(5, 1, 2).food("minecraft:chicken").tameable().build(),
			// Surume, the giant Kraken. Beat the odds and tame one with fish.
			neutral("kraken").swims().size(2.2f, 2.5f).scale(2.0f).health(70).attack(10).speed(0.8).armor(4).knockback(1.0)
					.xp(20).voice("sea_monster").spawn(1, 1, 1).food("minecraft:cod").tameable().build(),
			// Megalo, Shirahoshi's shark friend. Tame and ride it under the sea.
			neutral("megalo").swims().size(1.6f, 1.2f).scale(1.6f).health(40).attack(8).speed(1.1)
					.xp(10).voice("sea_monster").spawn(3, 1, 2).food("minecraft:cod").rideable().build(),
			// Sea Monkeys swim in groups and make huge waves.
			neutral("sea_monkey").swims().size(0.7f, 1.2f).health(20).attack(4).speed(1.0)
					.xp(5).voice("monkey").spawn(5, 2, 4).food("minecraft:kelp").herd().build(),

			// ================= Hostile: attack on sight =================
			// Giant fighting rabbits of Drum Island's snow. They leap at you. Beat one, feed it carrots, ride it (it jumps high).
			hostile("lapahn").size(1.2f, 2.4f).health(45).attack(8).speed(0.3).armor(4).knockback(1.0).leaps().day()
					.xp(15).voice("bear").spawn(15, 1, 2).food("minecraft:carrot").rideable().build(),
			// Alabasta's desert scorpions. Their sting is poisonous.
			hostile("sand_scorpion").size(1.1f, 0.8f).health(20).attack(4).speed(0.3).armor(2).poison(6).day()
					.xp(8).voice("bug").spawn(25, 1, 3).build(),
			// Caesar Clown's poison-gas slime from Punk Hazard. Always smiling.
			hostile("smiley").size(1.3f, 1.4f).scale(1.1f).health(30).attack(3).speed(0.2).poison(8)
					.xp(12).sounds("", "entity.slime.hurt", "entity.slime.death").spawn(10, 1, 1).build(),
			// Fierce winged fish that attack boats on the Grand Line.
			hostile("fighting_fish").swims().size(1.4f, 1.2f).scale(1.4f).health(30).attack(7).speed(1.1).armor(2).knockback(0.5)
					.xp(12).voice("sea_monster").spawn(10, 1, 2).build(),
			// Crocodile's banana-headed crocodiles. Tough, slow and very hungry. Beat one down, feed it beef, and ride it.
			hostile("bananawani").size(2.0f, 1.2f).scale(1.5f).health(60).attack(10).speed(0.25).armor(6).knockback(1.0).day()
					.xp(25).voice("reptile").spawn(6, 1, 1).food("minecraft:beef").rideable().build(),
			// The king of Little Garden's jungle.
			hostile("tyrannosaurus").size(1.8f, 3.0f).scale(1.6f).health(90).attack(14).speed(0.28).armor(6).knockback(1.5).day()
					.xp(40).voice("reptile").spawn(2, 1, 1).build(),
			// Sharks of the White Sea in the sky, also seen in warm seas below.
			hostile("sky_shark").swims().size(1.4f, 1.0f).scale(1.4f).health(25).attack(6).speed(1.2)
					.xp(10).voice("sea_monster").spawn(8, 2, 3).build(),
			// Nola, the giant python of Upper Yard that swallowed a whole tribe's treasure.
			hostile("nola").size(2.0f, 1.2f).scale(2.5f).health(80).attack(12).speed(0.25).armor(4).knockback(1.0).day()
					.xp(40).voice("reptile").spawn(2, 1, 1).build(),
			// Baboons of Kuraigana Island that copy the fighting style of whoever they watched.
			hostile("humandrill").size(0.8f, 1.5f).health(25).attack(5).speed(0.33).leaps()
					.xp(8).voice("monkey").spawn(12, 2, 3).build(),
			// Thriller Bark's three-headed zombie fox-dog. Beat it down, then feed it rotten flesh: a zombie guard dog.
			hostile("cerberus").size(1.0f, 1.3f).scale(1.2f).health(35).attack(7).speed(0.33).leaps()
					.xp(10).voice("wolf").spawn(8, 1, 2).food("minecraft:rotten_flesh").tameable().build(),
			// A beast from Impel Down's Level 2, now loose in the Nether.
			hostile("basilisk").size(1.8f, 1.3f).scale(1.6f).health(60).attack(10).speed(0.25).armor(6).poison(5).day()
					.xp(25).voice("snake").spawn(6, 1, 1).build(),
			// Impel Down's lion with a scorpion tail.
			hostile("manticore").size(1.3f, 1.5f).scale(1.3f).health(55).attack(9).speed(0.3).armor(4).poison(6).leaps().day()
					.xp(25).voice("cat").spawn(6, 1, 1).build(),
			// The giant dragon of Punk Hazard (one of Vegapunk's experiments). Its bite burns.
			// Beat it below 30% health, then feed it magma cream: a dragon you can fly.
			hostile("punk_hazard_dragon").size(2.6f, 2.6f).scale(2.0f).health(150).attack(16).speed(0.3).armor(10).knockback(2.0)
					.fire(5).day().xp(80).voice("dragon").spawn(1, 1, 1).food("minecraft:magma_cream").rideable().build(),
			// Striped sea cats, cousins of the Sea Kings.
			hostile("sea_cat").swims().size(2.0f, 1.8f).scale(1.8f).health(45).attack(9).speed(1.0).armor(2).knockback(1.0)
					.xp(15).voice("cat").spawn(4, 1, 1).build(),
			// Big Mom's living trees from the Seducing Woods.
			hostile("homie_tree").size(1.0f, 2.2f).scale(1.2f).health(40).attack(7).speed(0.22).armor(4).knockback(0.5)
					.xp(12).voice("tree").spawn(8, 1, 2).build(),
			// Vegapunk's Kuma-shaped Marine robots. Very rare, very dangerous.
			hostile("pacifista").size(1.2f, 2.4f).scale(1.2f).health(100).attack(14).speed(0.25).armor(10).knockback(1.5)
					.xp(50).voice("machine").spawn(1, 1, 1).build(),
			// The giant gorillas of Rusukaina, where Luffy trained for two years. Like Luffy, beat one and it becomes your friend
			// (feed it an apple once it's down). It fights by your side.
			hostile("rusukaina_gorilla").size(1.4f, 2.2f).scale(1.3f).health(70).attack(12).speed(0.3).armor(4).knockback(1.5)
					.leaps().xp(20).voice("bear").spawn(4, 1, 2).food("minecraft:apple").tameable().build(),

			// ================= Underground: only in caves (added 2026-10-25) =================
			// Crabs whose shells grow Sea Prism crystals, from the Seastone Grottos. Drop raw seastone.
			neutral("prism_crab").size(0.9f, 0.6f).health(18).attack(4).speed(0.22).armor(6).xp(5)
					.voice("bug").spawn(8, 1, 3).underground(0, 50).build(),
			// Mogura: the giant moles of the underground. Tame one with carrots and ride it.
			neutral("cave_mole").size(1.2f, 0.9f).health(30).attack(5).speed(0.25).knockback(0.5).xp(6)
					.voice("mole").spawn(6, 1, 2).food("minecraft:carrot").rideable().underground(-20, 50).build(),
			// Long armoured centipedes from the dark tunnels. Their bite is poisonous.
			hostile("cave_centipede").size(1.0f, 0.5f).health(22).attack(5).speed(0.3).armor(2).poison(4).leaps()
					.xp(8).voice("bug").spawn(30, 1, 2).underground(-64, 30).build(),
			// Lives by the deep sulfur vents. Its bite sets you on fire; heat doesn't hurt it.
			hostile("sulfur_salamander").size(0.8f, 0.5f).health(26).attack(6).speed(0.28).armor(2).fire(4)
					.xp(9).voice("snake").spawn(25, 1, 2)
					.underground(-64, -8).build(),
			// Stone warriors left by the Void Century kingdom to guard its ruins. Rare in the deep caves.
			hostile("ancient_sentinel").size(1.0f, 2.1f).health(80).attack(11).speed(0.22).armor(10).knockback(1.5)
					.xp(30).voice("machine").spawn(3, 1, 1)
					.underground(-64, 0).build()
	);

	/** Builds a CreatureSpecies one setting at a time, so each line above reads like a description. */
	private static final class Builder {
		private final String id;
		private final Behavior behavior;
		private boolean swims;
		private float width = 0.9f, height = 1.4f, scale = 1.0f;
		private double health = 20, damage = 0, speed = 0.25, armor = 0, knockback = 0;
		private int poison, fire, xp = 3;
		private boolean leaps, dayActive, tameable, rideable, herd, sleeps;
		private String ambient = "", hurt = "", death = "", food = "";
		private int weight = 5, min = 1, max = 2;
		private String harvestTool = "", harvestDrop = "";
		private int harvestCount;
		private int caveMinY = 1, caveMaxY = 0; // min > max = not a cave creature

		private Builder(String id, Behavior behavior) {
			this.id = id;
			this.behavior = behavior;
		}

		Builder swims() { swims = true; return this; }
		Builder size(float w, float h) { width = w; height = h; return this; }
		Builder scale(float s) { scale = s; return this; }
		Builder health(double h) { health = h; return this; }
		Builder attack(double d) { damage = d; return this; }
		Builder speed(double s) { speed = s; return this; }
		Builder armor(double a) { armor = a; return this; }
		Builder knockback(double k) { knockback = k; return this; }
		Builder poison(int seconds) { poison = seconds; return this; }
		Builder fire(int seconds) { fire = seconds; return this; }
		Builder leaps() { leaps = true; return this; }
		Builder day() { dayActive = true; return this; }
		Builder xp(int x) { xp = x; return this; }
		Builder food(String item) { food = item; return this; }
		Builder tameable() { tameable = true; return this; }
		Builder rideable() { rideable = true; tameable = true; return this; }
		Builder herd() { herd = true; return this; }
		Builder sleeps() { sleeps = true; return this; }

		/** Uses the vanilla mob's sounds, like sound("polar_bear"). */
		Builder sound(String mob) {
			return sounds("entity." + mob + ".ambient", "entity." + mob + ".hurt", "entity." + mob + ".death");
		}

		/** Uses one of the mod's own creature voices (sound/WorldSounds.VOICES), like voice("bear"). */
		Builder voice(String voice) {
			String base = "onepiece_sounds:creature." + voice;
			return sounds(base + "_ambient", base + "_hurt", base + "_death");
		}

		Builder sounds(String ambient, String hurt, String death) {
			this.ambient = ambient;
			this.hurt = hurt;
			this.death = death;
			return this;
		}

		Builder spawn(int weight, int min, int max) {
			this.weight = weight;
			this.min = min;
			this.max = max;
			return this;
		}

		Builder harvest(String tool, String drop, int count) {
			harvestTool = tool;
			harvestDrop = drop;
			harvestCount = count;
			return this;
		}

		/** A cave creature: spawns only underground, between these heights. */
		Builder underground(int minY, int maxY) {
			caveMinY = minY;
			caveMaxY = maxY;
			return this;
		}

		CreatureSpecies build() {
			return new CreatureSpecies(id, behavior, swims, width, height, scale, health, damage, speed, armor, knockback,
					poison, fire, leaps, dayActive, xp, ambient, hurt, death, weight, min, max,
					food, tameable, rideable, herd, sleeps, harvestTool, harvestDrop, harvestCount, caveMinY, caveMaxY);
		}
	}
}
