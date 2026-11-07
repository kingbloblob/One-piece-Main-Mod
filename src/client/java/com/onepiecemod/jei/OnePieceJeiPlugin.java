package com.onepiecemod.jei;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import mezz.jei.api.IModPlugin;
import mezz.jei.api.JeiPlugin;
import mezz.jei.api.constants.VanillaTypes;
import mezz.jei.api.recipe.types.IRecipeType;
import mezz.jei.api.registration.IIngredientAliasRegistration;
import mezz.jei.api.registration.IRecipeCatalystRegistration;
import mezz.jei.api.registration.IRecipeCategoryRegistration;
import mezz.jei.api.registration.IRecipeRegistration;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.config.ModConfig;
import com.onepiecemod.crafting.Station;
import com.onepiecemod.fruitdex.FruitLore;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;
import com.onepiecemod.recipeview.client.ItemDescriptions;
import com.onepiecemod.recipeview.client.RecipeIndex;
import com.onepiecemod.recipeview.client.ViewRecipe;

/**
 * Shows the mod's own recipes in JEI, if JEI is installed: one page per crafting station (with its locks,
 * like "Requires: Beat Smoker"), one page for drops, trades and quest rewards, and every item's description
 * on JEI's Information page. Devil Fruits get their own Information page (power, moves, where to find one)
 * and search names, so typing "Gum-Gum" or "Luffy" in JEI finds the Gomu Gomu no Mi. JEI finds this class through the "jei_mod_plugin" entrypoint in fabric.mod.json;
 * without JEI nothing here is ever loaded.
 */
@JeiPlugin
public class OnePieceJeiPlugin implements IModPlugin {
	private static final List<StationType> STATIONS = new ArrayList<>();
	private static final IRecipeType<ViewRecipe> SOURCES = IRecipeType.create(OnePieceMod.MOD_ID, "sources", ViewRecipe.class);

	private record StationType(Station station, IRecipeType<ViewRecipe> type) {}

	static {
		for (Station station : Station.values()) {
			STATIONS.add(new StationType(station, IRecipeType.create(OnePieceMod.MOD_ID, "station_" + station.id(), ViewRecipe.class)));
		}
	}

	@Override
	public Identifier getPluginUid() {
		return OnePieceMod.id("jei_plugin");
	}

	@Override
	public void registerCategories(IRecipeCategoryRegistration registration) {
		var guiHelper = registration.getJeiHelpers().getGuiHelper();
		for (StationType type : STATIONS) {
			registration.addRecipeCategories(new ViewRecipeCategory(type.type(), guiHelper,
					Component.literal(type.station().title() + " (Tier " + type.station().tier() + ")"), stationItem(type.station()), true));
		}
		registration.addRecipeCategories(new ViewRecipeCategory(SOURCES, guiHelper,
				Component.literal("One Piece: Drops, Trades & Quests"), new ItemStack(Items.CHEST), false));
	}

	@Override
	public void registerRecipes(IRecipeRegistration registration) {
		List<ViewRecipe> all = RecipeIndex.get().all();
		for (StationType type : STATIONS) {
			String key = "station:" + type.station().id();
			registration.addRecipes(type.type(), all.stream().filter(recipe -> key.equals(recipe.jeiCategory)).toList());
		}
		registration.addRecipes(SOURCES, all.stream().filter(recipe -> "source".equals(recipe.jeiCategory)).toList());

		fruitInfo(registration);

		// Item descriptions on JEI's Information page.
		for (Item item : BuiltInRegistries.ITEM) {
			Identifier id = BuiltInRegistries.ITEM.getKey(item);
			if (id.getNamespace().startsWith(OnePieceMod.MOD_ID)) {
				String text = ItemDescriptions.describe(id);
				if (text != null) {
					registration.addIngredientInfo(new ItemStack(item), VanillaTypes.ITEM_STACK, Component.literal(text));
				}
			}
		}
	}

	/** Information pages for every Devil Fruit: what it does, its two moves, and where to get one. */
	private static void fruitInfo(IRecipeRegistration registration) {
		Map<String, List<String>> bosses = fruitBosses();
		for (DevilFruit fruit : DevilFruits.ALL) {
			Item item = ModItems.DEVIL_FRUITS.get(fruit.id());
			if (item == null) {
				continue;
			}
			FruitLore.Entry lore = FruitLore.get(fruit.id());
			List<Component> lines = new ArrayList<>();
			String type = fruit.type().name().charAt(0) + fruit.type().name().substring(1).toLowerCase(java.util.Locale.ROOT);
			lines.add(Component.literal((lore.english().isEmpty() ? "" : lore.english() + ", ") + "a " + type + " fruit."));
			lines.add(Component.translatable("fruit.onepiece." + fruit.id() + ".desc"));
			lines.add(Component.literal("Power key: " + fruit.primary() + ". Sneak + power key: " + fruit.secondary() + "."));
			StringBuilder where = new StringBuilder("Found: ");
			float chance = ModConfig.fruitLeafChance();
			where.append(chance > 0 ? "rarely from breaking leaves (1 in " + String.format("%,d", Math.round(1 / chance)) + " across all fruits)" : "not from leaves on this world");
			List<String> from = bosses.get(fruit.id());
			if (from != null) {
				where.append(", or by beating ").append(String.join(" or ", from)).append(" the first time");
			}
			lines.add(Component.literal(where + "."));
			lines.add(Component.literal("Eat only one: a second fruit kills you, and fruit users sink in the sea."));
			registration.addIngredientInfo(new ItemStack(item), VanillaTypes.ITEM_STACK, lines.toArray(Component[]::new));
		}
	}

	/** Fruit id -> names of the bosses who drop it, from characters.json. */
	private static Map<String, List<String>> fruitBosses() {
		Map<String, List<String>> bosses = new HashMap<>();
		for (CharacterData who : CharacterData.all().values()) {
			if (who.fruitItem != null && who.fruitItem.startsWith(OnePieceMod.MOD_ID + ":")) {
				bosses.computeIfAbsent(who.fruitItem.substring(OnePieceMod.MOD_ID.length() + 1), k -> new ArrayList<>()).add(who.name);
			}
		}
		return bosses;
	}

	/** Search names: a fruit's English name and its users' names find it in JEI. */
	@Override
	public void registerIngredientAliases(IIngredientAliasRegistration registration) {
		for (DevilFruit fruit : DevilFruits.ALL) {
			Item item = ModItems.DEVIL_FRUITS.get(fruit.id());
			if (item == null) {
				continue;
			}
			FruitLore.Entry lore = FruitLore.get(fruit.id());
			List<String> aliases = new ArrayList<>();
			if (!lore.english().isEmpty()) {
				aliases.add(lore.english());
			}
			if (lore.user() != null && !lore.user().isEmpty() && !lore.user().equals("Unknown")) {
				aliases.add(lore.user());
			}
			aliases.add(fruit.type().name().toLowerCase(java.util.Locale.ROOT));
			registration.addAliases(item, aliases);
		}
	}

	@Override
	public void registerRecipeCatalysts(IRecipeCatalystRegistration registration) {
		for (StationType type : STATIONS) {
			ItemStack block = stationItem(type.station());
			if (!block.isEmpty()) {
				registration.addCraftingStation(type.type(), block.getItem());
			}
		}
	}

	private static ItemStack stationItem(Station station) {
		return CharacterData.stack("onepiece:" + station.id(), 1);
	}
}
