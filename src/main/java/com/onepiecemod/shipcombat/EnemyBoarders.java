package com.onepiecemod.shipcombat;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.bounty.MarineRank;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.sound.WorldSounds;

/**
 * Enemies board YOU. When a Marine or pirate ship (tier 1 and up) is hunting your ship, sails within GRAPPLE_RANGE
 * and your hull is below half, she may throw grappling lines and send a boarding party swinging onto your deck.
 * Fight them off (with your crew's help) before they overrun the ship: beat every boarder and everyone aboard gets
 * berries. Keeping your hull above half keeps them off: cannon them first, or patch up with planks.
 */
public class EnemyBoarders {
	/** Tag on every boarder, so the mod can tell them apart from other Marines and pirates. */
	public static final String TAG = "onepiece_boarder";

	private static final double GRAPPLE_RANGE = 36;
	private static final float BOARD_BELOW = 0.5f;
	private static final float CHANCE = 0.2f;               // per second, once everything else fits
	private static final int COOLDOWN = 20 * 45;            // ticks before the same enemy ship sends another party
	private static final int MAX_ON_DECK = 6;
	private static final int GIVE_UP_TICKS = 20 * 60 * 4;

	private record Raid(ServerLevel level, ShipEntity target, String from, List<UUID> boarders, int tier, long started) {
	}

	private static final List<Raid> RAIDS = new ArrayList<>();
	private static final Map<ShipEntity, Long> NEXT_PARTY = new WeakHashMap<>();

	/** Once a second (from ShipCombat). */
	static void tick(MinecraftServer server) {
		for (ShipEntity ship : ShipCombat.loadedShips()) {
			ShipBrain brain = ShipBrain.of(ship);
			if (brain == null || brain.tier < 1 || ship.sinking || ship.isRemoved() || !(ship.level() instanceof ServerLevel level)) {
				continue;
			}
			ShipEntity target = brain.target(level);
			if (target == null || ShipBrain.isAi(target) || ship.distanceTo(target) > GRAPPLE_RANGE
					|| ShipHull.get(target) > ShipHull.max(target) * BOARD_BELOW) {
				continue;
			}
			long now = level.getGameTime();
			if (now < NEXT_PARTY.getOrDefault(ship, 0L) || level.getRandom().nextFloat() >= CHANCE) {
				continue;
			}
			List<ServerPlayer> defenders = new ArrayList<>();
			for (ServerPlayer player : ShipEntity.playersAboard(target)) {
				if (!player.isCreative() && !player.isSpectator()) {
					defenders.add(player);
				}
			}
			if (defenders.isEmpty() || boardersOn(target) >= MAX_ON_DECK) {
				continue;
			}
			NEXT_PARTY.put(ship, now + COOLDOWN);
			sendParty(level, ship, brain, target, defenders);
		}

		Iterator<Raid> it = RAIDS.iterator();
		while (it.hasNext()) {
			Raid raid = it.next();
			if (raid.target().isRemoved() || raid.target().sinking || raid.level().getGameTime() - raid.started() > GIVE_UP_TICKS) {
				it.remove();
				continue;
			}
			if (alive(raid) == 0) {
				repelled(raid);
				it.remove();
			}
		}
	}

	private static void sendParty(ServerLevel level, ShipEntity from, ShipBrain brain, ShipEntity target, List<ServerPlayer> defenders) {
		List<Vec3> deck = target.seatPositions();
		if (deck.isEmpty()) {
			return;
		}
		int size = Math.min(4, 2 + brain.tier / 2);
		List<UUID> party = new ArrayList<>();
		Vec3 start = from.position().add(0, from.getLayout().waterline + 2, 0);
		for (int i = 0; i < size; i++) {
			Mob boarder = brain.faction == ShipBrain.Faction.MARINE ? marine(level, defenders.get(0), brain.tier) : pirate(level, brain.tier);
			if (boarder == null) {
				continue;
			}
			// Land at the back of the deck, away from the wheel, spread out.
			Vec3 spot = deck.get(deck.size() - 1 - (i % deck.size()));
			boarder.snapTo(spot.x, spot.y + 0.05, spot.z, level.getRandom().nextFloat() * 360f, 0);
			boarder.setTarget(defenders.get(i % defenders.size()));
			boarder.addTag(TAG);
			level.addFreshEntity(boarder);
			party.add(boarder.getUUID());
			// A line of puffs where the grappling rope swung across.
			Vec3 line = spot.subtract(start);
			for (int step = 1; step < 8; step++) {
				Vec3 p = start.add(line.scale(step / 8.0)).add(0, Math.sin(Math.PI * step / 8.0) * 3, 0);
				level.sendParticles(ParticleTypes.CLOUD, p.x, p.y, p.z, 1, 0, 0, 0, 0);
			}
		}
		if (party.isEmpty()) {
			return;
		}
		level.playSound(null, target.blockPosition(), WorldSounds.BOARDING, SoundSource.HOSTILE, 1.5f, 1.1f);
		String name = from.getName().getString();
		for (ServerPlayer player : defenders) {
			player.sendSystemMessage(Component.literal("Boarders from the " + name + "! Repel them before they take the ship!")
					.withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
		}
		RAIDS.add(new Raid(level, target, name, party, brain.tier, level.getGameTime()));
	}

	private static int boardersOn(ShipEntity target) {
		int count = 0;
		for (Raid raid : RAIDS) {
			if (raid.target() == target) {
				count += alive(raid);
			}
		}
		return count;
	}

	private static int alive(Raid raid) {
		int alive = 0;
		for (UUID id : raid.boarders()) {
			Entity boarder = raid.level().getEntity(id);
			if (boarder != null && boarder.isAlive()) {
				alive++;
			}
		}
		return alive;
	}

	private static void repelled(Raid raid) {
		for (ServerPlayer player : ShipEntity.playersAboard(raid.target())) {
			com.onepiecemod.advancement.AdvancementFeature.grant(player, "journey/repel_boarders");
			player.sendSystemMessage(Component.literal("Boarders repelled! The " + raid.from() + "'s men are beaten.").withStyle(ChatFormatting.GOLD));
			raid.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8f, 1.2f);
			ItemStack berries = new ItemStack(CharacterFeature.BERRY, 4 + raid.tier() * 2);
			if (!player.getInventory().add(berries)) {
				player.spawnAtLocation(raid.level(), berries);
			}
		}
	}

	private static Mob marine(ServerLevel level, ServerPlayer hunted, int tier) {
		MarineEntity marine = BountyFeature.MARINE.create(level, EntitySpawnReason.EVENT);
		if (marine == null) {
			return null;
		}
		marine.setRank(tier >= 3 && level.getRandom().nextInt(3) == 0 ? MarineRank.LIEUTENANT
				: level.getRandom().nextBoolean() ? MarineRank.RIFLEMAN : MarineRank.RECRUIT);
		marine.setHunted(hunted);
		return marine;
	}

	private static Mob pirate(ServerLevel level, int tier) {
		SeaPirateEntity pirate = ShipCombatFeature.SEA_PIRATE.create(level, EntitySpawnReason.EVENT);
		if (pirate == null) {
			return null;
		}
		pirate.setup(false, tier, level.getRandom());
		return pirate;
	}
}
