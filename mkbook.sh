#!/bin/bash

BASEDIR=$(dirname $(realpath $0))
docker build -t ryu-book:latest -f Dockerfile .
docker run -it \
       --mount "type=bind,source=$BASEDIR,target=/home/osrg/ryu-book" \
       --name ryubook ryu-book:latest

ZOMBIES="$(docker ps -aq -f status=exited)"
[ -z "$ZOMBIES" ] || docker rm "$ZOMBIES"

DANGLING="$(docker image ls -aq -f dangling=true)"
[ -z "$DANGLING" ] || docker rmi "$DANGLING"
