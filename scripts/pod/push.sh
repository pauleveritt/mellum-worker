#!/usr/bin/env bash
# From the Mac: copy this commit to a running pod and set it up. No git remote is involved, so an
# unpushed commit can be tested as it stands. Renting the pod is a separate, per-rental yes.
#
#   scripts/pod/push.sh HOST PORT
set -euo pipefail
host="${1:?usage: scripts/pod/push.sh HOST PORT}"
port="${2:?usage: scripts/pod/push.sh HOST PORT}"
cd "$(dirname "$0")/../.."
remote="/opt/mellum/repo"
ssh="ssh -p $port -o StrictHostKeyChecking=accept-new root@$host"
$ssh "mkdir -p $remote /opt/mellum/done && rm -f /opt/mellum/done/lock"
git archive HEAD | $ssh "tar -x -C $remote"
$ssh "echo $(git rev-parse HEAD) > $remote/REVISION"
$ssh "bash $remote/scripts/pod/bootstrap.sh"
