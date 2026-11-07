package com.onepiecemod.multiplayer;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.UUIDUtil;

/**
 * A crew of real players, saved on the server (see PlayerCrews).
 * The captain is the player who ran /crew create. Their hired crewmates stay in the crew feature;
 * this only adds the other players who joined, plus alliances with other crews.
 */
public class PirateCrew {
	public static final Codec<PirateCrew> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.STRING.fieldOf("name").forGetter(crew -> crew.name),
			UUIDUtil.CODEC.listOf().fieldOf("members").forGetter(crew -> crew.members),
			UUIDUtil.CODEC.listOf().fieldOf("allies").forGetter(crew -> crew.allies),
			Codec.unboundedMap(UUIDUtil.STRING_CODEC, Codec.LONG).fieldOf("bounties").forGetter(crew -> crew.bounties),
			Codec.unboundedMap(UUIDUtil.STRING_CODEC, Codec.STRING).fieldOf("names").forGetter(crew -> crew.names),
			Codec.LONG.optionalFieldOf("owed", 0L).forGetter(crew -> crew.owed),
			Codec.unboundedMap(UUIDUtil.STRING_CODEC, Codec.STRING).optionalFieldOf("roles", Map.of()).forGetter(crew -> crew.roles)
	).apply(instance, PirateCrew::new));

	/** The crew's name, copied from the captain's crew every few seconds. */
	public String name;
	/** Players who joined (not the captain). */
	public final List<UUID> members;
	/** Captains of allied crews. */
	public final List<UUID> allies;
	/** Last bounty we saw for each player in the crew, captain included, so it can be shown while they're offline. */
	public final Map<UUID, Long> bounties;
	/** Last name we saw for each player in the crew, captain included. */
	public final Map<UUID, String> names;
	/** The captain's share of crew bounties, waiting for the captain to log in. */
	public long owed;
	/** The job each player does aboard (see PlayerRoles): player id -> role id. The captain has none. */
	public final Map<UUID, String> roles;

	public PirateCrew(String name, List<UUID> members, List<UUID> allies, Map<UUID, Long> bounties, Map<UUID, String> names, long owed,
			Map<UUID, String> roles) {
		this.name = name;
		this.members = new ArrayList<>(members);
		this.allies = new ArrayList<>(allies);
		this.bounties = new HashMap<>(bounties);
		this.names = new HashMap<>(names);
		this.owed = owed;
		this.roles = new HashMap<>(roles);
	}

	public static PirateCrew create(String name) {
		return new PirateCrew(name, List.of(), List.of(), Map.of(), Map.of(), 0, Map.of());
	}

	/** Everyone's last known name, or a short placeholder. */
	public String nameOf(UUID player) {
		return names.getOrDefault(player, "someone");
	}

	/** All crew bounties added together: the number the Marines print on the crew's poster. */
	public long totalBounty() {
		long total = 0;
		for (long bounty : bounties.values()) {
			total += bounty;
		}
		return total;
	}
}
