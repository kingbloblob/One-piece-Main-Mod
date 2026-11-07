package com.onepiecemod.career;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.levelgen.Heightmap;

import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.bounty.EventBosses;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.shipcombat.SeaPirateEntity;
import com.onepiecemod.shipcombat.ShipCombatFeature;

/**
 * Who shows up for the careers, and where: the squads for orders, ambushes and backup.
 * The kit ids are NPC kits from npc_kits.json; "rev_*" means a Revolutionary soldier dressed by this package.
 */
final class CareerSquads {
	private CareerSquads() {
	}

	/** A pirate crew for a Marine to bring in, toughest first. tier = the Marine's rank (0-10). */
	static List<String> pirateCrew(int tier, int size) {
		String leader = tier < 2 ? "pirate" : "pirate_captain";
		List<String> crew = tier < 2 ? List.of("rookie_pirate", "rookie_pirate", "pirate")
				: tier < 5 ? List.of("pirate", "pirate_gunner", "pirate", "fishman")
				: tier < 8 ? List.of("baroque_agent", "donquixote", "fishman", "pirate_gunner")
				: List.of("gifter", "headliner", "blackbeard_pirate", "donquixote");
		return squad(leader, crew, size);
	}

	/** A Navy garrison for a Revolutionary to drive out. tier = the Revolutionary's rank (0-7). */
	static List<String> navyGarrison(int tier, int size) {
		String leader = tier < 2 ? "marine" : tier < 4 ? "marine_officer" : tier < 6 ? "elite_marine" : "vice_admiral";
		List<String> crew = tier < 2 ? List.of("marine_recruit", "marine", "marine_rifle")
				: tier < 4 ? List.of("marine", "marine_rifle", "marine")
				: tier < 6 ? List.of("marine_officer", "marine_rifle", "cp_agent")
				: List.of("cp0_agent", "marine_officer", "pacifista", "marine_rifle");
		return squad(leader, crew, size);
	}

	/** Backup soldiers for a player of this career and rank. */
	static List<String> backup(Career career, int rank, int size) {
		if (career == Career.MARINE) {
			String leader = rank < 3 ? "marine" : rank < 6 ? "marine_officer" : rank < 9 ? "elite_marine" : "vice_admiral";
			return squad(leader, List.of("marine", "marine_rifle", "marine"), size);
		}
		return squad(rank < 3 ? "rev_soldier" : "rev_officer", List.of("rev_soldier", "rev_gunner", "rev_soldier"), size);
	}

	private static List<String> squad(String leader, List<String> crew, int size) {
		List<String> kits = new ArrayList<>();
		kits.add(leader);
		for (int i = 1; i < size; i++) {
			kits.add(crew.get((i - 1) % crew.size()));
		}
		return kits;
	}

	/** Makes one enemy NPC from a kit (Marine kits become onepiece:marine, the rest onepiece:sea_pirate). */
	static HumanNpc enemy(ServerLevel level, String kit, double toughness) {
		HumanNpc npc = com.onepiecemod.npc.NpcKit.get(kit) != null && "marine".equals(com.onepiecemod.npc.NpcKit.get(kit).faction)
				? BountyFeature.MARINE.create(level, EntitySpawnReason.EVENT)
				: ShipCombatFeature.SEA_PIRATE.create(level, EntitySpawnReason.EVENT);
		if (npc == null) {
			return null;
		}
		npc.applyKit(kit, level.getRandom());
		if (toughness > 1.0) {
			npc.getAttribute(Attributes.MAX_HEALTH).setBaseValue(npc.getMaxHealth() * toughness);
			npc.setHealth(npc.getMaxHealth());
		}
		return npc;
	}

	/** Makes one backup soldier for this player. */
	static CareerAllyEntity ally(ServerLevel level, ServerPlayer owner, Career career, String kit, int rank) {
		CareerAllyEntity ally = CareerFeature.CAREER_ALLY.create(level, EntitySpawnReason.EVENT);
		if (ally == null) {
			return null;
		}
		RandomSource random = level.getRandom();
		boolean marine = career == Career.MARINE;
		ally.setup(owner, marine);
		if (marine) {
			ally.applyKit(kit, random);
		} else {
			// Revolutionaries borrow a pirate kit's weapons and fighting styles, then get their own look and name.
			boolean officer = kit.equals("rev_officer");
			ally.applyKit(officer ? "pirate_captain" : kit.equals("rev_gunner") ? "pirate_gunner" : "pirate", random);
			ally.setCareerSkin((officer ? "rev_officer_" + random.nextInt(REV_OFFICER_SKINS) : "rev_soldier_" + random.nextInt(REV_SOLDIER_SKINS)));
			ally.setCustomName(Component.literal((officer ? "Revolutionary Officer " : "Revolutionary ")
					+ com.onepiecemod.npc.NpcNames.surname(random)));
		}
		// Higher ranks get tougher backup.
		double toughness = 1.0 + 0.1 * rank;
		ally.getAttribute(Attributes.MAX_HEALTH).setBaseValue(ally.getMaxHealth() * toughness);
		ally.setHealth(ally.getMaxHealth());
		return ally;
	}

	/** How many skins tools/careers/gen_career_skins.py paints for each Revolutionary group. */
	static final int REV_SOLDIER_SKINS = 12;
	static final int REV_OFFICER_SKINS = 6;

	/** Puts a spawned enemy into the world: it goes after the player and is cleaned up if it ever unloads. */
	static void place(ServerLevel level, HumanNpc npc, BlockPos pos, ServerPlayer target, String tag) {
		npc.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, level.getRandom().nextFloat() * 360f, 0f);
		npc.addTag(tag);
		npc.setPersistenceRequired();
		EventBosses.markUntilUnloaded(npc);
		if (npc instanceof MarineEntity marine) {
			marine.setHunted(target);
		} else {
			npc.setTarget(target);
		}
		level.addFreshEntity(npc);
	}

	/** A dry, open spot on the ground between min and max blocks from the player, or null. */
	static BlockPos spotNear(ServerLevel level, BlockPos center, int min, int max) {
		RandomSource random = level.getRandom();
		for (int attempt = 0; attempt < 16; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			int distance = min + (max > min ? random.nextInt(max - min + 1) : 0);
			int x = (int) Math.floor(center.getX() + Math.cos(angle) * distance);
			int z = (int) Math.floor(center.getZ() + Math.sin(angle) * distance);
			BlockPos pos = dryGround(level, x, z);
			if (pos != null && Math.abs(pos.getY() - center.getY()) < 24) {
				return pos;
			}
		}
		return null;
	}

	/** The surface at x, z if it is dry, solid ground with room to stand, else null. */
	static BlockPos dryGround(ServerLevel level, int x, int z) {
		if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
			return null;
		}
		BlockPos pos = surface(level, x, z);
		boolean dry = level.getFluidState(pos).isEmpty() && level.getFluidState(pos.below()).isEmpty()
				&& level.getBlockState(pos.below()).isSolid() && level.getBlockState(pos.above()).isAir();
		return dry ? pos : null;
	}

	static BlockPos surface(ServerLevel level, int x, int z) {
		return new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
	}

	/** Is this NPC a pirate (for a Marine to hunt)? */
	static boolean isPirate(Object entity) {
		return entity instanceof SeaPirateEntity || entity instanceof com.onepiecemod.empire.PirateGuardEntity
				|| entity instanceof com.onepiecemod.bounty.BountyHunterEntity;
	}
}
