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
