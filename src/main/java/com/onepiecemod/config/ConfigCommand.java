package com.onepiecemod.config;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.suggestion.SuggestionProvider;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * /onepiece_config, for server admins and modpack testing (needs cheats / operator level 2):
 *   /onepiece_config list               every setting and its value
 *   /onepiece_config get <setting>      one setting, with what it does
 *   /onepiece_config set <setting> <value>   change it and save the file
 *   /onepiece_config preset <name>      story, simple, standard or challenge: sets the Easy Play settings together
 *   /onepiece_config reload             read config/onepiece.properties again after editing it by hand
 *
 * Settings marked "needs a restart" only change after the server restarts.
 */
public final class ConfigCommand {
	private ConfigCommand() {
	}

	private static final SuggestionProvider<CommandSourceStack> KEYS = (context, builder) -> {
		java.util.List<String> keys = new java.util.ArrayList<>();
		for (ModConfig.Setting setting : ModConfig.settings()) {
			keys.add(setting.key());
		}
		return SharedSuggestionProvider.suggest(keys, builder);
	};

	private static final SuggestionProvider<CommandSourceStack> PRESETS = (context, builder) -> {
		java.util.List<String> ids = new java.util.ArrayList<>();
		for (ModConfig.Preset preset : ModConfig.presets()) {
			ids.add(preset.id());
		}
		return SharedSuggestionProvider.suggest(ids, builder);
	};

	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("onepiece_config")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.literal("list").executes(ConfigCommand::list))
						.then(Commands.literal("reload").executes(context -> {
							ModConfig.load();
							context.getSource().sendSuccess(() -> Component.literal("Reloaded config/onepiece.properties.")
									.withStyle(ChatFormatting.GREEN), true);
							return 1;
						}))
						.then(Commands.literal("preset")
								.executes(ConfigCommand::listPresets)
								.then(Commands.argument("name", StringArgumentType.word()).suggests(PRESETS)
										.executes(ConfigCommand::preset)))
						.then(Commands.literal("get")
								.then(Commands.argument("setting", StringArgumentType.word()).suggests(KEYS)
										.executes(ConfigCommand::get)))
						.then(Commands.literal("set")
								.then(Commands.argument("setting", StringArgumentType.word()).suggests(KEYS)
										.then(Commands.argument("value", StringArgumentType.word())
												.executes(ConfigCommand::set))))
		));
	}

	private static int list(CommandContext<CommandSourceStack> context) {
		String category = "";
		for (ModConfig.Setting setting : ModConfig.settings()) {
			if (!setting.category().equals(category)) {
				category = setting.category();
				String title = category;
				context.getSource().sendSuccess(() -> Component.literal("== " + title + " ==").withStyle(ChatFormatting.GOLD), false);
			}
			context.getSource().sendSuccess(() -> line(setting), false);
		}
		return 1;
	}

	private static int listPresets(CommandContext<CommandSourceStack> context) {
		ModConfig.Preset current = ModConfig.currentPreset();
		for (ModConfig.Preset preset : ModConfig.presets()) {
			boolean on = preset == current;
			context.getSource().sendSuccess(() -> Component.literal(preset.id() + (on ? " (current)" : "")).withStyle(on ? ChatFormatting.YELLOW : ChatFormatting.AQUA)
					.append(Component.literal(" - " + preset.help()).withStyle(ChatFormatting.GRAY)), false);
		}
		return 1;
	}

	private static int preset(CommandContext<CommandSourceStack> context) {
		ModConfig.Preset preset = ModConfig.preset(StringArgumentType.getString(context, "name"));
		if (preset == null) {
			context.getSource().sendFailure(Component.literal("Presets: story, simple, standard, challenge."));
			return 0;
		}
		ModConfig.apply(preset);
		ModConfig.save();
		context.getSource().sendSuccess(() -> Component.literal("Preset " + preset.label() + ": " + preset.help()).withStyle(ChatFormatting.GREEN), true);
		return 1;
	}

	private static int get(CommandContext<CommandSourceStack> context) {
		ModConfig.Setting setting = ModConfig.setting(StringArgumentType.getString(context, "setting"));
		if (setting == null) {
			context.getSource().sendFailure(Component.literal("There's no setting called that. Try /onepiece_config list."));
			return 0;
		}
		context.getSource().sendSuccess(() -> line(setting), false);
		context.getSource().sendSuccess(() -> Component.literal(setting.comment().replace("\n", " ")
				+ " Default: " + setting.format(setting.defaultValue())).withStyle(ChatFormatting.GRAY), false);
		return 1;
	}

	private static int set(CommandContext<CommandSourceStack> context) {
		String key = StringArgumentType.getString(context, "setting");
		String problem = ModConfig.setFromText(key, StringArgumentType.getString(context, "value"));
		if (problem != null) {
			context.getSource().sendFailure(Component.literal(problem));
			return 0;
		}
		ModConfig.save();
		ModConfig.Setting setting = ModConfig.setting(key);
		context.getSource().sendSuccess(() -> Component.literal("Set ").append(line(setting))
				.append(setting.needsRestart() ? Component.literal(" (needs a restart)").withStyle(ChatFormatting.RED) : Component.empty()), true);
		return 1;
	}

	private static Component line(ModConfig.Setting setting) {
		double value = ModConfig.get(setting.key());
		boolean changed = Math.abs(value - setting.defaultValue()) > 1e-9;
		return Component.literal(setting.key() + " = ").withStyle(ChatFormatting.WHITE)
				.append(Component.literal(setting.format(value)).withStyle(changed ? ChatFormatting.YELLOW : ChatFormatting.AQUA));
	}
}
