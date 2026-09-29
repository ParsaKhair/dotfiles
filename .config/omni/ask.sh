#!/usr/bin/env bash
# omni — LLM fallback ("rigorous" path).
# Usage: ask.sh "free text request"
# Hands the request to Claude Code headless with a small, safe set of
# desktop-action tools.  This is the slow path (a few seconds), used only when
# the deterministic router finds no match — or when you explicitly force it.
set -uo pipefail

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$self_dir/config.sh"
# shellcheck source=/dev/null
source "$self_dir/lib.sh"

query="$*"
[ -z "${query// }" ] && exit 0

command -v claude >/dev/null 2>&1 || {
  notify-send "omni" "claude CLI not found on PATH"; exit 1
}

notify-send -t 2000 "omni · thinking" "$query"

sys="You are a desktop command router on a Hyprland/Wayland Fedora machine.
Prefer to DO the action with a single shell command rather than explain it.
Openers: PDFs and generic files -> '$PDF_CMD <path>' (falls back to xdg-open);
folders / 'show in ranger' -> '$TERMINAL -e $FILE_MANAGER <path>';
editing -> '$TERMINAL -e $EDITOR_CMD <path>'; web URLs -> 'librewolf <url>';
window/desktop control -> hyprctl.
Course files live under '$OMNI_SEM_DIR', organised as <course>/<...>. Course
short-names look like phys5531, be5570. Canvas base is $CANVAS_BASE.
Be terse: run the command, then reply with one short line of what you did."

model_args=()
[ -n "${OMNI_MODEL:-}" ] && model_args=(--model "$OMNI_MODEL")

out="$(claude -p "$query" \
  "${model_args[@]}" \
  --append-system-prompt "$sys" \
  --add-dir "$DOCS_ROOT" \
  --allowedTools \
      "Bash(xdg-open:*)" "Bash(zathura:*)" "Bash(librewolf:*)" \
      "Bash(hyprctl:*)" "Bash($TERMINAL:*)" "Bash($FILE_MANAGER:*)" \
      "Bash(ls:*)" "Bash(find:*)" "Bash(rg:*)" "Bash(cat:*)" "Bash(echo:*)" \
      Read Glob Grep \
  2>/dev/null)"

if [ -n "${out// }" ]; then
  notify-send "omni" "$out"
else
  notify-send "omni" "done"
fi
