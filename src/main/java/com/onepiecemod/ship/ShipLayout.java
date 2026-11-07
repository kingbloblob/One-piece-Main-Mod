package com.onepiecemod.ship;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import io.netty.buffer.ByteBuf;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * The blocks a ship is made of, frozen while it sails.
 *
 * Every position is relative to the ship's centre block (0, 0, 0 is the middle of the bottom layer),
 * in the direction the ship was facing when it was put together. ShipEntity turns them as the ship turns.
 */
public final class ShipLayout {
	/** One block of the ship. nbt holds chest contents and similar, and only lives on the server. */
	public record ShipBlock(BlockPos pos, BlockState state, Optional<CompoundTag> nbt) {
		public static final Codec<ShipBlock> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				BlockPos.CODEC.fieldOf("pos").forGetter(ShipBlock::pos),
				BlockState.CODEC.fieldOf("state").forGetter(ShipBlock::state),
				CompoundTag.CODEC.optionalFieldOf("nbt").forGetter(ShipBlock::nbt)
		).apply(instance, ShipBlock::new));

		// Players' games only need to know what to draw, so the chest contents are left out.
		public static final StreamCodec<ByteBuf, ShipBlock> STREAM_CODEC = StreamCodec.composite(
				BlockPos.STREAM_CODEC, ShipBlock::pos,
				ByteBufCodecs.idMapper(Block.BLOCK_STATE_REGISTRY), ShipBlock::state,
				(pos, state) -> new ShipBlock(pos, state, Optional.empty())
		);
	}

	/** A painted flag or sail on the ship, so it can still be drawn while sailing. */
	public record FlagEntry(BlockPos pos, FlagDesign design) {
		public static final Codec<FlagEntry> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				BlockPos.CODEC.fieldOf("pos").forGetter(FlagEntry::pos),
				FlagDesign.CODEC.fieldOf("design").forGetter(FlagEntry::design)
		).apply(instance, FlagEntry::new));

		public static final StreamCodec<ByteBuf, FlagEntry> STREAM_CODEC = StreamCodec.composite(
				BlockPos.STREAM_CODEC, FlagEntry::pos,
				FlagDesign.STREAM_CODEC, FlagEntry::design,
				FlagEntry::new
		);
	}

	public static final Codec<ShipLayout> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			ShipBlock.CODEC.listOf().fieldOf("blocks").forGetter(layout -> layout.blocks),
			FlagEntry.CODEC.listOf().optionalFieldOf("flags", List.of()).forGetter(layout -> layout.flags),
			BlockPos.CODEC.fieldOf("helm").forGetter(layout -> layout.helm),
			Direction.CODEC.fieldOf("bow").forGetter(layout -> layout.bow),
			Codec.FLOAT.fieldOf("waterline").forGetter(layout -> layout.waterline)
	).apply(instance, ShipLayout::new));

	public static final StreamCodec<ByteBuf, ShipLayout> STREAM_CODEC = StreamCodec.composite(
			ShipBlock.STREAM_CODEC.apply(ByteBufCodecs.list()), layout -> layout.blocks,
			FlagEntry.STREAM_CODEC.apply(ByteBufCodecs.list()), layout -> layout.flags,
			BlockPos.STREAM_CODEC, layout -> layout.helm,
			Direction.STREAM_CODEC, layout -> layout.bow,
			ByteBufCodecs.FLOAT, layout -> layout.waterline,
			ShipLayout::new
	);

	public static final ShipLayout EMPTY = new ShipLayout(List.of(), List.of(), BlockPos.ZERO, Direction.SOUTH, 0);

	public final List<ShipBlock> blocks;
	public final List<FlagEntry> flags;
	/** Where the Ship's Wheel is. The captain stands just behind it. */
	public final BlockPos helm;
	/** Which way the front of the ship pointed when it was put together. */
	public final Direction bow;
	/** How many blocks of the ship sit under the water. Keeps it floating at the same height. */
	public final float waterline;

	// Worked out from the blocks above, on both the server and the players' games.
	public final int sails;
	public final List<Vec3> seats;
	public final BlockPos min;
	public final BlockPos max;
	private final Map<BlockPos, FlagDesign> flagsByPos = new HashMap<>();
	private final Map<BlockPos, Integer> indexByPos = new HashMap<>();

	public ShipLayout(List<ShipBlock> blocks, List<FlagEntry> flags, BlockPos helm, Direction bow, float waterline) {
		this.blocks = new ArrayList<>(blocks); // Not fixed: chest contents change while sailing (see setNbt).
		this.flags = List.copyOf(flags);
		this.helm = helm;
		this.bow = bow;
		this.waterline = waterline;

		int minX = 0, minY = 0, minZ = 0, maxX = 0, maxY = 0, maxZ = 0;
		Set<BlockPos> filled = new HashSet<>();
		int sailCount = 0;
		for (int i = 0; i < this.blocks.size(); i++) {
			ShipBlock block = this.blocks.get(i);
			BlockPos p = block.pos();
			filled.add(p);
			indexByPos.put(p, i);
			minX = Math.min(minX, p.getX());
			minY = Math.min(minY, p.getY());
			minZ = Math.min(minZ, p.getZ());
			maxX = Math.max(maxX, p.getX());
			maxY = Math.max(maxY, p.getY());
			maxZ = Math.max(maxZ, p.getZ());
			if (block.state().is(BlockTags.WOOL)) {
				sailCount++;
			}
		}
		// A painted sail counts as one sail per block it covers.
		for (FlagEntry flag : this.flags) {
			flagsByPos.put(flag.pos(), flag.design());
			if (flag.design().style() == FlagDesign.STYLE_SAIL) {
				sailCount += flag.design().size() * flag.design().size();
			}
		}
		this.sails = sailCount;
		this.min = new BlockPos(minX, minY, minZ);
		this.max = new BlockPos(maxX, maxY, maxZ);
		this.seats = findSeats(filled);
	}

	/** Which block of the ship is at a position, or -1 if that spot is empty. */
	public int indexAt(BlockPos pos) {
		return indexByPos.getOrDefault(pos, -1);
	}

	/** Updates the saved contents (chest items and so on) of one block while the ship sails. */
	public void setNbt(int index, CompoundTag nbt) {
		ShipBlock block = blocks.get(index);
		blocks.set(index, new ShipBlock(block.pos(), block.state(), Optional.of(nbt)));
	}

	public int size() {
		return blocks.size();
	}

	/** Painted flags by position, for quick lookup when drawing. */
	public Map<BlockPos, FlagDesign> flagMap() {
		return flagsByPos;
	}

	/**
	 * Spots where people stand while sailing, as feet positions relative to the ship's centre.
	 * Seat 0 is the captain's spot right behind the wheel. The others are open deck spaces, closest to the wheel first.
	 */
	private List<Vec3> findSeats(Set<BlockPos> filled) {
		List<Vec3> result = new ArrayList<>();
		BlockPos captain = helm.relative(bow.getOpposite());
		result.add(new Vec3(captain.getX(), captain.getY(), captain.getZ()));

		List<BlockPos> deck = new ArrayList<>();
		for (BlockPos p : filled) {
			BlockPos feet = p.above();
			// Only spots near the wheel's height, so nobody ends up standing on top of a mast.
			boolean nearDeckHeight = Math.abs(feet.getY() - helm.getY()) <= 3;
			if (nearDeckHeight && !filled.contains(feet) && !filled.contains(feet.above()) && !feet.equals(captain)) {
				deck.add(feet);
			}
		}
		deck.sort(Comparator.comparingDouble(p -> p.distSqr(helm)));
		for (int i = 0; i < Math.min(deck.size(), 15); i++) {
			BlockPos p = deck.get(i);
			result.add(new Vec3(p.getX(), p.getY(), p.getZ()));
		}
		return result;
	}
}
