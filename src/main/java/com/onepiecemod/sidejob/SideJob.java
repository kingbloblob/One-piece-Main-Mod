package com.onepiecemod.sidejob;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.BlockPos;

/**
 * One side job a player has taken: a town request or a Wanted contract. Saved on the player.
 *
 * @param id       a short random id; it also tags the job's enemies and its keepsake item
 * @param kind     FETCH, CULL_PIRATES, CULL_MONSTERS, LOST (town requests) or CREW, FRUIT, BEAST, CONVICT (contracts)
 * @param giver    the townsperson who asked (UUID as text)
 * @param giverName "Mira the Fisher"
 * @param town     the town's name ("Foosha Village"), for messages
 * @param origin   where the job was taken (hand-in works near here if the giver is gone)
 * @param target   where the enemies or the lost thing are (origin for jobs without a place)
 * @param item     FETCH: the item id to bring; LOST: the keepsake's item id; contracts: kit or creature id
 * @param count    how many to bring or beat
 * @param progress kills so far (CULL); 1 once the keepsake is placed (LOST); unused otherwise
 * @param title    "Wanted: Red-Eye Barlow" or "Fresh fish for the market"
 * @param name     the target's or keepsake's name
 * @param berries  Berries paid when it's done (Pirate XP is the same number)
 * @param bounty   contracts: the target's bounty (5% of it is added to yours when you take them down)
 */
public record SideJob(String id, String kind, String giver, String giverName, String town, BlockPos origin, BlockPos target,
		String item, int count, int progress, String title, String name, int berries, long bounty) {

	public static final Codec<SideJob> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.STRING.fieldOf("id").forGetter(SideJob::id),
			Codec.STRING.fieldOf("kind").forGetter(SideJob::kind),
			Codec.STRING.fieldOf("giver").forGetter(SideJob::giver),
			Codec.STRING.fieldOf("giver_name").forGetter(SideJob::giverName),
			Codec.STRING.fieldOf("town").forGetter(SideJob::town),
			BlockPos.CODEC.fieldOf("origin").forGetter(SideJob::origin),
			BlockPos.CODEC.fieldOf("target").forGetter(SideJob::target),
			Codec.STRING.fieldOf("item").forGetter(SideJob::item),
			Codec.INT.fieldOf("count").forGetter(SideJob::count),
			Codec.INT.fieldOf("progress").forGetter(SideJob::progress),
			Codec.STRING.fieldOf("title").forGetter(SideJob::title),
			Codec.STRING.fieldOf("name").forGetter(SideJob::name),
			Codec.INT.fieldOf("berries").forGetter(SideJob::berries),
			Codec.LONG.fieldOf("bounty").forGetter(SideJob::bounty)
	).apply(instance, SideJob::new));

	public boolean isContract() {
		return switch (kind) {
			case "CREW", "FRUIT", "BEAST", "CONVICT" -> true;
			default -> false;
		};
	}

	/** Jobs with a place to go to: contracts and lost keepsakes. */
	public boolean hasPlace() {
		return isContract() || "LOST".equals(kind);
	}

	public SideJob withProgress(int value) {
		return new SideJob(id, kind, giver, giverName, town, origin, target, item, count, value, title, name, berries, bounty);
	}

	public SideJob withTarget(BlockPos pos) {
		return new SideJob(id, kind, giver, giverName, town, origin, pos, item, count, progress, title, name, berries, bounty);
	}
}
