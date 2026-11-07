package com.onepiecemod.vegapunk;

import com.onepiecemod.util.Motion;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.Difficulty;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.advancement.AdvancementFeature;
import com.onepiecemod.bounty.NavyCalm;
import com.onepiecemod.character.BossAbility;
import com.onepiecemod.character.BossStrikes;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.config.ModConfig;
import com.onepiecemod.fx.MoveFx;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;
import com.onepiecemod.power.FruitControl;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.story.StoryGates;
import com.onepiecemod.story.StoryProgress;

/**
 * Pacifista and Seraphim hunts: roaming mini-bosses that come looking for strong pirates.
 *
 * Every minute each player in the right waters may be found by one (see eligible()):
 *  - Pacifista from the Sabaody chapter on, in the second half of Paradise, the New World, Sabaody and Egghead.
 *  - The giant Mark III in the New World, once you've reached Fish-Man Island.
 *  - Seraphim in the New World once Wano is done (the Egghead era).
 * A hunt walks out of the trees 28-44 blocks away, has a boss bar, and uses signature moves with warning circles.
 * If you get far away or die, it gives up and leaves. Nothing about a hunt is saved: after a restart it is gone.
 *
 * Beaten, they drop the parts for cyborg upgrades (VegapunkItems, Cyborg).
 */
public class VegapunkHunts {
	public static final String TAG = "onepiece_vegapunk_hunt";

	private static final int ROLL_EVERY = 1200;        // A roll per player each minute...
	private static final float CHANCE = 0.08f;         // ...8% of them find a hunt (about every 12 minutes in the right seas),
	private static final float HOT_CHANCE = 0.18f;     // more at Sabaody and Egghead.
	private static final int REST = 20 * 60 * 10;      // and then 10 minutes without one.
	private static final double BAR_RANGE = 48.0;
	private static final double GIVE_UP_RANGE = 96.0;
	private static final int GIVE_UP_TICKS = 20 * 30;
	private static final int MAX_AGE = 20 * 60 * 15;

	private static final Map<UUID, Hunt> ACTIVE = new HashMap<>();
	/** Game time when a player may be found by the next hunt. */
	private static final Map<UUID, Long> REST_UNTIL = new HashMap<>();
	private static int serial = 0;

	private enum Kind { LASER, BLAST, PAW, CHARM, QUAKE }

	/** A move announced by a warning circle that lands when its fuse runs out. */
	private static final class Telegraph {
		final Kind kind;
		final Vec3 at;
		final double radius;
		final float damage;
		int fuse;

		Telegraph(Kind kind, Vec3 at, double radius, int fuse, float damage) {
			this.kind = kind;
			this.at = at;
			this.radius = radius;
			this.fuse = fuse;
			this.damage = damage;
		}
	}

	private static final class Hunt {
		final HuntUnit unit;
		final ServerLevel level;
		final UUID entity;
		final UUID player;
		final ServerBossEvent bar;
		final BossStrikes strikes = new BossStrikes();
		final List<Telegraph> telegraphs = new ArrayList<>();
		int cooldown = 80;
		int moveIndex = 0;
		int age = 0;
		int away = 0;
		int leaving = -1;
		boolean flame = false;

		Hunt(HuntUnit unit, ServerLevel level, UUID entity, UUID player, Component name) {
			this.unit = unit;
			this.level = level;
			this.entity = entity;
			this.player = player;
			this.bar = new ServerBossEvent(UUID.randomUUID(), name, unit.barColor, BossEvent.BossBarOverlay.NOTCHED_10);
		}
	}

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(VegapunkHunts::tick);
		// While a Pacifista or Seraphim hunts you, the Navy doesn't send a squad or a raid on top of it.
		com.onepiecemod.bounty.NavyCalm.register(player -> ACTIVE.values().stream().anyMatch(hunt -> hunt.player.equals(player.getUUID())));

		// Hunts are never saved: one that loads from disk (after a restart) is a leftover.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(TAG) && !ACTIVE.containsKey(entity.getUUID())) {
				entity.discard();
			}
		});

		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(entity.level() instanceof ServerLevel level) || !(entity instanceof HumanNpc npc)) {
				return;
			}
			Hunt hunt = ACTIVE.remove(entity.getUUID());
			if (hunt != null) {
				defeated(hunt, npc, level);
			} else if (source.getEntity() instanceof Player) {
				commonDrops(npc, level);
			}
		});

		// Seraphim burn with the Lunarian flame: fire can't hurt them.
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			if (source.is(DamageTypeTags.IS_FIRE) && entity.entityTags().contains(TAG)) {
				Hunt hunt = ACTIVE.get(entity.getUUID());
				return hunt == null || !hunt.unit.seraphim;
			}
			return true;
		});
	}

	// ---------- Starting a hunt ----------

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % ROLL_EVERY == 0) {
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				roll(player);
			}
		}
		Iterator<Hunt> it = ACTIVE.values().iterator();
		while (it.hasNext()) {
			Hunt hunt = it.next();
			if (!tickHunt(server, hunt)) {
				hunt.bar.removeAllPlayers();
				it.remove();
			}
		}
	}

	private static void roll(ServerPlayer player) {
		ServerLevel level = player.level();
		if (level.getDifficulty() == Difficulty.PEACEFUL || player.isCreative() || player.isSpectator()
				|| level.getGameTime() < REST_UNTIL.getOrDefault(player.getUUID(), 0L) || huntOf(player) != null
				|| !NavyCalm.canStart(player)) {
			return;
		}
		List<HuntUnit> units = eligible(player);
		if (units.isEmpty()) {
			return;
		}
		float chance = hotSpot(player) ? HOT_CHANCE : CHANCE;
		if (player.getRandom().nextFloat() < chance) {
			start(player, pick(units, player.getRandom()), false);
		}
	}

	private static boolean hotSpot(ServerPlayer player) {
		String biome = biomeId(player);
		return biome.equals("onepiece:sabaody") || biome.equals("onepiece:egghead");
	}

	private static String biomeId(ServerPlayer player) {
		return player.level().getBiome(player.blockPosition()).unwrapKey().map(key -> key.identifier().toString()).orElse("");
	}

	/** The units that may come for this player here and now. */
	public static List<HuntUnit> eligible(ServerPlayer player) {
		List<HuntUnit> units = new ArrayList<>();
		if (player.level().dimension() != Level.OVERWORLD) {
			return units;
		}
		boolean gates = StoryGates.gatesOn(player);
		StoryProgress story = StoryProgress.orStart(player);
		String biome = biomeId(player);
		boolean egghead = biome.equals("onepiece:egghead");
		boolean sabaody = biome.equals("onepiece:sabaody") || biome.equals("onepiece:red_line_heights");
		CalmBelt.Sea sea = CalmBelt.seaByDistance(player.blockPosition());
		double distance = Math.sqrt(player.getX() * player.getX() + player.getZ() * player.getZ());
		boolean newWorld = sea == CalmBelt.Sea.NEW_WORLD || egghead;
		boolean lateParadise = newWorld || sabaody || (sea == CalmBelt.Sea.GRAND_LINE && distance > 2500);

		if (lateParadise && (!gates || story.reached(StoryGates.SABAODY))) {
			units.add(HuntUnit.PACIFISTA);
		}
		if (newWorld && (!gates || story.reached("fishman_island"))) {
			units.add(HuntUnit.MARK_III);
		}
		if (newWorld && (!gates || story.completed(StoryGates.AFTER_WANO))) {
			units.add(HuntUnit.S_BEAR);
			units.add(HuntUnit.S_HAWK);
			units.add(HuntUnit.S_SNAKE);
			units.add(HuntUnit.S_SHARK);
		}
		return units;
	}

	private static HuntUnit pick(List<HuntUnit> units, RandomSource random) {
		int total = 0;
		for (HuntUnit unit : units) {
			total += unit.weight;
		}
		int roll = random.nextInt(Math.max(1, total));
		for (HuntUnit unit : units) {
			roll -= unit.weight;
			if (roll < 0) {
				return unit;
			}
		}
		return units.get(0);
	}

	/**
	 * Sends a unit after a player. Returns the unit's name, or null if there was no dry ground to walk in from.
	 * near = true (the test command) puts it 10 blocks away instead of out of sight.
	 */
	public static String start(ServerPlayer player, HuntUnit unit, boolean near) {
		ServerLevel level = player.level();
		BlockPos spot = findSpot(level, player, near, (int) Math.ceil(1.95 * unit.scale));
		if (spot == null) {
			return null;
		}
		HumanNpc npc = NpcFeature.spawn(level, unit.kit, spot, (float) Math.toDegrees(Math.atan2(player.getX() - spot.getX(), spot.getZ() - player.getZ())));
		if (npc == null) {
			return null;
		}
		boolean rogue = com.onepiecemod.career.Careers.isMarine(player);
		String name = (rogue ? "Rogue " : "") + (unit.name.contains("%d") ? String.format(unit.name, 10 + (serial++ % 90)) : unit.name);
		dress(npc, unit, name);
		npc.setTarget(player);

		Component barName = Component.literal(name).withStyle(unit.seraphim ? ChatFormatting.LIGHT_PURPLE : ChatFormatting.YELLOW);
		Hunt hunt = new Hunt(unit, level, npc.getUUID(), player.getUUID(), barName);
		ACTIVE.put(npc.getUUID(), hunt);
		REST_UNTIL.put(player.getUUID(), level.getGameTime() + REST);

		String where = direction(player.position(), npc.position()) + ", " + (int) Math.sqrt(player.distanceToSqr(npc)) + " blocks";
		player.sendSystemMessage(Component.literal(unit.arrival).withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
		player.sendSystemMessage(Component.literal(name + " is hunting you! (" + where + ")")
				.withStyle(unit.seraphim ? ChatFormatting.LIGHT_PURPLE : ChatFormatting.GOLD, ChatFormatting.BOLD));
		if (rogue) {
			player.sendSystemMessage(Component.literal("Its control chip is scrambled: it attacks Marines too!").withStyle(ChatFormatting.RED));
		}
		player.sendSystemMessage(Component.literal("<" + name + "> " + unit.line).withStyle(ChatFormatting.WHITE));
		level.playSound(null, npc.blockPosition(), unit.seraphim ? SoundEvents.PHANTOM_FLAP : SoundEvents.IRON_GOLEM_STEP,
				SoundSource.HOSTILE, 2.0f, unit.seraphim ? 0.6f : 0.5f);
		if (unit.seraphim) {
			level.sendParticles(ParticleTypes.LARGE_SMOKE, npc.getX(), npc.getY() + 1.5, npc.getZ(), 20, 0.6, 0.6, 0.6, 0.02);
		}
		return name;
	}

	/** Turns a freshly spawned kit NPC into the hunt unit: tougher, bigger, its own look and style. */
	private static void dress(HumanNpc npc, HuntUnit unit, String name) {
		if (unit.skin != null) {
			npc.setSkin(unit.skin);
		}
		if (unit == HuntUnit.S_HAWK) {
			npc.setItemSlot(EquipmentSlot.MAINHAND, CharacterData.stack("minecraft:netherite_sword", 1));
		} else { // Pacifistas and the rest fight with lasers and their bodies, never a held weapon.
			npc.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
		}
		npc.setItemSlot(EquipmentSlot.OFFHAND, ItemStack.EMPTY);
		npc.setDropChance(EquipmentSlot.MAINHAND, 0.0f);
		npc.setStyle(unit.style);
		setBase(npc, Attributes.MAX_HEALTH, unit.health * ModConfig.npcHealth());
		setBase(npc, Attributes.ATTACK_DAMAGE, unit.damage * ModConfig.npcDamage() - CharacterData.weaponBonus(npc.getMainHandItem()));
		setBase(npc, Attributes.ARMOR, unit.armor);
		setBase(npc, Attributes.KNOCKBACK_RESISTANCE, unit == HuntUnit.MARK_III ? 1.0 : 0.85);
		setBase(npc, Attributes.SCALE, unit.scale);
		setBase(npc, Attributes.FOLLOW_RANGE, 64.0);
		npc.setHealth(npc.getMaxHealth());
		npc.setCustomName(Component.literal(name));
		npc.addTag(TAG);
		npc.addTag("onepiece_vp_" + unit.id);
		npc.setPersistenceRequired();
	}

	private static void setBase(LivingEntity entity, net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute, double value) {
		AttributeInstance instance = entity.getAttribute(attribute);
		if (instance != null) {
			instance.setBaseValue(value);
		}
	}

	private static BlockPos findSpot(ServerLevel level, ServerPlayer player, boolean near, int height) {
		RandomSource random = player.getRandom();
		for (int attempt = 0; attempt < 16; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			int distance = near ? 8 + random.nextInt(4) : 28 + random.nextInt(17);
			int x = (int) Math.floor(player.getX() + Math.cos(angle) * distance);
			int z = (int) Math.floor(player.getZ() + Math.sin(angle) * distance);
			if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
				continue;
			}
			BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
			if (standable(level, pos, height) && Math.abs(pos.getY() - player.getY()) < 16) {
				return pos;
			}
		}
		return null;
	}

	/** Dry solid ground with room above for the unit (big ones need more). */
	private static boolean standable(ServerLevel level, BlockPos pos, int height) {
		if (!level.getBlockState(pos.below()).isSolid() || !level.getFluidState(pos.below()).isEmpty()) {
			return false;
		}
		for (int dy = 0; dy < height; dy++) {
			BlockPos p = pos.above(dy);
			if (!level.getBlockState(p).getCollisionShape(level, p).isEmpty() || !level.getFluidState(p).isEmpty()) {
				return false;
			}
		}
		return true;
	}

	private static String direction(Vec3 from, Vec3 to) {
		double angle = Math.toDegrees(Math.atan2(to.x - from.x, from.z - to.z));
		String[] names = {"north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"};
		return names[(int) Math.floorMod(Math.round(angle / 45.0), 8)];
	}

	/** The hunt going after this player, or null. */
	private static Hunt huntOf(ServerPlayer player) {
		for (Hunt hunt : ACTIVE.values()) {
			if (hunt.player.equals(player.getUUID())) {
				return hunt;
			}
		}
		return null;
	}

	public static int activeCount() {
		return ACTIVE.size();
	}

	public static List<String> describe() {
		List<String> lines = new ArrayList<>();
		for (Hunt hunt : ACTIVE.values()) {
			Entity entity = hunt.level.getEntity(hunt.entity);
			lines.add(hunt.unit.id + (entity == null ? " (unloaded)" : " at " + entity.blockPosition().toShortString())
					+ ", " + hunt.age / 20 + " s");
		}
		return lines;
	}

	/** Ends every hunt now (the command). */
	public static int stopAll() {
		int n = 0;
		for (Hunt hunt : List.copyOf(ACTIVE.values())) {
			Entity entity = hunt.level.getEntity(hunt.entity);
			if (entity != null) {
				entity.discard();
			}
			hunt.bar.removeAllPlayers();
			n++;
		}
		ACTIVE.clear();
		return n;
	}

	// ---------- A hunt in progress ----------

	/** Returns false when the hunt is over (gone, given up). */
	private static boolean tickHunt(MinecraftServer server, Hunt hunt) {
		if (!(hunt.level.getEntity(hunt.entity) instanceof HumanNpc npc) || npc.isRemoved() || !npc.isAlive()) {
			return false;
		}
		ServerLevel level = hunt.level;
		hunt.age++;
		hunt.bar.setProgress(Math.max(0f, npc.getHealth() / npc.getMaxHealth()));
		if (hunt.age % 10 == 0) {
			updateBar(hunt, npc);
		}

		if (hunt.leaving >= 0) {
			return leave(hunt, npc);
		}

		ServerPlayer player = server.getPlayerList().getPlayer(hunt.player);
		boolean present = player != null && player.isAlive() && player.level() == level && !player.isSpectator() && !player.isCreative();
		if (present && player.distanceToSqr(npc) < GIVE_UP_RANGE * GIVE_UP_RANGE) {
			hunt.away = 0;
			if (npc.getTarget() == null || !npc.getTarget().isAlive()) {
				npc.setTarget(player);
			}
		} else {
			hunt.away++;
		}
		if (hunt.away > GIVE_UP_TICKS || hunt.age > MAX_AGE || (player != null && !player.isAlive())) {
			hunt.leaving = 40;
			String why = player != null && !player.isAlive() ? "Target down. Returning to base." : "Target lost. Returning to base.";
			for (ServerPlayer p : hunt.bar.getPlayers()) {
				p.sendSystemMessage(Component.literal("<" + npc.getCustomName().getString() + "> " + why).withStyle(ChatFormatting.GRAY));
			}
			return true;
		}

		hunt.strikes.tick(npc, level);
		tickTelegraphs(hunt, npc, level);
		if (hunt.unit.seraphim) {
			seraphimTick(hunt, npc, level);
		}

		LivingEntity target = npc.getTarget();
		if (hunt.cooldown > 0) {
			hunt.cooldown--;
			return true;
		}
		if (target == null || !target.isAlive() || npc.distanceToSqr(target) > 26 * 26 || !npc.getSensing().hasLineOfSight(target)) {
			return true;
		}
		signatureMove(hunt, npc, target, level);
		return true;
	}

	private static void updateBar(Hunt hunt, HumanNpc npc) {
		for (ServerPlayer p : List.copyOf(hunt.bar.getPlayers())) {
			if (p.isRemoved() || p.level() != hunt.level || p.distanceToSqr(npc) > BAR_RANGE * BAR_RANGE) {
				hunt.bar.removePlayer(p);
			}
		}
		for (ServerPlayer p : hunt.level.players()) {
			if (!p.isSpectator() && p.distanceToSqr(npc) <= BAR_RANGE * BAR_RANGE) {
				hunt.bar.addPlayer(p);
			}
		}
	}

	/** Gives up: Pacifista stomp away in a cloud of steam, Seraphim fly off. */
	private static boolean leave(Hunt hunt, HumanNpc npc) {
		npc.setTarget(null);
		npc.getNavigation().stop();
		hunt.leaving--;
		if (hunt.leaving % 5 == 0) {
			hunt.level.sendParticles(hunt.unit.seraphim ? ParticleTypes.FLAME : ParticleTypes.CLOUD,
					npc.getX(), npc.getY() + 1, npc.getZ(), 8, 0.4, 0.8, 0.4, 0.03);
		}
		if (hunt.leaving <= 0) {
			hunt.level.sendParticles(ParticleTypes.POOF, npc.getX(), npc.getY() + 1, npc.getZ(), 30, 0.6, 1.0, 0.6, 0.05);
			hunt.level.playSound(null, npc.blockPosition(), SoundEvents.PHANTOM_FLAP, SoundSource.HOSTILE, 1.5f, 0.7f);
			npc.discard();
			return false;
		}
		return true;
	}

	private static float damage(HumanNpc npc) {
		return (float) npc.getAttributeValue(Attributes.ATTACK_DAMAGE);
	}

	/** The unit's signature moves, taking turns. Harder ones come quicker below half health. */
	private static void signatureMove(Hunt hunt, HumanNpc npc, LivingEntity target, ServerLevel level) {
		float dmg = damage(npc);
		boolean angry = npc.getHealth() < npc.getMaxHealth() * 0.5f;
		int move = hunt.moveIndex++ % 2;
		Vec3 at = target.position();
		switch (hunt.unit) {
			case PACIFISTA -> {
				if (move == 0) {
					laserVolley(hunt, npc, target, dmg, angry ? 4 : 3);
				} else {
					shout(npc, level, "Laser rain.");
					hunt.strikes.signature("rain_light", npc, target, level, dmg * 0.8f, angry ? 2 : 0);
				}
				hunt.cooldown = angry ? 90 : 130;
			}
			case MARK_III -> {
				switch (hunt.moveIndex % 3) {
					case 0 -> hunt.strikes.signature("ground_wave", npc, target, level, dmg, 0);
					case 1 -> laserVolley(hunt, npc, target, dmg, 5);
					default -> hunt.strikes.signature("rain_light", npc, target, level, dmg * 0.9f, angry ? 4 : 2);
				}
				hunt.cooldown = angry ? 80 : 110;
			}
			case S_BEAR -> {
				if (move == 0) {
					shout(npc, level, "Pad Ho!");
					hunt.telegraphs.add(new Telegraph(Kind.PAW, at, 2.5, 16, dmg * 0.6f));
				} else {
					shout(npc, level, "Ursus Shock!");
					com.onepiecemod.anim.CombatAnims.play(npc, com.onepiecemod.anim.Anim.SUMMON, 40);
					hunt.telegraphs.add(new Telegraph(Kind.BLAST, at, 5.0, 40, dmg * 1.5f));
				}
				hunt.cooldown = angry ? 90 : 120;
			}
			case S_HAWK -> {
				if (move == 0) {
					shout(npc, level, "Black Blade.");
					hunt.strikes.signature("slash_line", npc, target, level, dmg * 1.1f, 0);
				} else {
					wingDash(npc, target, level, dmg);
				}
				hunt.cooldown = angry ? 80 : 110;
			}
			case S_SNAKE -> {
				if (move == 0) {
					shout(npc, level, "Slave Arrow!");
					hunt.telegraphs.add(new Telegraph(Kind.CHARM, at, 3.0, 20, dmg * 0.6f));
				} else {
					shout(npc, level, "Perfume Femur!");
					wingDash(npc, target, level, dmg);
				}
				hunt.cooldown = angry ? 90 : 120;
			}
			case S_SHARK -> {
				if (move == 0) {
					shout(npc, level, "Five Thousand Tile Fist!");
					com.onepiecemod.anim.CombatAnims.play(npc, com.onepiecemod.anim.Anim.GROUND_SLAM, 24);
					hunt.telegraphs.add(new Telegraph(Kind.QUAKE, npc.position(), 6.0, 24, dmg * 1.1f));
				} else {
					shout(npc, level, "Vagabond Drill!");
					wingDash(npc, target, level, dmg * 1.1f);
				}
				hunt.cooldown = angry ? 90 : 120;
			}
		}
	}

	private static void shout(HumanNpc npc, ServerLevel level, String text) {
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(npc) < 32 * 32) {
				p.sendOverlayMessage(Component.literal(npc.getCustomName().getString() + ": " + text).withStyle(ChatFormatting.RED));
			}
		}
	}

	/** Laser beams at where the target stands (and around it). Each has a warning circle; keep moving. */
	private static void laserVolley(Hunt hunt, HumanNpc npc, LivingEntity target, float dmg, int count) {
		RandomSource random = npc.getRandom();
		com.onepiecemod.anim.CombatAnims.play(npc, com.onepiecemod.anim.Anim.POINT);
		hunt.level.playSound(null, npc.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 1.5f, 1.8f);
		for (int i = 0; i < count; i++) {
			Vec3 spot = i == 0 ? target.position() : target.position().add((random.nextDouble() - 0.5) * 6, 0, (random.nextDouble() - 0.5) * 6);
			hunt.telegraphs.add(new Telegraph(Kind.LASER, spot, 1.8, 14 + i * 5, dmg * 0.85f));
		}
	}

	/** Seraphim swoop: a flap of the wings and they're on you. */
	private static void wingDash(HumanNpc npc, LivingEntity target, ServerLevel level, float dmg) {
		Vec3 to = target.position().subtract(npc.position());
		Vec3 dir = to.normalize();
		npc.setDeltaMovement(dir.x * 1.4, 0.45, dir.z * 1.4);
		Motion.sync(npc);
		com.onepiecemod.anim.CombatAnims.play(npc, npc.getMainHandItem().isEmpty() ? com.onepiecemod.anim.Anim.KICK : com.onepiecemod.anim.Anim.THRUST);
		level.playSound(null, npc.blockPosition(), SoundEvents.PHANTOM_FLAP, SoundSource.HOSTILE, 1.2f, 1.2f);
		level.sendParticles(ParticleTypes.LARGE_SMOKE, npc.getX(), npc.getY() + 1.2, npc.getZ(), 10, 0.4, 0.3, 0.4, 0.02);
		if (to.length() < 6) {
			target.hurtServer(level, npc.damageSources().mobAttack(npc), dmg * 0.9f);
			target.knockback(0.8, -dir.x, -dir.z, target.damageSources().generic(), 0.0f);
		}
	}

	private static void tickTelegraphs(Hunt hunt, HumanNpc npc, ServerLevel level) {
		Iterator<Telegraph> it = hunt.telegraphs.iterator();
		while (it.hasNext()) {
			Telegraph t = it.next();
			t.fuse--;
			if (t.fuse > 0) {
				if (t.fuse % 3 == 0) {
					BossStrikes.ring(level, t.at, t.radius, t.fuse <= 6 ? 0xFFFFE040 : 0xFFE02020);
				}
				continue;
			}
			it.remove();
			land(t, npc, level);
		}
	}

	private static void land(Telegraph t, HumanNpc npc, ServerLevel level) {
		switch (t.kind) {
			case LASER -> {
				Vec3 from = npc.getEyePosition();
				Vec3 to = t.at.add(0, 0.3, 0);
				MoveFx.spawn(level, MoveFx.LASER.style(), from, to.subtract(from), MoveFx.LASER.color(), MoveFx.LASER.color2(), 1.0f, 8, npc, null);
				level.playSound(null, t.at.x, t.at.y, t.at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 0.9f, 1.4f);
				level.sendParticles(ParticleTypes.EXPLOSION, t.at.x, t.at.y + 0.3, t.at.z, 1, 0, 0, 0, 0);
				for (LivingEntity victim : victims(npc, level, t.at, t.radius)) {
					victim.hurtServer(level, npc.damageSources().mobAttack(npc), t.damage);
					victim.igniteForSeconds(2);
				}
			}
			case BLAST -> { // Ursus Shock: compressed air bursts like a bomb.
				MoveFx.spawn(level, com.onepiecemod.fx.MoveStyle.SPHERE, t.at.add(0, 1, 0), Vec3.ZERO, 0xFFFFFFFF, 0xFFF5A0C0, (float) t.radius, 16, npc, null);
				level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, t.at.x, t.at.y + 0.5, t.at.z, 1, 0, 0, 0, 0);
				level.playSound(null, t.at.x, t.at.y, t.at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0f, 0.6f);
				for (LivingEntity victim : victims(npc, level, t.at, t.radius)) {
					victim.hurtServer(level, npc.damageSources().mobAttack(npc), t.damage);
					Vec3 push = victim.position().subtract(t.at).normalize();
					victim.setDeltaMovement(push.x * 1.5, 0.7, push.z * 1.5);
					Motion.sync(victim);
				}
			}
			case PAW -> { // Pad Ho: a paw-shaped blast of air that throws you high.
				MoveFx.spawn(level, MoveFx.PAW_ORB.style(), npc.getEyePosition(), t.at.add(0, 1, 0).subtract(npc.getEyePosition()),
						MoveFx.PAW_ORB.color(), MoveFx.PAW_ORB.color2(), MoveFx.PAW_ORB.size(), 10, npc, MoveFx.PAW_ORB.trail());
				level.playSound(null, t.at.x, t.at.y, t.at.z, com.onepiecemod.sound.BossSounds.PAW, SoundSource.HOSTILE, 1.5f, 1.0f);
				for (LivingEntity victim : victims(npc, level, t.at, t.radius)) {
					victim.hurtServer(level, npc.damageSources().mobAttack(npc), t.damage);
					victim.setDeltaMovement(victim.getDeltaMovement().x, 1.4, victim.getDeltaMovement().z);
					Motion.sync(victim);
				}
			}
			case CHARM -> { // Slave Arrow: hearts that turn you to stone for a moment.
				LivingEntity first = null;
				for (LivingEntity victim : victims(npc, level, t.at, t.radius)) {
					victim.hurtServer(level, npc.damageSources().mobAttack(npc), t.damage);
					FruitControl.apply(victim, new MobEffectInstance(MobEffects.SLOWNESS, 50, 5));
					FruitControl.apply(victim, new MobEffectInstance(MobEffects.MINING_FATIGUE, 50, 2));
					first = first == null ? victim : first;
				}
				if (first != null) {
					BossAbility.use("petrify", npc, first, level);
				} else {
					MoveFx.spawn(level, MoveFx.HEART_ORB.style(), npc.getEyePosition(), t.at.subtract(npc.getEyePosition()),
							MoveFx.HEART_ORB.color(), MoveFx.HEART_ORB.color2(), MoveFx.HEART_ORB.size(), 10, npc, MoveFx.HEART_ORB.trail());
				}
			}
			case QUAKE -> { // A Fish-Man Karate punch that shakes the water in your body.
				MoveFx.shockwave(level, npc.position(), t.radius, MoveFx.QUAKE, MoveFx.QUAKE_OUT);
				level.sendParticles(ParticleTypes.SPLASH, npc.getX(), npc.getY() + 0.5, npc.getZ(), 60, t.radius / 2, 0.3, t.radius / 2, 0.2);
				level.playSound(null, npc.blockPosition(), com.onepiecemod.sound.ModSounds.MOVE_QUAKE, SoundSource.HOSTILE, 1.8f, 0.9f);
				for (LivingEntity victim : victims(npc, level, npc.position(), t.radius)) {
					victim.hurtServer(level, npc.damageSources().mobAttack(npc), t.damage);
					Vec3 push = victim.position().subtract(npc.position()).normalize();
					victim.setDeltaMovement(push.x * 1.8, 0.5, push.z * 1.8);
					Motion.sync(victim);
				}
			}
		}
	}

	/** Who a move can hit: players and their crewmates and pets, never the unit itself or Marines. */
	private static List<LivingEntity> victims(HumanNpc npc, ServerLevel level, Vec3 at, double radius) {
		return level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(radius, 3, radius), e -> e != npc && e.isAlive()
				&& e.position().distanceToSqr(at) <= radius * radius + 4
				&& !(e instanceof Player p && (p.isCreative() || p.isSpectator()))
				&& (e instanceof Player || e instanceof com.onepiecemod.crew.CrewmateEntity
						|| (e instanceof com.onepiecemod.creature.CreatureEntity pet && pet.isTamed())));
	}

	/** Lunarian flame: below half health a Seraphim's back bursts into fire and its skin hardens. */
	private static void seraphimTick(Hunt hunt, HumanNpc npc, ServerLevel level) {
		npc.clearFire();
		if (!hunt.flame && npc.getHealth() < npc.getMaxHealth() * 0.5f) {
			hunt.flame = true;
			setBase(npc, Attributes.ARMOR, hunt.unit.armor + 8);
			setBase(npc, Attributes.MOVEMENT_SPEED, npc.getAttributeBaseValue(Attributes.MOVEMENT_SPEED) * 1.15);
			level.playSound(null, npc.blockPosition(), SoundEvents.BLAZE_SHOOT, SoundSource.HOSTILE, 1.5f, 0.6f);
			level.sendParticles(ParticleTypes.FLAME, npc.getX(), npc.getY() + 1.4, npc.getZ(), 40, 0.4, 0.4, 0.4, 0.06);
			shout(npc, level, "Lunarian flame, ignite.");
		}
		if (hunt.flame && hunt.age % 4 == 0) {
			Vec3 back = npc.position().add(0, npc.getBbHeight() * 0.75, 0).subtract(npc.getLookAngle().multiply(1, 0, 1).scale(0.4));
			level.sendParticles(ParticleTypes.FLAME, back.x, back.y, back.z, 2, 0.15, 0.1, 0.15, 0.01);
		}
		// Black wings: they hop up to targets on roofs or ledges.
		LivingEntity target = npc.getTarget();
		if (target != null && npc.onGround() && target.getY() > npc.getY() + 2.5 && hunt.age % 40 == 0) {
			npc.setDeltaMovement(npc.getDeltaMovement().x, 1.0, npc.getDeltaMovement().z);
			Motion.sync(npc);
			level.playSound(null, npc.blockPosition(), SoundEvents.PHANTOM_FLAP, SoundSource.HOSTILE, 1.0f, 1.0f);
		}
		npc.resetFallDistance();
	}

	// ---------- Loot ----------

	private static void defeated(Hunt hunt, HumanNpc npc, ServerLevel level) {
		hunt.bar.removeAllPlayers();
		// Achievements (tools/advancements/gen_advancements.py, wonders tab).
		if (level.getServer().getPlayerList().getPlayer(hunt.player) instanceof ServerPlayer hunted) {
			if (!hunt.unit.seraphim) {
				AdvancementFeature.grant(hunted, "wonders/pacifista");
			}
			if (hunt.unit == HuntUnit.MARK_III) {
				AdvancementFeature.grant(hunted, "wonders/mark_iii");
			}
			if (hunt.unit.seraphim) {
				AdvancementFeature.grant(hunted, "wonders/seraphim");
				AdvancementFeature.grant(hunted, "wonders/all_seraphim", hunt.unit.id);
			}
		}
		RandomSource random = npc.getRandom();
		switch (hunt.unit) {
			case PACIFISTA -> {
				drop(npc, level, VegapunkItems.PACIFISTA_SCRAP, 3 + random.nextInt(3));
				drop(npc, level, VegapunkItems.LASER_CORE, 1);
				if (random.nextFloat() < 0.25f) {
					drop(npc, level, VegapunkItems.VEGAPUNK_CHIP, 1);
				}
			}
			case MARK_III -> {
				drop(npc, level, VegapunkItems.PACIFISTA_SCRAP, 6 + random.nextInt(4));
				drop(npc, level, VegapunkItems.LASER_CORE, 2);
				if (random.nextFloat() < 0.6f) {
					drop(npc, level, VegapunkItems.VEGAPUNK_CHIP, 1);
				}
			}
			default -> {
				drop(npc, level, VegapunkItems.PACIFISTA_SCRAP, 2 + random.nextInt(3));
				drop(npc, level, VegapunkItems.SERAPHIM_FEATHER, 2 + (random.nextBoolean() ? 1 : 0));
				drop(npc, level, VegapunkItems.VEGAPUNK_CHIP, 1);
			}
		}
		level.sendParticles(ParticleTypes.EXPLOSION, npc.getX(), npc.getY() + 1, npc.getZ(), 3, 0.5, 0.5, 0.5, 0);
		level.sendParticles(ParticleTypes.ELECTRIC_SPARK, npc.getX(), npc.getY() + 1, npc.getZ(), 30, 0.6, 0.8, 0.6, 0.2);
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(npc) < BAR_RANGE * BAR_RANGE) {
				p.sendSystemMessage(Component.literal(npc.getCustomName().getString() + " is down! Its parts are scattered on the ground.")
						.withStyle(ChatFormatting.GREEN));
			}
		}
	}

	/** Ordinary Pacifista and Seraphim (patrols at Sabaody and Egghead, raids) drop a little too. */
	private static void commonDrops(HumanNpc npc, ServerLevel level) {
		RandomSource random = npc.getRandom();
		if ("pacifista".equals(npc.getKitId()) && random.nextFloat() < 0.4f) {
			drop(npc, level, VegapunkItems.PACIFISTA_SCRAP, 1);
		} else if ("seraphim".equals(npc.getKitId())) {
			if (random.nextFloat() < 0.5f) {
				drop(npc, level, VegapunkItems.PACIFISTA_SCRAP, 1);
			}
			if (random.nextFloat() < 0.15f) {
				drop(npc, level, VegapunkItems.SERAPHIM_FEATHER, 1);
			}
		}
	}

	private static void drop(HumanNpc npc, ServerLevel level, Item item, int count) {
		if (count > 0) {
			npc.spawnAtLocation(level, new ItemStack(item, count));
		}
	}
}
