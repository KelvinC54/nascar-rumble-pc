# Tool reference

The tools find the workspace from their own location: the parent of `tools/`. Override it with `NR_ROOT`. They read the disc path from `nascar-rumble-recomp/game.toml`; override it with `NR_DISC`. On Windows, run Python with `-X utf8` if the console has trouble with Unicode.

## Disc and format research

| Tool | Purpose |
|---|---|
| `extract_disc.py <game.bin> <out>` | Extract the ISO9660 filesystem from a MODE2/2352 `.bin` |
| `walk_chunks.py <file>` | List the reversed-FourCC chunks of a `.TRK` / `.PSX` container |
| `shoc_resources.py <file> [out]` | List and reassemble EA SHOC resources (SHDR / SDAT) |
| `page_chunks.py <page.bin>` | List the sub-blocks of a `pag` texture page |
| `scan_formats.py <file>…` | Look for known texture signatures (TIM, SHPP, …) |
| `extract_textures.py <out> <file>… [--mips]` | Write texture pages as PNG |
| `dump_raw_blocks.py <out> <file>…` | Write raw PIX blocks and CLUTs for hashing |
| `xxh3sum.c` | XXH3-64 of files (the same hash DuckStation pack names use) |
| `mips_dis.py` | Minimal R3000 disassembler, used to find the demo track roll |

## Driving the game

| Tool | Purpose |
|---|---|
| `psxdbg.py` | Client for the debug server (debug build, TCP 4370, one request per connection) |
| `find_track_var.py` | Find the RAM bytes for the selected location and track |
| `drive.ps1 -Keys "X,Return" -Shot out.png` | Send keypresses to the game window and take a screenshot |
| `capture_all.py` | Unattended HD dump capture over all demo tracks |
| `shot_probe.py <label> [--pack dir\|none]` | Headless hi-res screenshots for comparing packs |

## HD pack

| Tool | Purpose |
|---|---|
| `build_pack.py stage / finalize` | Build the pack (see [guide 2](2-hd-textures.md)) |
| `ai_gate.py <work>` | Score how much detail the AI upscale kept |
| `compare_sheet.py <work> <out.png>` | Comparison sheet: nearest, Lanczos, AI |

## Performance

| Tool | Purpose |
|---|---|
| `perf_probe.sh <label> <secs>` | Headless guest fps log (`BUILD=` selects the build folder) |
| `hd_probe.py` | HD texture counter deltas (debug build) |
| `sampler.c` + `sampler_report.py` | Sampling profiler and symbolizer |
| `pgo_build.sh [dir] [PGXP] [secs]` | Manual PGO build |
| `nrpaths.py` | Shared workspace and disc path resolution |
