package com.onepiecemod.hideout;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Every pirate hideout in the world, saved on the Overworld: one per captain.
 * The flag block itself holds the stash; this list is what the rest of the mod can read even while the
 * hideout's chunks are unloaded (where it is, how strong it is, what happened while the captain was away).
 */
public final class Hideouts {
	/** How far the claim reaches from the flag (a circle, measured flat). */
	public static final int RADIUS = 32;
	/** Hideouts (and pirate kingdoms) must be at least this far apart. */
	public static final int SPACING = 96;

	/**
	 * One hideout.
	 * @param level       0..5, see {@link HideoutLevels}
	 * @param defence     defence rating from the last survey (used when the Navy attacks while the captain is away)
	 * @param threat      the captain's Navy threat level the last time they were online
	 * @param lastSiege   game time of the last Navy attack (or of the claim, so new hideouts get a quiet start)
	 * @param news        what happened while the captain was away, told to them next time they're online ("" = nothing)
	 * @param lossPercent share of the stash the Navy took while away, taken out when the flag next loads
	 * @param crates      Navy supply crates won while away, put in the stash when the flag next loads
	 */
	public record Hideout(BlockPos pos, String crewName, int level, int defence, int threat, long lastSiege,
			int held, int lost, String news, int lossPercent, int crates) {
		public static final Codec<Hideout> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				BlockPos.CODEC.fieldOf("pos").forGetter(Hideout::pos),
				Codec.STRING.optionalFieldOf("crew", "").forGetter(Hideout::crewName),
				Codec.INT.optionalFieldOf("level", 0).forGetter(Hideout::level),
				Codec.INT.optionalFieldOf("defence", 0).forGetter(Hideout::defence),
				Codec.INT.optionalFieldOf("threat", 0).forGetter(Hideout::threat),
				Codec.LONG.optionalFieldOf("last_siege", 0L).forGetter(Hideout::lastSiege),
				Codec.INT.optionalFieldOf("held", 0).forGetter(Hideout::held),
				Codec.INT.optionalFieldOf("lost", 0).forGetter(Hideout::lost),
				Codec.STRING.optionalFieldOf("news", "").forGetter(Hideout::news),
				Codec.INT.optionalFieldOf("loss_percent", 0).forGetter(Hideout::lossPercent),
				Codec.INT.optionalFieldOf("crates", 0).forGetter(Hideout::crates)
		).apply(instance, Hideout::new));

		public Hideout withStats(String crew, int newLevel, int newDefence) {
			return new Hideout(pos, crew, newLevel, newDefence, threat, lastSiege, held, lost, news, lossPercent, crates);
		}

		public Hideout withThreat(int newThreat) {
			return new Hideout(pos, crewName, level, defence, newThreat, lastSiege, held, lost, news, lossPercent, crates);
		}

		public Hideout siegeDone(long time, boolean won, String newNews, int loss, int newCrates) {
			String joined = news.isEmpty() ? newNews : newNews.isEmpty() ? news : news + "\n" + newNews;
			return new Hideout(pos, crewName, level, defence, threat, time, held + (won ? 1 : 0), lost + (won ? 0 : 1),
					joined, Math.min(75, lossPercent + loss), crates + newCrates);
		}

		public Hideout newsTold() {
			return new Hideout(pos, crewName, level, defence, threat, lastSiege, held, lost, "", lossPercent, crates);
		}

		public Hideout pendingApplied() {
			return new Hideout(pos, crewName, level, defence, threat, lastSiege, held, lost, news, 0, 0);
		}

		public boolean contains(Vec3 at) {
			double dx = at.x - (pos.getX() + 0.5);
			double dz = at.z - (pos.getZ() + 0.5);
			return dx * dx + dz * dz <= RADIUS * RADIUS && Math.abs(at.y - pos.getY()) < 40;
		}
	}

	public static final AttachmentType<Map<String, Hideout>> HIDEOUTS = AttachmentRegistry.create(
			OnePieceMod.id("hideouts"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Hideout.CODEC)));

	private Hideouts() {
	}

	static void initialize() {
		// Touching the class registers the attachment.
	}

	public static Map<String, Hideout> all(MinecraftServer server) {
		return server.overworld().getAttachedOrElse(HIDEOUTS, Map.of());
	}

	/** The captain's hideout, or null. */
	public static Hideout of(MinecraftServer server, UUID captain) {
		return captain == null ? null : all(server).get(captain.toString());
	}

	public static void put(MinecraftServer server, UUID captain, Hideout hideout) {
		Map<String, Hideout> map = new HashMap<>(all(server));
		map.put(captain.toString(), hideout);
		server.overworld().setAttached(HIDEOUTS, map);
	}

	public static void remove(MinecraftServer server, UUID captain) {
		Map<String, Hideout> map = new HashMap<>(all(server));
		if (map.remove(captain.toString()) != null) {
			server.overworld().setAttached(HIDEOUTS, map);
		}
	}

	/** Whose hideout has its flag at this spot, or null. */
	public static UUID ownerAt(MinecraftServer server, BlockPos pos) {
		for (Map.Entry<String, Hideout> entry : all(server).entrySet()) {
			if (entry.getValue().pos().equals(pos)) {
				return UUID.fromString(entry.getKey());
			}
		}
		return null;
	}

	/** The captain whose claim this spot is in (Overworld only), or null. */
	public static UUID claimAt(ServerLevel level, Vec3 at) {
		if (level != level.getServer().overworld()) {
			return null;
		}
		for (Map.Entry<String, Hideout> entry : all(level.getServer()).entrySet()) {
			if (entry.getValue().contains(at)) {
				return UUID.fromString(entry.getKey());
			}
		}
		return null;
	}

	/** True if this entity stands in its own captain's hideout. */
	public static boolean inOwnClaim(Entity entity, UUID captain) {
		if (!(entity.level() instanceof ServerLevel level) || level != level.getServer().overworld()) {
			return false;
		}
		Hideout hideout = of(level.getServer(), captain);
		return hideout != null && hideout.contains(entity.position());
	}

	/** The flag's block entity, if its chunk is loaded. */
	public static HideoutFlagBlockEntity flag(MinecraftServer server, UUID captain) {
		Hideout hideout = of(server, captain);
		if (hideout == null) {
			return null;
		}
		ServerLevel level = server.overworld();
		if (!level.isLoaded(hideout.pos())) {
			return null;
		}
		return level.getBlockEntity(hideout.pos()) instanceof HideoutFlagBlockEntity flag ? flag : null;
	}
}
