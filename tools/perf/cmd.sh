#!/bin/sh
# usage: cmd.sh "/command"
export DISPLAY=:99
xdotool key t; sleep 0.6; xdotool type --delay 15 "$1"; sleep 0.3; xdotool key Return; sleep 0.5
