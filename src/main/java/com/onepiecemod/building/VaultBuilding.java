package com.onepiecemod.building;

import java.util.Map;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterFeature;

/**
 * Treasure Vault: a stone strongroom with treasure inside.
 * Berries you put in the vault are safe: they stay there when you die.
 * Every in-game day the vault adds a little interest (1%, at most 100 Berries a day,
 * and at most 7 days are counted if you stay away a long time).
 *
 * Right-click holding Berries: put them in. Sneak + right-click with an empty hand: take out 64.
 * Every finished vault opens the same account, so you can store at one and collect at another.
 */
public class VaultBuilding extends Multiblock {
	private static final int MAX_INTEREST_PER_DAY = 100;
	private static final int MAX_DAYS_COUNTED = 7;

	/** The Berries a player keeps in vaults, and the last day interest was added. */
	public record Account(long berries, long lastDay) {
		public static final Codec<Account> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.LONG.fieldOf("berries").forGetter(Account::berries),
				Codec.LONG.fieldOf("last_day").forGetter(Account::lastDay)
		).apply(instance, Account::new));
	}

	public static final AttachmentType<Account> ACCOUNT = AttachmentRegistry.create(
			OnePieceMod.id("vault_account"),
			builder -> builder.persistent(Account.CODEC).copyOnDeath() // Vault Berries survive death.
	);

	public static void initialize() {
		// Loading this class is enough to register the attachment.
	}

	public VaultBuilding() {
		super("treasure_vault", "Treasure Vault");
		fill("stone or brick blocks for the 5x5 floor", Parts.STRONG, Blocks.STONE_BRICKS.defaultBlockState(), square(-1, 2));
		fill("stone or brick blocks for the 5x5 ceiling", Parts.STRONG, Blocks.STONE_BRICKS.defaultBlockState(), square(3, 2));
		fill("stone or brick blocks (or a door) for the walls, 3 tall all the way around",
				state -> Parts.STRONG.test(state) || Parts.DOOR.test(state), Blocks.STONE_BRICKS.defaultBlockState(), join(ring(0, 2), ring(1, 2), ring(2, 2)));
		atLeastAt("door in the walls", Parts.DOOR, join(ring(0, 2), ring(1, 2)), 1, Map.of(
				new BlockPos(0, 0, 2), Blocks.IRON_DOOR.defaultBlockState(),
				new BlockPos(0, 1, 2), Blocks.IRON_DOOR.defaultBlockState().setValue(DoorBlock.HALF, DoubleBlockHalf.UPPER)));
		contains("Chest inside", Parts.CHEST, new BlockPos(-1, 0, -1), new BlockPos(1, 2, 1), 1);
		contains("treasure blocks inside (Gold Blocks, Berry Blocks or Shandora Gold Bricks)", Parts.TREASURE,
				new BlockPos(-1, 0, -1), new BlockPos(1, 2, 1), 2);

		planLine("Floor: a 5x5 square of stone or brick blocks (Seastone Bricks are the toughest look).");
		planLine("Walls: stone or brick all around the edge of the floor, 3 blocks tall, with one door.");
		planLine("Ceiling: a 5x5 layer of stone or brick on top of the walls.");
		planLine("Inside the 3x3 room: a Chest and 2 treasure blocks (Gold Blocks, Berry Blocks or Shandora Gold Bricks).");
		planLine("The Treasure Vault block goes on the floor in the very middle.");
	}

	@Override
	public String purpose() {
		return "Right-click it holding Berries to store them safely; they earn a little interest every day.";
	}

	@Override
	public void use(ServerPlayer player, BuildingRegistry.Entry entry) {
		ServerLevel level = (ServerLevel) player.level();
		Account account = payInterest(player, BuildingRegistry.day(level));
		ItemStack held = player.getItemInHand(InteractionHand.MAIN_HAND);
		BlockPos pos = entry.pos();

		if (held.is(CharacterFeature.BERRY)) {
			int amount = held.getCount();
			held.shrink(amount);
			account = new Account(account.berries() + amount, account.lastDay());
			player.setAttached(ACCOUNT, account);
			level.playSound(null, pos, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.BLOCKS, 1.0f, 1.0f);
			player.sendSystemMessage(Component.literal("Stored " + amount + " Berries. Vault balance: " + account.berries() + " Berries.")
					.withStyle(ChatFormatting.GOLD));
			return;
		}
		if (player.isShiftKeyDown() && held.isEmpty()) {
			int amount = (int) Math.min(64, account.berries());
			if (amount == 0) {
				player.sendSystemMessage(Component.literal("Your vault is empty.").withStyle(ChatFormatting.GRAY));
				return;
			}
			account = new Account(account.berries() - amount, account.lastDay());
			player.setAttached(ACCOUNT, account);
			Parts.give(player, new ItemStack(CharacterFeature.BERRY, amount));
			level.playSound(null, pos, SoundEvents.ARMOR_EQUIP_GOLD.value(), SoundSource.BLOCKS, 1.0f, 0.8f);
			player.sendSystemMessage(Component.literal("Took out " + amount + " Berries. Vault balance: " + account.berries() + " Berries.")
					.withStyle(ChatFormatting.GOLD));
			return;
		}
		player.sendSystemMessage(Component.literal("Vault balance: " + account.berries() + " Berries.").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Right-click holding Berries to store them. Sneak + right-click with an empty hand to take out 64.")
				.withStyle(ChatFormatting.GRAY));
	}

	/** Adds the interest earned since the last visit and returns the updated account. */
	private static Account payInterest(ServerPlayer player, long today) {
		Account account = player.getAttachedOrElse(ACCOUNT, new Account(0, today));
		long days = Math.min(MAX_DAYS_COUNTED, today - account.lastDay());
		long earned = 0;
		long berries = account.berries();
		for (int i = 0; i < days && berries >= 50; i++) {
			long interest = Math.min(MAX_INTEREST_PER_DAY, berries / 100);
			berries += interest;
			earned += interest;
		}
		account = new Account(berries, today);
		player.setAttached(ACCOUNT, account);
		if (earned > 0) {
			player.sendSystemMessage(Component.literal("Your vault earned " + earned + " Berries of interest while you were away.")
					.withStyle(ChatFormatting.GREEN));
		}
		return account;
	}
}
