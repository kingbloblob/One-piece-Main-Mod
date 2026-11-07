package com.onepiecemod.crew;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.UUIDUtil;

/**
 * A captain's crew, saved on the captain.
 *
 * @param name    the crew's name, like "Straw Hat Pirates"
 * @param members which crewmate (by its unique id) fills each role, keyed by role id
 * @param hires   how many crewmates the captain has ever hired. Each hire costs more than the last,
 *                and this never goes down, so dismissing and re-hiring is not a cheap trick.
 */
public record Crew(String name, Map<String, UUID> members, int hires) {
	public static final Codec<Crew> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.STRING.fieldOf("name").forGetter(Crew::name),
			Codec.unboundedMap(Codec.STRING, UUIDUtil.CODEC).fieldOf("members").forGetter(Crew::members),
			Codec.INT.optionalFieldOf("hires", 0).forGetter(Crew::hires)
	).apply(instance, Crew::new));

	public static Crew create(String name) {
		return new Crew(name, Map.of(), 0);
	}

	public UUID member(CrewRole role) {
		return members.get(role.id());
	}

	public int size() {
		return members.size();
	}

	public Crew withMember(CrewRole role, UUID crewmateId) {
		Map<String, UUID> newMembers = new HashMap<>(members);
		newMembers.put(role.id(), crewmateId);
		return new Crew(name, newMembers, hires + 1);
	}

	public Crew withoutMember(CrewRole role) {
		Map<String, UUID> newMembers = new HashMap<>(members);
		newMembers.remove(role.id());
		return new Crew(name, newMembers, hires);
	}
}
