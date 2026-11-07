package com.onepiecemod.mining;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.entity.vehicle.minecart.AbstractMinecartContainer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LevelEvent;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.resource.Resources;

/**
 * The Mining Drill's state: fuel, the fitted bit, how far it has dug, and anything it couldn't drop off yet.
 *
 * Every few ticks it breaks the next block of a 3x3 tunnel in front of it (one layer at a time), using one unit of
 * fuel and one use of the bit. Better bits dig faster, go further and cut harder rock. A miner crewmate standing by
 * speeds it up (see MinerWorkGoal). It never breaks chests or other block entities, unbreakable blocks or rock its
 * bit can't cut (those are left in the wall), and it stops when it opens into water or lava.
 */
public class MiningDrillBlockEntity extends BlockEntity {
	public static final int MAX_FUEL = 4000;

	private int fuel;
	private int bitTier;
	private int bitLeft;
	private int depth;
	private boolean on = true;
	private String status = "Fit a drill bit and add fuel";
	private long boostUntil;
	private int cooldown;
	private int mined;
	private List<ItemStack> pending = new ArrayList<>();

	public MiningDrillBlockEntity(BlockPos pos, BlockState state) {
		super(MiningFeature.DRILL_ENTITY, pos, state);
	}

	// ---------------- Numbers per bit ----------------

	/** Ticks per block. */
	public static int speed(int tier) {
		return switch (tier) {
			case 3 -> 10;
			case 2 -> 18;
			default -> 30;
		};
	}

	/** How far the tunnel can go. */
	public static int maxLength(int tier) {
		return switch (tier) {
			case 3 -> 128;
			case 2 -> 64;
			default -> 32;
		};
	}

	/** Blocks a fresh bit can cut before it wears out. */
	public static int bitLife(int tier) {
		return switch (tier) {
			case 3 -> 9000;
			case 2 -> 2400;
			default -> 600;
		};
	}

	/** Blocks of digging one item of fuel gives, 0 if it isn't fuel. */
	public static int fuelValue(ItemStack stack) {
		if (stack.is(Items.COAL) || stack.is(Items.CHARCOAL)) {
			return 24;
		}
		if (stack.is(Resources.SULFUR)) {
			return 32;
		}
		if (stack.is(Items.BLAZE_ROD)) {
			return 48;
		}
		if (stack.is(MiningFeature.ELECTRO_CRYSTAL)) {
			return 160;
		}
		return stack.is(Items.COAL_BLOCK) ? 216 : 0;
	}

	// ---------------- Used by the block and the miner crewmate ----------------

	public int fuel() {
		return fuel;
	}

	public int bitTier() {
		return bitTier;
	}

	public int bitLeft() {
		return bitLeft;
	}

	public boolean isOn() {
		return on;
	}

	public boolean finished() {
		return bitTier > 0 && depth >= maxLength(bitTier);
	}

	/** A miner standing by: digs 40% faster for the next few seconds. */
	public void boost(long until) {
		boostUntil = Math.max(boostUntil, until);
	}

	/** Adds up to `count` of the fuel stack. Returns how many were used. */
	public int addFuel(ItemStack stack, int count, boolean creative) {
		int value = fuelValue(stack);
		int used = 0;
		while (used < count && value > 0 && fuel + value <= MAX_FUEL) {
			fuel += value;
			used++;
		}
		if (!creative) {
			stack.shrink(used);
		}
		if (used > 0 && status.startsWith("Out of fuel")) {
			status = "Digging";
		}
		setChanged();
		return used;
	}

	/** Fits a new drill bit from the stack. A worn old bit is scrapped. */
	public void fitBit(ItemStack stack, ServerPlayer player) {
		int tier = MiningFeature.bitTier(stack);
		if (tier == 0) {
			return;
		}
		if (bitTier > 0 && bitLeft == bitLife(bitTier) && player != null) {
			ItemStack old = new ItemStack(MiningFeature.bitItem(bitTier));
			if (!player.getInventory().add(old)) {
				player.drop(old, false, net.minecraft.util.Prediction.SERVER_ONLY);
			}
		}
		bitTier = tier;
		bitLeft = bitLife(tier);
		if (player == null || !player.isCreative()) {
			stack.shrink(1);
		}
		status = "Digging";
		on = true;
		setChanged();
	}

	public void toggle() {
		on = !on;
		status = on ? "Digging" : "Switched off";
		setChanged();
	}

	/** The containers the drill drops into: Ore Carts, chests and barrels touching it, and chest minecarts beside it. */
	public List<Container> outputs() {
		List<Container> out = new ArrayList<>();
		if (level == null) {
			return out;
		}
		Direction front = getBlockState().getValue(MiningDrillBlock.FACING);
		for (Direction dir : Direction.values()) {
			if (dir != front && level.getBlockEntity(worldPosition.relative(dir)) instanceof Container c
					&& !(c instanceof MiningDrillBlockEntity)) {
				out.add(c);
			}
		}
		out.addAll(level.getEntitiesOfClass(AbstractMinecartContainer.class, new AABB(worldPosition).inflate(1.5)));
		return out;
	}

	public Component statusLine() {
		String bit = bitTier == 0 ? "no bit" : bitName(bitTier) + " bit (" + bitLeft + " left)";
		return Component.literal("Mining Drill: " + status + " | fuel " + fuel + " | " + bit + " | depth " + depth + "/"
				+ maxLength(Math.max(1, bitTier))).withStyle(on ? ChatFormatting.GOLD : ChatFormatting.GRAY);
	}

	public void report(ServerPlayer player) {
		player.sendSystemMessage(Component.literal("Mining Drill").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal(" Status: " + (on ? status : "Switched off (sneak + right-click to start)")));
		player.sendSystemMessage(Component.literal(" Fuel: " + fuel + " blocks of digging (coal, sulfur, blaze rods, electro crystals)"));
		player.sendSystemMessage(Component.literal(" Bit: " + (bitTier == 0 ? "none: right-click with a drill bit"
				: bitName(bitTier) + ", " + bitLeft + "/" + bitLife(bitTier) + " uses left")));
		player.sendSystemMessage(Component.literal(" Tunnel: " + depth + "/" + maxLength(Math.max(1, bitTier)) + " blocks, "
				+ mined + " blocks dug"));
		int carts = outputs().size();
		player.sendSystemMessage(Component.literal(" Output: " + (carts == 0 ? "nothing! Put an Ore Cart or chest right next to it"
				: carts + " cart/chest" + (carts > 1 ? "s" : "") + " beside it")).withStyle(carts == 0 ? ChatFormatting.RED : ChatFormatting.WHITE));
		if (level != null && level.getGameTime() < boostUntil) {
			player.sendSystemMessage(Component.literal(" A crewmate is working the drill (40% faster).").withStyle(ChatFormatting.GREEN));
		}
	}

	private static String bitName(int tier) {
		return switch (tier) {
			case 3 -> "Sea Prism";
			case 2 -> "Seastone";
			default -> "Adam";
		};
	}

	// ---------------- Digging ----------------

	public static void serverTick(Level level, BlockPos pos, BlockState state, MiningDrillBlockEntity drill) {
		if (!(level instanceof ServerLevel server)) {
			return;
		}
		if (drill.cooldown > 0) {
			drill.cooldown--;
			return;
		}
		boolean working = drill.on && drill.step(server, pos, state);
		if (state.getValue(MiningDrillBlock.LIT) != working) {
			level.setBlock(pos, state.setValue(MiningDrillBlock.LIT, working), Block.UPDATE_CLIENTS);
		}
	}

	/** One step of work. Returns true while the drill is busy digging. */
	private boolean step(ServerLevel level, BlockPos pos, BlockState state) {
		if (!pending.isEmpty() && !flush()) {
			return idle(outputs().isEmpty() ? "No Ore Cart or chest beside the drill" : "Cart full: empty it to carry on", 40);
		}
		if (bitTier == 0) {
			return idle(bitLeft == 0 && mined > 0 ? "Bit worn out: fit a new one" : "No drill bit", 40);
		}
		if (fuel <= 0) {
			return idle("Out of fuel", 40);
		}
		if (depth >= maxLength(bitTier)) {
			return idle("Tunnel finished (" + depth + " blocks). Break and re-place the drill to dig again", 100);
		}
		Direction front = state.getValue(MiningDrillBlock.FACING);
		BlockPos center = pos.relative(front, depth + 1);
		if (!level.isLoaded(center)) {
			return idle("Waiting: the tunnel's end is too far away to load", 100);
		}
		ItemStack pick = new ItemStack(MiningFeature.bitPickaxe(bitTier));
		List<BlockPos> layer = layer(center, front);
		for (BlockPos p : layer) {
			if (!level.getFluidState(p).isEmpty() && level.getFluidState(p).isSource()) {
				on = false;
				return idle("Stopped: the tunnel broke into " + (level.getFluidState(p).is(net.minecraft.tags.FluidTags.LAVA) ? "lava" : "water"), 40);
			}
		}
		for (BlockPos p : layer) {
			BlockState target = level.getBlockState(p);
			if (target.isAir() || !target.getFluidState().isEmpty() || target.getDestroySpeed(level, p) < 0
					|| level.getBlockEntity(p) != null || target.is(MiningFeature.MINING_DRILL)) {
				continue;
			}
			if (target.requiresCorrectToolForDrops() && !pick.isCorrectToolForDrops(target)) {
				status = "Digging (left " + target.getBlock().getName().getString() + " in the wall: needs a better bit)";
				continue;
			}
			dig(level, p, target, pick);
			cooldown = level.getGameTime() < boostUntil ? speed(bitTier) * 6 / 10 : speed(bitTier);
			return true;
		}
		depth++; // This layer is clear: move on.
		setChanged();
		cooldown = 2;
		return true;
	}

	private void dig(ServerLevel level, BlockPos p, BlockState target, ItemStack pick) {
		List<ItemStack> drops = Block.getDrops(target, level, p, null, null, pick);
		level.levelEvent(LevelEvent.PARTICLES_DESTROY_BLOCK, p, Block.getId(target));
		level.removeBlock(p, false);
		pending.addAll(drops);
		flush();
		fuel--;
		mined++;
		if (--bitLeft <= 0) {
			bitTier = 0;
			bitLeft = 0;
			level.playSound(null, worldPosition, SoundEvents.ITEM_BREAK.value(), SoundSource.BLOCKS, 1.0f, 0.8f);
		} else if (mined % 4 == 0) {
			level.playSound(null, worldPosition, SoundEvents.GRINDSTONE_USE, SoundSource.BLOCKS, 0.4f, 0.7f);
		}
		if (!status.startsWith("Digging (left")) {
			status = "Digging";
		}
		setChanged();
	}

	private boolean idle(String why, int wait) {
		status = why;
		cooldown = wait;
		return false;
	}

	/** The 3x3 face of the tunnel at this point, middle first. */
	private static List<BlockPos> layer(BlockPos center, Direction front) {
		Direction a;
		Direction b;
		if (front.getAxis() == Direction.Axis.Y) {
			a = Direction.EAST;
			b = Direction.SOUTH;
		} else {
			a = front.getClockWise();
			b = Direction.UP;
		}
		List<BlockPos> out = new ArrayList<>();
		out.add(center);
		for (int i = -1; i <= 1; i++) {
			for (int j = -1; j <= 1; j++) {
				if (i != 0 || j != 0) {
					out.add(center.relative(a, i).relative(b, j));
				}
			}
		}
		return out;
	}

	/** Puts what's waiting into the carts. True when nothing is left over. */
	private boolean flush() {
		List<Container> outs = outputs();
		List<ItemStack> left = new ArrayList<>();
		for (ItemStack stack : pending) {
			ItemStack rest = stack;
			for (Container c : outs) {
				rest = HopperBlockEntity.addItem(null, c, rest, null);
				c.setChanged();
				if (rest.isEmpty()) {
					break;
				}
			}
			if (!rest.isEmpty()) {
				left.add(rest);
			}
		}
		pending = left;
		return pending.isEmpty();
	}

	// ---------------- Saving ----------------

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putInt("Fuel", fuel);
		output.putInt("BitTier", bitTier);
		output.putInt("BitLeft", bitLeft);
		output.putInt("Depth", depth);
		output.putInt("Mined", mined);
		output.putBoolean("On", on);
		output.putString("Status", status);
		if (!pending.isEmpty()) {
			output.store("Pending", ItemStack.CODEC.listOf(), pending);
		}
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		fuel = input.getIntOr("Fuel", 0);
		bitTier = input.getIntOr("BitTier", 0);
		bitLeft = input.getIntOr("BitLeft", 0);
		depth = input.getIntOr("Depth", 0);
		mined = input.getIntOr("Mined", 0);
		on = input.getBooleanOr("On", true);
		status = input.getStringOr("Status", "Digging");
		pending = new ArrayList<>(input.read("Pending", ItemStack.CODEC.listOf()).orElse(List.of()));
	}
}
