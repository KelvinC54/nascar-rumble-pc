@echo off
rem Opens the psxrecomp launcher before the game: Controls page = keyboard / gamepad
rem remapping (saved to keybinds.ini / input.ini), then press LAUNCH to play.
rem The Play bats reuse these bindings, so run this once and then play normally.
rem Put this file in the workspace root and set DISC to YOUR OWN dump's .cue file.
set DISC=C:\Games\NASCAR Rumble\NASCAR Rumble.cue
set PSX_INTERNAL_RESOLUTION=display
set PSX_SUPERSAMPLE=1
set PSX_PERSPECTIVE_TEXTURING=1
cd /d "%~dp0nascar-rumble-recomp\build-nopgxp"
start "" NascarRumble_Recompiled.exe --launcher --game ..\game.toml --disc "%DISC%"
