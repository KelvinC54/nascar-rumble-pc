# 1. Build the native game

This guide turns your own NASCAR Rumble disc into a native Windows executable with psxrecomp, then applies this repo's patches and builds two variants:

| Build | Folder | Use |
|---|---|---|
| **Fast** (PGO, no PGXP) | `build-nopgxp` | Smooth races. This is the default launcher. |
| **PGXP** | `build-release` | No polygon wobble or texture warping, but about 25% more CPU in races |
| **Debug** (optional) | `build-debug` | Debug server on TCP 4370. Needed for the texture capture in guide 2. |

All commands assume the workspace is `C:\NascarPC` (this repo) and your disc is at `C:\Games\NASCAR Rumble\NASCAR Rumble.cue`. Change both to match your setup.

## 1.1 Get the workspace, toolchain and psxrecomp

In PowerShell:

```powershell
git clone https://github.com/KelvinC54/nascar-rumble-pc C:\NascarPC
cd C:\NascarPC

# Portable clang + cmake + ninja (the toolchain psxrecomp uses on Windows)
Invoke-WebRequest https://github.com/RetroPortingToolKit/RetroPorting-Toolchains/releases/download/v1.0.14/cmake-clang-v1-windows-x64.zip -OutFile toolchain.zip
Expand-Archive toolchain.zip -DestinationPath toolchain   # toolchain\bin\clang.exe must exist
Remove-Item toolchain.zip

# psxrecomp itself (only its new-project wizard is used from this copy)
git clone https://github.com/RetroPortingToolKit/psxrecomp.git psxrecomp
```

If the zip extracts into a nested folder, move its contents so that `C:\NascarPC\toolchain\bin\clang.exe` exists.

> **Important (Windows):** psxrecomp's scripts need **Git Bash**, not WSL. Before building, put the toolchain and Git first on `PATH` in every shell you use:
>
> ```powershell
> $env:PATH = "C:\NascarPC\toolchain\bin;C:\Program Files\Git\bin;$env:PATH"
> $env:TOOLCHAIN_DIR = "C:\NascarPC\toolchain"
> ```
>
> With a plain `bash` on `PATH`, Windows may start WSL bash instead, and the build fails in confusing ways.

## 1.2 Generate the game project from your disc

The psxrecomp new-project wizard does the following:

- Probes your disc and checks it against known USA dumps.
- Extracts only the boot executable.
- Seeds the function list.
- Recompiles the MIPS code into C, under `nascar-rumble-recomp\generated\`.
- Builds once.

```powershell
powershell -ExecutionPolicy Bypass -File psxrecomp\tools\new_project_layout\setup_project.ps1 `
  -Disc 'C:\Games\NASCAR Rumble\NASCAR Rumble.cue' -Dir C:\NascarPC `
  -Name NascarRumbleRecomp -GithubRepo nascar-rumble-recomp -Players 2 -Yes `
  -EnableRecompUi -NoNetplay -NoCi -FetchBoxart -NoGithub -Generate -EnableBuild *> setup.log
```

It creates `C:\NascarPC\nascar-rumble-recomp\`, a local git repo with its own copy of psxrecomp as a submodule.

- **"Generate failed" is a known false error.** Windows PowerShell 5.1 treats git's CRLF warnings on stderr as fatal and reports `Generate failed` even when generation worked. If `nascar-rumble-recomp\generated\SLUS_010.68_full_00.c` and similar files exist, it worked.
- **A 1-track `.cue` gives a warning about netplay and catalog gates.** That is fine for single-player.
- **The boxart fetch may 404.** That is harmless.

## 1.3 Apply this repo's patches

```powershell
cd C:\NascarPC\nascar-rumble-recomp
git apply ..\patches\project-pgxp-option.diff                 # NASCAR_PGXP CMake option + internal_resolution
git -C psxrecomp apply ..\..\patches\psxrecomp-hd-texture-perf.diff
```

The patches do the following:

- **`project-pgxp-option.diff`** turns PGXP into a CMake option (`-DNASCAR_PGXP=OFF` for the fast build). It also makes 3D render at the display's resolution by default.
- **`psxrecomp-hd-texture-perf.diff`** has two runtime fixes that matter once an HD pack is loaded:
  - **`gpu_hd_textures.cpp`:** when the largest replacement already covers a draw, the draw uses it directly. Without this, the CPU builds a new composited image every draw, thousands of times per second.
  - **`duckstation_texture_pack.cpp`:** a lazy 64×64-tile occupancy grid lets VRAM-write invalidation skip writes that touch no tracked texture. Without it, every invalidation walks every tracked rectangle.

  See [performance notes](3-performance.md).

The patches were made against psxrecomp commit `a7b37e07`, and they also apply to master as of November 2026. If `git apply` fails on a newer master, pin the framework to that commit and regenerate the game C before building:

```sh
git -C psxrecomp checkout a7b37e079e8c6e98e04cd1cd42ba559e95911ea7
git -C psxrecomp submodule update --init --recursive
git -C psxrecomp apply ../../patches/psxrecomp-hd-texture-perf.diff
python psxrecomp/psxrecomp_cli.py generate --config game.toml --project-root .
```

## 1.4 Build

Open **Git Bash** (with `PATH` set as above, or `export PATH="/c/NascarPC/toolchain/bin:/c/Program Files/Git/bin:$PATH"`).

**PGXP build** (`build-release`):

```sh
cd /c/NascarPC/nascar-rumble-recomp
python psxrecomp/psxrecomp_cli.py rebuild --config game.toml --project-root . --build-dir build-release --no-pgo
```

**Fast build** (`build-nopgxp`, PGO trained on a demo race; it takes about 15 minutes):

```sh
sh /c/NascarPC/tools/pgo_build.sh build-nopgxp OFF 200
```

1. The script builds an instrumented exe with the debug server.
2. It runs the game headless into the attract demo for 200 s and quits it cleanly through the debug server, so the profile is written.
3. It merges the profile and rebuilds optimized.

Always use a **fresh** build folder. Don't use the CLI's `--force-pgo`: release builds have no debug `quit`, so no profile gets written, and the CLI also resets `NASCAR_PGXP`.

**Debug build** (`build-debug`, only needed for guide 2):

```sh
T=/c/NascarPC/toolchain/bin
cmake -S . -B build-debug -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSX_DEBUG_TOOLS=ON \
  -DCMAKE_C_COMPILER=$T/clang.exe -DCMAKE_CXX_COMPILER=$T/clang++.exe -DCMAKE_MAKE_PROGRAM=$T/ninja.exe
cmake --build build-debug
```

Building everything compiles about 400 files. If CMake says `unknown target`, just build all targets as shown.

## 1.5 Play

Copy `launchers\*.bat` to `C:\NascarPC\`. Then open each one and set `DISC=` to your `.cue` file.

| Setting (in the .bat) | Meaning |
|---|---|
| `PSX_INTERNAL_RESOLUTION` | `display` (match the monitor), or `4x`, `8x`, `4k`, … |
| `PSX_SUPERSAMPLE` | `1` = off. `1.5` gives smoother edges but costs GPU. |
| `PSX_PERSPECTIVE_TEXTURING` | `1` = no affine texture swimming |
| `PSX_GEOMETRY_CORRECTION` | `1` = PGXP. Only has an effect in the PGXP build. |

Controls:

- **F11 or Alt+Enter** toggles fullscreen.
- **Keyboard:** X is Cross and Enter is Start.
- **Gamepads** work through the launcher's input settings. Start the exe without `--no-launcher` to get the launcher UI.

## 1.6 Install the demo-track mod (for guide 2)

Copy the mod into each build that should have it. The capture only needs the debug build.

```sh
mkdir -p build-debug/mods/installed
cp -r /c/NascarPC/mods-src/nascar.demo-track build-debug/mods/installed/
```

The mod patches two instructions in the attract-demo setup:

- `0x80089568`: the location roll `rand() % (unlocked+4)`.
- `0x800895A8`: the track roll `rand() % 3`.

Both become constants (`addiu v1/v0, zero, N`) taken from the mod options `location` (0–7) and `track` (0–2). Players never see the difference; the demo just always races the chosen track.
