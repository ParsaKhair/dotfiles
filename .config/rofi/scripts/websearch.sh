#!/usr/bin/env bash

query=$(rofi -dmenu -p "Search")

[ -z "$query" ] && exit 0

librewolf "https://duckduckgo.com/?q=$(printf '%s' "$query" | jq -sRr @uri)"
