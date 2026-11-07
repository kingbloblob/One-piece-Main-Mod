package com.onepiecemod.character;

import java.util.List;
import java.util.Optional;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

/**
 * A Wanted Poster or a Vivre Card.
 * - Wanted Poster: use it on a block to make the boss version of that character appear.
 *   Beat them and the poster brings them back on Hard, then Expert. Sneak while using it for a Normal fight.
 *   Emperors and Admirals go on past Expert, up the Legend Ladder (see TitanLadder).
 * - Vivre Card: like in the anime, it slides toward its owner. Right-click it to see which way their home is.
 *   When you get there, right-click again and they'll be waiting for you.
 *   In creative mode you can also use it on a block to place the character right away.
 */
public class CharacterSummonItem extends Item {
	private final String characterId;
	private final boolean boss;

	public CharacterSummonItem(String characterId, boolean boss, Properties properties) {
		super(properties);
		this.characterId = characterId;
		this.boss = boss;
	}

	@Override
	public Component getName(ItemStack stack) {
		String name = CharacterData.get(characterId).name;
		return Component.literal(boss ? "Wanted: " + name : "Vivre Card: " + name);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (boss) {
			return InteractionResult.PASS;
		}
		if (level instanceof ServerLevel serverLevel) {
			followCard(serverLevel, player);
		}
		return InteractionResult.SUCCESS;
	}

	/** The Vivre Card points the way, and the owner appears once you've arrived. */
	private void followCard(ServerLevel level, Player player) {
		CharacterData character = CharacterData.get(characterId);
		String home = Locations.home(characterId);
		if (home == null) {
			player.sendSystemMessage(Component.literal("The card just trembles. " + character.name + " could be anywhere.").withStyle(ChatFormatting.GRAY));
			return;
		}
		if (!(player instanceof ServerPlayer serverPlayer)) {
			return;
		}
		// The search runs in the background (a far one can take a while); the card answers when it's done.
		if (!Locations.findLater(serverPlayer, home, (who, found) -> pointTo(who, character, home, found))) {
			player.sendSystemMessage(Component.literal("The card is still trembling...").withStyle(ChatFormatting.GRAY));
		}
	}

	private void pointTo(ServerPlayer player, CharacterData character, String home, Optional<Locations.Found> found) {
		ServerLevel level = (ServerLevel) player.level();
		if (found.isEmpty()) {
			player.sendSystemMessage(Component.literal("The card doesn't move. " + Locations.name(home) + " isn't in these seas.").withStyle(ChatFormatting.GRAY));
			return;
		}

		BlockPos pos = found.get().pos();
		int distance = Locations.distance(player.blockPosition(), pos);
		String place = Locations.name(home) + (Locations.onlyLastSeen(characterId) ? ", where " + character.name + " was last seen" : "");
		if (distance > 48) {
			player.sendSystemMessage(Component.literal("The Vivre Card slides " + Locations.direction(player.blockPosition(), pos) + ", toward "
					+ place + ". About " + distance + " blocks away.").withStyle(ChatFormatting.AQUA));
			return;
		}

		// We're here. If the owner isn't around (they might have wandered off), they show up now.
		List<CharacterEntity> nearby = level.getEntitiesOfClass(CharacterEntity.class, player.getBoundingBox().inflate(64),
				entity -> entity.getCharacterId().equals(characterId) && !entity.isBoss());
		if (nearby.isEmpty()) {
			CharacterEntity entity = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.TRIGGERED);
			if (entity != null) {
				Vec3 spot = player.position().add(player.getLookAngle().multiply(3, 0, 3));
				BlockPos ground = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, BlockPos.containing(spot));
				entity.setPos(ground.getX() + 0.5, ground.getY(), ground.getZ() + 0.5);
				entity.setCharacter(characterId, false);
				level.addFreshEntity(entity);
			}
		}
		player.sendSystemMessage(Component.literal("You found " + character.name + "!").withStyle(ChatFormatting.GOLD));
	}

	/** The hardest fight this player has unlocked against this boss. */
	private int unlockedDifficulty(Player player) {
		if (CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, characterId + ":hard")) {
			return CharacterEntity.EXPERT;
		}
		if (CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, characterId)) {
			return CharacterEntity.HARD;
		}
		return CharacterEntity.NORMAL;
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		if (!boss && (context.getPlayer() == null || !context.getPlayer().isCreative())) {
			return InteractionResult.PASS; // In survival a Vivre Card shows the way instead (see use()).
		}
		if (context.getLevel() instanceof ServerLevel level) {
			CharacterEntity character = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.SPAWN_ITEM_USE);
			if (character != null) {
				BlockPos pos = context.getClickedPos().relative(context.getClickedFace());
				character.setPos(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5);
				if (context.getPlayer() != null) {
					// Face the player who used the item.
					character.setYRot(context.getPlayer().getYRot() + 180);
					character.setYHeadRot(character.getYRot());
				}
				character.setCharacter(characterId, boss);
				if (boss && context.getPlayer() != null && !context.getPlayer().isShiftKeyDown()) {
					if (TitanLadder.unlocked(context.getPlayer(), characterId)) {
						character.setLegendRung(TitanLadder.nextRung(context.getPlayer(), characterId)); // Past Expert: the Legend Ladder.
					} else {
						character.setDifficulty(unlockedDifficulty(context.getPlayer()));
					}
				}
				level.addFreshEntity(character);

				if (context.getPlayer() == null || !context.getPlayer().isCreative()) {
					context.getItemInHand().shrink(1);
				}
			}
		}
		return InteractionResult.SUCCESS;
	}
}
