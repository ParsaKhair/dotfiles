#!/usr/bin/env bash
# omni — build the file index for the current semester.
# Output TSV columns:  KIND <tab> TARGET <tab> COURSE <tab> LABEL
#   KIND   = dir | file
#   TARGET = absolute path
#   COURSE = course short-name (folder), or "." for loose files
#   LABEL  = what the user sees / fuzzy-matches in rofi
set -uo pipefail

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$self_dir/config.sh"
# shellcheck source=/dev/null
source "$self_dir/lib.sh"

# File types worth surfacing.
OMNI_EXTS=(pdf ipynb tex docx pptx xlsx md csv)

omni_build_index() {
  local sem="$OMNI_SEM_DIR"
  [ -d "$sem" ] || { : > "$OMNI_INDEX"; return; }

  {
    # Course folders (immediate children) -> dir rows.
    find "$sem" -mindepth 1 -maxdepth 1 -type d \
         -not -name '.*' 2>/dev/null | sort |
    while IFS= read -r d; do
      local course; course="$(basename "$d")"
      printf 'dir\t%s\t%s\t%s/\n' "$d" "$course" "$course"
    done

    # Files of interest, anywhere under the semester dir.
    local expr=()
    local e
    for e in "${OMNI_EXTS[@]}"; do expr+=(-iname "*.$e" -o); done
    unset 'expr[${#expr[@]}-1]'   # drop trailing -o

    find "$sem" -type d \( -name .git -o -name node_modules -o -name __pycache__ \
                           -o -name .ipynb_checkpoints -o -name build \) -prune -o \
         -type f \( "${expr[@]}" \) -print 2>/dev/null | sort |
    while IFS= read -r f; do
      local rel course label
      rel="${f#"$sem"/}"                 # path relative to semester dir
      course="${rel%%/*}"                # first segment
      if [ "$course" = "$rel" ]; then    # loose file in semester root
        course="."; label="$rel"
      else
        label="$course · ${rel#*/}"      # course · path/within/course
      fi
      printf 'file\t%s\t%s\t%s\n' "$f" "$course" "$label"
    done
  } > "$OMNI_INDEX.tmp" && mv "$OMNI_INDEX.tmp" "$OMNI_INDEX"
}

# Rebuild only when something under the semester dir is newer than the cache
# (or the cache is missing).  Keeps the hot path instant.
omni_ensure_index() {
  if [ ! -s "$OMNI_INDEX" ]; then omni_build_index; return; fi
  if [ -n "$(find "$OMNI_SEM_DIR" -newer "$OMNI_INDEX" -print -quit 2>/dev/null)" ]; then
    omni_build_index
  fi
}

# Run directly (e.g. `index.sh`) -> force a rebuild.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  omni_build_index
  printf 'omni: indexed %s entries under %s\n' "$(wc -l < "$OMNI_INDEX")" "$OMNI_SEM_DIR"
fi
