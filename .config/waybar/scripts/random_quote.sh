#!/usr/bin/env bash
# Print one random quote from quotes.txt as Waybar JSON.

QUOTES_FILE="$HOME/.config/waybar/quotes.txt"

# If the file doesn't exist or isn't readable, bail
if [ ! -r "$QUOTES_FILE" ]; then
  jq -cn '{text: "", tooltip: "No quotes file", class: "empty"}'
  exit 0
fi

# Pick a random non-blank line, trimming stray whitespace and CRs
quote="$(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$QUOTES_FILE" \
  | grep -v '^$' | shuf -n 1)"

# jq handles escaping; the full quote also goes in the tooltip in case
# Waybar truncates it.
jq -cn --arg q "$quote" '{text: $q, tooltip: $q, class: "quote"}'
