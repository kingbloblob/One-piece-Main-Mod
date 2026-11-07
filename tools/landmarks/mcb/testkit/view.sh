#!/bin/bash
# view.sh out.png x y z fx fy fz [wait]
python3 /root/rcon.py "tp Tester $2 $3 $4 facing $5 $6 $7" >/dev/null
sleep ${8:-12}
python3 /root/shot.py $1 >/dev/null
