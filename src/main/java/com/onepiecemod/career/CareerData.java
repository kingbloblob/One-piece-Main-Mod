package com.onepiecemod.career;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.BlockPos;

/**
 * A player's career, saved on the player and kept on death.
 *
 * @param career        "pirate", "marine" or "revolutionary"
 * @param rank          index into the career's rank list
 * @param points        Merit (Marines) or Liberation (Revolutionaries) earned since joining
 * @param strikes       times a Marine hurt the Navy; 3 means a court-martial
 * @param missionsDone  orders carried out
 * @param lastPaidDay   last in-game day a salary was paid
 * @param backupReadyAt game time when backup can be called again
 * @param flags         one-off notes: "deserter", "invited", "told_<rank>"...
 * @param mission       the orders the player is on right now, if any
 */
public record CareerData(String career, int rank, int points, int strikes, int missionsDone, long lastPaidDay,
		long backupReadyAt, List<String> flags, Optional<Mission> mission) {
	public static final CareerData EMPTY = new CareerData(Career.PIRATE.id, 0, 0, 0, 0, -1L, 0L, List.of(), Optional.empty());

	/**
	 * One set of orders: beat a group of enemies at a place.
	 * @param kind      "hunt" (Marines go after a pirate crew) or "liberate" (Revolutionaries drive out a garrison)
	 * @param place     where, for the player to read ("Arlong Park", "a cove")
	 * @param remaining enemies still standing
	 * @param tier      how tough the enemies are (the rank when the orders were given)
	 * @param reward    Merit or Liberation for finishing
	 */
	public record Mission(String kind, String place, int x, int y, int z, int remaining, int total, int tier, int reward) {
		public static final Codec<Mission> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.STRING.fieldOf("kind").forGetter(Mission::kind),
				Codec.STRING.fieldOf("place").forGetter(Mission::place),
				Codec.INT.fieldOf("x").forGetter(Mission::x),
				Codec.INT.fieldOf("y").forGetter(Mission::y),
				Codec.INT.fieldOf("z").forGetter(Mission::z),
				Codec.INT.fieldOf("remaining").forGetter(Mission::remaining),
				Codec.INT.fieldOf("total").forGetter(Mission::total),
				Codec.INT.fieldOf("tier").forGetter(Mission::tier),
				Codec.INT.fieldOf("reward").forGetter(Mission::reward)
		).apply(instance, Mission::new));

		public BlockPos pos() {
			return new BlockPos(x, y, z);
		}

		public Mission withRemaining(int left) {
			return new Mission(kind, place, x, y, z, left, total, tier, reward);
		}

		public Mission at(BlockPos pos) {
			return new Mission(kind, place, pos.getX(), pos.getY(), pos.getZ(), remaining, total, tier, reward);
		}
	}

	public static final Codec<CareerData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.STRING.optionalFieldOf("career", Career.PIRATE.id).forGetter(CareerData::career),
			Codec.INT.optionalFieldOf("rank", 0).forGetter(CareerData::rank),
			Codec.INT.optionalFieldOf("points", 0).forGetter(CareerData::points),
			Codec.INT.optionalFieldOf("strikes", 0).forGetter(CareerData::strikes),
			Codec.INT.optionalFieldOf("missions_done", 0).forGetter(CareerData::missionsDone),
			Codec.LONG.optionalFieldOf("last_paid_day", -1L).forGetter(CareerData::lastPaidDay),
			Codec.LONG.optionalFieldOf("backup_ready_at", 0L).forGetter(CareerData::backupReadyAt),
			Codec.STRING.listOf().optionalFieldOf("flags", List.of()).forGetter(CareerData::flags),
			Mission.CODEC.optionalFieldOf("mission").forGetter(CareerData::mission)
	).apply(instance, CareerData::new));

	public Career path() {
		return Career.byId(career);
	}

	public Career.Rank currentRank() {
		return path().rank(rank);
	}

	/** The next rank up, or null at the top (or for pirates). */
	public Career.Rank nextRank() {
		Career path = path();
		return rank + 1 < path.ranks.size() ? path.ranks.get(rank + 1) : null;
	}

	public boolean has(String flag) {
		return flags.contains(flag);
	}

	public CareerData withFlag(String flag) {
		if (flags.contains(flag)) {
			return this;
		}
		List<String> list = new ArrayList<>(flags);
		list.add(flag);
		return new CareerData(career, rank, points, strikes, missionsDone, lastPaidDay, backupReadyAt, list, mission);
	}

	/** Starts a new career at its lowest rank. Flags (like "deserter") stay. */
	public CareerData joined(Career path, long today) {
		return new CareerData(path.id, 0, 0, 0, 0, today, 0L, flags, Optional.empty());
	}

	public CareerData withRank(int newRank) {
		return new CareerData(career, newRank, points, 0, missionsDone, lastPaidDay, backupReadyAt, flags, mission);
	}

	public CareerData withPoints(int newPoints) {
		return new CareerData(career, rank, Math.max(0, newPoints), strikes, missionsDone, lastPaidDay, backupReadyAt, flags, mission);
	}

	public CareerData withStrikes(int newStrikes) {
		return new CareerData(career, rank, points, newStrikes, missionsDone, lastPaidDay, backupReadyAt, flags, mission);
	}

	public CareerData withPaidDay(long day) {
		return new CareerData(career, rank, points, strikes, missionsDone, day, backupReadyAt, flags, mission);
	}

	public CareerData withBackupReadyAt(long time) {
		return new CareerData(career, rank, points, strikes, missionsDone, lastPaidDay, time, flags, mission);
	}

	public CareerData withMission(Mission newMission) {
		return new CareerData(career, rank, points, strikes, missionsDone, lastPaidDay, backupReadyAt, flags, Optional.ofNullable(newMission));
	}

	public CareerData missionDone() {
		return new CareerData(career, rank, points, strikes, missionsDone + 1, lastPaidDay, backupReadyAt, flags, Optional.empty());
	}
}
