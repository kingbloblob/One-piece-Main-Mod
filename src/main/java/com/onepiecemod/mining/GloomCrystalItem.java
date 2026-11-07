package com.onepiecemod.mining;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

import net.fabricmc.fabric.api.tag.convention.v2.ConventionalBlockTags;

/**
 * Gloom Crystal, from the misty rock of Thriller Bark and Kuraigana. Crush one (use it) and the ghostly light
 * shows you the ores hidden in the rock around you: the kinds within 12 blocks, and where the nearest ones are.
 */
public class GloomCrystalItem extends Item {
	private static final int RANGE = 12;

	public GloomCrystalItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(level instanceof ServerLevel server) || !(player instanceof ServerPlayer sp)) {
			return InteractionResult.SUCCESS;
		}
		BlockPos center = player.blockPosition();
		Map<String, List<BlockPos>> found = new LinkedHashMap<>();
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-RANGE, -RANGE, -RANGE), center.offset(RANGE, RANGE, RANGE))) {
			BlockState state = server.getBlockState(pos);
			if (state.is(ConventionalBlockTags.ORES) || state.is(MiningFeature.SEA_PRISM_VEIN)) {
				found.computeIfAbsent(state.getBlock().getName().getString(), k -> new ArrayList<>()).add(pos.immutable());
			}
		}
		ItemStack stack = player.getItemInHand(hand);
		if (!player.isCreative()) {
			stack.shrink(1);
		}
		player.getCooldowns().addCooldown(stack, 40);
		server.playSound(null, center, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0f, 0.6f);
		if (found.isEmpty()) {
			sp.sendSystemMessage(Component.literal("The gloom finds no ore within " + RANGE + " blocks.").withStyle(ChatFormatting.DARK_PURPLE));
			return InteractionResult.SUCCESS;
		}
		sp.sendSystemMessage(Component.literal("The gloom reveals ore in the rock around you:").withStyle(ChatFormatting.LIGHT_PURPLE));
		List<Map.Entry<String, List<BlockPos>>> kinds = new ArrayList<>(found.entrySet());
		kinds.sort(Comparator.comparingDouble(e -> nearest(e.getValue(), center).distSqr(center)));
		for (Map.Entry<String, List<BlockPos>> e : kinds) {
			BlockPos near = nearest(e.getValue(), center);
			sp.sendSystemMessage(Component.literal(" - " + e.getKey() + " x" + e.getValue().size() + ": nearest "
					+ describe(near.subtract(center))).withStyle(ChatFormatting.GRAY));
			// A wisp of light at each of the nearest few blocks of this ore (only you see it).
			e.getValue().stream().sorted(Comparator.comparingDouble(p -> p.distSqr(center))).limit(4).forEach(p ->
					server.sendParticles(sp, ParticleTypes.END_ROD, true, true, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5,
							6, 0.3, 0.3, 0.3, 0.01));
		}
		return InteractionResult.SUCCESS;
	}

	private static BlockPos nearest(List<BlockPos> list, BlockPos center) {
		return list.stream().min(Comparator.comparingDouble(p -> p.distSqr(center))).orElse(center);
	}

	/** "5 blocks east, 3 down" style directions. */
	static String describe(BlockPos d) {
		List<String> parts = new ArrayList<>();
		if (d.getX() != 0) {
			parts.add(Math.abs(d.getX()) + (d.getX() > 0 ? " east" : " west"));
		}
		if (d.getZ() != 0) {
			parts.add(Math.abs(d.getZ()) + (d.getZ() > 0 ? " south" : " north"));
		}
		if (d.getY() != 0) {
			parts.add(Math.abs(d.getY()) + (d.getY() > 0 ? " up" : " down"));
		}
		return parts.isEmpty() ? "right here" : String.join(", ", parts);
	}
}
