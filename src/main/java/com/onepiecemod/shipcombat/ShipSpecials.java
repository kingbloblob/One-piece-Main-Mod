package com.onepiecemod.shipcombat;

import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.deco.DecoBlocks;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipLayout;

/**
 * The Thousand Sunny's special moves, for any ship with a Cola Engine aboard. The captain uses them:
 *  - Coup de Burst (I): the engine blasts the whole ship out of the sea and through the air, about 80 blocks.
 *    Great for escaping, crossing a reef or jumping over a Marine blockade. Burns 1 Cola Crate.
 *  - Gaon Cannon (N): needs the Sunny's lion figurehead at the bow too. After a short charge the lion fires a huge
 *    beam straight ahead that tears through ships in its path. Burns 3 Cola Crates.
 */
public class ShipSpecials {
	private static final int BURST_COLA = 1;
	private static final int BURST_COOLDOWN = 20 * 30;
	private static final int GAON_COLA = 3;
	private static final int GAON_COOLDOWN = 20 * 60;
	private static final int GAON_CHARGE = 30;
	private static final double GAON_RANGE = 96;
	private static final float GAON_SHIP_DAMAGE = 180f;
	private static final float GAON_ENTITY_DAMAGE = 30f;

	private static final Map<ShipEntity, Long> BURST_READY = new WeakHashMap<>();
	private static final Map<ShipEntity, Long> GAON_READY = new WeakHashMap<>();
	/** Gaon Cannons charging: the ship, when it fires, and who gave the order. */
	private static final Map<ShipEntity, Charge> CHARGING = new WeakHashMap<>();

	private record Charge(long fireAt, ServerPlayer captain) {
	}

	static void use(ServerPlayer player, boolean gaon) {
		ShipEntity ship = ShipEntity.aboard(player);
		if (ship == null || ship.sinking) {
			return;
		}
		if (ship.getControllingPassenger() != player) {
			player.sendOverlayMessage(Component.literal("Only the captain at the wheel can give that order.").withStyle(ChatFormatting.YELLOW));
			return;
		}
		if (!has(ship.getLayout(), ShipFeature.COLA_ENGINE)) {
			player.sendOverlayMessage(Component.literal("This ship has no Cola Engine. Build one at a Shipwright's Bench and put it aboard.")
					.withStyle(ChatFormatting.YELLOW));
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		if (gaon) {
			gaon(player, ship, level, now);
		} else {
			burst(player, ship, level, now);
		}
	}

	private static void burst(ServerPlayer player, ShipEntity ship, ServerLevel level, long now) {
		if (now < BURST_READY.getOrDefault(ship, 0L)) {
			player.sendOverlayMessage(Component.literal("The Cola Engine is still cooling down (" + (BURST_READY.get(ship) - now) / 20 + " s).")
					.withStyle(ChatFormatting.GRAY));
			return;
		}
		if (!payCola(player, BURST_COLA)) {
			return;
		}
		BURST_READY.put(ship, now + BURST_COOLDOWN);
		ship.coupDeBurst();
		// The blast from the stern.
		float yaw = ship.getYRot() * Mth.DEG_TO_RAD;
		Vec3 back = new Vec3(Mth.sin(yaw), 0, -Mth.cos(yaw)).scale(ship.getBbWidth() * 0.4);
		Vec3 stern = ship.position().add(back).add(0, ship.getLayout().waterline + 1, 0);
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, stern.x, stern.y, stern.z, 1, 0, 0, 0, 0);
		level.sendParticles(ParticleTypes.CLOUD, stern.x, stern.y, stern.z, 60, 2, 1, 2, 0.3);
		level.sendParticles(ParticleTypes.SPLASH, ship.getX(), ship.getY() + ship.getLayout().waterline, ship.getZ(), 120, 4, 0.5, 4, 0.5);
		level.playSound(null, BlockPos.containing(stern), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.NEUTRAL, 4.0f, 0.6f);
		level.playSound(null, BlockPos.containing(stern), SoundEvents.FIREWORK_ROCKET_LARGE_BLAST, SoundSource.NEUTRAL, 4.0f, 0.5f);
		for (ServerPlayer crew : ShipEntity.playersAboard(ship)) {
			crew.sendSystemMessage(Component.literal("COUP DE BURST!").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		}
	}

	private static void gaon(ServerPlayer player, ShipEntity ship, ServerLevel level, long now) {
		if (!has(ship.getLayout(), ShipFeature.FIGUREHEAD_SUNNY)) {
			player.sendOverlayMessage(Component.literal("The Gaon Cannon fires from the Sunny's lion: put a Sunny Figurehead at your bow.")
					.withStyle(ChatFormatting.YELLOW));
			return;
		}
		if (CHARGING.containsKey(ship)) {
			return;
		}
		if (now < GAON_READY.getOrDefault(ship, 0L)) {
			player.sendOverlayMessage(Component.literal("The Gaon Cannon is still cooling down (" + (GAON_READY.get(ship) - now) / 20 + " s).")
					.withStyle(ChatFormatting.GRAY));
			return;
		}
		if (!payCola(player, GAON_COLA)) {
			return;
		}
		GAON_READY.put(ship, now + GAON_COOLDOWN);
		CHARGING.put(ship, new Charge(now + GAON_CHARGE, player));
		level.playSound(null, ship.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.NEUTRAL, 4.0f, 0.5f);
		for (ServerPlayer crew : ShipEntity.playersAboard(ship)) {
			crew.sendSystemMessage(Component.literal("Gaon Cannon... charging!").withStyle(ChatFormatting.AQUA));
		}
	}

	/** Every tick: charging Gaon Cannons glow, then fire. */
	static void tick(MinecraftServer server) {
		Iterator<Map.Entry<ShipEntity, Charge>> it = CHARGING.entrySet().iterator();
		while (it.hasNext()) {
			Map.Entry<ShipEntity, Charge> entry = it.next();
			ShipEntity ship = entry.getKey();
			if (ship.isRemoved() || ship.sinking || !(ship.level() instanceof ServerLevel level)) {
				it.remove();
				continue;
			}
			Vec3 mouth = mouth(ship);
			if (mouth == null) {
				it.remove();
				continue;
			}
			long left = entry.getValue().fireAt() - level.getGameTime();
			if (left > 0) {
				level.sendParticles(ParticleTypes.END_ROD, mouth.x, mouth.y, mouth.z, 4, 0.6, 0.6, 0.6, 0.05);
				level.sendParticles(ParticleTypes.ELECTRIC_SPARK, mouth.x, mouth.y, mouth.z, 3, 0.4, 0.4, 0.4, 0.1);
				continue;
			}
			it.remove();
			fireGaon(level, ship, mouth, entry.getValue().captain());
		}
	}

	private static void fireGaon(ServerLevel level, ShipEntity ship, Vec3 mouth, ServerPlayer captain) {
		float yaw = ship.getYRot() * Mth.DEG_TO_RAD;
		Vec3 ahead = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		Set<ShipEntity> hitShips = new HashSet<>();
		Set<LivingEntity> hitPeople = new HashSet<>();
		AABB reach = new AABB(mouth, mouth.add(ahead.scale(GAON_RANGE))).inflate(40, 16, 40);
		var ships = level.getEntitiesOfClass(ShipEntity.class, reach, other -> other != ship && !other.sinking);
		double end = GAON_RANGE;
		for (double d = 1; d <= GAON_RANGE; d += 0.5) {
			Vec3 at = mouth.add(ahead.scale(d));
			BlockState state = level.getBlockState(BlockPos.containing(at));
			if (!state.canBeReplaced() && !state.getCollisionShape(level, BlockPos.containing(at)).isEmpty()) {
				end = d; // The beam hits land and bursts there (no blocks are broken).
				break;
			}
			for (ShipEntity other : ships) {
				if (!hitShips.contains(other) && (other.blockAt(at) || other.blockAt(at.add(0, -1, 0)) || other.blockAt(at.add(0, 1, 0)))) {
					hitShips.add(other);
					ShipHull.damage(other, GAON_SHIP_DAMAGE, captain, at, ship);
				}
			}
			if (((int) (d * 2)) % 4 == 0) {
				hitPeople.addAll(level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(1.5),
						victim -> victim != captain && ShipEntity.aboard(victim) != ship));
				level.sendParticles(ParticleTypes.SONIC_BOOM, at.x, at.y, at.z, 1, 0, 0, 0, 0);
			}
			level.sendParticles(ParticleTypes.END_ROD, at.x, at.y, at.z, 2, 0.3, 0.3, 0.3, 0.02);
		}
		for (LivingEntity victim : hitPeople) {
			victim.hurtServer(level, level.damageSources().indirectMagic(captain, captain), GAON_ENTITY_DAMAGE);
		}
		Vec3 last = mouth.add(ahead.scale(end));
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, last.x, last.y, last.z, 1, 0, 0, 0, 0);
		level.playSound(null, BlockPos.containing(mouth), SoundEvents.WARDEN_SONIC_BOOM, SoundSource.NEUTRAL, 6.0f, 0.5f);
		level.playSound(null, BlockPos.containing(last), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.NEUTRAL, 6.0f, 0.7f);
		for (ServerPlayer crew : ShipEntity.playersAboard(ship)) {
			crew.sendSystemMessage(Component.literal("GAON CANNON!").withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD));
		}
		if (captain != null && !hitShips.isEmpty()) {
			captain.sendOverlayMessage(Component.literal("Direct hit on " + hitShips.size() + (hitShips.size() == 1 ? " ship!" : " ships!"))
					.withStyle(ChatFormatting.GOLD));
		}
	}

	/** Where the beam comes out: the front of the lion figurehead furthest toward the bow. */
	private static Vec3 mouth(ShipEntity ship) {
		ShipLayout layout = ship.getLayout();
		Vec3 best = null;
		double bestAhead = -Double.MAX_VALUE;
		for (ShipLayout.ShipBlock block : layout.blocks) {
			if (block.state().is(ShipFeature.FIGUREHEAD_SUNNY)) {
				double ahead = block.pos().getX() * layout.bow.getStepX() + block.pos().getZ() * layout.bow.getStepZ();
				if (ahead > bestAhead) {
					bestAhead = ahead;
					best = new Vec3(block.pos().getX() + layout.bow.getStepX(), block.pos().getY() + 0.5, block.pos().getZ() + layout.bow.getStepZ());
				}
			}
		}
		return best == null ? null : ship.position().add(ship.rotate(best, 1.0f));
	}

	private static boolean has(ShipLayout layout, net.minecraft.world.level.block.Block block) {
		for (ShipLayout.ShipBlock entry : layout.blocks) {
			if (entry.state().is(block)) {
				return true;
			}
		}
		return false;
	}

	/** Takes Cola Crates from the captain's pack (free in creative). False, with a message, if there aren't enough. */
	private static boolean payCola(ServerPlayer player, int crates) {
		if (player.isCreative()) {
			return true;
		}
		Item cola = DecoBlocks.COLA_CRATE.asItem();
		if (Cannons.countAmmo(player.getInventory(), cola) < crates) {
			player.sendOverlayMessage(Component.literal("Not enough cola! This needs " + crates + " Cola Crate" + (crates == 1 ? "" : "s") + ".")
					.withStyle(ChatFormatting.RED));
			return false;
		}
		int left = crates;
		for (int slot = 0; slot < player.getInventory().getContainerSize() && left > 0; slot++) {
			var stack = player.getInventory().getItem(slot);
			if (stack.is(cola)) {
				int take = Math.min(left, stack.getCount());
				stack.shrink(take);
				left -= take;
			}
		}
		return true;
	}
}
