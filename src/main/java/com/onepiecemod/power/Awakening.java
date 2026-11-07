package com.onepiecemod.power;

import com.onepiecemod.util.Motion;
import com.onepiecemod.sound.ModSounds;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.BiConsumer;
import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.story.StoryGates;

/**
 * Devil Fruit awakening. It is meant to be very hard to get:
 *
 * 1. Reach 1,000 mastery. You get 1 mastery each time one of your fruit's moves hits an enemy,
 *    and you lose a tenth of it every time you die.
 * 2. Beat 5 different story bosses (from their Wanted Posters).
 * 3. Then, the next time an enemy would kill you, your fruit awakens instead, like Luffy against Kaido.
 *
 * Mastery also makes your moves hit harder as it grows (see FruitAbilities.power).
 *
 * Once awakened, press Y to enter your awakened form for a short time, and you get a passive bonus:
 * Paramecia moves recharge 25% faster, Logia dodge 75% of attacks, Zoan users always regenerate.
 */
public class Awakening {
	public static final int MASTERY_NEEDED = 1000; // Default; the settings file can change it, so use masteryNeeded().

	public static int masteryNeeded() {
		return com.onepiecemod.config.ModConfig.awakeningMastery();
	}
	public static final int BOSSES_NEEDED = 5;
	private static final int AWAKENED_COOLDOWN_SECONDS = 180;

	/** One awakened form: an aura that hits everything nearby every second, plus effects on you. */
	private record Form(String name, int seconds, double radius, float damage, ParticleOptions particle,
			BiConsumer<ServerPlayer, LivingEntity> onTarget, Consumer<ServerPlayer> everySecond, List<MobEffectInstance> selfEffects) {
		/** Most forms only need the target. */
		Form(String name, int seconds, double radius, float damage, ParticleOptions particle,
				Consumer<LivingEntity> onTarget, Consumer<ServerPlayer> everySecond, List<MobEffectInstance> selfEffects) {
			this(name, seconds, radius, damage, particle, (player, target) -> onTarget.accept(target), everySecond, selfEffects);
		}
	}

	private record Active(Form form, long endTick) {
	}

	private static final Consumer<LivingEntity> NOTHING = target -> { };
	private static final Consumer<ServerPlayer> NOTHING_SELF = player -> { };

	/** Gear 5's feral second stage (see WildNika): a short-range aura of rubbery bites that keep you alive. */
	private static final Form WILD_NIKA = new Form(WildNika.NAME, WildNika.SECONDS, 4.5, 5, ParticleTypes.CLOUD,
			(player, target) -> { launch(target, 0.5); player.heal(1); }, WildNika::everySecond, List.of());

	private static final Map<UUID, Active> ACTIVE = new HashMap<>();
	private static final Map<UUID, Long> READY_AT = new HashMap<>();
	/** Rumble Ball awakenings: player -> game time the borrowed awakening ends. */
	private static final Map<UUID, Long> TEMPORARY = new HashMap<>();
	/** Fruit mastery needed before a Rumble Ball can force an awakening. */
	public static final int RUMBLE_MASTERY = 250;

	public static int getMastery(Player player) {
		Integer mastery = player.getAttached(ModAttachments.FRUIT_MASTERY);
		return mastery == null ? 0 : mastery;
	}

	public static boolean isAwakened(Player player) {
		return Boolean.TRUE.equals(player.getAttached(ModAttachments.AWAKENED));
	}

	/** Awakened for good, or for a little while thanks to a Rumble Ball. Use this for the awakened bonuses. */
	public static boolean isAwakenedNow(Player player) {
		if (isAwakened(player)) {
			return true;
		}
		Long end = TEMPORARY.get(player.getUUID());
		return end != null && player.level().getGameTime() < end;
	}

	/**
	 * Rumble Ball: forces the fruit to awaken for a while, even before the real awakening.
	 * The awakened form starts right away (ignoring the Y cooldown) and the awakened bonuses last the
	 * whole time. Returns false (and says why) if the fruit is not trained enough to answer.
	 */
	public static boolean rumbleAwaken(ServerPlayer player, DevilFruit fruit, int seconds) {
		if (!isAwakened(player) && getMastery(player) < RUMBLE_MASTERY) {
			player.sendSystemMessage(Component.literal("Your fruit isn't trained enough to answer the Rumble Ball ("
					+ getMastery(player) + "/" + RUMBLE_MASTERY + " mastery). You just get the strength boost.").withStyle(ChatFormatting.GRAY));
			return false;
		}
		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		if (!isAwakened(player)) {
			TEMPORARY.merge(player.getUUID(), now + seconds * 20L, Math::max);
		}
		startForm(player, fruit, level, now, Math.max(seconds, form(fruit).seconds()));
		player.sendSystemMessage(Component.literal("The Rumble Ball forces your fruit to awaken for " + seconds + " seconds!")
				.withStyle(ChatFormatting.LIGHT_PURPLE));
		com.onepiecemod.advancement.AdvancementFeature.grant(player, "powers/rumble_awakening");
		return true;
	}

	public static boolean isFormActive(Player player) {
		return ACTIVE.containsKey(player.getUUID());
	}

	public static int bossesBeaten(Player player) {
		List<String> bosses = player.getAttached(CharacterAttachments.BOSSES_DEFEATED);
		return bosses == null ? 0 : bosses.size();
	}

	private static boolean readyToAwaken(Player player) {
		return !isAwakened(player) && getMastery(player) >= masteryNeeded() && bossesBeaten(player) >= BOSSES_NEEDED
				&& StoryGates.awakeningAllowed(player); // The story opens awakening after Wano.
	}

	/** Called by FruitAbilities when one of your moves hits something. */
	static void addMastery(ServerPlayer player, DevilFruit fruit) {
		int before = getMastery(player);
		if (before >= masteryNeeded()) {
			return;
		}
		int after = before + 1;
		player.setAttached(ModAttachments.FRUIT_MASTERY, after);

		if (after % 100 == 0) {
			player.sendSystemMessage(Component.translatable("message.onepiece.mastery_up", after, masteryNeeded(),
					String.format(java.util.Locale.ROOT, "%.2f", FruitAbilities.power(player))).withStyle(ChatFormatting.AQUA));
		}
		if (after == masteryNeeded()) {
			player.sendSystemMessage(Component.translatable("message.onepiece.mastery_max", BOSSES_NEEDED).withStyle(ChatFormatting.LIGHT_PURPLE));
		}
	}

	/** Paramecia users who have awakened recharge their moves 25% faster. */
	static double cooldownMultiplier(ServerPlayer player, DevilFruit fruit) {
		return isAwakenedNow(player) && fruit.type() == DevilFruit.Type.PARAMECIA ? 0.75 : 1.0;
	}

	/** Awakened Logia users dodge 75% of attacks, and nothing touches you in your awakened form. */
	static float adjustDodgeChance(ServerPlayer player, DevilFruit fruit, float chance) {
		if (isFormActive(player)) {
			return 1.0f;
		}
		if (isAwakenedNow(player) && fruit.type() == DevilFruit.Type.LOGIA) {
			return Math.max(chance, 0.75f);
		}
		return chance;
	}

	/** The Awaken key (Y). Before awakening, it shows how far along you are. */
	static void useAwakening(ServerPlayer player, DevilFruit fruit) {
		Active running = ACTIVE.get(player.getUUID());
		if (running != null && isAwakenedNow(player) && WildNika.canShift(player, fruit, running.form().name())) {
			// Luffy goes feral: Y again during Gear 5 (also a Rumble Ball's) swaps it for Wild Nika (chapter 1198).
			ServerLevel level = (ServerLevel) player.level();
			ACTIVE.put(player.getUUID(), new Active(WILD_NIKA, level.getGameTime() + WildNika.SECONDS * 20L));
			WildNika.start(player, level);
			return;
		}
		if (!isAwakened(player)) {
			player.sendOverlayMessage(Component.translatable("message.onepiece.awakening_progress",
					Math.min(getMastery(player), masteryNeeded()), masteryNeeded(),
					Math.min(bossesBeaten(player), BOSSES_NEEDED), BOSSES_NEEDED).withStyle(ChatFormatting.LIGHT_PURPLE));
			return;
		}

		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		long readyAt = READY_AT.getOrDefault(player.getUUID(), 0L);
		if (now < readyAt) {
			player.sendOverlayMessage(Component.translatable("message.onepiece.power_cooldown", (readyAt - now + 19) / 20).withStyle(ChatFormatting.GRAY));
			return;
		}

		READY_AT.put(player.getUUID(), now + AWAKENED_COOLDOWN_SECONDS * 20L);
		startForm(player, fruit, level, now, form(fruit).seconds());
	}

	private static void startForm(ServerPlayer player, DevilFruit fruit, ServerLevel level, long now, int seconds) {
		Form form = form(fruit);
		ACTIVE.put(player.getUUID(), new Active(form, now + seconds * 20L));
		for (MobEffectInstance effect : form.selfEffects()) {
			player.addEffect(seconds == form.seconds() ? effect
					: new MobEffectInstance(effect.getEffect(), seconds * 20, effect.getAmplifier()));
		}

		FruitAbilities.particles(level, player, ParticleTypes.EXPLOSION_EMITTER, 1);
		com.onepiecemod.fx.MoveFx.transform(player, level, fruit);
		FruitAbilities.sound(level, player, com.onepiecemod.sound.FruitSounds.awakening(fruit));
		player.sendOverlayMessage(Component.literal(form.name() + "!").withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.BOLD));
	}

	public static void initialize() {
		// The final trial: at the brink of death, a ready fruit awakens instead of letting you die.
		ServerLivingEntityEvents.ALLOW_DEATH.register((entity, source, amount) -> {
			if (entity instanceof ServerPlayer player && source.getEntity() != null && DevilFruitPowers.hasAnyFruit(player) && readyToAwaken(player)) {
				awaken(player);
				return false; // false means "don't die".
			}
			return true;
		});

		// Dying costs some of your mastery (a tenth by default, set in the config; only before you awaken).
		ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> {
			ACTIVE.remove(oldPlayer.getUUID());
			TEMPORARY.remove(oldPlayer.getUUID());
			if (!alive && !isAwakened(newPlayer) && getMastery(newPlayer) > 0) {
				int mastery = getMastery(newPlayer);
				int lost = (int) (mastery * com.onepiecemod.config.ModConfig.deathMasteryLoss()); // 10% by default, none in Simple mode.
				if (lost > 0) {
					newPlayer.setAttached(ModAttachments.FRUIT_MASTERY, mastery - lost);
				}
			}
		});

		// Run each awakened form's aura once a second, and end forms whose time is up.
		ServerTickEvents.END_LEVEL_TICK.register(level -> {
			if (level.getGameTime() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : level.getPlayers(p -> true)) {
				// Awakened Zoan users always regenerate.
				DevilFruit fruit = DevilFruitPowers.getFruit(player);
				if (fruit != null && fruit.type() == DevilFruit.Type.ZOAN && isAwakenedNow(player)) {
					player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 60, 0, true, false, true));
				}

				Active active = ACTIVE.get(player.getUUID());
				if (active == null) {
					continue;
				}
				if (level.getGameTime() >= active.endTick() || !player.isAlive() || SeaWeakness.isDrained(player)) {
					ACTIVE.remove(player.getUUID());
					continue;
				}

				Form form = active.form();
				if (form.radius() > 0) {
					for (LivingEntity target : FruitAbilities.nearby(player, level, form.radius())) {
						if (form.damage() > 0) {
							FruitAbilities.hit(player, target, level, form.damage());
						}
						form.onTarget().accept(player, target);
					}
				}
				form.everySecond().accept(player);
				if (form.radius() > 0) {
					com.onepiecemod.fx.MoveFx.pulse(player, level, form.particle(), form.radius());
				}
				level.sendParticles(form.particle(), player.getX(), player.getY() + 1, player.getZ(), 40,
						Math.max(form.radius() / 2, 1), 1.0, Math.max(form.radius() / 2, 1), 0.05);
			}
		});
	}

	private static void awaken(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		player.setAttached(ModAttachments.AWAKENED, true);
		player.setHealth(player.getMaxHealth());
		player.removeAllEffects();
		player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 200, 3));
		player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 2));
		player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 200, 2));

		LightningBolt bolt = new LightningBolt(EntityTypes.LIGHTNING_BOLT, level);
		bolt.setPos(player.position());
		bolt.setVisualOnly(true);
		level.addFreshEntity(bolt);
		FruitAbilities.particles(level, player, ParticleTypes.EXPLOSION_EMITTER, 3);
		FruitAbilities.sound(level, player, ModSounds.FRUIT_AWAKEN);

		level.getServer().getPlayerList().broadcastSystemMessage(
				Component.translatable("message.onepiece.awakened", player.getDisplayName()).withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.BOLD), false);
		player.sendSystemMessage(Component.translatable("message.onepiece.awakened_hint").withStyle(ChatFormatting.GRAY));
	}

	// ---------- Every fruit's awakened form ----------

	private static MobEffectInstance fx(Holder<MobEffect> effect, int seconds, int level) {
		return new MobEffectInstance(effect, seconds * 20, level);
	}

	/** The name of a fruit's awakened form, like "Gear 5: Sun God Nika". Shown in the Devil Fruit Encyclopedia. */
	public static String formName(DevilFruit fruit) {
		return form(fruit).name();
	}

	private static Form form(DevilFruit fruit) {
		String id = fruit.id();
		return switch (id) {
			// ---- Iconic Paramecia ----
			case "gomu_gomu_no_mi" -> new Form("Gear 5: Sun God Nika", 30, 6, 4, ParticleTypes.CLOUD,
					target -> launch(target, 0.9), NOTHING_SELF,
					List.of(fx(MobEffects.STRENGTH, 30, 2), fx(MobEffects.SPEED, 30, 1), fx(MobEffects.JUMP_BOOST, 30, 2), fx(MobEffects.RESISTANCE, 30, 0)));
			case "gura_gura_no_mi" -> new Form("Shattering the World", 20, 14, 6, ParticleTypes.EXPLOSION,
					target -> launch(target, 0.6), NOTHING_SELF, List.of(fx(MobEffects.RESISTANCE, 20, 1)));
			case "ope_ope_no_mi" -> new Form("Perfect Operation", 20, 0, 0, ParticleTypes.HAPPY_VILLAGER,
					NOTHING, player -> player.heal(4), List.of(fx(MobEffects.ABSORPTION, 20, 3), fx(MobEffects.RESISTANCE, 20, 1)));
			case "ito_ito_no_mi" -> new Form("Birdcage", 20, 16, 3, ParticleTypes.CRIT,
					target -> FruitControl.apply(target, fx(MobEffects.SLOWNESS, 2, 1)), NOTHING_SELF, List.of(fx(MobEffects.RESISTANCE, 20, 0)));
			case "mochi_mochi_no_mi" -> new Form("Mochi World", 20, 10, 2, ParticleTypes.WHITE_ASH,
					target -> FruitAbilities.petrify(target, 30), NOTHING_SELF, List.of(fx(MobEffects.RESISTANCE, 20, 1)));
			case "doku_doku_no_mi" -> new Form("Venom Demon: Hell's Judgment", 20, 10, 2, ParticleTypes.WITCH,
					target -> { FruitControl.apply(target, fx(MobEffects.POISON, 3, 1)); FruitControl.apply(target, fx(MobEffects.WITHER, 3, 0)); }, NOTHING_SELF, List.of());
			case "kage_kage_no_mi" -> new Form("Shadows Asgard", 30, 0, 0, ParticleTypes.SQUID_INK, NOTHING, NOTHING_SELF,
					List.of(fx(MobEffects.STRENGTH, 30, 2), fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.ABSORPTION, 30, 3), fx(MobEffects.HEALTH_BOOST, 30, 2)));
			case "soru_soru_no_mi" -> new Form("Soul Harvest", 20, 10, 3, ParticleTypes.WITCH,
					target -> FruitControl.apply(target, fx(MobEffects.WEAKNESS, 3, 1)), player -> player.heal(2), List.of());
			case "hana_hana_no_mi" -> new Form("Gigantesco Mano", 20, 10, 4, ParticleTypes.CRIT,
					target -> FruitAbilities.petrify(target, 20), NOTHING_SELF, List.of());
			case "nikyu_nikyu_no_mi" -> new Form("Ursus Shock", 15, 12, 5, ParticleTypes.CLOUD,
					target -> launch(target, 0.5), NOTHING_SELF, List.of(fx(MobEffects.RESISTANCE, 15, 1)));
			case "mero_mero_no_mi" -> new Form("Perfume Femur Storm", 20, 12, 1, ParticleTypes.HEART,
					target -> FruitAbilities.petrify(target, 40), NOTHING_SELF, List.of());
			case "yomi_yomi_no_mi" -> new Form("Soul King", 20, 10, 3, ParticleTypes.SNOWFLAKE,
					FruitAbilities::freeze, NOTHING_SELF, List.of(fx(MobEffects.SPEED, 20, 1)));
			case "zushi_zushi_no_mi" -> new Form("Meteor Storm", 20, 12, 4, ParticleTypes.CLOUD,
					target -> slam(target), NOTHING_SELF, List.of());

			// ---- Logia: become your element completely ----
			case "mera_mera_no_mi" -> logia("Great Flame Commandment: Flame Emperor", 8, 4, ParticleTypes.FLAME, target -> target.igniteForSeconds(4));
			case "magu_magu_no_mi" -> logia("Volcanic Body", 8, 5, ParticleTypes.LAVA, target -> target.igniteForSeconds(8));
			case "hie_hie_no_mi" -> new Form("Ice Age: Frozen World", 20, 10, 3, ParticleTypes.SNOWFLAKE, FruitAbilities::freeze,
					player -> FruitAbilities.freezeWater((ServerLevel) player.level(), player, player.blockPosition(), 10, false), List.of());
			case "yuki_yuki_no_mi" -> logia("Endless Blizzard", 10, 2, ParticleTypes.SNOWFLAKE, FruitAbilities::freeze);
			case "pika_pika_no_mi" -> new Form("Light Body", 20, 8, 4, ParticleTypes.END_ROD,
					target -> FruitControl.apply(target, fx(MobEffects.GLOWING, 3, 0)), NOTHING_SELF, List.of(fx(MobEffects.SPEED, 20, 3)));
			case "goro_goro_no_mi" -> new Form("Raigo: Thunder God", 20, 14, 0, ParticleTypes.ELECTRIC_SPARK,
					target -> { if (target.getRandom().nextFloat() < 0.25f) FruitAbilities.lightning((ServerLevel) target.level(), target.position()); }, NOTHING_SELF, List.of());
			case "suna_suna_no_mi" -> logia("Ground Death", 10, 2, ParticleTypes.WHITE_ASH, target -> { FruitControl.apply(target, fx(MobEffects.WITHER, 3, 0)); FruitControl.apply(target, fx(MobEffects.HUNGER, 3, 2)); });
			case "moku_moku_no_mi" -> logia("Smoke World", 10, 1, ParticleTypes.LARGE_SMOKE, target -> { FruitControl.apply(target, fx(MobEffects.BLINDNESS, 3, 0)); FruitControl.apply(target, fx(MobEffects.SLOWNESS, 3, 1)); });
			case "yami_yami_no_mi" -> logia("Liberation", 12, 3, ParticleTypes.SQUID_INK, target -> { FruitControl.apply(target, fx(MobEffects.SLOWNESS, 2, 2)); FruitControl.apply(target, fx(MobEffects.DARKNESS, 3, 0)); });
			case "numa_numa_no_mi" -> logia("Swamp World", 10, 2, ParticleTypes.SQUID_INK, target -> FruitAbilities.petrify(target, 30));
			case "gasu_gasu_no_mi" -> logia("Gas Planet", 10, 2, ParticleTypes.WITCH, target -> FruitControl.apply(target, fx(MobEffects.POISON, 3, 1)));
			case "mori_mori_no_mi" -> new Form("Living Forest", 20, 10, 3, ParticleTypes.HAPPY_VILLAGER,
					target -> FruitControl.apply(target, fx(MobEffects.SLOWNESS, 3, 2)), player -> player.heal(2), List.of());

			// ---- Mythical Zoans ----
			case "uo_uo_no_mi_seiryu" -> new Form("Thunder Bagua Dragon", 30, 8, 5, ParticleTypes.FLAME,
					target -> target.igniteForSeconds(4), NOTHING_SELF,
					List.of(fx(MobEffects.STRENGTH, 30, 2), fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.SLOW_FALLING, 30, 0), fx(MobEffects.FIRE_RESISTANCE, 30, 0)));
			case "tori_tori_no_mi_phoenix" -> new Form("Phoenix Rebirth", 30, 0, 0, ParticleTypes.SOUL_FIRE_FLAME, NOTHING,
					player -> { player.heal(3); healFriends(player); },
					List.of(fx(MobEffects.SPEED, 30, 1), fx(MobEffects.SLOW_FALLING, 30, 0), fx(MobEffects.RESISTANCE, 30, 1)));
			case "inu_inu_no_mi_okuchi_no_makami" -> new Form("Divine Wolf of the Snow", 30, 8, 3, ParticleTypes.SNOWFLAKE,
					FruitAbilities::freeze, NOTHING_SELF, List.of(fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.SPEED, 30, 1)));
			case "hito_hito_no_mi_daibutsu" -> new Form("Golden Buddha Shockwave", 30, 10, 4, ParticleTypes.EXPLOSION,
					target -> launch(target, 0.4), NOTHING_SELF, List.of(fx(MobEffects.RESISTANCE, 30, 2)));
			case "hebi_hebi_no_mi_yamata_no_orochi" -> new Form("Eight-Headed Fury", 30, 8, 3, ParticleTypes.WITCH,
					target -> FruitControl.apply(target, fx(MobEffects.POISON, 3, 1)), NOTHING_SELF, List.of(fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.HEALTH_BOOST, 30, 2)));

			// ---- More Paramecia (2026-11-03: every fruit gets its own awakening) ----
			case "bara_bara_no_mi" -> para("Bara Bara Festival", 8, 3, ParticleTypes.CRIT, target -> launch(target, 0.3), fx(MobEffects.RESISTANCE, 20, 0), fx(MobEffects.SPEED, 20, 0));
			case "jiki_jiki_no_mi" -> para("Punk Rotten", 10, 3, ParticleTypes.ELECTRIC_SPARK, Awakening::pull, fx(MobEffects.RESISTANCE, 20, 1));
			case "wara_wara_no_mi" -> para("Straw Man Hex", 10, 2, ParticleTypes.WHITE_ASH, target -> { slow(target, 0); weak(target, 0); }, fx(MobEffects.RESISTANCE, 20, 0));
			case "toshi_toshi_no_mi" -> para("Age of Ages", 8, 2, ParticleTypes.ENCHANT, target -> weak(target, 1), fx(MobEffects.SPEED, 20, 1));
			case "fuku_fuku_no_mi" -> para("Fox Fire Wardrobe", 8, 3, ParticleTypes.FLAME, target -> target.igniteForSeconds(3), fx(MobEffects.RESISTANCE, 20, 0), fx(MobEffects.FIRE_RESISTANCE, 20, 0));
			case "nomi_nomi_no_mi" -> para("Total Recall", 8, 2, ParticleTypes.ENCHANT, target -> FruitControl.apply(target, fx(MobEffects.GLOWING, 3, 0)), fx(MobEffects.HASTE, 20, 1), fx(MobEffects.SPEED, 20, 1), fx(MobEffects.NIGHT_VISION, 20, 0));
			case "horo_horo_no_mi" -> para("Negative Hollow Storm", 12, 1, ParticleTypes.SOUL, target -> { weak(target, 1); slow(target, 0); }, fx(MobEffects.INVISIBILITY, 20, 0));
			case "bisu_bisu_no_mi" -> para("Biscuit Soldier Army", 8, 3, ParticleTypes.WHITE_ASH, NOTHING, fx(MobEffects.ABSORPTION, 20, 3), fx(MobEffects.RESISTANCE, 20, 1));
			case "pero_pero_no_mi" -> para("Candy Maiden", 10, 2, ParticleTypes.HEART, target -> FruitAbilities.petrify(target, 30), fx(MobEffects.RESISTANCE, 20, 0));
			case "mira_mira_no_mi" -> para("Mirror Labyrinth", 8, 3, ParticleTypes.END_ROD, target -> FruitControl.apply(target, fx(MobEffects.BLINDNESS, 3, 0)), fx(MobEffects.SPEED, 20, 1));
			case "netsu_netsu_no_mi" -> para("Netsu Heat Dome", 8, 4, ParticleTypes.FLAME, target -> target.igniteForSeconds(5), fx(MobEffects.FIRE_RESISTANCE, 20, 0));
			case "bari_bari_no_mi" -> para("Barrier Crash", 6, 4, ParticleTypes.END_ROD, (player, target) -> FruitAbilities.push(target, player, 1.0, 0.3), fx(MobEffects.RESISTANCE, 20, 2));
			case "hobi_hobi_no_mi" -> para("Toy Kingdom", 10, 2, ParticleTypes.ENCHANT, target -> FruitAbilities.petrify(target, 40), fx(MobEffects.SPEED, 20, 0));
			case "doru_doru_no_mi" -> para("Candle Champion", 8, 3, ParticleTypes.WHITE_ASH, target -> FruitAbilities.petrify(target, 30), fx(MobEffects.RESISTANCE, 20, 1));
			case "bomu_bomu_no_mi" -> para("Living Bomb", 6, 6, ParticleTypes.EXPLOSION, target -> launch(target, 0.4), fx(MobEffects.RESISTANCE, 20, 0));
			case "kilo_kilo_no_mi" -> para("10,000 Kilo Meteor", 8, 4, ParticleTypes.CLOUD, target -> slam(target), fx(MobEffects.SLOW_FALLING, 20, 0), fx(MobEffects.RESISTANCE, 20, 0));
			case "supa_supa_no_mi" -> para("Steel Spiral", 6, 5, ParticleTypes.CRIT, NOTHING, fx(MobEffects.RESISTANCE, 20, 1));
			case "mane_mane_no_mi" -> para("Memoir Masquerade", 8, 3, ParticleTypes.ENCHANT, target -> slow(target, 0), fx(MobEffects.SPEED, 20, 1), fx(MobEffects.STRENGTH, 20, 0));
			case "noro_noro_no_mi" -> para("Noroma Photon Storm", 12, 1, ParticleTypes.ENCHANT, target -> slow(target, 2), fx(MobEffects.SPEED, 20, 0));
			case "doa_doa_no_mi" -> para("Door World", 6, 3, ParticleTypes.PORTAL, target -> launch(target, 0.3), fx(MobEffects.INVISIBILITY, 20, 0), fx(MobEffects.SPEED, 20, 1));
			case "awa_awa_no_mi" -> para("Golden Rush Bubbles", 10, 2, ParticleTypes.BUBBLE_POP, target -> weak(target, 1), fx(MobEffects.SPEED, 20, 0));
			case "fuwa_fuwa_no_mi" -> para("Lion's Flight", 10, 3, ParticleTypes.CLOUD, target -> launch(target, 0.7), fx(MobEffects.SLOW_FALLING, 20, 0));
			case "ishi_ishi_no_mi" -> para("Stone Colossus", 8, 4, ParticleTypes.CLOUD, target -> slam(target), fx(MobEffects.RESISTANCE, 20, 1), fx(MobEffects.HEALTH_BOOST, 20, 1));
			case "hira_hira_no_mi" -> para("Flag Wall", 6, 3, ParticleTypes.CRIT, (player, target) -> FruitAbilities.push(target, player, 0.8, 0.2), fx(MobEffects.RESISTANCE, 20, 1));
			case "nagi_nagi_no_mi" -> para("Silent Assassin", 8, 3, ParticleTypes.SQUID_INK, target -> { weak(target, 0); slow(target, 0); }, fx(MobEffects.INVISIBILITY, 20, 0), fx(MobEffects.SPEED, 20, 0));
			case "horu_horu_no_mi" -> new Form("Hormone Overdrive", 20, 0, 0, ParticleTypes.HEART, NOTHING,
					player -> { player.heal(2); healFriends(player); }, List.of(fx(MobEffects.STRENGTH, 20, 0), fx(MobEffects.SPEED, 20, 0)));
			case "bane_bane_no_mi" -> para("Spring Death Knock", 8, 4, ParticleTypes.CLOUD, target -> launch(target, 0.8), fx(MobEffects.JUMP_BOOST, 20, 2), fx(MobEffects.SPEED, 20, 1));
			case "kira_kira_no_mi" -> para("Diamond Fortress", 6, 3, ParticleTypes.END_ROD, NOTHING, fx(MobEffects.RESISTANCE, 20, 2), fx(MobEffects.ABSORPTION, 20, 2));
			case "woshu_woshu_no_mi" -> para("Wash and Wring", 8, 2, ParticleTypes.SPLASH, target -> weak(target, 1), fx(MobEffects.RESISTANCE, 20, 0));
			case "oto_oto_no_mi" -> new Form("Battle Symphony", 20, 10, 2, ParticleTypes.NOTE, NOTHING, Awakening::healFriends,
					List.of(fx(MobEffects.STRENGTH, 20, 0), fx(MobEffects.SPEED, 20, 0)));
			case "shiro_shiro_no_mi" -> para("Castle Cannonade", 12, 4, ParticleTypes.EXPLOSION, NOTHING, fx(MobEffects.RESISTANCE, 20, 1));
			case "baku_baku_no_mi" -> new Form("Munch-Munch Factory", 20, 6, 4, ParticleTypes.CRIT, NOTHING, player -> player.heal(2), List.of(fx(MobEffects.RESISTANCE, 20, 0)));
			case "choki_choki_no_mi" -> para("Paper Storm", 8, 4, ParticleTypes.CRIT, target -> slow(target, 0), fx(MobEffects.SPEED, 20, 0));
			case "fude_fude_no_mi" -> para("Living Ink", 8, 3, ParticleTypes.SQUID_INK, target -> FruitControl.apply(target, fx(MobEffects.BLINDNESS, 3, 0)), fx(MobEffects.RESISTANCE, 20, 0));
			case "kibi_kibi_no_mi" -> new Form("Kibi Dango Feast", 20, 10, 1, ParticleTypes.HAPPY_VILLAGER, target -> { slow(target, 0); weak(target, 0); },
					Awakening::healFriends, List.of(fx(MobEffects.REGENERATION, 20, 0)));
			case "toki_toki_no_mi" -> para("Time Freeze", 12, 1, ParticleTypes.END_ROD, target -> FruitAbilities.petrify(target, 40), fx(MobEffects.SPEED, 20, 1));
			case "memo_memo_no_mi" -> para("Memory Wipe", 10, 1, ParticleTypes.ENCHANT, target -> { FruitControl.apply(target, fx(MobEffects.BLINDNESS, 3, 0)); weak(target, 0); }, fx(MobEffects.SPEED, 20, 0));
			case "riki_riki_no_mi" -> new Form("Champion's Might", 20, 0, 0, ParticleTypes.CRIT, NOTHING, NOTHING_SELF,
					List.of(fx(MobEffects.STRENGTH, 20, 1), fx(MobEffects.RESISTANCE, 20, 0), fx(MobEffects.SPEED, 20, 0)));
			case "wapu_wapu_no_mi" -> para("Warp Barrage", 8, 4, ParticleTypes.PORTAL, target -> launch(target, 0.3), fx(MobEffects.SPEED, 20, 1));
			case "shiku_shiku_no_mi" -> para("Plague Cloud", 10, 2, ParticleTypes.SPORE_BLOSSOM_AIR, target -> { FruitControl.apply(target, fx(MobEffects.POISON, 3, 0)); FruitControl.apply(target, fx(MobEffects.HUNGER, 3, 1)); }, fx(MobEffects.RESISTANCE, 20, 0));
			case "beta_beta_no_mi" -> para("Mucus Flood", 8, 2, ParticleTypes.ITEM_SLIME, target -> slow(target, 1), fx(MobEffects.RESISTANCE, 20, 0));
			case "pamu_pamu_no_mi" -> para("Chain Rupture", 6, 6, ParticleTypes.EXPLOSION, NOTHING, fx(MobEffects.RESISTANCE, 20, 0));
			case "sui_sui_no_mi" -> para("Sea of Ground", 8, 3, ParticleTypes.SPLASH, target -> slam(target), fx(MobEffects.SPEED, 20, 1));
			case "buki_buki_no_mi" -> para("Weapon Body", 10, 4, ParticleTypes.CRIT, NOTHING, fx(MobEffects.RESISTANCE, 20, 0), fx(MobEffects.STRENGTH, 20, 0));
			case "guru_guru_no_mi" -> para("Propeller Cyclone", 8, 3, ParticleTypes.CLOUD, target -> launch(target, 0.6), fx(MobEffects.SLOW_FALLING, 20, 0));
			case "modo_modo_no_mi" -> new Form("Rewind", 20, 8, 2, ParticleTypes.ENCHANT, target -> weak(target, 1), player -> player.heal(3), List.of());
			case "sube_sube_no_mi" -> para("Slippery World", 8, 2, ParticleTypes.HEART, (player, target) -> { slow(target, 1); FruitAbilities.push(target, player, 0.6, 0.1); }, fx(MobEffects.SPEED, 20, 1));
			case "ori_ori_no_mi" -> para("Black Cage Prison", 12, 2, ParticleTypes.SQUID_INK, target -> FruitAbilities.petrify(target, 40), fx(MobEffects.RESISTANCE, 20, 0));
			case "chiyu_chiyu_no_mi" -> new Form("Healing Rain", 20, 0, 0, ParticleTypes.HAPPY_VILLAGER, NOTHING,
					player -> { player.heal(4); healFriends(player); }, List.of(fx(MobEffects.REGENERATION, 20, 1)));
			case "nui_nui_no_mi" -> para("Stitch the World", 10, 2, ParticleTypes.CRIT, target -> FruitAbilities.petrify(target, 30), fx(MobEffects.RESISTANCE, 20, 0));
			case "ton_ton_no_mi" -> para("Ten-Thousand Ton Crush", 8, 5, ParticleTypes.CLOUD, target -> slam(target), fx(MobEffects.RESISTANCE, 20, 1));
			case "ato_ato_no_mi" -> para("Living Gallery", 10, 2, ParticleTypes.ENCHANT, target -> { FruitAbilities.petrify(target, 30); FruitControl.apply(target, fx(MobEffects.GLOWING, 3, 0)); }, fx(MobEffects.SPEED, 20, 0));
			case "sabi_sabi_no_mi" -> para("Rust Storm", 10, 3, ParticleTypes.WHITE_ASH, target -> weak(target, 1), fx(MobEffects.RESISTANCE, 20, 0));
			case "mato_mato_no_mi" -> para("Bullseye Rain", 16, 3, ParticleTypes.CRIT, target -> FruitControl.apply(target, fx(MobEffects.GLOWING, 3, 0)), fx(MobEffects.SPEED, 20, 0));

			// ---- More Zoans ----
			case "hito_hito_no_mi" -> zoan("Monster Point", 6, 4, ParticleTypes.CRIT, target -> launch(target, 0.5), fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.HEALTH_BOOST, 30, 1));
			case "ryu_ryu_no_mi_allosaurus" -> zoan("Jurassic Rampage", 5, 5, ParticleTypes.CRIT, NOTHING, fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.SPEED, 30, 0));
			case "ryu_ryu_no_mi_pteranodon" -> zoan("Sky King Dive", 6, 4, ParticleTypes.CLOUD, target -> launch(target, 0.5), fx(MobEffects.SPEED, 30, 1), fx(MobEffects.SLOW_FALLING, 30, 0));
			case "neko_neko_no_mi_leopard" -> zoan("Feline Assassin", 5, 5, ParticleTypes.CRIT, NOTHING, fx(MobEffects.SPEED, 30, 1), fx(MobEffects.STRENGTH, 30, 1));
			case "mogu_mogu_no_mi" -> zoan("Earthquake Tunnel", 8, 3, ParticleTypes.CLOUD, target -> slam(target), fx(MobEffects.HASTE, 30, 1), fx(MobEffects.RESISTANCE, 30, 0));
			case "uma_uma_no_mi" -> zoan("Wild Stampede", 6, 3, ParticleTypes.CLOUD, (player, target) -> FruitAbilities.push(target, player, 1.0, 0.3), fx(MobEffects.SPEED, 30, 2));
			case "sara_sara_no_mi_axolotl" -> zoan("Regeneration Pool", 6, 2, ParticleTypes.SPLASH, target -> FruitControl.apply(target, fx(MobEffects.POISON, 3, 0)), fx(MobEffects.REGENERATION, 30, 1), fx(MobEffects.WATER_BREATHING, 30, 0));
			case "inu_inu_no_mi_wolf" -> zoan("Pack Leader", 6, 4, ParticleTypes.CRIT, target -> weak(target, 0), fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.SPEED, 30, 0));
			case "inu_inu_no_mi_jackal" -> zoan("Desert Hunter", 6, 4, ParticleTypes.WHITE_ASH, target -> FruitControl.apply(target, fx(MobEffects.HUNGER, 3, 1)), fx(MobEffects.SPEED, 30, 1));
			case "neko_neko_no_mi_saber_tiger" -> zoan("Saber Fang", 5, 5, ParticleTypes.CRIT, NOTHING, fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.SPEED, 30, 0));
			case "ryu_ryu_no_mi_pachycephalosaurus" -> zoan("Iron Skull", 5, 5, ParticleTypes.CRIT, (player, target) -> FruitAbilities.push(target, player, 1.2, 0.3), fx(MobEffects.RESISTANCE, 30, 1));
			case "ryu_ryu_no_mi_triceratops" -> zoan("Triple Horn Charge", 5, 5, ParticleTypes.CRIT, (player, target) -> FruitAbilities.push(target, player, 1.0, 0.4), fx(MobEffects.RESISTANCE, 30, 1));
			case "ryu_ryu_no_mi_spinosaurus" -> zoan("Sail Fin Rampage", 6, 5, ParticleTypes.CRIT, NOTHING, fx(MobEffects.STRENGTH, 30, 1));
			case "ryu_ryu_no_mi_nidhogg" -> zoan("Ragnarok Thunder", 9, 5, ParticleTypes.ELECTRIC_SPARK,
					target -> { if (target.getRandom().nextInt(4) == 0) FruitAbilities.lightning((ServerLevel) target.level(), target.position()); slow(target, 1); },
					fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.HEALTH_BOOST, 30, 2), fx(MobEffects.SLOW_FALLING, 30, 0));
			case "ryu_ryu_no_mi_brachiosaurus" -> zoan("Titan Neck Sweep", 9, 4, ParticleTypes.CLOUD, target -> launch(target, 0.6), fx(MobEffects.HEALTH_BOOST, 30, 2));
			case "zou_zou_no_mi_mammoth" -> zoan("Ancient Mammoth", 8, 4, ParticleTypes.CLOUD, target -> slam(target), fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.HEALTH_BOOST, 30, 1));
			case "zou_zou_no_mi" -> zoan("Trunk Typhoon", 7, 3, ParticleTypes.CLOUD, (player, target) -> FruitAbilities.push(target, player, 1.0, 0.3), fx(MobEffects.RESISTANCE, 30, 0));
			case "ushi_ushi_no_mi_giraffe" -> zoan("Neck Hammer Storm", 6, 4, ParticleTypes.CRIT, target -> slam(target), fx(MobEffects.STRENGTH, 30, 0));
			case "ushi_ushi_no_mi_bison" -> zoan("Stampede Charge", 6, 4, ParticleTypes.CLOUD, (player, target) -> FruitAbilities.push(target, player, 1.2, 0.3), fx(MobEffects.RESISTANCE, 30, 0), fx(MobEffects.SPEED, 30, 0));
			case "tori_tori_no_mi_falcon" -> zoan("Falcon Storm", 6, 3, ParticleTypes.CLOUD, target -> launch(target, 0.5), fx(MobEffects.SPEED, 30, 1), fx(MobEffects.SLOW_FALLING, 30, 0));
			case "hebi_hebi_no_mi_anaconda" -> zoan("Serpent Coil", 6, 3, ParticleTypes.CRIT, target -> FruitAbilities.petrify(target, 30), fx(MobEffects.HEALTH_BOOST, 30, 1));
			case "hebi_hebi_no_mi_king_cobra" -> zoan("Venom Strike", 6, 3, ParticleTypes.WITCH, target -> FruitControl.apply(target, fx(MobEffects.POISON, 3, 1)), fx(MobEffects.SPEED, 30, 0));
			case "inu_inu_no_mi_kyubi_no_kitsune" -> zoan("Nine-Tail Foxfire", 8, 3, ParticleTypes.SOUL_FIRE_FLAME, target -> target.igniteForSeconds(4), fx(MobEffects.SPEED, 30, 0), fx(MobEffects.INVISIBILITY, 30, 0));
			case "kumo_kumo_no_mi_rosamygale_grauvogeli" -> zoan("Spider Queen's Web", 10, 2, ParticleTypes.WHITE_ASH, target -> FruitAbilities.petrify(target, 30), fx(MobEffects.STRENGTH, 30, 0));

			// ---- Everyone else, by fruit type ----
			default -> switch (fruit.type()) {
				// Awakened Paramecia change the world around them.
				case PARAMECIA -> new Form("Awakened " + fruit.name(), 20, 8, 3, ParticleTypes.ENCHANT,
						target -> FruitControl.apply(target, fx(MobEffects.SLOWNESS, 2, 0)), NOTHING_SELF,
						List.of(fx(MobEffects.STRENGTH, 20, 1), fx(MobEffects.RESISTANCE, 20, 0)));
				case LOGIA -> logia("Awakened " + fruit.name(), 8, 3, ParticleTypes.ENCHANT, NOTHING);
				// Awakened Zoans get monstrous strength and toughness.
				case ZOAN -> new Form("Awakened " + fruit.name(), 30, 0, 0, ParticleTypes.CRIT, NOTHING, NOTHING_SELF,
						List.of(fx(MobEffects.STRENGTH, 30, 2), fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.SPEED, 30, 0),
								fx(MobEffects.REGENERATION, 30, 1), fx(MobEffects.HEALTH_BOOST, 30, 2)));
			};
		};
	}

	/** A Paramecia awakening: 20 seconds, an aura around you, plus effects on you. */
	private static Form para(String name, double radius, float damage, ParticleOptions particle, Consumer<LivingEntity> onTarget, MobEffectInstance... self) {
		return new Form(name, 20, radius, damage, particle, onTarget, NOTHING_SELF, List.of(self));
	}

	private static Form para(String name, double radius, float damage, ParticleOptions particle, BiConsumer<ServerPlayer, LivingEntity> onTarget, MobEffectInstance... self) {
		return new Form(name, 20, radius, damage, particle, onTarget, NOTHING_SELF, List.of(self));
	}

	/** A Zoan awakening: 30 seconds of a monstrous body. Always regenerates a little. */
	private static Form zoan(String name, double radius, float damage, ParticleOptions particle, Consumer<LivingEntity> onTarget, MobEffectInstance... self) {
		return zoan(name, radius, damage, particle, (player, target) -> onTarget.accept(target), self);
	}

	private static Form zoan(String name, double radius, float damage, ParticleOptions particle, BiConsumer<ServerPlayer, LivingEntity> onTarget, MobEffectInstance... self) {
		List<MobEffectInstance> effects = new java.util.ArrayList<>(List.of(self));
		effects.add(fx(MobEffects.REGENERATION, 30, 0));
		return new Form(name, 30, radius, damage, particle, onTarget, NOTHING_SELF, effects);
	}

	private static void pull(ServerPlayer player, LivingEntity target) {
		FruitAbilities.push(target, player, -0.8, 0.2);
	}

	private static void slow(LivingEntity target, int level) {
		FruitControl.apply(target, fx(MobEffects.SLOWNESS, 3, level));
	}

	private static void weak(LivingEntity target, int level) {
		FruitControl.apply(target, fx(MobEffects.WEAKNESS, 3, level));
	}

	private static Form logia(String name, double radius, float damage, ParticleOptions particle, Consumer<LivingEntity> onTarget) {
		return new Form(name, 20, radius, damage, particle, onTarget, NOTHING_SELF, List.of(fx(MobEffects.RESISTANCE, 20, 0)));
	}

	private static void launch(LivingEntity target, double up) {
		target.setDeltaMovement(target.getDeltaMovement().x, up, target.getDeltaMovement().z);
		Motion.sync(target);
	}

	private static void slam(LivingEntity target) {
		target.setDeltaMovement(0, -1.5, 0);
		Motion.sync(target);
	}

	private static void healFriends(ServerPlayer player) {
		for (Player friend : player.level().getEntitiesOfClass(Player.class, player.getBoundingBox().inflate(10))) {
			friend.addEffect(fx(MobEffects.REGENERATION, 3, 1));
		}
	}
}
