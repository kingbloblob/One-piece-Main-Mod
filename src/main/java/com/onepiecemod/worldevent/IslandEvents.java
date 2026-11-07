package com.onepiecemod.worldevent;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Prediction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BarrelBlockEntity;
import net.minecraft.world.level.storage.loot.BuiltInLootTables;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;
import com.onepiecemod.sound.ModSounds;
import com.onepiecemod.stats.StatTraining;

/**
 * Island events: short things that happen around you while you explore an island, each from that island's story.
 *  - Raids: a gang shows up to bully the town (Buggy's clowns in the East Blue, Baroque Works in Alabasta,
 *    Bellamy's gang on Jaya, the Gifters in Wano...). Beat them all within 5 minutes for a reward.
 *  - Thriller Bark at night: Moria's zombies climb out of the graves.
 *  - Sabaody and the Red Line: a Celestial Dragon walks past. Kneel (sneak) until they're gone,
 *    or the Navy raises your bounty and sends Marines.
 *  - Washed-up supplies: a barrel from a wrecked merchant ship lands near you.
 *  - Wild beasts: Lapahn on Drum, Bananawani in Alabasta, dinosaurs on Little Garden, Humandrills on Kuraigana...
 *  - Skypiea: Enel's Judgment, lightning that follows you for 30 seconds.
 * About one event every 20-30 minutes you spend on Grand Line islands, never on Peaceful (the drift barrel still comes).
 * Nothing is saved: an event that's running when the server stops is called off, and its gang is removed.
 */
public class IslandEvents {
	public static final String TAG = "onepiece_island_event";
	private static final int CHECK_EVERY = 20 * 60;
	private static final float CHANCE = 0.12f;
	/** After an event (won, lost or called off) a player gets no new one for this long. */
	private static final long COOLDOWN = 20L * 60 * 15;
	private static final int TIME_LIMIT = 20 * 60 * 5;
	private static final int KNEEL_TICKS = 20 * 25;
	private static final int LIGHTNING_TICKS = 20 * 30;
	private static final double LEAVE_DISTANCE = 80;

	enum Kind { RAID, ZOMBIES, KNEEL, DRIFT, BEAST, LIGHTNING }

	/** One kind of event on some islands. kit = an npc_kits.json kit (RAID), a creature id (BEAST), or null. */
	record Def(String id, Kind kind, List<String> biomes, String announce, @Nullable String kit, int count,
			@Nullable String name, int berries, String win) {
	}

	static final List<Def> DEFS = List.of(
			new Def("buggy_raid", Kind.RAID, List.of("east_blue", "orange_town"),
					"Buggy's crew is raiding the town! Flashy cannonballs everywhere!", "buggy_pirate", 4, null, 12,
					"The clowns run back to their Big Top. The townsfolk cheer for you!"),
			new Def("alvida_raid", Kind.RAID, List.of("loguetown"),
					"Pirates are looting the market of Loguetown, the town where Roger was born and died!", "rookie_pirate", 4, null, 14,
					"The market is safe. A shopkeeper slips you a few Berries."),
			new Def("arlong_tribute", Kind.RAID, List.of("conomi_islands"),
					"Arlong's Fish-Men are collecting tribute from the villages!", "fishman", 3, "Arlong Pirate", 18,
					"The villagers won't have to pay this month. Bellemere would be proud."),
			new Def("baroque_sabotage", Kind.RAID, List.of("alabasta"),
					"Baroque Works agents are sabotaging the water stores of Alabasta!", "baroque_agent", 4, null, 22,
					"The water stores are safe. Alabasta thanks you."),
			new Def("bellamy_gang", Kind.RAID, List.of("jaya"),
					"Bellamy's gang wants a fight! They laugh at anyone who dreams of Sky Island.", "pirate", 4, "Bellamy Pirate", 22,
					"So much for laughing at dreamers. Mock Town goes quiet."),
			new Def("wapol_soldiers", Kind.RAID, List.of("drum_island"),
					"Wapol's old soldiers are back to loot the villages of Drum Island!", "bandit", 4, "Wapol's Soldier", 20,
					"The soldiers flee into the snow. The Drum villagers bring you hot soup."),
			new Def("hody_attack", Kind.RAID, List.of("fishman_reef"),
					"The New Fish-Man Pirates are attacking the plaza! They hate humans and anyone who helps them.", "fishman", 4,
					"New Fish-Man Pirate", 35, "The plaza is safe. Fish-Men and humans cheer together."),
			new Def("donquixote_enforcers", Kind.RAID, List.of("dressrosa", "green_bit"),
					"Donquixote Family enforcers are rounding up townsfolk for the toy factory!", "donquixote", 3, null, 40,
					"The enforcers are beaten. Somewhere, a toy soldier salutes you."),
			new Def("big_mom_tax", Kind.RAID, List.of("whole_cake", "cacao_island"),
					"Big Mom's collectors are here for the sweets tax! Pay up... or fight.", "big_mom_pirate", 4, "Big Mom Pirate", 45,
					"No tax today! The townsfolk share their candy with you."),
			new Def("gifters", Kind.RAID, List.of("wano", "kuri"),
					"Beasts Pirates Gifters are bullying the townsfolk of Wano!", "gifter", 3, null, 55,
					"The Gifters are beaten. Wano's people whisper about a hero."),
			new Def("blackbeard_ambush", Kind.RAID, List.of("hachinosu"),
					"Blackbeard's men want your head. Zehahaha!", "blackbeard_pirate", 4, null, 70,
					"The ambush failed. Pirates' Island grows a little more careful around you."),
			// ---- Paradise to the early New World (the long middle of the game) ----
			new Def("lapahn_stampede", Kind.BEAST, List.of("drum_island"),
					"A pack of Lapahn is stampeding down from the Drum Rockies! Those rabbits are huge!", "lapahn", 3, null, 24,
					"The Lapahn scatter into the snow. The villagers can sleep tonight."),
			new Def("bananawani_loose", Kind.BEAST, List.of("alabasta"),
					"Bananawani crawled out of the lake under Rain Dinners and are heading for the town!", "bananawani", 2, null, 28,
					"The Bananawani slink back to Crocodile's lake. Nobody gets eaten today."),
			new Def("mr3_trap", Kind.RAID, List.of("little_garden"),
					"Baroque Works agents are sneaking through the jungle to trap you in Mr. 3's wax!", "baroque_agent", 3,
					"Baroque Works Agent", 26, "The agents flee. Dorry and Brogy laugh so hard the jungle shakes. Gegyagyagya!"),
			new Def("dinosaur_charge", Kind.BEAST, List.of("little_garden"),
					"The ground shakes... a Tyrannosaurus bursts out of the prehistoric jungle!", "tyrannosaurus", 1, null, 32,
					"The dinosaur goes down with a thud. That's dinner for a giant!"),
			new Def("enel_judgment", Kind.LIGHTNING, List.of("skypiea"),
					"\"Judgment!\" Enel is throwing lightning at you from the sky. Keep moving and survive!", null, 0, null, 30,
					"The clouds go quiet. Enel got bored of you... for now."),
			new Def("divine_soldiers", Kind.RAID, List.of("skypiea"),
					"Enel's Divine Soldiers march in to drive the blue sea dwellers off God's land!", "bandit", 4, "Divine Soldier", 30,
					"The Divine Soldiers retreat to the Upper Yard. The Shandia nod at you with respect."),
			new Def("cp9_bridge", Kind.RAID, List.of("enies_lobby"),
					"CP9 agents block your way across the Bridge of Hesitation!", "cp_agent", 2, "CP9 Agent", 40,
					"The agents fall. The Bridge of Hesitation is yours."),
			new Def("human_shop_kidnappers", Kind.RAID, List.of("sabaody"),
					"Human Shop kidnappers are grabbing people off the street to sell at the auction!", "bandit", 4,
					"Human Shop Kidnapper", 35, "The kidnappers run. Shakky says the first drink is on the house next time."),
			new Def("humandrill_ambush", Kind.BEAST, List.of("kuraigana"),
					"The Humandrills of Kuraigana copied the swords of fallen soldiers... and they want a fight!", "humandrill", 3, null, 40,
					"The Humandrills back off into the ruins. Somewhere, Mihawk sips his wine."),
			new Def("caesar_henchmen", Kind.RAID, List.of("punk_hazard_burning", "punk_hazard_frozen"),
					"Caesar Clown's gas-mask henchmen are hunting intruders on Punk Hazard!", "pirate_gunner", 4, "Caesar's Henchman", 45,
					"The henchmen run off coughing. Shurororo... Caesar won't be happy."),
			new Def("punk_hazard_dragon", Kind.BEAST, List.of("punk_hazard_burning"),
					"A dragon from Vegapunk's old experiments swoops down over the burning island!", "punk_hazard_dragon", 1, null, 55,
					"The dragon crashes into the lava fields. Even Law would be impressed."),
			new Def("jack_poison", Kind.RAID, List.of("zou"),
					"Jack's Beasts Pirates are back on Zou with poison gas! The Minks need help!", "gifter", 3, "Beasts Pirate", 50,
					"The Beasts Pirates flee down the elephant's leg. The Minks shout \"GARCHU!\""),
			new Def("homie_forest", Kind.BEAST, List.of("whole_cake"),
					"The Seducing Woods come alive! Big Mom's Homie trees are closing in.", "homie_tree", 2, null, 45,
					"The trees fall silent. Their souls go back to Big Mom."),
			new Def("battle_snake_test", Kind.BEAST, List.of("amazon_lily"),
					"A Kuja warrior's battle snake wants to test the stranger's strength!", "battle_snake", 1, null, 38,
					"The snake bows its head. The Kuja warriors whisper that you're strong... for an outsider."),
			new Def("cp0_egghead", Kind.RAID, List.of("egghead"),
					"CP0 agents land on Egghead to 'take care' of Dr. Vegapunk!", "cp0_agent", 2, null, 70,
					"The agents vanish with a Soru. Vegapunk's satellites cheer in six voices."),
			new Def("thriller_zombies", Kind.ZOMBIES, List.of("thriller_bark"),
					"Night falls on Thriller Bark... Moria's zombies climb out of the graves!", null, 6, "Thriller Bark Zombie", 30,
					"The zombies crumble. Salt in their mouths would have been faster."),
			new Def("celestial_dragon", Kind.KNEEL, List.of("sabaody", "red_line", "red_line_heights"),
					"A Celestial Dragon is coming down the road! KNEEL (hold sneak) until they've passed, or else...", null, 0, null, 10,
					"The Celestial Dragon passes without looking at you. Nobody got shot today."),
			new Def("wreck_supplies", Kind.DRIFT, List.of("*"),
					"Crates from a wrecked merchant ship washed up nearby!", null, 0, null, 0,
					"")
	);

	/** One player's running event. */
	static class Active {
		final Def def;
		final UUID player;
		final ServerLevel level;
		final BlockPos center;
		final List<Mob> gang = new ArrayList<>();
		final ServerBossEvent bar;
		int ticks;
		int kneeling;
		boolean anyKilled;
		net.minecraft.world.phys.Vec3 lastSpot;

		Active(Def def, ServerPlayer player) {
			this.def = def;
			this.player = player.getUUID();
			this.level = (ServerLevel) player.level();
			this.center = player.blockPosition();
			this.bar = new ServerBossEvent(UUID.randomUUID(), Component.literal(def.kind == Kind.KNEEL ? "Kneel! (hold sneak)" : title(def)),
					def.kind == Kind.KNEEL || def.kind == Kind.LIGHTNING ? BossEvent.BossBarColor.YELLOW : BossEvent.BossBarColor.RED, BossEvent.BossBarOverlay.PROGRESS);
			bar.addPlayer(player);
		}

		void cleanUp() {
			bar.removeAllPlayers();
			for (Mob mob : gang) {
				if (mob.isAlive()) {
					mob.discard();
				}
			}
		}
	}

	private static final Map<UUID, Active> ACTIVE = new HashMap<>();
	private static final Map<UUID, Long> NEXT = new HashMap<>();

	static void initialize() {
		// Gang members left over from an event that isn't running any more (the server stopped mid-event).
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(TAG) && ACTIVE.values().stream().noneMatch(a -> a.gang.contains(entity))) {
				entity.discard();
			}
		});
	}

	static void tick(MinecraftServer server) {
		Iterator<Active> it = ACTIVE.values().iterator();
		while (it.hasNext()) {
			Active event = it.next();
			if (!tickEvent(server, event)) {
				event.cleanUp();
				it.remove();
				NEXT.put(event.player, server.overworld().getGameTime() + COOLDOWN);
			}
		}
		if (server.getTickCount() % CHECK_EVERY != 0) {
			return;
		}
		long now = server.overworld().getGameTime();
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			if (ACTIVE.containsKey(player.getUUID()) || now < NEXT.getOrDefault(player.getUUID(), 0L)
					|| player.getRandom().nextFloat() >= CHANCE) {
				continue;
			}
			Def def = pick(player, false);
			if (def != null) {
				start(player, def);
			}
		}
	}

	static void stopAll() {
		for (Active event : ACTIVE.values()) {
			event.cleanUp();
		}
		ACTIVE.clear();
		NEXT.clear();
	}

	// ---- Choosing and starting ----

	/** An event that fits where the player stands, or null. forced = ignore the time of day (for the command). */
	@Nullable
	static Def pick(ServerPlayer player, boolean forced) {
		if (player.level().dimension() != Level.OVERWORLD || player.isCreative() || player.isSpectator()
				|| player.isInWater() || player.isPassenger()) {
			return null;
		}
		ServerLevel level = (ServerLevel) player.level();
		String biome = level.getBiome(player.blockPosition()).unwrapKey().map(ResourceKey::identifier)
				.map(id -> "onepiece".equals(id.getNamespace()) ? id.getPath() : "").orElse("");
		if (biome.isEmpty()) {
			return null; // Only Grand Line islands (the mod's biomes) have events.
		}
		boolean peaceful = level.getDifficulty() == Difficulty.PEACEFUL;
		List<Def> fits = new ArrayList<>();
		for (Def def : DEFS) {
			if (!def.biomes.contains(biome) && !def.biomes.contains("*")) {
				continue;
			}
			if (peaceful && def.kind != Kind.DRIFT) {
				continue;
			}
			if (def.kind == Kind.ZOMBIES && level.isBrightOutside() && !forced) {
				continue;
			}
			fits.add(def);
			if (def.kind != Kind.DRIFT) {
				fits.add(def); // The island's own events come up twice as often as drifting supplies.
			}
		}
		return fits.isEmpty() ? null : fits.get(player.getRandom().nextInt(fits.size()));
	}

	/** Starts an event for the player. Returns why it couldn't start, or null. */
	@Nullable
	static String start(ServerPlayer player, Def def) {
		if (ACTIVE.containsKey(player.getUUID())) {
			return "You're already in an island event.";
		}
		ServerLevel level = (ServerLevel) player.level();
		RandomSource random = player.getRandom();
		if (def.kind == Kind.DRIFT) {
			return drift(player, level, random) ? null : "No dry ground nearby for the crates.";
		}
		Active event = new Active(def, player);
		if (def.kind == Kind.RAID || def.kind == Kind.ZOMBIES || def.kind == Kind.BEAST) {
			BlockPos around = WorldEvents.landingSpot(level, player.blockPosition(), 18, 28, random);
			if (around == null) {
				event.bar.removeAllPlayers();
				return "No dry ground nearby for them to come from.";
			}
			for (int i = 0; i < def.count; i++) {
				BlockPos pos = WorldEvents.landingSpot(level, around, 0, 4, random);
				Mob mob = spawnOne(level, def, pos != null ? pos : around, random);
				if (mob != null) {
					mob.addTag(TAG);
					mob.setTarget(player);
					event.gang.add(mob);
				}
			}
			if (event.gang.isEmpty()) {
				event.bar.removeAllPlayers();
				return "Nobody came.";
			}
		}
		ACTIVE.put(player.getUUID(), event);
		ModSounds.play(player, ModSounds.NEWS_COO, 0.8f);
		player.sendSystemMessage(Component.literal("[Island Event] ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(def.announce).withStyle(ChatFormatting.YELLOW)));
		return null;
	}

	@Nullable
	private static Mob spawnOne(ServerLevel level, Def def, BlockPos pos, RandomSource random) {
		float yaw = random.nextFloat() * 360f;
		if (def.kind == Kind.BEAST) {
			var type = com.onepiecemod.creature.Creatures.TYPES.get(def.kit);
			Mob beast = type == null ? null : type.create(level, EntitySpawnReason.EVENT);
			if (beast == null) {
				return null;
			}
			beast.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, yaw, 0);
			level.addFreshEntity(beast);
			return beast;
		}
		if (def.kind == Kind.ZOMBIES) {
			Mob zombie = (random.nextInt(3) == 0 ? EntityTypes.SKELETON : EntityTypes.ZOMBIE).create(level, EntitySpawnReason.EVENT);
			if (zombie == null) {
				return null;
			}
			zombie.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, yaw, 0);
			zombie.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), EntitySpawnReason.EVENT, null);
			if (def.name != null) {
				zombie.setCustomName(Component.literal(def.name));
			}
			level.addFreshEntity(zombie);
			return zombie;
		}
		HumanNpc npc = NpcFeature.spawn(level, def.kit, pos, yaw);
		if (npc != null && def.name != null) {
			npc.setCustomName(Component.literal(def.name));
		}
		return npc;
	}

	/** Puts a barrel of shipwreck supplies on dry ground near the player. */
	private static boolean drift(ServerPlayer player, ServerLevel level, RandomSource random) {
		BlockPos pos = WorldEvents.landingSpot(level, player.blockPosition(), 8, 20, random);
		if (pos == null) {
			return false;
		}
		level.setBlockAndUpdate(pos, Blocks.BARREL.defaultBlockState());
		if (level.getBlockEntity(pos) instanceof BarrelBlockEntity barrel) {
			barrel.setLootTable(random.nextInt(4) == 0 ? BuiltInLootTables.SHIPWRECK_TREASURE : BuiltInLootTables.SHIPWRECK_SUPPLY,
					random.nextLong());
		}
		NEXT.put(player.getUUID(), level.getGameTime() + COOLDOWN);
		ModSounds.play(player, ModSounds.NEWS_COO, 0.6f);
		player.sendSystemMessage(Component.literal("[Island Event] ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal("Crates from a wrecked merchant ship washed up at " + pos.getX() + ", " + pos.getY() + ", "
						+ pos.getZ() + ". Finders keepers!").withStyle(ChatFormatting.YELLOW)));
		return true;
	}

	// ---- Running ----

	/** Returns false when the event is over. */
	private static boolean tickEvent(MinecraftServer server, Active event) {
		ServerPlayer player = server.getPlayerList().getPlayer(event.player);
		if (player == null || !player.isAlive() || player.level() != event.level
				|| player.blockPosition().distSqr(event.center) > LEAVE_DISTANCE * LEAVE_DISTANCE) {
			if (player != null) {
				player.sendSystemMessage(Component.literal("[Island Event] You left. The trouble passes without you.").withStyle(ChatFormatting.GRAY));
			}
			return false;
		}
		event.ticks++;
		if (event.def.kind == Kind.KNEEL) {
			return tickKneel(player, event);
		}
		if (event.def.kind == Kind.LIGHTNING) {
			return tickLightning(player, event);
		}
		int left = 0;
		for (Mob mob : event.gang) {
			if (mob.isAlive() && !mob.isRemoved()) {
				left++;
			} else if (mob.isDeadOrDying() || mob.getRemovalReason() == Entity.RemovalReason.KILLED) {
				event.anyKilled = true;
			}
		}
		event.bar.setName(Component.literal(title(event.def) + " - " + left + " left"));
		event.bar.setProgress(Math.max(0f, 1f - event.ticks / (float) TIME_LIMIT));
		if (left == 0) {
			if (event.anyKilled) {
				win(player, event.def);
			}
			return false;
		}
		if (event.ticks >= TIME_LIMIT) {
			player.sendSystemMessage(Component.literal("[Island Event] Too slow! They got away with the loot.").withStyle(ChatFormatting.RED));
			return false;
		}
		return true;
	}

	private static boolean tickKneel(ServerPlayer player, Active event) {
		if (player.isShiftKeyDown()) {
			event.kneeling++;
		}
		event.bar.setProgress(Math.min(1f, event.ticks / (float) KNEEL_TICKS));
		if (event.ticks < KNEEL_TICKS) {
			return true;
		}
		if (event.kneeling >= KNEEL_TICKS * 2 / 3) {
			win(player, event.def);
		} else {
			player.sendSystemMessage(Component.literal("[Island Event] \"How DARE you stand in my presence!\" The Celestial Dragon calls for an Admiral...")
					.withStyle(ChatFormatting.RED));
			Bounty.raise(player, 10_000_000L, "Refused to kneel to a Celestial Dragon", false);
			for (int i = 0; i < (Bounty.get(player) > 0 ? 2 : 0); i++) { // Marines (career) get no bounty and no Marines sent after them.
				BlockPos pos = WorldEvents.landingSpot(event.level, player.blockPosition(), 10, 18, player.getRandom());
				if (pos != null) {
					HumanNpc marine = NpcFeature.spawn(event.level, "marine", pos, 0f);
					if (marine != null) {
						marine.setTarget(player);
					}
				}
			}
		}
		return false;
	}

	/**
	 * Enel's Judgment: every 1.5 s a bolt falls where you stood a moment ago (or right next to it), so you
	 * have to keep moving. The bolts don't set anything on fire. Survive 30 seconds to win.
	 */
	private static boolean tickLightning(ServerPlayer player, Active event) {
		event.bar.setName(Component.literal("Enel's Judgment - keep moving!"));
		event.bar.setProgress(Math.max(0f, 1f - event.ticks / (float) LIGHTNING_TICKS));
		if (event.ticks % 10 == 0) {
			event.lastSpot = player.position(); // the next bolt aims here
		}
		if (event.ticks % 30 == 15 && event.lastSpot != null) {
			RandomSource random = player.getRandom();
			net.minecraft.world.phys.Vec3 at = event.lastSpot.add(random.nextInt(3) - 1, 0, random.nextInt(3) - 1);
			net.minecraft.world.entity.LightningBolt bolt = new net.minecraft.world.entity.LightningBolt(EntityTypes.LIGHTNING_BOLT, event.level);
			bolt.setPos(at);
			bolt.setVisualOnly(true);
			event.level.addFreshEntity(bolt);
			event.level.playSound(null, at.x, at.y, at.z, net.minecraft.sounds.SoundEvents.LIGHTNING_BOLT_THUNDER,
					net.minecraft.sounds.SoundSource.WEATHER, 1.5f, 1.1f);
			if (player.position().distanceToSqr(at) < 2.5 * 2.5) {
				player.hurtServer(event.level, event.level.damageSources().lightningBolt(), 6f);
				event.kneeling++; // counts hits
			}
		}
		if (event.ticks < LIGHTNING_TICKS) {
			return true;
		}
		win(player, event.def);
		if (event.kneeling == 0) {
			player.sendSystemMessage(Component.literal("Not one bolt touched you! Even the priests are impressed.").withStyle(ChatFormatting.AQUA));
		}
		return false;
	}

	private static void win(ServerPlayer player, Def def) {
		player.sendSystemMessage(Component.literal("[Island Event] ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(def.win).withStyle(ChatFormatting.GREEN)));
		if (def.berries > 0) {
			ItemStack berries = new ItemStack(CharacterFeature.BERRY, def.berries);
			if (!player.getInventory().add(berries)) {
				player.drop(berries, false, Prediction.SERVER_ONLY);
			}
			player.sendSystemMessage(Component.literal("+" + def.berries + " Berries").withStyle(ChatFormatting.GOLD));
			StatTraining.addXp(player, def.berries, true);
		}
		ModSounds.play(player, ModSounds.QUEST_COMPLETE, 0.8f);
	}

	private static String title(Def def) {
		return switch (def.kind) {
			case ZOMBIES -> "Thriller Bark zombies";
			case KNEEL -> "Kneel!";
			case BEAST -> "Wild beasts";
			case LIGHTNING -> "Enel's Judgment";
			default -> "Island raid";
		};
	}

	// ---- For /worldevent islandevent ----

	static List<String> ids() {
		return DEFS.stream().map(Def::id).toList();
	}

	@Nullable
	static String startById(ServerPlayer player, @Nullable String id) {
		Def def = id == null ? pick(player, true) : DEFS.stream().filter(d -> d.id.equals(id)).findFirst().orElse(null);
		if (def == null) {
			return id == null ? "No island event fits this place (try a Grand Line island, not Peaceful)." : "No island event called " + id + ".";
		}
		return start(player, def);
	}

	static boolean stop(ServerPlayer player) {
		Active event = ACTIVE.remove(player.getUUID());
		if (event == null) {
			return false;
		}
		event.cleanUp();
		return true;
	}
}
