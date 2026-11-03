#!/bin/sh
# Manual PGO build of a variant dir (default build-nopgxp, PGXP off):
# instrumented build with debug tools -> headless demo-race train -> clean debug quit
# -> llvm-profdata merge -> optimized build (debug tools off).
# Use a fresh build dir (a cache made by another configure may reset options).
# usage: sh pgo_build.sh [build-dir] [NASCAR_PGXP ON|OFF] [train-seconds]
set -e
HERE=$(cd "$(dirname "$0")" && pwd -W)
ROOT=$(cygpath -u "$(python -I -c "import sys; sys.path.insert(0, r'$HERE'); import nrpaths; print(nrpaths.ROOT)")")
DISC=$(python -I -c "import sys; sys.path.insert(0, r'$HERE'); import nrpaths; print(nrpaths.DISC)")
T=$ROOT/toolchain/bin
export PATH="$T:/c/Program Files/Git/bin:$PATH"
B=${1:-build-nopgxp}; PG=${2:-OFF}; SECS=${3:-200}
cd "$ROOT/nascar-rumble-recomp"
cfg() { cmake -S . -B $B -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=$T/clang.exe \
  -DCMAKE_CXX_COMPILER=$T/clang++.exe -DCMAKE_MAKE_PROGRAM=$T/ninja.exe -DPSXRECOMP_REQUIRE_GAME_C=ON \
  -DNASCAR_PGXP=$PG "$@" > /dev/null; }
cfg -DPSX_PGO=generate -DPSX_DEBUG_TOOLS=ON
cmake --build $B > /dev/null
rm -rf $B/pgo; mkdir -p $B/pgo
cd $B
env LLVM_PROFILE_FILE="$PWD/pgo/run-%p.profraw" PSX_DEBUG_SERVER=1 PSX_HOST_MUTE=1 PSX_INTERNAL_RESOLUTION=display \
  PSX_SUPERSAMPLE=1.5 PSX_PERSPECTIVE_TEXTURING=1 ./NascarRumble_Recompiled.exe --no-launcher --headless-opengl \
  --game ../game.toml --disc "$DISC" --debug-port 4370 > pgo/train.log 2>&1 &
sleep $SECS
python -I -c "import sys; sys.path.insert(0, r'$HERE'); from psxdbg import Psx; Psx().cmd('quit')"
wait
cd ..
llvm-profdata merge -o $B/pgo/default.profdata $B/pgo/*.profraw
cfg -DPSX_PGO=use -DPSX_DEBUG_TOOLS=OFF
cmake --build $B > /dev/null
ls -la $B/NascarRumble_Recompiled.exe $B/pgo/default.profdata
