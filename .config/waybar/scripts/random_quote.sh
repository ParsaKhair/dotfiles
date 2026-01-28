#!/usr/bin/env bash

QUOTES_FILE="$HOME/.config/waybar/quotes.txt"

# If the file doesn't exist or isn't readable, bail
if [ ! -r "$QUOTES_FILE" ]; then
  echo "No quotes file"
  exit 1
fi

# Pick a random line
quote="$(shuf -n 1 "$QUOTES_FILE")"

# For simplicity, just output the quote as plain text
# Waybar will handle it as-is.
echo "$quote"
