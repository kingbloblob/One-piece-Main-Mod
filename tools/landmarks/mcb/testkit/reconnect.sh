#!/bin/bash
export DISPLAY=:99
xdotool mousemove 798 536 click 1; sleep 2
xdotool mousemove 800 773 click 1; sleep 2
xdotool key ctrl+a; xdotool type --delay 50 "localhost:25565"; sleep 1; xdotool key Return; sleep 20
python3 /root/rcon.py "gamemode spectator Tester" "time set noon"
