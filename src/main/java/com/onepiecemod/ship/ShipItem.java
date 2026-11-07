package com.onepiecemod.ship;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * A famous ship as an item (the Going Merry, the Thousand Sunny...). Right-click while looking at deep open sea and
 * the real, full-size ship appears there, ready to board. The story hands these out: Kaya's gift at Syrup Village,
 * Franky's work after Enies Lobby.
 */
public class ShipItem extends Item {
	private final String shipId;

	public ShipItem(String shipId, Properties properties) {
		super(properties);
		this.shipId = shipId;
	}

	public String shipId() {
		return shipId;
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		BlockHitResult hit = getPlayerPOVHitResult(level, player, ClipContext.Fluid.SOURCE_ONLY);
		boolean onWater = hit.getType() == HitResult.Type.BLOCK && level.getFluidState(hit.getBlockPos()).is(FluidTags.WATER);
		if (level.isClientSide()) {
			return onWater ? InteractionResult.SUCCESS : InteractionResult.PASS;
		}
		if (!onWater) {
			player.sendOverlayMessage(Component.literal("Look at the sea to launch her.").withStyle(ChatFormatting.YELLOW));
			return InteractionResult.FAIL;
		}
		ServerLevel server = (ServerLevel) level;
		ShipTemplates.Spec spec = ShipTemplates.spec(server.getServer(), shipId);
		if (spec == null) {
			player.sendOverlayMessage(Component.literal("This ship's plans are missing (" + shipId + ").").withStyle(ChatFormatting.RED));
			return InteractionResult.FAIL;
		}

		// Put the ship ahead of the player, far enough that they end up beside her and not inside the hull.
		int clearance = ShipTemplates.clearance(spec);
		Vec3 look = player.getLookAngle();
		Vec3 flat = new Vec3(look.x, 0, look.z);
		if (flat.lengthSqr() < 1.0e-4) {
			flat = new Vec3(0, 0, 1);
		}
		flat = flat.normalize();
		Vec3 center = player.position().add(flat.scale(clearance + 3));
		int cx = Mth.floor(center.x);
		int cz = Mth.floor(center.z);
		Integer surface = deepWater(server, cx, cz);
		if (surface != null) {
			// Check a ring and a cross at the ship's size, not every block: ships are big.
			for (int step = 0; step < 16 && surface != null; step++) {
				double angle = step * Math.PI / 8;
				int r = step % 2 == 0 ? clearance : clearance / 2;
				if (deepWater(server, cx + Mth.floor(Math.cos(angle) * r), cz + Mth.floor(Math.sin(angle) * r)) == null) {
					surface = null;
				}
			}
		}
		if (surface == null) {
			player.sendOverlayMessage(Component.literal("The " + spec.name + " needs open sea about " + clearance
					+ " blocks all around, at least 4 deep. Head further out.").withStyle(ChatFormatting.YELLOW));
			return InteractionResult.FAIL;
		}

		ShipEntity ship = ShipTemplates.spawn(server, shipId, cx, surface, cz, player.getYRot());
		if (ship == null) {
			player.sendOverlayMessage(Component.literal("Couldn't launch the " + spec.name + ".").withStyle(ChatFormatting.RED));
			return InteractionResult.FAIL;
		}
		server.playSound(null, BlockPos.containing(center), com.onepiecemod.sound.WorldSounds.SHIP_LAUNCH, SoundSource.PLAYERS, 2.0f, 1.0f);
		player.sendSystemMessage(Component.literal("The " + spec.name + " is launched! Right-click her to climb aboard; the first aboard takes the wheel.")
				.withStyle(ChatFormatting.GOLD));
		stack.consume(1, player);
		return InteractionResult.SUCCESS;
	}

	/** The Y just above the water's surface if this column is open sea at least 4 blocks deep, otherwise null. */
	private static Integer deepWater(ServerLevel level, int x, int z) {
		if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
			return null;
		}
		int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
		int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
		BlockPos water = new BlockPos(x, top - 1, z);
		if (!level.getFluidState(water).is(FluidTags.WATER) || top - floor < 4) {
			return null;
		}
		return top;
	}
}
