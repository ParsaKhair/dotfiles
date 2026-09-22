#!/usr/bin/env bash

# Display a transient layer-shell OSD without adding to notification history.
volume=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oE '[0-9]+%' | head -n 1 | tr -d '%')
muted=$(pactl get-sink-mute @DEFAULT_SINK@ | awk '{print $2}')
[[ $volume =~ ^[0-9]+$ ]] || exit 1

if [[ $muted == yes ]]; then
  progress=0
else
  progress=$volume
  (( progress > 100 )) && progress=100
fi

exec /usr/bin/python3 "$(dirname -- "$0")/volume-osd.py" "$progress" "$muted"
