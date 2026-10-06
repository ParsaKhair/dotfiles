# dotfiles

Personal Fedora + Hyprland configuration. `main` tracks the current desktop setup.

## Installation

1. Clone with `git clone https://github.com/ParsaKhair/dotfiles.git ~/dotfiles`.
2. Install the applications below, including `zathura-pdf-poppler` for PDF previews.
3. Back up your existing configuration, then link `~/dotfiles/.config` to
   `~/.config`, or link individual application directories selectively.
4. Link the files in `.local/share/applications` and `.local/share/dbus-1/services`
   into the matching directories under `~/.local/share`, then run
   `update-desktop-database ~/.local/share/applications`.

Adjust monitor settings and machine-specific paths before logging into Hyprland.
Application caches, logs, and CopyQ clipboard data and process locks stay local.

## Applications

### Hyprland, Waybar, and Rofi

Coordinated desktop styling, workspace indicators, and network, audio, and
notification controls. `Super+E` opens Nemo; `Alt+Space` opens Rofi's file browser
with ranger integration.

### Nemo and ranger

Nemo handles folders and browser **Show in Folder** actions; the duplicate
Nautilus launcher is hidden. In ranger, `i` opens a floating image or PDF preview,
and notebooks open in VS Code. Inline image previews are disabled for Alacritty.

### qimgv and Zathura

qimgv is the default for JPEG, PNG, GIF, BMP, and WebP images. Ranger uses qimgv
for image previews and Zathura for PDFs, centered in floating Hyprland windows.

### Claude Desktop

Native Wayland rendering improves HiDPI clarity. Launcher overrides include a
workaround for a Chromium/Hyprland color-management startup crash.

### Neovim and VS Code

Neovim includes LaTeX, snippets, and R/Python workflow customizations. VS Code
uses autosave, opens Claude Code in the panel, and hides the secondary sidebar
by default.

### systemd user services

The VCC timer checks GitHub inactivity every fifteen minutes. It depends on
`~/vcc-lab`, its Python environment, and `~/vcc2026`; use it only on machines
with that project setup.
