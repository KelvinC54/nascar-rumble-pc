@echo off
rem Default build with PGXP: no polygon wobble / texture warping, ~25% more CPU in races.
rem Put this file in the workspace root and set DISC to YOUR OWN dump's .cue file.
set DISC=C:\Games\NASCAR Rumble\NASCAR Rumble.cue
set PSX_INTERNAL_RESOLUTION=display
set PSX_SUPERSAMPLE=1.5
set PSX_GEOMETRY_CORRECTION=1
set PSX_PERSPECTIVE_TEXTURING=1
rem Use the key / gamepad bindings set in "NASCAR Rumble Settings.bat".
for %%f in (keybinds.ini input.ini) do if exist "%~dp0nascar-rumble-recomp\build-nopgxp\%%f" copy /y "%~dp0nascar-rumble-recomp\build-nopgxp\%%f" "%~dp0nascar-rumble-recomp\build-release\" >nul
cd /d "%~dp0nascar-rumble-recomp\build-release"
start "" NascarRumble_Recompiled.exe --no-launcher --game ..\game.toml --disc "%DISC%"
