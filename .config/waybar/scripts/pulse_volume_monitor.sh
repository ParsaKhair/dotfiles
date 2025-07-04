#!/bin/bash

# Replace '1' with the signal number you configured in Waybar for custom/volume-bar
WAYBAR_VOLUME_SIGNAL=1

# Find the PID of Waybar
WAYBAR_PID=$(pgrep waybar)

if [[ -z "$WAYBAR_PID" ]]; then
  echo "Waybar is not running."
  exit 1
fi

pactl subscribe | grep --line-buffered "sink" | while read -r event; do
  echo "Detected volume change"
  VOL=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '\d+%' | head -1 | tr -d '%')
  echo "Volume: $VOL"
  echo "$VOL" >"/home/parsa/.cache/waybar_volume_level"
  pkill -RTMIN+"$WAYBAR_VOLUME_SIGNAL" waybar
done
