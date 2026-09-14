#!/usr/bin/env bash

# Replace the previous volume toast and show SwayNC's native progress bar.
volume=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oE '[0-9]+%' | head -n 1 | tr -d '%')
muted=$(pactl get-sink-mute @DEFAULT_SINK@ | awk '{print $2}')
[[ $volume =~ ^[0-9]+$ ]] || exit 1

if [[ $muted == yes ]]; then
  label="Muted"
  progress=0
else
  label="${volume}%"
  progress=$volume
  (( progress > 100 )) && progress=100
fi

notify-send --app-name="Volume" --urgency=low --expire-time=1800 \
  --hint=string:x-canonical-private-synchronous:volume \
  --hint="int:value:$progress" "Volume" "$label"
