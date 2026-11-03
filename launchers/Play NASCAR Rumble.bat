@echo off
rem Fast build (PGO, no PGXP). F11 / Alt+Enter = fullscreen.
rem Put this file in the workspace root (next to nascar-rumble-recomp\) and set DISC
rem to YOUR OWN dump's .cue file.
set DISC=C:\Games\NASCAR Rumble\NASCAR Rumble.cue
rem 3D renders at your monitor's resolution; try 4x, 8x, 4k instead of "display".
set PSX_INTERNAL_RESOLUTION=display
rem Supersample: 1.5 = smoother edges but heavier on the GPU.
set PSX_SUPERSAMPLE=1
set PSX_PERSPECTIVE_TEXTURING=1
cd /d "%~dp0nascar-rumble-recomp\build-nopgxp"
start "" NascarRumble_Recompiled.exe --no-launcher --game ..\game.toml --disc "%DISC%"
