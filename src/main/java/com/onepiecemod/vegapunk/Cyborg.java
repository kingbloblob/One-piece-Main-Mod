package com.onepiecemod.vegapunk;

import com.onepiecemod.util.Motion;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.deco.DecoBlocks;
import com.onepiecemod.deco.DecoItems;
import com.onepiecemod.fx.MoveFx;
import com.onepiecemod.multiplayer.PlayerCrews;

/**
 * The player's cyborg body, Franky style. Modules installed by right-clicking them raise an upgrade's tier (see
 * CyborgUpgrade). Everything runs on Cola: the Cola Engine holds the fuel and refills itself from Colas (and Cola
 * Crates) in your bag, like the fridge in Franky's belly.
 *
 * Key C fires the Radical Beam, Sneak + C the Coup de Vent (client: vegapunk/client/VegapunkClient).
 */
public class Cyborg {
	/** Fuel in one Cola. A Cola Crate is worth 8. */
	public static final int COLA = 100;
	private static final int BEAM_FUEL = COLA;
	private static final int VENT_FUEL = COLA / 2;

	public static final AttachmentType<CyborgData> DATA = AttachmentRegistry.create(
			OnePieceMod.id("cyborg"),
			builder -> builder.persistent(CyborgData.CODEC).copyOnDeath());

	private static final Identifier FRAME_ARMOR = OnePieceMod.id("cyborg_frame_armor");
	private static final Identifier FRAME_TOUGHNESS = OnePieceMod.id("cyborg_frame_toughness");
	private static final Identifier FRAME_KNOCKBACK = OnePieceMod.id("cyborg_frame_knockback");
	private static final Identifier ARM_DAMAGE = OnePieceMod.id("cyborg_arm_damage");
	private static final Identifier ENGINE_SPEED = OnePieceMod.id("cyborg_engine_speed");
	private static final Identifier FLAME_ARMOR = OnePieceMod.id("cyborg_lunarian_flame");

	/** Game time when each player's beam / air cannon is ready again. Short, so not saved. */
	private static final Map<UUID, Long> READY_AT = new HashMap<>();
	/** Ticks of sprinting since fuel was last burned. */
	private static final Map<UUID, Integer> SPRINT = new HashMap<>();

	/** The tiers this game's own player has (set from the server's sync), for item tooltips. */
	public static volatile CyborgData clientData = CyborgData.EMPTY;

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(Cyborg::tick);
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> sync(handler.getPlayer()));
		ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> sync(newPlayer));
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			READY_AT.remove(handler.getPlayer().getUUID());
			SPRINT.remove(handler.getPlayer().getUUID());
		});

		// Lunarian Plating: fire slides off. Tier I ignores a third of the burns, II two thirds, III all of them (lava too).
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			if (!(entity instanceof ServerPlayer player) || !source.is(DamageTypeTags.IS_FIRE)) {
				return true;
			}
			int tier = get(player).tier(CyborgUpgrade.LUNARIAN_PLATING);
			return tier < 3 && player.getRandom().nextInt(3) >= tier;
		});
	}

	public static CyborgData get(Player player) {
		return player.getAttachedOrElse(DATA, CyborgData.EMPTY);
	}

	public static void set(ServerPlayer player, CyborgData data) {
		player.setAttached(DATA, data);
		applyModifiers(player, data);
		sync(player);
	}

	public static void sync(ServerPlayer player) {
		CyborgData data = get(player);
		ServerPlayNetworking.send(player, new VegapunkPayloads.Sync(data.tiers(), data.fuel(), data.tank()));
	}

	// ---------- Installing modules ----------

	/** What installing the next tier uses up besides the module itself. */
	public record Cost(int chips, int feathers) {
		public String text() {
			if (chips == 0 && feathers == 0) {
				return "just the module";
			}
			String s = chips + " Vegapunk Chip" + (chips == 1 ? "" : "s");
			return feathers > 0 ? s + " and " + feathers + " Seraphim Feather" : s;
		}
	}

	public static Cost installCost(int nextTier) {
		return switch (nextTier) {
			case 2 -> new Cost(1, 0);
			case 3 -> new Cost(2, 1);
			default -> new Cost(0, 0);
		};
	}

	/** Right-clicking a module: installs the next tier if the player has everything. */
	public static boolean install(ServerPlayer player, CyborgUpgrade upgrade, ItemStack module) {
		CyborgData data = get(player);
		int tier = data.tier(upgrade);
		if (tier >= CyborgUpgrade.MAX_TIER) {
			player.sendOverlayMessage(Component.literal(upgrade.title + " is already at tier III.").withStyle(ChatFormatting.YELLOW));
			return false;
		}
		Cost cost = installCost(tier + 1);
		boolean creative = player.isCreative();
		if (!creative && (count(player, VegapunkItems.VEGAPUNK_CHIP) < cost.chips() || count(player, VegapunkItems.SERAPHIM_FEATHER) < cost.feathers())) {
			player.sendSystemMessage(Component.literal("Tier " + roman(tier + 1) + " of " + upgrade.title + " also needs " + cost.text() + ".")
					.withStyle(ChatFormatting.RED));
			return false;
		}
		if (!creative) {
			take(player, VegapunkItems.VEGAPUNK_CHIP, cost.chips());
			take(player, VegapunkItems.SERAPHIM_FEATHER, cost.feathers());
			module.shrink(1);
		}
		set(player, data.withTier(upgrade, tier + 1));

		ServerLevel level = player.level();
		level.playSound(null, player.blockPosition(), SoundEvents.SMITHING_TABLE_USE, SoundSource.PLAYERS, 1.0f, 0.8f);
		level.playSound(null, player.blockPosition(), SoundEvents.IRON_GOLEM_REPAIR, SoundSource.PLAYERS, 1.0f, 1.2f);
		level.sendParticles(ParticleTypes.ELECTRIC_SPARK, player.getX(), player.getY() + 1, player.getZ(), 30, 0.4, 0.6, 0.4, 0.1);
		player.sendSystemMessage(Component.literal("SUUUPER! " + upgrade.title + " tier " + roman(tier + 1) + " installed: ")
				.withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD)
				.append(Component.literal(upgrade.tiers.get(tier)).withStyle(ChatFormatting.WHITE)));
		if (upgrade == CyborgUpgrade.RADICAL_BEAM || upgrade == CyborgUpgrade.COUP_DE_VENT) {
			player.sendSystemMessage(Component.literal(get(player).tier(CyborgUpgrade.COLA_ENGINE) == 0
					? "It runs on Cola: install a Cola Engine to carry fuel."
					: "Press C to fire it (Sneak + C for Coup de Vent). It burns Cola from your engine.").withStyle(ChatFormatting.GRAY));
		}
		return true;
	}

	private static int count(Player player, Item item) {
		int total = 0;
		for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
			ItemStack stack = player.getInventory().getItem(slot);
			if (stack.is(item)) {
				total += stack.getCount();
			}
		}
		return total;
	}

	private static void take(Player player, Item item, int amount) {
		for (int slot = 0; slot < player.getInventory().getContainerSize() && amount > 0; slot++) {
			ItemStack stack = player.getInventory().getItem(slot);
			if (stack.is(item)) {
				int used = Math.min(amount, stack.getCount());
				stack.shrink(used);
				amount -= used;
			}
		}
	}

	public static String roman(int tier) {
		return switch (tier) {
			case 1 -> "I";
			case 2 -> "II";
			case 3 -> "III";
			default -> "0";
		};
	}

	// ---------- Every few ticks ----------

	private static void tick(MinecraftServer server) {
		boolean slow = server.getTickCount() % 10 == 0;
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			CyborgData data = get(player);
			if (!data.any()) {
				continue;
			}
			engineTick(player, data);
			int plating = data.tier(CyborgUpgrade.LUNARIAN_PLATING);
			// Seraphim wings: hold Sneak in the air to glide down.
			if (plating >= 3 && player.isShiftKeyDown() && !player.onGround() && !player.isInWater()
					&& player.getDeltaMovement().y < -0.1 && !player.getAbilities().flying) {
				player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 10, 0, true, false, true));
				if (server.getTickCount() % 4 == 0) {
					player.level().sendParticles(ParticleTypes.FLAME, player.getX(), player.getY() + 1.2, player.getZ(), 2, 0.3, 0.1, 0.3, 0.01);
				}
			}
			if (slow) {
				applyModifiers(player, get(player));
				refuel(player);
			}
		}
	}

	/** Sprinting with fuel in the tank is a little faster, and burns a Cola every 25 seconds of running. */
	private static void engineTick(ServerPlayer player, CyborgData data) {
		if (data.tier(CyborgUpgrade.COLA_ENGINE) == 0 || data.fuel() <= 0 || !player.isSprinting()) {
			return;
		}
		int ticks = SPRINT.merge(player.getUUID(), 1, Integer::sum);
		if (ticks >= 25) { // 25 ticks of sprinting = 1 fuel, so 100 fuel lasts 2500 ticks.
			SPRINT.put(player.getUUID(), 0);
			player.setAttached(DATA, data.withFuel(data.fuel() - 1));
		}
	}

	/** The engine tops itself up from Colas in your bag whenever there's room for a whole one. */
	private static void refuel(ServerPlayer player) {
		CyborgData data = get(player);
		int room = data.tank() - data.fuel();
		if (room < COLA || player.isCreative()) {
			if (player.isCreative() && data.fuel() < data.tank()) {
				set(player, data.withFuel(data.tank()));
			}
			return;
		}
		Item crate = DecoBlocks.COLA_CRATE.asItem();
		int added = 0;
		while (room - added >= COLA) {
			if (count(player, DecoItems.COLA) > 0) {
				take(player, DecoItems.COLA, 1);
				player.getInventory().placeItemBackInInventory(new ItemStack(net.minecraft.world.item.Items.GLASS_BOTTLE), net.minecraft.util.Prediction.SERVER_ONLY);
				added += COLA;
			} else if (room - added >= COLA * 8 && count(player, crate) > 0) {
				take(player, crate, 1);
				added += COLA * 8;
			} else {
				break;
			}
		}
		if (added > 0) {
			set(player, data.withFuel(data.fuel() + added));
			player.level().playSound(null, player.blockPosition(), SoundEvents.GENERIC_DRINK.value(), SoundSource.PLAYERS, 0.6f, 1.2f);
			player.sendOverlayMessage(Component.literal("Cola Engine refuelled: " + fuelText(get(player))).withStyle(ChatFormatting.AQUA));
		} else if (server(player).getTickCount() % 200 == 0) {
			sync(player); // Keeps the fuel shown on screen honest while sprinting burns it.
		}
	}

	private static MinecraftServer server(ServerPlayer player) {
		return player.level().getServer();
	}

	public static String fuelText(CyborgData data) {
		return String.format("%.1f / %d Colas", data.fuel() / (double) COLA, data.tank() / COLA);
	}

	/** Puts the stat bonuses on the player. Only touches our own modifiers, and only when they change. */
	static void applyModifiers(ServerPlayer player, CyborgData data) {
		int frame = data.tier(CyborgUpgrade.IRON_FRAME);
		modifier(player, Attributes.ARMOR, FRAME_ARMOR, 2.0 * frame, AttributeModifier.Operation.ADD_VALUE);
		modifier(player, Attributes.ARMOR_TOUGHNESS, FRAME_TOUGHNESS, 1.0 * frame, AttributeModifier.Operation.ADD_VALUE);
		modifier(player, Attributes.KNOCKBACK_RESISTANCE, FRAME_KNOCKBACK, frame >= 3 ? 0.3 : 0.05 * frame, AttributeModifier.Operation.ADD_VALUE);

		int arm = data.tier(CyborgUpgrade.STRONG_RIGHT);
		double bare = player.getMainHandItem().isEmpty() ? 1.5 * arm : 0.0;
		modifier(player, Attributes.ATTACK_DAMAGE, ARM_DAMAGE, arm + bare, AttributeModifier.Operation.ADD_VALUE);

		int engine = data.tier(CyborgUpgrade.COLA_ENGINE);
		boolean running = engine > 0 && data.fuel() > 0 && player.isSprinting();
		modifier(player, Attributes.MOVEMENT_SPEED, ENGINE_SPEED, running ? 0.05 * engine : 0.0, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);

		// Lunarian flame: badly hurt, the plating lights up and hardens.
		int plating = data.tier(CyborgUpgrade.LUNARIAN_PLATING);
		boolean flame = plating >= 2 && player.getHealth() < player.getMaxHealth() * 0.35f && !player.isInWaterOrRain();
		modifier(player, Attributes.ARMOR, FLAME_ARMOR, flame ? 2.0 * plating : 0.0, AttributeModifier.Operation.ADD_VALUE);
		if (flame) {
			player.level().sendParticles(ParticleTypes.FLAME, player.getX(), player.getY() + 1.3, player.getZ(), 4, 0.25, 0.2, 0.25, 0.01);
		}
	}

	private static void modifier(Player player, Holder<Attribute> attribute, Identifier id, double amount, AttributeModifier.Operation operation) {
		AttributeInstance instance = player.getAttribute(attribute);
		if (instance == null) {
			return;
		}
		AttributeModifier current = instance.getModifier(id);
		if (amount == 0.0) {
			if (current != null) {
				instance.removeModifier(id);
			}
			return;
		}
		if (current == null || current.amount() != amount) {
			instance.addOrUpdateTransientModifier(new AttributeModifier(id, amount, operation));
		}
	}

	// ---------- C key ----------

	/** The player pressed C (sneak = Coup de Vent). */
	public static void use(ServerPlayer player, boolean sneaking) {
		CyborgData data = get(player);
		CyborgUpgrade move = sneaking ? CyborgUpgrade.COUP_DE_VENT : CyborgUpgrade.RADICAL_BEAM;
		int tier = data.tier(move);
		if (tier == 0) {
			if (data.any()) {
				player.sendOverlayMessage(Component.literal("No " + move.title + " module installed.").withStyle(ChatFormatting.GRAY));
			}
			return;
		}
		long now = player.level().getGameTime();
		long ready = READY_AT.getOrDefault(player.getUUID(), 0L);
		if (now < ready) {
			player.sendOverlayMessage(Component.literal(String.format("Recharging... %.1f s", (ready - now) / 20.0)).withStyle(ChatFormatting.GRAY));
			return;
		}
		int fuel = sneaking ? VENT_FUEL : BEAM_FUEL;
		if (data.fuel() < fuel && !player.isCreative()) {
			player.sendOverlayMessage(Component.literal(data.tank() == 0 ? "No Cola Engine to power it!"
					: "Out of Cola! (" + fuelText(data) + ")").withStyle(ChatFormatting.RED));
			player.level().playSound(null, player.blockPosition(), SoundEvents.DISPENSER_FAIL, SoundSource.PLAYERS, 0.8f, 1.0f);
			return;
		}
		if (sneaking) {
			coupDeVent(player, tier);
			READY_AT.put(player.getUUID(), now + 120 - 20L * tier);
		} else {
			radicalBeam(player, tier);
			READY_AT.put(player.getUUID(), now + 180 - 20L * tier);
		}
		if (!player.isCreative()) {
			set(player, get(player).withFuel(data.fuel() - fuel));
		}
		player.sendOverlayMessage(Component.literal(move.title + "! Cola: " + fuelText(get(player))).withStyle(ChatFormatting.AQUA));
	}

	/** Radical Beam: a laser from the chest, straight where you look. Stops at walls; never breaks blocks. */
	private static void radicalBeam(ServerPlayer player, int tier) {
		ServerLevel level = player.level();
		double range = 20 + 6 * tier;
		float damage = 8 + 4 * tier;
		Vec3 eye = player.getEyePosition();
		Vec3 direction = player.getLookAngle();
		Vec3 end = eye;
		LivingEntity hit = null;
		for (double d = 0.5; d <= range; d += 0.5) {
			Vec3 point = eye.add(direction.scale(d));
			BlockPos pos = BlockPos.containing(point);
			if (!level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) {
				break;
			}
			end = point;
			List<LivingEntity> found = level.getEntitiesOfClass(LivingEntity.class, new AABB(point, point).inflate(0.5),
					e -> validTarget(player, e));
			if (!found.isEmpty()) {
				hit = found.get(0);
				break;
			}
		}
		com.onepiecemod.anim.CombatAnims.play(player, com.onepiecemod.anim.Anim.POINT);
		Vec3 start = MoveFx.hand(player); // Drawn from the hand, so the beam doesn't fill your own screen.
		MoveFx.spawn(level, MoveFx.LASER.style(), start, end.subtract(start), MoveFx.LASER.color(), MoveFx.LASER.color2(),
				0.5f + 0.15f * tier, 10, player, null);
		level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.2f, 2.0f);
		level.playSound(null, end.x, end.y, end.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.6f, 1.5f);
		level.sendParticles(ParticleTypes.EXPLOSION, end.x, end.y, end.z, 1, 0, 0, 0, 0);
		if (hit != null) {
			hit.hurtServer(level, player.damageSources().playerAttack(player), damage);
			hit.igniteForSeconds(2 + tier);
		}
		// The blast where it lands catches anyone right next to it.
		for (LivingEntity near : level.getEntitiesOfClass(LivingEntity.class, new AABB(end, end).inflate(1.8),
				e -> e != null && validTarget(player, e))) {
			if (near != hit) {
				near.hurtServer(level, player.damageSources().playerAttack(player), damage * 0.4f);
			}
		}
	}

	/** Coup de Vent: a blast of compressed air from the arms. Look down to launch yourself up instead. */
	private static void coupDeVent(ServerPlayer player, int tier) {
		ServerLevel level = player.level();
		Vec3 look = player.getLookAngle();
		com.onepiecemod.anim.CombatAnims.play(player, com.onepiecemod.anim.Anim.PUNCH);
		level.playSound(null, player.blockPosition(), SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.PLAYERS, 1.2f, 0.7f);
		if (tier >= 2 && player.getXRot() > 55) {
			// Franky's "Coup de Boo": blast the ground and fly up.
			player.setDeltaMovement(player.getDeltaMovement().x, 0.8 + 0.3 * tier, player.getDeltaMovement().z);
			Motion.sync(player);
			player.resetFallDistance();
			level.sendParticles(ParticleTypes.GUST_EMITTER_SMALL, player.getX(), player.getY(), player.getZ(), 1, 0, 0, 0, 0);
			level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY(), player.getZ(), 20, 0.6, 0.1, 0.6, 0.05);
			return;
		}
		double reach = 5 + tier;
		Vec3 eye = player.getEyePosition();
		for (int i = 1; i <= reach; i++) {
			Vec3 p = eye.add(look.scale(i));
			level.sendParticles(ParticleTypes.GUST, p.x, p.y, p.z, 1, 0.1 * i, 0.1 * i, 0.1 * i, 0);
		}
		for (LivingEntity victim : level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(reach),
				e -> validTarget(player, e))) {
			Vec3 to = victim.position().add(0, victim.getBbHeight() / 2, 0).subtract(eye);
			if (to.length() > reach || to.normalize().dot(look) < 0.6) {
				continue;
			}
			victim.hurtServer(level, player.damageSources().playerAttack(player), 2.0f * tier + 2);
			Vec3 push = to.normalize().scale(1.2 + 0.5 * tier);
			victim.setDeltaMovement(victim.getDeltaMovement().add(push.x, 0.35 + 0.1 * tier, push.z));
			Motion.sync(victim);
		}
	}

	/** Same rules as Devil Fruit moves: not you, not Creative players, not your pets, crew or allies. */
	private static boolean validTarget(ServerPlayer player, LivingEntity entity) {
		if (entity == player || !entity.isAlive()) {
			return false;
		}
		if (entity instanceof Player other && (other.isCreative() || other.isSpectator())) {
			return false;
		}
		if (entity instanceof TamableAnimal pet && pet.isOwnedBy(player)) {
			return false;
		}
		return !PlayerCrews.friendly(player.level().getServer(), player, entity);
	}
}
