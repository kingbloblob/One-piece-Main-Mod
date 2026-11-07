package com.onepiecemod.hideout;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.loot.LootParams;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.bounty.EventBosses;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.bounty.MarineHunters;
import com.onepiecemod.bounty.MarineRank;
import com.onepiecemod.bounty.MarineWarship;
import com.onepiecemod.bounty.NavyCalm;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.multiplayer.PlayerCrews;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.ShipHull;
import com.onepiecemod.sound.ModSounds;
import com.onepiecemod.weapon.WeaponItems;

/**
 * The Navy attacks your hideout.
 *
 * While the captain is near (within 160 blocks), now and then the Marines come for the hideout itself: a minute's
 * warning, then waves of Marines landing at the edge of the claim, a warship shelling from the sea at higher bounties,
 * and a famous officer leading the last wave. They fight whoever defends the place, and head for the flag: if
 * Marines stand at the flag for 30 seconds with no defender beside it, the hideout falls and they carry off a third
 * of the stash. The hideout's own cannons fire at them (one cannonball from the stash per shot).
 *
 * While the captain is away, attacks still happen, but they're settled by numbers: the hideout's defence rating
 * against the Navy's strength. The captain hears about it on the Den Den Mushi.
 *
 * Attacks need a bounty and a hideout of level 1 or more, and are at least two days apart (three while away).
 */
public final class HideoutSiege {
	public static final String TAG = "onepiece_hideout_siege";

	private static final int CHECK_EVERY_TICKS = 20 * 60;
	private static final double NEAR = 160.0;
	private static final long GAP_TICKS = 24000L * 2;
	private static final long AWAY_GAP_TICKS = 24000L * 3;
	private static final int WARNING_TICKS = 20 * 60;
	private static final int BETWEEN_WAVES_TICKS = 20 * 12;
	private static final int WAVE_TICKS = 20 * 240;
	private static final int CAPTURE_TICKS = 20 * 30;
	private static final int LEAVE_TICKS = 20 * 60;
	private static final int CANNON_RELOAD_TICKS = 20 * 4;
	private static final double CANNON_RANGE = 56.0;

	/** By threat level 0..5. */
	private static final float[] CHANCE = {0f, 0.01f, 0.015f, 0.02f, 0.03f, 0.04f};
	private static final float[] AWAY_CHANCE = {0f, 0.003f, 0.005f, 0.007f, 0.01f, 0.012f};
	private static final int[] CANNON_EVERY = {0, 0, 180, 140, 110, 80};
	private static final String[][] COMMANDERS = {{}, {}, {}, {"tashigi"}, {"smoker", "tashigi"}, {"smoker", "lucci"}};

	private static final ResourceKey<LootTable> SUPPLY_LOOT = ResourceKey.create(Registries.LOOT_TABLE, OnePieceMod.id("chests/marine"));

	private static final Map<UUID, Siege> SIEGES = new HashMap<>();

	private HideoutSiege() {
	}

	public static boolean isUnderAttack(UUID captain) {
		return captain != null && SIEGES.containsKey(captain);
	}

	/** True if this player is defending (or attacking) any hideout right now: no other Navy raids start meanwhile. */
	static boolean busy(ServerPlayer player) {
		if (SIEGES.containsKey(player.getUUID())) {
			return true;
		}
		for (Siege siege : SIEGES.values()) {
			if (siege.level == player.level() && player.distanceToSqr(Vec3.atCenterOf(siege.flag)) < 100 * 100) {
				return true;
			}
		}
		return false;
	}

	static void initialize() {
		NavyCalm.register(HideoutSiege::busy);
	}

	static void tick(MinecraftServer server) {
		Iterator<Siege> it = SIEGES.values().iterator();
		while (it.hasNext()) {
			Siege siege = it.next();
			if (!siege.tick(server)) {
				siege.cleanUp();
				it.remove();
			}
		}
		if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
			return;
		}
		ServerLevel overworld = server.overworld();
		long now = overworld.getGameTime();
		boolean peaceful = overworld.getDifficulty() == Difficulty.PEACEFUL;
		for (Map.Entry<String, Hideouts.Hideout> entry : Hideouts.all(server).entrySet()) {
			UUID owner = UUID.fromString(entry.getKey());
			Hideouts.Hideout hideout = entry.getValue();
			ServerPlayer captain = server.getPlayerList().getPlayer(owner);
			if (captain != null && Bounty.threatLevel(captain) != hideout.threat()) {
				hideout = hideout.withThreat(Bounty.threatLevel(captain));
				Hideouts.put(server, owner, hideout);
			}
			if (captain != null && !hideout.news().isEmpty()) {
				tellNews(captain, hideout);
				hideout = hideout.newsTold();
				Hideouts.put(server, owner, hideout);
			}
			if (peaceful || SIEGES.containsKey(owner) || hideout.level() < 1 || hideout.threat() < 1) {
				continue;
			}
			float rate = com.onepiecemod.config.ModConfig.navyRaidRate();
			boolean near = captain != null && captain.level() == overworld
					&& captain.distanceToSqr(Vec3.atCenterOf(hideout.pos())) < NEAR * NEAR;
			if (near) {
				if (now - hideout.lastSiege() >= GAP_TICKS && !captain.isCreative() && !captain.isSpectator()
						&& !NavyCalm.isBusy(captain) && overworld.isLoaded(hideout.pos())
						&& captain.getRandom().nextFloat() < CHANCE[hideout.threat()] * rate) {
					start(captain);
				}
			} else if (now - hideout.lastSiege() >= AWAY_GAP_TICKS
					&& overworld.getRandom().nextFloat() < AWAY_CHANCE[hideout.threat()] * rate) {
				awayAttack(server, owner, hideout);
			}
		}
	}

	private static void tellNews(ServerPlayer captain, Hideouts.Hideout hideout) {
		captain.sendSystemMessage(Component.literal("[Den Den Mushi] Puru puru puru... News from your hideout:").withStyle(ChatFormatting.AQUA));
		for (String line : hideout.news().split("\n")) {
			captain.sendSystemMessage(Component.literal("  " + line).withStyle(ChatFormatting.GRAY));
		}
	}

	/** The Navy attacks while the captain isn't there: the defence rating decides. */
	static void awayAttack(MinecraftServer server, UUID owner, Hideouts.Hideout hideout) {
		ServerLevel overworld = server.overworld();
		int strength = 10 + 8 * hideout.threat() + overworld.getRandom().nextInt(11);
		boolean held = hideout.defence() >= strength;
		String news = held
				? "The Navy attacked your hideout while you were away, and the crew drove them off! (defence " + hideout.defence()
						+ " vs " + strength + ") They left a supply crate behind: it's in the stash."
				: "The Navy broke into your hideout while you were away (defence " + hideout.defence() + " vs " + strength
						+ ") and carried off part of the stash. More cannons, ammo and crew would have stopped them.";
		Hideouts.put(server, owner, hideout.siegeDone(overworld.getGameTime(), held, news, held ? 0 : 30, held ? 1 : 0));
		ServerPlayer captain = server.getPlayerList().getPlayer(owner);
		if (captain != null) {
			ModSounds.play(captain, ModSounds.DEN_DEN_MUSHI_CALL);
			Hideouts.Hideout updated = Hideouts.of(server, owner);
			tellNews(captain, updated);
			Hideouts.put(server, owner, updated.newsTold());
		}
	}

	/** Starts an attack on the player's hideout now. Returns an error, or null if it started. */
	public static String start(ServerPlayer captain) {
		if (SIEGES.containsKey(captain.getUUID())) {
			return "The Navy is already attacking your hideout.";
		}
		HideoutFlagBlockEntity flag = Hideouts.flag(captain.level().getServer(), captain.getUUID());
		if (flag == null) {
			return "You have no hideout, or its flag isn't loaded (go closer).";
		}
		int threat = Math.max(1, Bounty.threatLevel(captain));
		Siege siege = new Siege(captain, flag, threat);
		SIEGES.put(captain.getUUID(), siege);
		siege.announce(captain);
		return null;
	}

	public static boolean stop(ServerPlayer captain) {
		Siege siege = SIEGES.remove(captain.getUUID());
		if (siege == null) {
			return false;
		}
		siege.cleanUp();
		return true;
	}

	/** A box of Navy supplies: a roll of the Marine loot table and some cannonballs, into the stash. */
	static void supplyCrate(ServerLevel level, HideoutFlagBlockEntity flag) {
		LootTable table = level.getServer().reloadableRegistries().getLootTable(SUPPLY_LOOT);
		LootParams params = new LootParams.Builder(level)
				.withParameter(LootContextParams.ORIGIN, Vec3.atCenterOf(flag.getBlockPos()))
				.create(LootContextParamSets.CHEST);
		for (ItemStack stack : table.getRandomItems(params)) {
			flag.store(stack);
		}
		flag.store(new ItemStack(WeaponItems.CANNONBALL, 4 + level.getRandom().nextInt(5)));
	}

	// ------------------------------------------------------------------------------------------

	private static final class Siege {
		final UUID owner;
		final ServerLevel level;
		final BlockPos flag;
		final int threat;
		final int totalWaves;
		final ServerBossEvent bar;
		final List<UUID> members = new ArrayList<>();
		final List<Shell> shells = new ArrayList<>();
		final Map<BlockPos, Integer> reload = new HashMap<>();
		final String crewName;

		int wave = 0;
		int countdown = WARNING_TICKS;
		int waveTicks;
		float waveHealth = 1;
		int capture;
		int awayTicks;
		int warshipTimer;
		UUID shipId;
		boolean noLanding;

		Siege(ServerPlayer captain, HideoutFlagBlockEntity flagEntity, int threat) {
			this.owner = captain.getUUID();
			this.level = (ServerLevel) captain.level();
			this.flag = flagEntity.getBlockPos();
			this.threat = threat;
			this.totalWaves = Math.min(5, 2 + threat / 2 + (flagEntity.level() >= 4 ? 1 : 0));
			this.warshipTimer = CANNON_EVERY[threat];
			this.crewName = flagEntity.crewName(level);
			this.countdown += com.onepiecemod.baseworks.BaseUpgrades.extraWarningTicks(level.getServer(), owner); // Lookout Post upgrade.
			this.bar = new ServerBossEvent(UUID.randomUUID(), Component.literal("Navy Assault"), BossEvent.BossBarColor.RED,
					BossEvent.BossBarOverlay.NOTCHED_10);
			this.bar.setProgress(0);
		}

		HideoutFlagBlockEntity flagEntity() {
			return level.isLoaded(flag) && level.getBlockEntity(flag) instanceof HideoutFlagBlockEntity entity ? entity : null;
		}

		Vec3 center() {
			return Vec3.atCenterOf(flag);
		}

		void announce(ServerPlayer captain) {
			Component warning = Component.literal("[Den Den Mushi] A Marine fleet is heading for the " + crewName
					+ " hideout! " + totalWaves + " waves, landing in " + (countdown / 20) + " seconds. Man the cannons!").withStyle(ChatFormatting.RED);
			for (ServerPlayer player : level.players()) {
				if (player.distanceToSqr(center()) < NEAR * NEAR) {
					player.sendSystemMessage(warning);
				}
			}
			level.playSound(null, flag, ModSounds.NAVY_BUGLE, SoundSource.HOSTILE, 4.0f, 1.0f);
			level.playSound(null, flag, SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 3.0f, 0.8f);
			HideoutFlagBlockEntity entity = flagEntity();
			if (entity != null && entity.cannonballs() == 0 && !entity.survey().cannons.isEmpty()) {
				captain.sendSystemMessage(Component.literal("Your cannons have no cannonballs! Put some in the flag's stash.")
						.withStyle(ChatFormatting.YELLOW));
			}
			if (CANNON_EVERY[threat] > 0) {
				ShipEntity ship = MarineWarship.spawn(level, flag, captain.getRandom());
				if (ship != null) {
					shipId = ship.getUUID();
					captain.sendSystemMessage(Component.literal("A Marine warship drops anchor offshore. Turn your cannons on it!")
							.withStyle(ChatFormatting.RED));
				}
			}
			bar.setName(Component.literal("Navy Assault: the fleet is coming"));
		}

		/** False when the attack is over. */
		boolean tick(MinecraftServer server) {
			HideoutFlagBlockEntity entity = flagEntity();
			ServerPlayer captain = server.getPlayerList().getPlayer(owner);
			if (entity == null || !owner.equals(entity.owner())) {
				if (!level.isLoaded(flag)) {
					resolveByNumbers(server, captain);
				} else {
					lose(server, captain, "The hideout's flag is gone. The Marines take what's left.");
				}
				return false;
			}
			boolean captainHere = captain != null && captain.level() == level && captain.distanceToSqr(center()) < 200 * 200;
			awayTicks = captainHere ? 0 : awayTicks + 1;
			if (awayTicks >= LEAVE_TICKS) {
				resolveByNumbers(server, captain);
				return false;
			}
			updateBar();
			tickWarship();
			tickShells(captain);
			tickCannons(entity, captain);

			if (countdown > 0) {
				countdown--;
				if (countdown == 20 * 10 && wave == 0) {
					tellAll(Component.literal("The Marines are landing in 10 seconds!").withStyle(ChatFormatting.RED));
				}
				if (countdown == 0) {
					wave++;
					spawnWave(captain);
					if (noLanding) {
						tellAll(Component.literal("The Marines found nowhere to land and turned back.").withStyle(ChatFormatting.GRAY));
						return false;
					}
				}
				return true;
			}

			if (level.getGameTime() % 20 == 0) {
				steer();
				if (tickCapture()) {
					lose(server, captain, "The Marines have taken the flag! They ransack the hideout.");
					return false;
				}
			}

			float health = 0;
			for (UUID id : members) {
				if (level.getEntity(id) instanceof LivingEntity living && living.isAlive()) {
					health += living.getHealth();
				}
			}
			bar.setProgress(Mth.clamp(health / waveHealth, 0, 1));
			if (health > 0 && ++waveTicks >= WAVE_TICKS) {
				retreatWave();
				health = 0;
				tellAll(Component.literal("The rest of this wave pulls back to the ships.").withStyle(ChatFormatting.GRAY));
			}
			if (health <= 0) {
				if (wave >= totalWaves) {
					win(server, captain);
					return false;
				}
				capture = 0;
				countdown = BETWEEN_WAVES_TICKS;
				bar.setName(Component.literal("Navy Assault: wave " + (wave + 1) + " of " + totalWaves + " is coming"));
				bar.setProgress(0);
			}
			return true;
		}

		void tellAll(Component message) {
			for (ServerPlayer player : level.players()) {
				if (player.distanceToSqr(center()) < (Hideouts.RADIUS + 48) * (Hideouts.RADIUS + 48)) {
					player.sendSystemMessage(message);
				}
			}
		}

		void updateBar() {
			double range = Hideouts.RADIUS + 48;
			for (ServerPlayer player : List.copyOf(bar.getPlayers())) {
				if (player.level() != level || player.distanceToSqr(center()) > range * range) {
					bar.removePlayer(player);
				}
			}
			for (ServerPlayer player : level.players()) {
				if (player.distanceToSqr(center()) < range * range) {
					bar.addPlayer(player);
				}
			}
		}

		// ---- Waves ----

		void spawnWave(ServerPlayer captain) {
			members.clear();
			waveHealth = 0;
			waveTicks = 0;
			boolean last = wave == totalWaves;
			int size = Math.min(12, 3 + threat + wave);
			for (int i = 0; i < size; i++) {
				MarineRank rank = i == 0 && (last || threat >= 3) ? MarineRank.CAPTAIN
						: i == 0 || (threat >= 4 && level.getRandom().nextFloat() < 0.15f) ? MarineRank.LIEUTENANT
						: threat >= 2 && level.getRandom().nextFloat() < 0.45f ? MarineRank.RIFLEMAN : MarineRank.RECRUIT;
				BlockPos spot = landingSpot();
				MarineEntity marine = spot == null ? null : BountyFeature.MARINE.create(level, EntitySpawnReason.EVENT);
				if (marine == null) {
					continue;
				}
				marine.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
				marine.setRank(rank);
				marine.addTag(TAG);
				members.add(marine.getUUID()); // Before adding: the leftover cleanup checks the list as it loads.
				level.addFreshEntity(marine);
				waveHealth += marine.getMaxHealth();
			}
			String commander = null;
			String[] choices = COMMANDERS[threat];
			if (last && choices.length > 0) {
				BlockPos spot = landingSpot();
				CharacterEntity boss = spot == null ? null : CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
				if (boss != null) {
					boss.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
					boss.setCharacter(choices[level.getRandom().nextInt(choices.length)], true);
					boss.addTag(MarineHunters.HUNTER_TAG);
					boss.addTag(TAG);
					EventBosses.mark(boss);
					members.add(boss.getUUID());
					level.addFreshEntity(boss);
					waveHealth += boss.getMaxHealth();
					commander = boss.getData().name;
				}
			}
			if (members.isEmpty()) {
				waveHealth = 1;
				noLanding = true;
				return;
			}
			String name = last ? "Navy Assault: final wave" : "Navy Assault: wave " + wave + " of " + totalWaves;
			bar.setName(Component.literal(commander != null ? name + " (" + commander + ")" : name));
			bar.setProgress(1);
			level.playSound(null, flag, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 4.0f, 1.0f);
			if (commander != null) {
				tellAll(Component.literal(commander + " leads the final wave against your hideout!").withStyle(ChatFormatting.RED));
			}
		}

		/**
		 * Where Marines come ashore: walking in from the sea toward the flag along a random line, the first dry ground
		 * (so outside the claim on a big island, on the beach of a small one).
		 */
		BlockPos landingSpot() {
			for (int attempt = 0; attempt < 16; attempt++) {
				double angle = level.getRandom().nextDouble() * Math.PI * 2;
				for (int distance = Hideouts.RADIUS + 14; distance >= 6; distance -= 2) {
					int x = Mth.floor(flag.getX() + Math.cos(angle) * distance);
					int z = Mth.floor(flag.getZ() + Math.sin(angle) * distance);
					if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
						continue;
					}
					BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
					if (level.getFluidState(pos.below()).isEmpty() && level.getBlockState(pos.below()).isSolid()
							&& level.getBlockState(pos).isAir() && level.getBlockState(pos.above()).isAir()
							&& Math.abs(pos.getY() - flag.getY()) < 20) {
						return pos;
					}
				}
			}
			return null;
		}

		boolean isDefender(Entity entity) {
			if (!entity.isAlive() || entity.isSpectator()) {
				return false;
			}
			if (entity instanceof ServerPlayer player) {
				return !player.isCreative() && (owner.equals(player.getUUID()) || sameCrew(player.getUUID()));
			}
			if (entity instanceof CrewmateEntity crewmate) {
				return !crewmate.isKnockedOut() && crewmate.getCaptainId() != null
						&& (owner.equals(crewmate.getCaptainId()) || sameCrew(crewmate.getCaptainId()));
			}
			return false;
		}

		boolean sameCrew(UUID captain) {
			UUID a = PlayerCrews.captainOf(level.getServer(), owner);
			UUID b = PlayerCrews.captainOf(level.getServer(), captain);
			return a != null && a.equals(b);
		}

		List<LivingEntity> defenders(double range) {
			return level.getEntitiesOfClass(LivingEntity.class, new AABB(flag).inflate(range, 24, range), this::isDefender);
		}

		List<Mob> attackers() {
			List<Mob> list = new ArrayList<>();
			for (UUID id : members) {
				if (level.getEntity(id) instanceof Mob mob && mob.isAlive()) {
					list.add(mob);
				}
			}
			return list;
		}

		/** Marines go for the nearest defender, or march on the flag. Resident crewmates go for the nearest Marine. */
		void steer() {
			List<LivingEntity> defenders = defenders(Hideouts.RADIUS + 24);
			List<Mob> attackers = attackers();
			for (Mob marine : attackers) {
				LivingEntity target = marine.getTarget();
				if (target == null || !target.isAlive() || (target instanceof CrewmateEntity c && c.isKnockedOut())) {
					LivingEntity nearest = nearest(marine, defenders, 18.0);
					marine.setTarget(nearest);
					if (nearest == null && marine.getNavigation().isDone()) {
						marine.getNavigation().moveTo(flag.getX() + 0.5, flag.getY(), flag.getZ() + 0.5, 1.0);
					}
				}
			}
			for (LivingEntity defender : defenders) {
				if (defender instanceof CrewmateEntity crewmate && (crewmate.getTarget() == null || !crewmate.getTarget().isAlive())) {
					List<LivingEntity> foes = new ArrayList<>(attackers);
					crewmate.setTarget(nearest(crewmate, foes, 24.0));
				}
			}
		}

		static <T extends LivingEntity> T nearest(Entity from, List<T> list, double range) {
			T best = null;
			double bestDistance = range * range;
			for (T entity : list) {
				double distance = entity.distanceToSqr(from);
				if (distance < bestDistance) {
					best = entity;
					bestDistance = distance;
				}
			}
			return best;
		}

		/** One second of the Marines trying to take the flag. True when they've taken it. */
		boolean tickCapture() {
			Vec3 center = center();
			boolean marineAtFlag = false;
			for (Mob marine : attackers()) {
				if (marine.distanceToSqr(center) < 4 * 4) {
					marineAtFlag = true;
					break;
				}
			}
			boolean defended = false;
			for (LivingEntity defender : defenders(6)) {
				if (defender.distanceToSqr(center) < 6 * 6) {
					defended = true;
					break;
				}
			}
			if (marineAtFlag && !defended) {
				capture += 20;
				if (capture == 20) {
					tellAll(Component.literal("Marines are at your flag! Get back there or the hideout falls!").withStyle(ChatFormatting.RED));
					level.playSound(null, flag, SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 3.0f, 1.2f);
				}
			} else {
				capture = Math.max(0, capture - 10);
			}
			if (capture > 0) {
				String base = wave == totalWaves ? "Navy Assault: final wave" : "Navy Assault: wave " + wave + " of " + totalWaves;
				bar.setName(Component.literal(base + " - flag " + (100 * capture / CAPTURE_TICKS) + "% taken"));
			}
			return capture >= CAPTURE_TICKS;
		}

		// ---- Cannons ----

		/** Each cannon in the claim fires at the nearest Marine (or the warship) in front of it, every 4 seconds. */
		void tickCannons(HideoutFlagBlockEntity entity, ServerPlayer captain) {
			if (level.getGameTime() % 10 != 0 || wave == 0) {
				return;
			}
			List<Mob> attackers = attackers();
			Entity warship = shipId != null ? level.getEntity(shipId) : null;
			if (attackers.isEmpty() && (warship == null || !warship.isAlive())) {
				return;
			}
			boolean warned = false;
			for (BlockPos cannon : entity.survey().cannons) {
				int left = reload.getOrDefault(cannon, 0) - 10;
				if (left > 0) {
					reload.put(cannon, left);
					continue;
				}
				BlockState state = level.getBlockState(cannon);
				if (!state.hasProperty(HorizontalDirectionalBlock.FACING)) {
					continue; // Broken since the last look-over.
				}
				Direction facing = state.getValue(HorizontalDirectionalBlock.FACING);
				Vec3 muzzle = Vec3.atCenterOf(cannon).add(facing.getStepX() * 0.8, 0.3, facing.getStepZ() * 0.8);
				Entity target = pick(muzzle, facing, attackers, warship);
				if (target == null) {
					continue;
				}
				if (!entity.takeCannonball()) {
					if (!warned && captain != null && level.getGameTime() % 200 == 0) {
						captain.sendOverlayMessage(Component.literal("Your cannons are out of cannonballs!").withStyle(ChatFormatting.RED));
					}
					warned = true;
					continue;
				}
				reload.put(cannon, com.onepiecemod.baseworks.BaseUpgrades.cannonReload(level.getServer(), owner, CANNON_RELOAD_TICKS)); // Gun Crews upgrade.
				Vec3 aim = target.position().add(level.getRandom().nextGaussian() * 1.2, 0.5, level.getRandom().nextGaussian() * 1.2);
				level.sendParticles(ParticleTypes.EXPLOSION, muzzle.x, muzzle.y, muzzle.z, 1, 0, 0, 0, 0);
				level.sendParticles(ParticleTypes.LARGE_SMOKE, muzzle.x, muzzle.y, muzzle.z, 8, 0.3, 0.3, 0.3, 0.03);
				level.playSound(null, cannon, ModSounds.CANNON, SoundSource.BLOCKS, 4.0f, 1.0f);
				shells.add(new Shell(muzzle, aim, Math.max(10, (int) (muzzle.distanceTo(aim) * 0.5)), true, target == warship));
			}
		}

		Entity pick(Vec3 muzzle, Direction facing, List<Mob> attackers, Entity warship) {
			Entity best = null;
			double bestDistance = CANNON_RANGE * CANNON_RANGE;
			for (Mob mob : attackers) {
				double distance = mob.distanceToSqr(muzzle);
				if (distance < bestDistance && distance > 9 && inFront(muzzle, facing, mob.position())) {
					best = mob;
					bestDistance = distance;
				}
			}
			if (best == null && warship != null && warship.isAlive() && warship.distanceToSqr(muzzle) < 90 * 90
					&& inFront(muzzle, facing, warship.position())) {
				best = warship;
			}
			return best;
		}

		/** Within about 70 degrees of where the barrel points. */
		static boolean inFront(Vec3 muzzle, Direction facing, Vec3 at) {
			double dx = at.x - muzzle.x;
			double dz = at.z - muzzle.z;
			double length = Math.sqrt(dx * dx + dz * dz);
			return length > 0 && (dx * facing.getStepX() + dz * facing.getStepZ()) / length > 0.34;
		}

		void tickWarship() {
			if (shipId == null || wave == 0) {
				return;
			}
			Entity ship = level.getEntity(shipId);
			if (ship == null || !ship.isAlive() || !ship.getPassengers().isEmpty() || (ship instanceof ShipEntity s && s.sinking)) {
				return;
			}
			if (--warshipTimer > 0) {
				return;
			}
			warshipTimer = CANNON_EVERY[threat];
			List<LivingEntity> targets = defenders(Hideouts.RADIUS + 8);
			Vec3 to = targets.isEmpty() ? center() : targets.get(level.getRandom().nextInt(targets.size())).position();
			to = to.add(level.getRandom().nextGaussian() * 3, 0, level.getRandom().nextGaussian() * 3);
			Vec3 from = ship.position().add(0, 3.5, 0);
			level.sendParticles(ParticleTypes.EXPLOSION, from.x, from.y, from.z, 1, 0, 0, 0, 0);
			level.playSound(null, BlockPos.containing(from), ModSounds.CANNON, SoundSource.HOSTILE, 6.0f, 1.0f);
			shells.add(new Shell(from, to, Math.max(20, (int) (from.distanceTo(to) * 0.8)), false, false));
		}

		/** Shells fly in an arc (smoke trail) and burst where they land. They never break blocks. */
		void tickShells(ServerPlayer captain) {
			Iterator<Shell> it = shells.iterator();
			while (it.hasNext()) {
				Shell shell = it.next();
				shell.age++;
				Vec3 pos = shell.positionAt(shell.age);
				level.sendParticles(ParticleTypes.LARGE_SMOKE, pos.x, pos.y, pos.z, 1, 0.05, 0.05, 0.05, 0);
				if (shell.age < shell.flightTicks) {
					continue;
				}
				it.remove();
				Vec3 at = shell.to;
				level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, at.x, at.y, at.z, 1, 0, 0, 0, 0);
				level.playSound(null, BlockPos.containing(at), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.BLOCKS, 2.5f, 1.0f);
				if (shell.ours) {
					// Our cannons only hurt the Navy.
					for (Mob mob : attackers()) {
						double distance = mob.position().distanceTo(at);
						if (distance < 3.5) {
							mob.hurtServer(level, captain != null ? level.damageSources().explosion(null, captain)
									: level.damageSources().explosion(null, null), (float) (14 - 3 * distance));
						}
					}
					if (shell.atShip && shipId != null && level.getEntity(shipId) instanceof ShipEntity ship) {
						ShipHull.damage(ship, ShipHull.CANNONBALL_DAMAGE, captain, at, null);
					}
				} else {
					for (LivingEntity victim : level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(3), this::isDefender)) {
						victim.hurtServer(level, level.damageSources().explosion(null, null), (float) Math.max(2, 9 - 2 * victim.position().distanceTo(at)));
					}
				}
			}
		}

		// ---- The end ----

		void win(MinecraftServer server, ServerPlayer captain) {
			HideoutFlagBlockEntity entity = flagEntity();
			int berries = 3 * totalWaves * threat;
			if (entity != null) {
				supplyCrate(level, entity);
				entity.store(new ItemStack(CharacterFeature.BERRY, berries));
			}
			long reward = 1_500_000L * totalWaves * threat;
			tellAll(Component.literal("The " + crewName + " held their hideout! The Navy retreats. A captured supply crate and "
					+ berries + " Berries are in the stash.").withStyle(ChatFormatting.GOLD));
			level.playSound(null, flag, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0f, 1.0f);
			if (captain != null) {
				Bounty.raise(captain, reward, "You held your hideout against a Navy assault.", true);
				for (ServerPlayer friend : level.players()) {
					if (friend != captain && friend.distanceToSqr(center()) < (Hideouts.RADIUS + 24) * (Hideouts.RADIUS + 24)
							&& PlayerCrews.friendly(server, captain, friend)) {
						Bounty.raise(friend, reward / 2, "You helped defend " + crewName + "'s hideout.", false);
					}
				}
			}
			saveResult(server, true, "");
		}

		void lose(MinecraftServer server, ServerPlayer captain, String why) {
			HideoutFlagBlockEntity entity = flagEntity();
			int taken = 0;
			if (entity != null) {
				taken = entity.loseShare(level, 0.33f);
				entity.markRaided(level);
			}
			tellAll(Component.literal(why + (taken > 0 ? " They carried off " + taken + " stacks from the stash." : ""))
					.withStyle(ChatFormatting.RED));
			tellAll(Component.literal("The crew will spend tomorrow patching the place up (no haul). Build more defences before they come back.")
					.withStyle(ChatFormatting.GRAY));
			saveResult(server, false, "");
		}

		/** The captain left (or the flag unloaded): the rest is settled by the defence rating. */
		void resolveByNumbers(MinecraftServer server, ServerPlayer captain) {
			Hideouts.Hideout hideout = Hideouts.of(server, owner);
			int defence = hideout != null ? hideout.defence() : 0;
			int left = totalWaves - wave + 1;
			int strength = 6 * left + 6 * threat + level.getRandom().nextInt(11);
			HideoutFlagBlockEntity entity = flagEntity();
			if (defence >= strength) {
				if (entity != null) {
					supplyCrate(level, entity);
				}
				String news = "You left during the Navy assault, but the crew held the hideout (defence " + defence + " vs " + strength + ").";
				saveResult(server, true, entity == null ? news + " A supply crate waits in the stash." : news);
				if (entity == null) {
					Hideouts.Hideout saved = Hideouts.of(server, owner);
					if (saved != null) {
						Hideouts.put(server, owner, saved.siegeDone(saved.lastSiege(), true, "", 0, 1));
					}
				}
			} else {
				if (entity != null) {
					entity.loseShare(level, 0.33f);
					entity.markRaided(level);
				}
				saveResult(server, false, "You left during the Navy assault and the hideout fell (defence " + defence + " vs " + strength
						+ "). The Marines carried off part of the stash.");
				if (entity == null) {
					Hideouts.Hideout saved = Hideouts.of(server, owner);
					if (saved != null) {
						Hideouts.put(server, owner, new Hideouts.Hideout(saved.pos(), saved.crewName(), saved.level(), saved.defence(),
								saved.threat(), saved.lastSiege(), saved.held(), saved.lost(), saved.news(), 33, saved.crates()));
					}
				}
			}
		}

		void saveResult(MinecraftServer server, boolean won, String news) {
			Hideouts.Hideout saved = Hideouts.of(server, owner);
			if (saved != null) {
				Hideouts.put(server, owner, saved.siegeDone(level.getGameTime(), won, news, 0, 0));
			}
		}

		void retreatWave() {
			for (UUID id : members) {
				Entity entity = level.getEntity(id);
				if (entity != null && entity.isAlive()) {
					level.sendParticles(ParticleTypes.CLOUD, entity.getX(), entity.getY() + 1, entity.getZ(), 15, 0.4, 0.6, 0.4, 0.02);
					entity.discard();
				}
			}
			members.clear();
		}

		void cleanUp() {
			bar.removeAllPlayers();
			retreatWave();
			if (shipId != null && level.getEntity(shipId) instanceof ShipEntity warship && ShipEntity.playersAboard(warship).isEmpty()) {
				warship.discard();
			}
		}
	}

	private static final class Shell {
		final Vec3 from;
		final Vec3 to;
		final int flightTicks;
		final boolean ours;
		final boolean atShip;
		int age;

		Shell(Vec3 from, Vec3 to, int flightTicks, boolean ours, boolean atShip) {
			this.from = from;
			this.to = to;
			this.flightTicks = flightTicks;
			this.ours = ours;
			this.atShip = atShip;
		}

		Vec3 positionAt(int tick) {
			double t = Math.min(1.0, tick / (double) flightTicks);
			double arc = from.distanceTo(to) * 0.25 * 4 * t * (1 - t);
			return from.lerp(to, t).add(0, arc, 0);
		}
	}

	/** Marines or officers left over from an attack that's no longer running (after a restart) go home. */
	static void cleanLeftover(Entity entity) {
		if (!entity.entityTags().contains(TAG)) {
			return;
		}
		for (Siege siege : SIEGES.values()) {
			if (siege.members.contains(entity.getUUID())) {
				return;
			}
		}
		entity.discard();
	}
}
