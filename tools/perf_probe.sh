#!/bin/sh
# Run a build headless into the attract demo and log guest fps every 2 s.
# usage: [BUILD=build-nopgxp] sh perf_probe.sh <label> <seconds> [ENV=VAL ...]   (log: <workspace>/perf_<label>.log)
HERE=$(cd "$(dirname "$0")" && pwd -W)
DISC=$(python -I -c "import sys; sys.path.insert(0, r'$HERE'); import nrpaths; print(nrpaths.DISC)")
ROOT=$(cygpath -u "$(python -I -c "import sys; sys.path.insert(0, r'$HERE'); import nrpaths; print(nrpaths.ROOT)")")
cd "$ROOT/nascar-rumble-recomp/${BUILD:-build-release}" || exit 1
label=$1; secs=$2; shift 2
env PSX_RUNTIME_PERF_DIAG=1 PSX_RUNTIME_PERF_DIAG_MS=2000 "$@" ./NascarRumble_Recompiled.exe --no-launcher \
  --headless-opengl --game ../game.toml --disc "$DISC" \
  > ../../perf_$label.log 2>&1 &
sleep "$secs"
taskkill //IM NascarRumble_Recompiled.exe //F > /dev/null
grep -o "guest=[0-9.]* Hz\|cpu=[0-9.]* tex=[0-9.]* draw=[0-9.]*\|work guest=[0-9.]*" ../../perf_$label.log \
  | paste -d' ' - - - | awk -v l=$label '{print l": "$0}'
