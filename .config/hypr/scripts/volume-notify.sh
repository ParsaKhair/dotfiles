#!/bin/bash

# Get volume and mute status
volume=$(pactl get-sink-volume @DEFAULT_SINK@ | awk '{print $5}' | tr -d '%')
muted=$(pactl get-sink-mute @DEFAULT_SINK@ | awk '{print $2}')

# Choose icon
if [ "$muted" = "yes" ]; then
  icon="🔇"
  bar="🔘"
else
  if [ "$volume" -lt 30 ]; then
    icon="🔈"
  elif [ "$volume" -lt 70 ]; then
    icon="🔉"
  else
    icon="🔊"
  fi

  # Build bar (20 characters)
  filled=$((volume / 5))
  empty=$((20 - filled))
  bar=$(printf "%${filled}s" | tr 'o' 'x')$(printf "%${empty}s" | tr ' ' ' ')
fi

# Send notification
dunstify -h string:x-dunst-stack-tag:volume_notification --appname="volume" -r 9993 -u low "Volume: $volume%" "$bar"
