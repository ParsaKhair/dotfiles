#!/bin/bash

# Path to a temporary file to store the display state and timestamp
STATE_FILE="~/.cache/waybar_volume_state"
TIMEOUT_SECONDS=2 # How long the volume bar should be visible

# % values     0   1-2 2-3 3-4 4-5 5-6 6-7 7-8
PARTIAL_CHARS=(" " "▏" "▎" "▍" "▌" "▋" "▊" "▉" "█")
BAR_EMPTY=" "
FULL_BLOCK="█"
# Returns % volume (e.g. calling when volume @ 73% returns 73)
get_volume() {
  pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '[0-9]+(?=%)' | head -n 1
}

generate_volume_bar() {
  local volume=$1
  local bar_length=20 #20 full blocks

  local bar_string=""
  local num_full_block=$((volume / 10))
  local remainder=$((volume % 10))

  for ((i = 0; i < num_full_block; i++)); do
    bar_string+="$FULL_BLOCK"
  done

  # remap numbers 0-9 to 0-7 to get correct partial bar
  local partial_index=$((remainder * 8 / 10))
  bar_string+="${PARTIAL_CHARS[$partial_index]}"

  # Pads bar with empty space. Checks if remainder to take into consideration
  local total_bar_length=10 # full bar length
  local current_visual_length=$((num_full_block + (remainder > 0 ? 1 : 0)))

  for ((i = current_visual_length; i < total_bar_length; i++)); do
    bar_string+=" "
  done

  echo "$bar_string"
}

main() {
  CURRENT_VOLUME=$(get_volume)
  NOW=$(date +%s)

  # Read previous state
  if [[ -f "$STATE_FILE" ]]; then
    read -r LAST_CHANGE_TIME LAST_VOLUME <"$STATE_FILE"
  else
    LAST_CHANGE_TIME=0
    LAST_VOLUME=$CURRENT_VOLUME # Initialize with current volume if no state file
  fi

  # Determine if volume has changed (allowing for slight jitter if necessary, but exact check is fine)
  if [[ "$CURRENT_VOLUME" -ne "$LAST_VOLUME" ]]; then
    # Volume changed, update state file and reset timer
    echo "$NOW $CURRENT_VOLUME" >"$STATE_FILE"
    LAST_CHANGE_TIME="$NOW"
    LAST_VOLUME="$CURRENT_VOLUME"
  fi

  # Determine if the bar should be visible based on the timer
  if ((NOW - LAST_CHANGE_TIME < TIMEOUT_SECONDS)); then
    local volume_bar=$(generate_volume_bar "$CURRENT_VOLUME")
    # Output the JSON for Waybar
    echo "$volume_bar"
  else
    # No recent change, hide the bar
    # Output empty JSON object to hide the module (thanks to hide-empty-text: true)
    echo ""
    # Clean up the state file if it exists and the bar is hidden
    if [[ -f "$STATE_FILE" ]]; then
      rm "$STATE_FILE"
    fi
  fi
}

main
