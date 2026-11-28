#!/usr/bin/env bash
# Pause or resume running training jobs (train_sft.py) so the Mac is free for a while.
#   r1d/pause.sh          freeze them (SIGSTOP): the GPU goes idle, nothing is lost
#   r1d/pause.sh resume   carry on from the exact point they stopped (SIGCONT)
#   r1d/pause.sh status   show them and whether they are paused
# A paused job keeps its memory (about 11-19 GB for the 1.5B); macOS may swap it out if something needs the room.
set -u
PAT=${PAUSE_PATTERN:-train_sft.py}
pids=$(pgrep -f "python.*$PAT" || true)
[ -z "$pids" ] && { echo "no job matching $PAT"; exit 0; }
case "${1:-pause}" in
  pause)  kill -STOP $pids && echo "paused: $pids" ;;
  resume) kill -CONT $pids && echo "resumed: $pids" ;;
  status) ps -o pid=,stat=,etime=,rss= -p $(echo $pids | tr ' ' ',') | awk '{s=($2 ~ /T/)?"PAUSED":"running"; printf "%s %s up %s, %.1f GB\n",$1,s,$3,$4/1048576}' ;;
  *) echo "usage: $0 [pause|resume|status]"; exit 1 ;;
esac
