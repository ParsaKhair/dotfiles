# shellcheck shell=bash
# omni — shared helpers.  Sourced after config.sh.

# When launched from a Hyprland keybind, PATH is just /usr/local/bin:/usr/bin —
# it does NOT include ~/.local/bin (where `claude` lives) or ~/bin. Interactive
# shells get those from .bashrc, which is why this works in a terminal but not
# from the keybind. Add them here so every omni script can find its tools.
case ":$PATH:" in *":$HOME/.local/bin:"*) : ;; *) PATH="$HOME/.local/bin:$HOME/bin:$PATH";; esac
export PATH

OMNI_DIR="${OMNI_DIR:-$HOME/.config/omni}"
OMNI_CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/omni"
OMNI_INDEX="$OMNI_CACHE/index.tsv"
mkdir -p "$OMNI_CACHE"

# Resolve the current semester folder name (honours SEMESTER override).
omni_semester() {
  if [ -n "${SEMESTER:-}" ]; then printf '%s\n' "$SEMESTER"; return; fi
  local y m yy season
  y=$(date +%Y); m=$(date +%-m); yy=${y: -2}
  if   [ "$m" -le 5 ]; then season=Spring
  elif [ "$m" -le 7 ]; then season=Summer
  else                     season=Fall
  fi
  printf '%s-%s\n' "$yy" "$season"
}

OMNI_SEM_DIR="$DOCS_ROOT/$(omni_semester)"
