package com.onepiecemod.resource;

import net.minecraft.util.Prediction;
import java.util.List;
import java.util.Map;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.endgame.VoidCentury;
import com.onepiecemod.story.StoryFeature;
import com.onepiecemod.story.StoryGates;
import com.onepiecemod.story.StoryPlaces;

/**
 * A Poneglyph: an unbreakable stone cube carved with the ancient script.
 *
 * The four Road Poneglyphs (Zou, Whole Cake Island, Wano and Hachinosu) are the only way to get the
 * Road Poneglyph rubbings that open Laugh Tale. Right-click one holding paper, with Kraken Ink in your
 * inventory. You need an archaeologist in your crew to read it, and the Whole Cake, Wano and Hachinosu
 * ones only once you've beaten Big Mom, Kaido and Blackbeard. Most Poneglyphs also give a page of the true history
 * (endgame/VoidCentury), and the one at Laugh Tale plays the Dawn once you have every page.
 */
public class PoneglyphBlock extends Block {
	/** A Road Poneglyph: the structure it stands in, which rubbing it gives (StoryFeature.RUBBINGS index), and its guardian boss. */
	private record Road(String structure, int rubbing, String boss, String place) {
	}

	private static final List<Road> ROADS = List.of(
			new Road("mokomo_dukedom", 0, "", "Zou"),
			new Road("whole_cake_chateau", 1, "big_mom", "Whole Cake Island"),
			new Road("onigashima", 2, "kaido", "Wano"),
			new Road("hachinosu", 3, "blackbeard", "Hachinosu"));

	private static final Map<String, String> HISTORY = Map.of(
			"ohara_library", "It tells of a great kingdom, and of a war 800 years ago that history tried to erase.",
			"shandora", "\"I came here and will lead the way to the end of this text.\" Someone signed it: Gol D. Roger.",
			"alubarna_palace", "It names an ancient weapon of terrible power: Pluton.",
			"ryugu_palace", "It is a letter of apology from Joy Boy, who could not keep his promise.",
			"laugh_tale", "The full story of the Void Century. You finally understand why they laughed.",
			"void_century_ruins", "It names the Great Kingdom, and the twenty kings who stood against it. Their names are scratched out.");

	public PoneglyphBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
			InteractionHand hand, BlockHitResult hitResult) {
		if (!(level instanceof ServerLevel serverLevel) || !(player instanceof ServerPlayer serverPlayer)) {
			return InteractionResult.SUCCESS;
		}
		// The twelve Lost Poneglyphs hidden around the world (poneglyph/PoneglyphHunt).
		if (com.onepiecemod.poneglyph.PoneglyphHunt.onUse(serverLevel, pos, serverPlayer)) {
			return InteractionResult.SUCCESS;
		}
		Road road = null;
		for (Road candidate : ROADS) {
			if (StoryPlaces.isInside(serverLevel, pos, candidate.structure())) {
				road = candidate;
			}
		}
		boolean gates = StoryGates.gatesOn(player);
		if (gates && !hasArchaeologist(player)) {
			tell(serverPlayer, "You can't read it. You need an archaeologist in your crew.", ChatFormatting.GRAY);
			return InteractionResult.SUCCESS;
		}
		// Every Poneglyph with a page of the true history writes it into your history (endgame/VoidCentury).
		for (VoidCentury.Page page : VoidCentury.PAGES) {
			if (page.place() != null && StoryPlaces.isInside(serverLevel, pos, page.place())) {
				VoidCentury.learn(serverPlayer, page);
			}
		}
		if (road == null) {
			if (StoryPlaces.isInside(serverLevel, pos, "laugh_tale") && VoidCentury.readLaughTale(serverPlayer)) {
				return InteractionResult.SUCCESS; // The Dawn.
			}
			for (Map.Entry<String, String> entry : HISTORY.entrySet()) {
				if (VoidCentury.pageAt(entry.getKey()) == null && StoryPlaces.isInside(serverLevel, pos, entry.getKey())) {
					tell(serverPlayer, entry.getValue(), ChatFormatting.GOLD);
					return InteractionResult.SUCCESS;
				}
			}
			for (VoidCentury.Page page : VoidCentury.PAGES) {
				if (page.place() != null && StoryPlaces.isInside(serverLevel, pos, page.place())) {
					return InteractionResult.SUCCESS; // The page was the message.
				}
			}
			tell(serverPlayer, "Ancient writing, carved into stone no one can break. It isn't a Road Poneglyph.", ChatFormatting.GRAY);
			return InteractionResult.SUCCESS;
		}

		Item rubbing = StoryFeature.RUBBINGS.get(road.rubbing());
		if (player.getInventory().countItem(rubbing) > 0) {
			tell(serverPlayer, "You already carry a rubbing of this Road Poneglyph.", ChatFormatting.GRAY);
			return InteractionResult.SUCCESS;
		}
		if (gates && !road.boss().isEmpty() && !CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, road.boss())) {
			tell(serverPlayer, "This Road Poneglyph is guarded. Defeat the ruler of " + road.place() + " before you can copy it.", ChatFormatting.RED);
			return InteractionResult.SUCCESS;
		}
		if (!stack.is(Items.PAPER) || (!player.isCreative() && player.getInventory().countItem(Resources.KRAKEN_INK) == 0)) {
			tell(serverPlayer, "A Road Poneglyph! Hold paper and carry Kraken Ink to make a rubbing.", ChatFormatting.AQUA);
			return InteractionResult.SUCCESS;
		}

		if (!player.isCreative()) {
			stack.shrink(1);
			useOne(player.getInventory(), Resources.KRAKEN_INK);
		}
		ItemStack copy = new ItemStack(rubbing);
		if (!player.getInventory().add(copy)) {
			player.drop(copy, false, Prediction.SERVER_ONLY);
		}
		level.playSound(null, pos, SoundEvents.BOOK_PAGE_TURN, SoundSource.BLOCKS, 1.0f, 0.8f);
		tell(serverPlayer, "Your archaeologist copies the Road Poneglyph of " + road.place() + ".", ChatFormatting.GOLD);
		return InteractionResult.SUCCESS;
	}

	@Override
	protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hitResult) {
		return useItemOn(ItemStack.EMPTY, state, level, pos, player, InteractionHand.MAIN_HAND, hitResult);
	}

	public static boolean hasArchaeologist(Player player) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		return crew != null && crew.member(CrewRole.ARCHAEOLOGIST) != null;
	}

	private static void useOne(Inventory inventory, Item item) {
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			if (inventory.getItem(i).is(item)) {
				inventory.getItem(i).shrink(1);
				return;
			}
		}
	}

	private static void tell(ServerPlayer player, String text, ChatFormatting color) {
		player.sendSystemMessage(Component.literal(text).withStyle(color));
	}
}
