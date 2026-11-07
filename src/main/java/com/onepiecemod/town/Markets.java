package com.onepiecemod.town;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.phys.AABB;

/**
 * Port markets. In market towns (Loguetown, Nanohana, Water 7, the Flower Capital...) the merchants set up around the
 * plaza from 7 am to 3 pm, hold up their wares and call out to anyone walking by. What they sell changes every day.
 *
 * Every few days a merchant ship from a far-off sea docks and a Foreign Trader sells rare goods (Log Poses, Dials,
 * Sea King scales...) until the market closes, then sails away again.
 */
public class Markets {
	public static final int OPEN = 1000;
	public static final int CLOSE = 9000;
	private static final List<String> SEAS = List.of("the North Blue", "the South Blue", "the West Blue", "the New World",
			"a Sky Island", "Fish-Man Island", "Wano", "the Red Line");

	public static boolean isOpen(ServerLevel level) {
		long time = level.getOverworldClockTime() % 24000L;
		return time >= OPEN && time < CLOSE;
	}

	/** Every third day or so (different for each town) a foreign ship comes in. */
	public static boolean shipDay(Town town) {
		long day = town.level.getOverworldClockTime() / 24000L;
		return Math.floorMod(day + town.key.hashCode(), 3) == 0;
	}

	static void tick(Town town, ServerLevel level, long gameTime) {
		if (!town.def.market || !town.scanned || gameTime % 20 != 0) {
			return;
		}
		AABB area = new AABB(town.plaza).inflate(48, 16, 48);
		List<TownsfolkEntity> people = level.getEntitiesOfClass(TownsfolkEntity.class, area, t -> t.townKey().equals(town.key));
		boolean open = isOpen(level);
		TownsfolkEntity trader = null;
		for (TownsfolkEntity person : people) {
			if (person.isVisitor()) {
				trader = person;
			}
		}
		if (!open) {
			if (trader != null) {
				sailAway(trader, level);
			}
			return;
		}
		if (trader == null && shipDay(town) && level.getRandom().nextInt(10) == 0) {
			arrive(town, level);
		}
		// Sellers at their stalls call out to players who walk by.
		for (TownsfolkEntity seller : people) {
			if (!(seller.job().marketer || seller.isVisitor()) || seller.isTrading() || !seller.readyToTalk()) {
				continue;
			}
			ServerPlayer near = (ServerPlayer) level.getNearestPlayer(seller, 8.0);
			if (near != null && !near.isSpectator() && level.getRandom().nextInt(6) == 0) {
				List<String> calls = seller.job().calls;
				if (!calls.isEmpty()) {
					seller.getLookControl().setLookAt(near);
					seller.shout(calls.get(level.getRandom().nextInt(calls.size())), 10);
					seller.didTalk(20 * 40);
				}
			}
		}
	}

	/** A Foreign Trader steps off a ship at the docks (or the plaza if the town has no docks). Returns null if there's no room. */
	public static TownsfolkEntity arrive(Town town, ServerLevel level) {
		BlockPos spot = !town.docks.isEmpty() ? town.docks.get(level.getRandom().nextInt(town.docks.size()))
				: town.marketSpots.get(level.getRandom().nextInt(town.marketSpots.size()));
		TownsfolkEntity trader = TownFeature.TOWNSFOLK.create(level, EntitySpawnReason.EVENT);
		if (trader == null) {
			return null;
		}
		trader.snapTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, level.getRandom().nextFloat() * 360f, 0);
		trader.settle(town, "foreign_trader", town.marketSpots.size() - 1, spot, level.getRandom());
		trader.makeVisitor();
		trader.holdWares();
		level.addFreshEntity(trader);
		String sea = SEAS.get(level.getRandom().nextInt(SEAS.size()));
		Component news = Component.literal("[" + town.name() + "] ").withStyle(ChatFormatting.AQUA)
				.append(Component.literal("A merchant ship from " + sea + " has docked! " + trader.shortName()
						+ " is selling rare goods at the market until it closes.").withStyle(ChatFormatting.GOLD));
		for (ServerPlayer player : level.players()) {
			if (player.blockPosition().closerThan(town.plaza, 128)) {
				player.sendSystemMessage(news);
			}
		}
		return trader;
	}

	private static void sailAway(TownsfolkEntity trader, ServerLevel level) {
		if (trader.isTrading()) {
			return;
		}
		level.sendParticles(ParticleTypes.CLOUD, trader.getX(), trader.getY() + 1, trader.getZ(), 12, 0.3, 0.5, 0.3, 0.02);
		trader.shout("The tide's turning. Off to the next island! Farewell!", 16);
		trader.discard();
	}
}
