#!/bin/bash

if test -z "$1"
then
    set 5 $2
fi

if test -z "$2"
then
    set $1 'test'
fi

arecord --device=hw:1,0 --format S16_LE --rate 44100 -c1 "${2}.wav" &
pid=`ps -a | grep "arecord"`
pid=${pid% * *}
pid=${pid%/*}
pid=${pid% *}
sleep ${1}s
kill $pid

# ffmpeg -i  "${2}.wav" -vn -ar 44100 -ac 1 -b:a 128k "${2}.mp3"
# rm "${2}.wav"