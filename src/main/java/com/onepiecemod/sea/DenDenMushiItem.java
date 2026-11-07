package com.onepiecemod.sea;

import com.onepiecemod.sound.ModSounds;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.Level;

import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * A Den Den Mushi, the snail phone of the One Piece world. "Puru puru puru... gacha!"
 *
 * Right-click: call your whole crew. Every crewmate who can hear you comes to your side and follows you.
 * Sneak + right-click: tell your whole crew to wait where they are.
 *
 * A crewmate can only hear the call if the area they're in is loaded (near a player)
 * and they're in the same dimension as you.
 */
public class DenDenMushiItem extends Item {
	private static final int COOLDOWN_TICKS = 100; // 5 seconds between calls.

	public DenDenMushiItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(level instanceof ServerLevel serverLevel) || !(player instanceof ServerPlayer captain)) {
			return InteractionResult.SUCCESS;
		}
		level.playSound(null, player.blockPosition(), ModSounds.DEN_DEN_MUSHI_CALL, SoundSource.PLAYERS, 1.0f, 1.0f);

		Crew crew = captain.getAttached(CrewAttachments.CREW);
		if (crew == null || crew.size() == 0) {
			captain.sendSystemMessage(Component.literal("Puru puru puru... Nobody picks up. You don't have a crew yet: try /crew create <name>.")
					.withStyle(ChatFormatting.GRAY));
			return InteractionResult.SUCCESS;
		}

		boolean gather = !player.isShiftKeyDown();
		int answered = 0;
		int tooFar = 0;
		for (UUID id : crew.members().values()) {
			Entity entity = serverLevel.getEntity(id);
			if (!(entity instanceof CrewmateEntity crewmate) || !crewmate.isAlive()) {
				tooFar++;
				continue;
			}
			if (gather) {
				// Hurry over: appear right next to the captain.
				double angle = answered * 0.8;
				crewmate.teleportTo(captain.getX() + Math.cos(angle) * 1.5, captain.getY(), captain.getZ() + Math.sin(angle) * 1.5);
				crewmate.getNavigation().stop();
				crewmate.setMode(CrewMode.FOLLOW);
			} else {
				crewmate.setMode(CrewMode.WAIT);
			}
			answered++;
		}

		String order = gather ? "\"Everyone, to me!\"" : "\"Everyone, stay where you are!\"";
		Component reply = answered == 0
				? Component.literal(" Nobody answers.").withStyle(ChatFormatting.GRAY)
				: Component.literal(" Gacha! " + answered + (answered == 1 ? " crewmate answered: " : " crewmates answered: ")
						+ (gather ? "\"On our way, Captain!\"" : "\"Aye, Captain!\"")).withStyle(ChatFormatting.GREEN);
		captain.sendSystemMessage(Component.literal("Puru puru puru... " + order).withStyle(ChatFormatting.GOLD).append(reply));
		if (tooFar > 0) {
			captain.sendSystemMessage(Component.literal(tooFar + (tooFar == 1 ? " crewmate is" : " crewmates are")
					+ " too far away to hear (in another dimension or an unloaded area).").withStyle(ChatFormatting.GRAY));
		}

		captain.getCooldowns().addCooldown(player.getItemInHand(hand), COOLDOWN_TICKS);
		return InteractionResult.SUCCESS;
	}
}
