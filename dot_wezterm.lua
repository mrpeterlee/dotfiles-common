local wezterm = require("wezterm")
local config = wezterm.config_builder()

local is_windows = wezterm.target_triple:find("windows") ~= nil
local is_darwin = wezterm.target_triple:find("darwin") ~= nil

-- Font and display settings
config.font = wezterm.font("CaskaydiaCove Nerd Font")
config.font_size = 14
config.max_fps = 240

if is_windows then
	config.default_prog = {
		"cmd.exe",
		"/s",
		"/k",
		"d:\\tool\\conda\\Scripts\\activate.bat d:\\tool\\conda & conda activate paper & d:\\lab\\paper\\winclient\\bin\\clink\\clink_x64.exe inject --profile d:\\home\\peter\\.clink",
	}
elseif is_darwin then
	config.default_prog = { "/opt/homebrew/bin/zsh", "-l" }
else
	config.default_prog = { "/usr/bin/zsh", "-l" }
end

-- Disable kitty keyboard protocol so that nvim (via tmux passthrough) cannot
-- switch WezTerm into CSI-u encoding, which breaks tmux's traditional bindings
config.enable_kitty_keyboard = false
config.enable_csi_u_key_encoding = false

-- Window appearance
config.window_decorations = "RESIZE"
config.window_background_opacity = 0.9
if is_darwin then
	config.macos_window_background_blur = 10
end
config.window_close_confirmation = "NeverPrompt"
config.enable_tab_bar = false
config.enable_scroll_bar = true
config.scrollback_lines = 999999

-- Mouse selection auto-copies to clipboard
config.selection_word_boundary = " \t\n{}[]()\"'`,;:@"
config.mouse_bindings = {
	{
		event = { Up = { streak = 1, button = "Left" } },
		mods = "NONE",
		action = wezterm.action.CompleteSelectionOrOpenLinkAtMouseCursor("ClipboardAndPrimarySelection"),
	},
}

-- Key bindings
config.keys = {
	{ key = "v", mods = "CTRL", action = wezterm.action.PasteFrom("Clipboard") },
	{ key = "+", mods = "ALT", action = wezterm.action.IncreaseFontSize },
	{ key = "=", mods = "ALT", action = wezterm.action.DecreaseFontSize },
	{ key = "n", mods = "CTRL", action = wezterm.action.ToggleFullScreen },
}

return config
