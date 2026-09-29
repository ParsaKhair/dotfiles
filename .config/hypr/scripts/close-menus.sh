#!/usr/bin/env bash

swaync-client -cp -sw >/dev/null 2>&1 &
gapplication action org.waybar.ConnectivityPanel close >/dev/null 2>&1 &
wait
