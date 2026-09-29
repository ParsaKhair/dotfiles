# dotfiles
Configuration files for my default Fedora machine

Nemo is the graphical file manager: directory MIME associations, Hyprland's
Super+E shortcut, and Firefox/LibreWolf's Show in Folder use it. The user desktop
override hides Nautilus's duplicate Files entry from rofi drun. Rofi's
recursivebrowser (Alt+Space) keeps its explicit ranger command.

`~/.config` links to this repository's `.config`. Install the two file-manager
overrides separately because `~/.local/share` is not linked to this repository:

```sh
mkdir -p ~/.local/share/applications ~/.local/share/dbus-1/services
ln -s ~/dotfiles/.local/share/applications/org.gnome.Nautilus.desktop ~/.local/share/applications/org.gnome.Nautilus.desktop
ln -s ~/dotfiles/.local/share/dbus-1/services/org.freedesktop.FileManager1.service ~/.local/share/dbus-1/services/org.freedesktop.FileManager1.service
update-desktop-database ~/.local/share/applications
```

The D-Bus override takes effect on the next FileManager1 activation. If Nautilus
already owns that service, finish any file operations and quit Nautilus first,
or log out and back in.

In ranger, press `i` on a PDF or image to open a graphical preview in Zathura
or qimgv. Under Hyprland it opens as a centered floating window (70% of the
monitor's width, 80% of its height). Close the viewer to return to ranger:
`q` in Zathura, or `Super+Shift+C` in either viewer. Other files still use ranger's
usual pager. Restart an already-running ranger after updating its configuration.

This uses the installed viewers without an overlay daemon or terminal graphics
protocol. Inline images are disabled because Alacritty cannot display ranger's
Kitty protocol previews; the normal preview column still shows text/metadata.
Required Fedora packages: `ranger`, `zathura`, `zathura-pdf-poppler`, and `qimgv`.
Floating applies only to previews opened with `i`, not regular viewer launches.
