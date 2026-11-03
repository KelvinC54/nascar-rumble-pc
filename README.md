# NASCAR Rumble on PC: native recompile toolkit

Tools, patches and step-by-step guides for running **NASCAR Rumble** (PlayStation, 2000, SLUS-01068) natively on Windows. It uses static recompilation ([psxrecomp](https://github.com/RetroPortingToolKit/psxrecomp)), not an emulator. On top of the base port it adds:

- **High resolution rendering.** 3D renders at your monitor's resolution or higher, with optional supersampling and perspective-correct texturing.
- **An HD texture pack pipeline.** It pulls the original textures off *your* disc, captures how the game recolours them at runtime, upscales them (Real-ESRGAN plus Lanczos, with a quality gate), and writes a DuckStation-format pack.
- **Race performance fixes.** These include two runtime patches, a no-PGXP build and a PGO build. On a laptop with an integrated GPU, races went from about 10–16 fps to about 50–60 fps.
- **A demo-track picker mod.** It makes the attract demo race a chosen track, so every track can be captured unattended.

> ## ⚠️ Disclaimer: fan made, not a game distribution
>
> This is an unofficial, non-commercial **fan project**, made as a hobby to help people who own the game play it on a PC. It is not affiliated with or endorsed by Electronic Arts, NASCAR or Sony.
>
> **This repository does not contain the game.** It contains no disc image, executable, game code (original or recompiled), textures, audio, video or texture pack. Everything game-related is produced locally on your own machine from **your own legally obtained copy** of the disc. Please do not open issues asking for game files, and do not upload builds or texture packs made from the game.
>
> ---
>
> **Indonesia:** Ini proyek **buatan fan (fan made)**. Tidak resmi, tidak komersial, dan tidak berafiliasi dengan EA, NASCAR, maupun Sony. Proyek ini **tidak bermaksud mendistribusikan game berlisensi**. Repo ini tidak berisi file game apa pun: tidak ada ISO/BIN, exe, kode game, tekstur, maupun texture pack. Semuanya dibuat sendiri di PC kamu dari **disc/backup milikmu sendiri**. Dibuat hanya untuk hobi dan untuk membantu orang lain yang ingin memainkan game ini di PC.

## What you need

- **Your own NASCAR Rumble (USA) disc or backup** as a `.cue` + `.bin` file.
- **Windows 10 or 11 (x64)** and a GPU with OpenGL 3.3.
- **[Git for Windows](https://git-scm.com/download/win)**, which provides the Git Bash shell.
- **Python 3.10 or newer**, then run `pip install pillow numpy`.
- **About 15 GB of free disk space** for the toolchain, the generated code and the builds.
- **Optional, for the HD textures:** a Vulkan GPU for Real-ESRGAN. Without one, the pipeline falls back to Lanczos.

## Guides

| Step | Guide | Result |
|---|---|---|
| 1 | [Build the native game](docs/1-build.md) | `NascarRumble_Recompiled.exe` running from your disc |
| 2 | [HD texture pack](docs/2-hd-textures.md) | Sharper track, sky and car textures, built from your disc |
| 3 | [Performance notes](docs/3-performance.md) | Why races lagged, what fixed it, and how to profile |
| – | [Tool reference](docs/tools.md) | What each script in `tools/` does |

## Repository layout

```
tools/        Python / shell / C helper tools (no binaries)
patches/      psxrecomp runtime patch + project CMake/game.toml patch
mods-src/     nascar.demo-track mod (declarative psxrecomp mod package)
launchers/    Play NASCAR Rumble.bat (fast) and (PGXP).bat
docs/         step-by-step guides
```

The guides assume this repository **is your workspace folder**. The toolchain, the psxrecomp checkout, the game project and the work folders are all created inside it and git-ignored. For example:

```
C:\NascarPC\            <- git clone of this repo
  toolchain\            <- portable clang/cmake/ninja (step 1)
  nascar-rumble-recomp\ <- generated game project + builds (step 1)
  disc-extract\  raw-blocks\  pack-work\   <- texture work (step 2)
```

## Credits

- [psxrecomp / RetroPortingToolKit](https://github.com/RetroPortingToolKit/psxrecomp) provides the recompiler, runtime, launcher and mod system. Its own license (PolyForm Noncommercial 1.0.0) applies to it and to the patches in `patches/`, which modify it.
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) by Xintao Wang et al. is used for the AI upscaling.
- The texture pack naming is the format DuckStation uses for texture replacements.

## License

The original tools, docs and mod in this repository are released under the [MIT License](LICENSE). The files in `patches/` are modifications of psxrecomp and stay under psxrecomp's PolyForm Noncommercial license. *NASCAR Rumble* and all of its content belong to their respective owners.
