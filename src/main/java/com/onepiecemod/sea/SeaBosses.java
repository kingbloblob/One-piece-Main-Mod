package com.onepiecemod.sea;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Prediction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.BossStrikes;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.resource.Resources;
import com.onepiecemod.util.Motion;

/**
 * The Sea King bosses: four legendary sea monsters, one for each sea. Each is a Sea King grown huge,
 * with its own color, health bar and special moves, and a trophy the first time you beat it.
 *  - Lord of the Coast (East Blue): the Sea King that took Shanks' arm. Bites grab you and drag you under.
 *  - Florian Phantom (Grand Line): a pale ghost of the Florian Triangle fog. Blinds you, vanishes, strikes from below.
 *  - Calm Belt Behemoth (Calm Belt): the biggest of the Calm Belt nest. Calls its brood and smashes the sea flat.
 *  - Ancient Sea King (New World): one of the oldest Sea Kings, the kind that answered Poseidon's call.
 *    (Its 1000 health is close to Minecraft's 1024 cap, so it gets its toughness from armor instead.)
 *
 * Two more guard the waters around Egghead (sea = null: no lure calls them, see EggheadWaters):
 *  - Mecha-Shark: Vegapunk's robot shark, the one that attacks the Thousand Sunny as it reaches Egghead.
 *  - Sea Beast Weapon: one of Lilith's cyborg Sea Kings. Fires lasers and missiles and calls its cyborg brood.
 *
 * How to meet one: a Sea Lord Lure thrown over deep water calls the boss of the sea you're in, and now and then
 * a wild Sea King turns out to be the boss itself (SeaKingSpawner). Bosses can't be tamed.
 * Ops can test with /seaboss summon <id>. Anyone can see their record with /seaboss.
 */
public final class SeaBosses {
	public enum Move { TIDAL_WAVE, WHIRLPOOL, DIVE_LUNGE, ROAR, BROOD, FOG, LASER, MISSILES }

	/** One boss. variant = which sea_king_<n>.png texture it wears. bounty = how much it raises your bounty the first time. */
	public record Boss(String id, String name, CalmBelt.Sea sea, int variant, double health, double damage, double armor, double scale,
			int berries, long bounty, String trophy, List<Move> moves, boolean snatches, String intro, String phaseLine) {
	}

	public static final Map<String, Boss> BOSSES = new LinkedHashMap<>();

	static {
		add(new Boss("lord_of_the_coast", "Lord of the Coast", CalmBelt.Sea.BLUE, 3, 320, 15, 6, 1.15,
				600, 8_000_000L, "coast_lord_fang", List.of(Move.TIDAL_WAVE, Move.ROAR, Move.DIVE_LUNGE), true,
				"The Lord of the Coast rises! The same Sea King that took a Yonko's arm...",
				"The Lord of the Coast thrashes in a rage!"));
		add(new Boss("florian_phantom", "Florian Phantom", CalmBelt.Sea.GRAND_LINE, 4, 560, 20, 8, 1.3,
				1500, 25_000_000L, "phantom_scale", List.of(Move.FOG, Move.DIVE_LUNGE, Move.WHIRLPOOL), false,
				"A pale shape glides out of the fog. The Florian Phantom has found you.",
				"The Phantom wails and the fog grows thick!"));
		add(new Boss("calm_belt_behemoth", "Calm Belt Behemoth", CalmBelt.Sea.CALM_BELT, 5, 820, 24, 10, 1.5,
				2500, 40_000_000L, "behemoth_horn", List.of(Move.TIDAL_WAVE, Move.BROOD, Move.ROAR, Move.DIVE_LUNGE), false,
				"The windless sea bulges upward. The Calm Belt Behemoth has come for its nest!",
				"The Behemoth roars and its brood answers!"));
		add(new Boss("ancient_sea_king", "Ancient Sea King", CalmBelt.Sea.NEW_WORLD, 6, 1000, 30, 18, 1.8,
				6000, 120_000_000L, "ancient_sea_king_fang",
				List.of(Move.TIDAL_WAVE, Move.WHIRLPOOL, Move.DIVE_LUNGE, Move.ROAR, Move.BROOD), true,
				"An Ancient Sea King surfaces, older than the World Government itself. It does not answer to you.",
				"The Ancient Sea King calls the deep to war!"));
		add(new Boss("mecha_shark", "Mecha-Shark", null, 7, 700, 26, 14, 1.2,
				3000, 60_000_000L, "mecha_shark_fin", List.of(Move.DIVE_LUNGE, Move.MISSILES, Move.TIDAL_WAVE), true,
				"A steel fin cuts through the waves. Vegapunk's Mecha-Shark guards the way to Egghead!",
				"The Mecha-Shark's eyes flash red. WARNING: COMBAT MODE."));
		add(new Boss("sea_beast_weapon", "Sea Beast Weapon", null, 8, 900, 28, 16, 1.5,
				4000, 80_000_000L, "beast_weapon_core", List.of(Move.LASER, Move.MISSILES, Move.BROOD, Move.LASER, Move.ROAR), false,
				"Steel plates and a cannon bolted to its head... one of Lilith's Sea Beast Weapons patrols Egghead's waters!",
				"The Sea Beast Weapon's cannon glows white-hot!"));
	}

	/** The four bosses of the seas (the lure calls them, and beating all four makes you a Sea King Slayer). */
	public static List<Boss> seaBosses() {
		return BOSSES.values().stream().filter(boss -> boss.sea() != null).toList();
	}

	private static void add(Boss boss) {
		BOSSES.put(boss.id(), boss);
	}

	public static final String BOSS_TAG = "onepiece_sea_boss";
	private static final String MINION_TAG = "onepiece_sea_boss_minion";
	private static final String ENRAGED_TAG = "onepiece_sea_boss_enraged";

	/** Boss ids this player has helped beat. Kept forever. */
	public static final AttachmentType<List<String>> DEFEATED = AttachmentRegistry.create(
			OnePieceMod.id("sea_bosses_defeated"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath());

	// ---------- Items ----------

	public static final Item SEA_LORD_LURE = register("sea_lord_lure", LureItem::new, new Item.Properties().stacksTo(4).rarity(Rarity.RARE));
	public static final Item COAST_LORD_FANG = trophy("coast_lord_fang", Rarity.RARE);
	public static final Item PHANTOM_SCALE = trophy("phantom_scale", Rarity.RARE);
	public static final Item BEHEMOTH_HORN = trophy("behemoth_horn", Rarity.EPIC);
	public static final Item ANCIENT_SEA_KING_FANG = trophy("ancient_sea_king_fang", Rarity.EPIC);
	public static final Item MECHA_SHARK_FIN = trophy("mecha_shark_fin", Rarity.EPIC);
	public static final Item BEAST_WEAPON_CORE = trophy("beast_weapon_core", Rarity.EPIC);

	private static Item trophy(String name, Rarity rarity) {
		return register(name, Item::new, new Item.Properties().stacksTo(16).rarity(rarity));
	}

	private static Item register(String name, java.util.function.Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
	}

	private static Item trophyItem(Boss boss) {
		return switch (boss.trophy()) {
			case "coast_lord_fang" -> COAST_LORD_FANG;
			case "phantom_scale" -> PHANTOM_SCALE;
			case "behemoth_horn" -> BEHEMOTH_HORN;
			case "mecha_shark_fin" -> MECHA_SHARK_FIN;
			case "beast_weapon_core" -> BEAST_WEAPON_CORE;
			default -> ANCIENT_SEA_KING_FANG;
		};
	}

	// ---------- Running moves ----------

	/** A move that is winding up (a warning on the water) or still going (a whirlpool, a grab). */
	private static final class Pending {
		final Move move;
		final Vec3 at;
		int ticks;
		UUID grabbed;
		List<Vec3> spots;

		Pending(Move move, Vec3 at, int ticks) {
			this.move = move;
			this.at = at;
			this.ticks = ticks;
		}
	}

	private static final Map<UUID, Pending> PENDING = new HashMap<>();
	/** A Lord of the Coast's grab: boss -> grabbed player and ticks left. */
	private static final Map<UUID, Pending> GRABS = new HashMap<>();
	/** Boss -> game time it may grab again, so a grabbed player gets a moment to breathe. */
	private static final Map<UUID, Long> NEXT_GRAB = new HashMap<>();

	public static void initialize() {
		CreativeModeTabEvents.modifyOutputEvent(SeaItems.TAB_KEY).register(output -> {
			output.accept(SEA_LORD_LURE);
			output.accept(COAST_LORD_FANG);
			output.accept(PHANTOM_SCALE);
			output.accept(BEHEMOTH_HORN);
			output.accept(ANCIENT_SEA_KING_FANG);
			output.accept(MECHA_SHARK_FIN);
			output.accept(BEAST_WEAPON_CORE);
		});
		EggheadWaters.initialize();
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("seaboss")
						.executes(context -> {
							record(context.getSource().getPlayerOrException());
							return 1;
						})
						.then(Commands.literal("summon")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("id", StringArgumentType.word())
										.suggests((context, builder) -> {
											BOSSES.keySet().forEach(builder::suggest);
											return builder.buildFuture();
										})
										.executes(context -> {
											ServerPlayer player = context.getSource().getPlayerOrException();
											Boss boss = BOSSES.get(StringArgumentType.getString(context, "id"));
											if (boss == null) {
												context.getSource().sendFailure(Component.literal("Unknown boss. Bosses: " + String.join(", ", BOSSES.keySet())));
												return 0;
											}
											Vec3 ahead = Vec3.directionFromRotation(0.0f, player.getYRot()).scale(14.0);
											Vec3 at = new Vec3(player.getX() + ahead.x, player.level().getSeaLevel() - 5, player.getZ() + ahead.z);
											return spawn((ServerLevel) player.level(), boss, at, player) != null ? 1 : 0;
										})))));
	}

	public static Boss get(String id) {
		return id == null || id.isEmpty() ? null : BOSSES.get(id);
	}

	/** The boss that lives in this sea. */
	public static Boss forSea(CalmBelt.Sea sea) {
		for (Boss boss : BOSSES.values()) {
			if (boss.sea() == sea) {
				return boss;
			}
		}
		return null;
	}

	/** Makes the boss in the water at this spot. Tells nearby players it has come. */
	public static SeaKingEntity spawn(ServerLevel level, Boss boss, Vec3 at, ServerPlayer near) {
		SeaKingEntity king = SeaEntities.SEA_KING.create(level, EntitySpawnReason.EVENT);
		if (king == null) {
			return null;
		}
		king.snapTo(at.x, at.y, at.z, near == null ? level.getRandom().nextFloat() * 360 : near.getYRot() + 180, 0);
		makeBoss(king, boss);
		level.addFreshEntity(king);
		level.sendParticles(ParticleTypes.SPLASH, at.x, level.getSeaLevel() + 1, at.z, 120, 3, 3, 3, 0.4);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.ELDER_GUARDIAN_CURSE, SoundSource.HOSTILE, 4.0f, 0.5f);
		for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, king.getBoundingBox().inflate(64))) {
			player.sendSystemMessage(Component.literal(boss.intro()).withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
		}
		return king;
	}

	/** Turns a fresh Sea King into a boss. */
	public static void makeBoss(SeaKingEntity king, Boss boss) {
		king.setSeaBoss(boss.id(), boss.variant());
		// Each boss has its own look: the Lord of the Coast is frilled like in the show, the Phantom whiskered,
		// the Behemoth horned (it drops a horn), the Ancient one armoured.
		king.setStyle(switch (boss.id()) {
			case "lord_of_the_coast" -> 3;
			case "florian_phantom" -> 2;
			case "calm_belt_behemoth" -> 1;
			case "ancient_sea_king" -> 5;
			case "mecha_shark" -> 6;
			case "sea_beast_weapon" -> 7;
			default -> king.getStyle();
		});
		king.addTag(BOSS_TAG);
		king.addTag("onepiece_tier_checked"); // Already as strong as it should be: the New World tier leaves it alone.
		king.setCustomName(Component.literal(boss.name()));
		king.getAttribute(Attributes.MAX_HEALTH).setBaseValue(boss.health() * com.onepiecemod.config.ModConfig.bossHealth());
		king.setHealth(king.getMaxHealth());
		king.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(boss.damage() * com.onepiecemod.config.ModConfig.bossDamage());
		king.getAttribute(Attributes.ARMOR).setBaseValue(boss.armor());
		if (king.getAttribute(Attributes.SCALE) != null) {
			king.getAttribute(Attributes.SCALE).setBaseValue(boss.scale());
		}
		king.getAttribute(Attributes.FOLLOW_RANGE).setBaseValue(64);
		king.setPersistenceRequired();
	}

	/** Called every tick from SeaKingEntity.customServerAiStep for bosses. */
	static void tick(SeaKingEntity king, ServerLevel level, Boss boss) {
		tickGrab(king, level);
		Pending pending = PENDING.get(king.getUUID());
		if (pending != null) {
			tickPending(king, level, boss, pending);
			return;
		}
		boolean enraged = king.getHealth() < king.getMaxHealth() * 0.5f;
		if (enraged && !king.entityTags().contains(ENRAGED_TAG)) {
			king.addTag(ENRAGED_TAG);
			shout(level, king, boss.phaseLine());
			roar(king, level);
		}
		if (!(king.getTarget() instanceof Player target) || !target.isAlive() || target.distanceTo(king) > 40) {
			return;
		}
		int every = enraged ? 90 : 150;
		if (king.tickCount % every != 0) {
			return;
		}
		Move move = boss.moves().get(king.getRandom().nextInt(boss.moves().size()));
		start(king, level, move, target);
	}

	private static void start(SeaKingEntity king, ServerLevel level, Move move, Player target) {
		switch (move) {
			case ROAR -> roar(king, level);
			case BROOD -> brood(king, level);
			case FOG -> {
				for (ServerPlayer player : players(king, 30)) {
					player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 120, 0));
					player.sendOverlayMessage(Component.literal("The fog swallows everything...").withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
				}
				level.sendParticles(ParticleTypes.CLOUD, king.getX(), king.getY() + 2, king.getZ(), 200, 10, 2, 10, 0.02);
				level.playSound(null, king.blockPosition(), SoundEvents.PHANTOM_AMBIENT, SoundSource.HOSTILE, 4.0f, 0.4f);
				king.setInvisible(true);
				PENDING.put(king.getUUID(), new Pending(Move.FOG, target.position(), 70));
			}
			case TIDAL_WAVE -> {
				PENDING.put(king.getUUID(), new Pending(Move.TIDAL_WAVE, king.position(), 30));
				level.playSound(null, king.blockPosition(), SoundEvents.ELDER_GUARDIAN_AMBIENT, SoundSource.HOSTILE, 4.0f, 0.5f);
				warn(king, "The sea is pulling back... a wave is coming!");
			}
			case WHIRLPOOL -> {
				PENDING.put(king.getUUID(), new Pending(Move.WHIRLPOOL, king.position(), 100));
				warn(king, "The water starts to spin. Get out of the whirlpool!");
			}
			case LASER -> {
				// Aims where you are now; a line of sparks shows where the beam will go. Step off the line.
				Vec3 from = mouth(king);
				Vec3 dir = target.getEyePosition().subtract(from).normalize();
				Pending laser = new Pending(Move.LASER, from.add(dir.scale(40)), 30);
				PENDING.put(king.getUUID(), laser);
				level.playSound(null, king.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 4.0f, 0.5f);
				warn(king, "Its cannon is charging a laser. Get off the red line!");
			}
			case MISSILES -> {
				PENDING.put(king.getUUID(), new Pending(Move.MISSILES, target.position(), 40));
				level.playSound(null, king.blockPosition(), SoundEvents.DISPENSER_LAUNCH, SoundSource.HOSTILE, 4.0f, 0.5f);
				warn(king, "Missiles! Watch for the red circles!");
			}
			case DIVE_LUNGE -> {
				BlockPos spot = BlockPos.containing(target.position());
				if (!level.getFluidState(spot).is(FluidTags.WATER) && !level.getFluidState(spot.below()).is(FluidTags.WATER)
						&& !level.getFluidState(spot.below(2)).is(FluidTags.WATER)) {
					roar(king, level); // Over land it can't come up from under you.
					return;
				}
				PENDING.put(king.getUUID(), new Pending(Move.DIVE_LUNGE, target.position(), 30));
				king.setDeltaMovement(0, -0.6, 0);
				warn(king, "It dove under. Move!");
			}
		}
	}

	private static void tickPending(SeaKingEntity king, ServerLevel level, Boss boss, Pending pending) {
		pending.ticks--;
		switch (pending.move) {
			case TIDAL_WAVE -> {
				if (pending.ticks % 5 == 0) {
					BossStrikes.ring(level, new Vec3(king.getX(), level.getSeaLevel(), king.getZ()), 12, pending.ticks <= 10 ? 0xFFFF55 : 0xFF3030);
				}
				if (pending.ticks <= 0) {
					wave(king, level);
				}
			}
			case WHIRLPOOL -> {
				double y = level.getSeaLevel() + 0.5;
				for (int i = 0; i < 6; i++) {
					double angle = (king.tickCount * 0.3) + i * Math.PI / 3;
					double radius = 2 + (pending.ticks % 20) * 0.6;
					level.sendParticles(ParticleTypes.SPLASH, king.getX() + Math.cos(angle) * radius, y, king.getZ() + Math.sin(angle) * radius, 3, 0.2, 0.1, 0.2, 0.1);
				}
				for (ServerPlayer player : players(king, 16)) {
					Vec3 pull = king.position().subtract(player.position()).multiply(1, 0, 1).normalize().scale(0.09);
					player.setDeltaMovement(player.getDeltaMovement().add(pull.x, -0.02, pull.z));
					Motion.sync(player);
					if (pending.ticks % 20 == 0) {
						player.hurtServer(level, king.damageSources().mobAttack(king), 3.0f);
					}
				}
			}
			case DIVE_LUNGE -> {
				if (pending.ticks % 5 == 0) {
					BossStrikes.ring(level, new Vec3(pending.at.x, level.getSeaLevel(), pending.at.z), 3.5, pending.ticks <= 10 ? 0xFFFF55 : 0xFF3030);
					level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, pending.at.x, level.getSeaLevel() - 1, pending.at.z, 20, 1.5, 0.5, 1.5, 0.1);
				}
				if (pending.ticks <= 0) {
					king.snapTo(pending.at.x, level.getSeaLevel() - 4, pending.at.z, king.getYRot(), -60);
					king.setDeltaMovement(0, 1.6, 0);
					level.sendParticles(ParticleTypes.SPLASH, pending.at.x, level.getSeaLevel() + 1, pending.at.z, 150, 2, 2, 2, 0.5);
					level.playSound(null, pending.at.x, pending.at.y, pending.at.z, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 4.0f, 0.5f);
					for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, new net.minecraft.world.phys.AABB(pending.at, pending.at).inflate(3.5, 4, 3.5))) {
						if (hits(king, player)) {
							player.hurtServer(level, king.damageSources().mobAttack(king), (float) king.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.3f);
							knockOff(player);
							player.setDeltaMovement(player.getDeltaMovement().add(0, 1.2, 0));
							Motion.sync(player);
						}
					}
				}
			}
			case FOG -> {
				if (pending.ticks % 10 == 0) {
					level.sendParticles(ParticleTypes.CLOUD, king.getX(), level.getSeaLevel() + 1, king.getZ(), 40, 6, 1, 6, 0.01);
				}
				if (pending.ticks <= 0) {
					king.setInvisible(false);
					if (king.getTarget() instanceof Player target) {
						Vec3 behind = target.position().subtract(Vec3.directionFromRotation(0, target.getYRot()).scale(8));
						if (SeaKingSpawner.isDeepWater(level, BlockPos.containing(behind))) {
							king.snapTo(behind.x, level.getSeaLevel() - 3, behind.z, target.getYRot(), 0);
						}
					}
					level.playSound(null, king.blockPosition(), SoundEvents.PHANTOM_SWOOP, SoundSource.HOSTILE, 4.0f, 0.5f);
				}
			}
			case LASER -> {
				Vec3 from = mouth(king);
				if (pending.ticks > 0 && pending.ticks % 3 == 0) {
					line(level, from, pending.at, pending.ticks <= 10 ? 0xFFFF55 : 0xFF3030, 0.8f);
				}
				if (pending.ticks <= 0) {
					laser(king, level, from, pending.at);
				}
			}
			case MISSILES -> {
				if (pending.ticks == 39) {
					// Five spots around where you stood: one right on it.
					RandomSource random = king.getRandom();
					pending.spots = new ArrayList<>();
					pending.spots.add(pending.at);
					for (int i = 0; i < 4; i++) {
						pending.spots.add(pending.at.add(random.nextGaussian() * 5, 0, random.nextGaussian() * 5));
					}
				}
				if (pending.spots != null && pending.ticks % 5 == 0) {
					for (Vec3 spot : pending.spots) {
						BossStrikes.ring(level, spot, 3.0, pending.ticks <= 15 ? 0xFFFF55 : 0xFF3030);
					}
				}
				if (pending.ticks <= 0 && pending.spots != null) {
					for (Vec3 spot : pending.spots) {
						level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, spot.x, spot.y + 0.5, spot.z, 1, 0, 0, 0, 0);
						level.sendParticles(ParticleTypes.SPLASH, spot.x, spot.y + 0.5, spot.z, 40, 1.5, 0.5, 1.5, 0.4);
						level.playSound(null, spot.x, spot.y, spot.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 2.0f, 0.9f);
						for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, new net.minecraft.world.phys.AABB(spot, spot).inflate(3, 4, 3))) {
							if (hits(king, player)) {
								player.hurtServer(level, king.damageSources().explosion(king, king), (float) king.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.55f);
								knockOff(player);
								Vec3 away = player.position().subtract(spot).multiply(1, 0, 1).normalize().scale(0.8);
								player.setDeltaMovement(away.x, 0.6, away.z);
								Motion.sync(player);
							}
						}
					}
				}
			}
			default -> pending.ticks = 0;
		}
		if (pending.ticks <= 0) {
			PENDING.remove(king.getUUID());
		}
	}

	/** The wave lands: everyone close is hurt, thrown back, and knocked off their boat. */
	private static void wave(SeaKingEntity king, ServerLevel level) {
		level.sendParticles(ParticleTypes.SPLASH, king.getX(), level.getSeaLevel() + 1, king.getZ(), 300, 8, 1.5, 8, 0.6);
		level.playSound(null, king.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 3.0f, 0.6f);
		for (ServerPlayer player : players(king, 12)) {
			player.hurtServer(level, king.damageSources().mobAttack(king), (float) king.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.6f);
			knockOff(player);
			Vec3 away = player.position().subtract(king.position()).multiply(1, 0, 1).normalize().scale(1.6);
			player.setDeltaMovement(away.x, 0.7, away.z);
			Motion.sync(player);
		}
	}

	/** Where a beam leaves its head (the cannon / the mouth). */
	private static Vec3 mouth(SeaKingEntity king) {
		return king.position().add(0, king.getBbHeight() * 0.6, 0).add(Vec3.directionFromRotation(0, king.getYHeadRot()).scale(king.getBbWidth() * 0.6));
	}

	private static void line(ServerLevel level, Vec3 from, Vec3 to, int color, float size) {
		Vec3 step = to.subtract(from);
		int count = (int) Math.max(1, step.length());
		net.minecraft.core.particles.DustParticleOptions dust = new net.minecraft.core.particles.DustParticleOptions(color, size * 2);
		for (int i = 0; i <= count; i++) {
			Vec3 at = from.add(step.scale(i / (double) count));
			level.sendParticles(dust, at.x, at.y, at.z, 1, 0.05, 0.05, 0.05, 0);
		}
	}

	/** The laser fires down the line it showed: anyone within 2 blocks of it is burned and knocked back. */
	private static void laser(SeaKingEntity king, ServerLevel level, Vec3 from, Vec3 to) {
		level.playSound(null, from.x, from.y, from.z, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.HOSTILE, 4.0f, 1.2f);
		Vec3 step = to.subtract(from);
		int count = (int) step.length();
		for (int i = 0; i <= count; i += 2) {
			Vec3 at = from.add(step.scale(i / (double) count));
			level.sendParticles(ParticleTypes.END_ROD, at.x, at.y, at.z, 3, 0.2, 0.2, 0.2, 0.01);
		}
		level.sendParticles(ParticleTypes.EXPLOSION, to.x, to.y, to.z, 3, 1, 1, 1, 0);
		for (ServerPlayer player : players(king, 44)) {
			Vec3 p = player.position().add(0, player.getBbHeight() / 2, 0);
			double t = Math.max(0, Math.min(1, p.subtract(from).dot(step) / step.lengthSqr()));
			if (p.distanceTo(from.add(step.scale(t))) < 2.0) {
				player.hurtServer(level, king.damageSources().mobAttack(king), (float) king.getAttributeValue(Attributes.ATTACK_DAMAGE) * 1.1f);
				player.igniteForSeconds(4);
				knockOff(player);
				Vec3 push = step.normalize().scale(1.2);
				player.setDeltaMovement(push.x, 0.5, push.z);
				Motion.sync(player);
			}
		}
	}

	private static void roar(SeaKingEntity king, ServerLevel level) {
		level.playSound(null, king.blockPosition(), SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 5.0f, 0.4f);
		level.sendParticles(ParticleTypes.SONIC_BOOM, king.getX(), king.getY() + king.getBbHeight(), king.getZ(), 1, 0, 0, 0, 0);
		for (ServerPlayer player : players(king, 20)) {
			player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 1));
			player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 0));
		}
	}

	/** Calls up to two ordinary Sea Kings, never more than four at once. */
	private static void brood(SeaKingEntity king, ServerLevel level) {
		int alive = level.getEntitiesOfClass(SeaKingEntity.class, king.getBoundingBox().inflate(64), k -> k.entityTags().contains(MINION_TAG)).size();
		RandomSource random = king.getRandom();
		int made = 0;
		for (int i = 0; i < 6 && alive + made < 4 && made < 2; i++) {
			double angle = random.nextDouble() * Math.PI * 2;
			double reach = king.getBbWidth() * 0.5 + 10; // clear of the boss's own huge body
			BlockPos spot = BlockPos.containing(king.getX() + Math.cos(angle) * reach, level.getSeaLevel() - 5, king.getZ() + Math.sin(angle) * reach);
			if (!SeaKingSpawner.isDeepWater(level, spot)) {
				continue;
			}
			SeaKingEntity minion = SeaEntities.SEA_KING.create(level, EntitySpawnReason.EVENT);
			if (minion != null) {
				minion.snapTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, random.nextFloat() * 360, 0);
				minion.addTag(MINION_TAG);
				if (minion.getAttribute(Attributes.SCALE) != null) {
					minion.getAttribute(Attributes.SCALE).setBaseValue(0.6); // its brood: young ones, still bigger than a boat
				}
				if ("sea_beast_weapon".equals(king.getSeaBoss())) {
					// Lilith's fleet: cyborg Sea Kings like the big one.
					minion.setLook(8, 7);
					minion.setCustomName(Component.literal("Cyborg Sea King"));
				}
				minion.setTarget(king.getTarget());
				level.addFreshEntity(minion);
				made++;
			}
		}
		if (made > 0) {
			warn(king, "sea_beast_weapon".equals(king.getSeaBoss()) ? "More of Lilith's cyborg Sea Kings close in!" : "More Sea Kings rise from the deep!");
		}
	}

	// ---------- The Lord of the Coast's grab ----------

	/** Called from SeaKingEntity.doHurtTarget after a bite lands. */
	static void onBite(SeaKingEntity king, Boss boss, Entity target) {
		if (!boss.snatches() || !(target instanceof ServerPlayer player) || GRABS.containsKey(king.getUUID())
				|| king.level().getGameTime() < NEXT_GRAB.getOrDefault(king.getUUID(), 0L) || king.getRandom().nextFloat() > 0.35f) {
			return;
		}
		Pending grab = new Pending(Move.DIVE_LUNGE, king.position(), 50);
		grab.grabbed = player.getUUID();
		GRABS.put(king.getUUID(), grab);
		knockOff(player);
		player.sendOverlayMessage(Component.literal(boss.name() + " has you in its jaws! Hit it to break free!").withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
	}

	private static void tickGrab(SeaKingEntity king, ServerLevel level) {
		Pending grab = GRABS.get(king.getUUID());
		if (grab == null) {
			return;
		}
		grab.ticks--;
		if (level.getEntity(grab.grabbed) instanceof ServerPlayer player && player.isAlive() && grab.ticks > 0) {
			Vec3 mouth = king.position().add(Vec3.directionFromRotation(0, king.getYRot()).scale(king.getBbWidth()));
			Vec3 pull = mouth.subtract(player.position()).scale(0.25);
			player.setDeltaMovement(pull.x, Math.min(pull.y, -0.15), pull.z);
			Motion.sync(player);
			if (grab.ticks % 20 == 0) {
				player.hurtServer(level, king.damageSources().mobAttack(king), 3.0f);
			}
			return;
		}
		GRABS.remove(king.getUUID());
		NEXT_GRAB.put(king.getUUID(), level.getGameTime() + 200);
	}

	/** Hitting a boss that holds you makes it let go. */
	static void onHurt(SeaKingEntity king, DamageSource source) {
		Pending grab = GRABS.get(king.getUUID());
		if (grab != null && source.getEntity() != null && source.getEntity().getUUID().equals(grab.grabbed)) {
			GRABS.remove(king.getUUID());
			NEXT_GRAB.put(king.getUUID(), king.level().getGameTime() + 200);
			if (source.getEntity() instanceof ServerPlayer player) {
				player.sendOverlayMessage(Component.literal("You broke free!").withStyle(ChatFormatting.GREEN));
			}
		}
	}

	// ---------- Defeat ----------

	static void onDeath(SeaKingEntity king, ServerLevel level, Boss boss, DamageSource source) {
		PENDING.remove(king.getUUID());
		GRABS.remove(king.getUUID());
		NEXT_GRAB.remove(king.getUUID());
		for (SeaKingEntity minion : level.getEntitiesOfClass(SeaKingEntity.class, king.getBoundingBox().inflate(96), k -> k.entityTags().contains(MINION_TAG))) {
			minion.discard();
		}
		// Everyone who fought nearby gets credit, not only whoever landed the last hit.
		List<ServerPlayer> credit = new ArrayList<>(players(king, 48));
		if (source.getEntity() instanceof ServerPlayer killer && !credit.contains(killer)) {
			credit.add(killer);
		}
		if (credit.isEmpty()) {
			return;
		}
		RandomSource random = king.getRandom();
		drop(king, level, new ItemStack(Resources.SEA_KING_SCALE, 6 + random.nextInt(6) + boss.variant() * 2));
		drop(king, level, new ItemStack(Resources.SEA_PEARL, 3 + random.nextInt(4)));
		drop(king, level, new ItemStack(SeaItems.SEA_KING_MEAT, 8 + random.nextInt(8)));
		if (random.nextFloat() < 0.5f) {
			drop(king, level, new ItemStack(Items.HEART_OF_THE_SEA));
		}
		if (boss.sea() == null) {
			// Egghead's guards are half machine: they drop Vegapunk tech too.
			drop(king, level, new ItemStack(com.onepiecemod.vegapunk.VegapunkItems.VEGAPUNK_CHIP, 1 + random.nextInt(2)));
			drop(king, level, new ItemStack(com.onepiecemod.vegapunk.VegapunkItems.LASER_CORE, 1));
		}
		float fruitChance = boss.sea() == CalmBelt.Sea.NEW_WORLD || boss.sea() == null ? 0.25f : 0.06f;
		if (random.nextFloat() < fruitChance && !ModItems.DEVIL_FRUITS.isEmpty()) {
			List<Item> fruits = List.copyOf(ModItems.DEVIL_FRUITS.values());
			drop(king, level, new ItemStack(fruits.get(random.nextInt(fruits.size()))));
		}
		for (ServerPlayer player : credit) {
			EggheadWaters.onBeaten(player, boss);
			List<String> beaten = player.getAttachedOrElse(DEFEATED, List.of());
			boolean first = !beaten.contains(boss.id());
			int berries = first ? boss.berries() : boss.berries() * 2 / 5;
			give(player, new ItemStack(CharacterFeature.BERRY, berries));
			if (first) {
				List<String> updated = new ArrayList<>(beaten);
				updated.add(boss.id());
				player.setAttached(DEFEATED, updated);
				give(player, new ItemStack(trophyItem(boss)));
				com.onepiecemod.bounty.Bounty.raise(player, boss.bounty(), "Defeated the " + boss.name(), false);
				player.sendSystemMessage(Component.literal("You defeated the " + boss.name() + "! (" + updated.size() + "/" + BOSSES.size()
						+ " sea bosses) The tale will be told in every port.").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
				com.onepiecemod.advancement.AdvancementFeature.grant(player, "wonders/" + boss.id());
				if (boss.sea() != null && seaBosses().stream().allMatch(sea -> updated.contains(sea.id()))) {
					com.onepiecemod.advancement.AdvancementFeature.grant(player, "wonders/sea_king_slayer");
					player.sendSystemMessage(Component.literal("Every sea's monster has fallen to you. Even Sea Kings will steer clear of your ship.")
							.withStyle(ChatFormatting.LIGHT_PURPLE));
				}
			} else {
				player.sendSystemMessage(Component.literal("You beat the " + boss.name() + " again. " + berries + " berries.").withStyle(ChatFormatting.GOLD));
			}
		}
	}

	private static void record(ServerPlayer player) {
		List<String> beaten = player.getAttachedOrElse(DEFEATED, List.of());
		player.sendSystemMessage(Component.literal("Sea King bosses beaten: " + beaten.size() + "/" + BOSSES.size()).withStyle(ChatFormatting.GOLD));
		for (Boss boss : BOSSES.values()) {
			boolean done = beaten.contains(boss.id());
			player.sendSystemMessage(Component.literal((done ? " [x] " : " [ ] ") + boss.name() + " - " + (boss.sea() == null ? "Egghead's waters" : boss.sea().title()))
					.withStyle(done ? ChatFormatting.GREEN : ChatFormatting.GRAY));
		}
		player.sendSystemMessage(Component.literal("The Mecha-Shark and Lilith's Sea Beast Weapon guard the sea around Egghead.").withStyle(ChatFormatting.DARK_AQUA));
		player.sendSystemMessage(Component.literal("Throw a Sea Lord Lure over deep water to call the boss of the sea you're in.").withStyle(ChatFormatting.DARK_AQUA));
	}

	// ---------- Helpers ----------

	private static List<ServerPlayer> players(SeaKingEntity king, double radius) {
		return king.level() instanceof ServerLevel level
				? level.getEntitiesOfClass(ServerPlayer.class, king.getBoundingBox().inflate(radius), player -> hits(king, player))
				: List.of();
	}

	private static boolean hits(SeaKingEntity king, ServerPlayer player) {
		return player.isAlive() && !player.isSpectator() && !player.isCreative() && king.canAttack(player);
	}

	private static void knockOff(ServerPlayer player) {
		if (player.isPassenger() && !(player.getVehicle() instanceof com.onepiecemod.pet.Pet)) {
			player.stopRiding();
		}
	}

	private static void warn(SeaKingEntity king, String text) {
		for (ServerPlayer player : players(king, 40)) {
			player.sendOverlayMessage(Component.literal(text).withStyle(ChatFormatting.YELLOW));
		}
	}

	private static void shout(ServerLevel level, SeaKingEntity king, String text) {
		for (ServerPlayer player : level.getEntitiesOfClass(ServerPlayer.class, king.getBoundingBox().inflate(64))) {
			player.sendSystemMessage(Component.literal(text).withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
		}
	}

	private static void drop(SeaKingEntity king, ServerLevel level, ItemStack stack) {
		king.spawnAtLocation(level, stack);
	}

	private static void give(ServerPlayer player, ItemStack stack) {
		if (!player.getInventory().add(stack)) {
			player.drop(stack, false, Prediction.SERVER_ONLY);
		}
	}

	/** The Sea Lord Lure: thrown over deep water, it calls the boss of the sea you're in. */
	public static class LureItem extends Item {
		public LureItem(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (!(level instanceof ServerLevel serverLevel) || !(player instanceof ServerPlayer serverPlayer)) {
				return InteractionResult.SUCCESS;
			}
			CalmBelt.Sea sea = CalmBelt.seaAt(level, player.blockPosition());
			Boss boss = sea == null ? null : forSea(sea);
			if (boss == null) {
				player.sendSystemMessage(Component.literal("Nothing answers the lure here. Use it out at sea.").withStyle(ChatFormatting.GRAY));
				return InteractionResult.FAIL;
			}
			if (!serverLevel.getEntitiesOfClass(SeaKingEntity.class, player.getBoundingBox().inflate(160), SeaKingEntity::isSeaBoss).isEmpty()) {
				player.sendSystemMessage(Component.literal("A sea boss is already hunting these waters.").withStyle(ChatFormatting.RED));
				return InteractionResult.FAIL;
			}
			Vec3 ahead = Vec3.directionFromRotation(0.0f, player.getYRot()).scale(16.0);
			BlockPos spot = BlockPos.containing(player.getX() + ahead.x, level.getSeaLevel() - 5, player.getZ() + ahead.z);
			if (!SeaKingSpawner.isDeepWater(serverLevel, spot)) {
				player.sendSystemMessage(Component.literal("Throw the lure over deep water (at least 8 blocks deep).").withStyle(ChatFormatting.GRAY));
				return InteractionResult.FAIL;
			}
			player.getCooldowns().addCooldown(player.getItemInHand(hand), 200);
			if (spawn(serverLevel, boss, Vec3.atBottomCenterOf(spot), serverPlayer) != null && !player.isCreative()) {
				player.getItemInHand(hand).shrink(1);
			}
			return InteractionResult.SUCCESS;
		}
	}
}
