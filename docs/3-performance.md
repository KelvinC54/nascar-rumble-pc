# 3. Performance notes

The test machine was a laptop with a Ryzen 5 6600H and its Radeon iGPU (2 GB of shared VRAM). With the HD pack loaded, races ran at **10–16 fps** while GPU load stayed low. The cause was **CPU**, not GPU.

Here is how it was found and fixed, so you can do the same on your machine.

## Measuring

```sh
BUILD=build-nopgxp sh tools/perf_probe.sh mytest 150
```

This runs a build headless into the attract demo race with `PSX_RUNTIME_PERF_DIAG=1` and prints the guest frame rate every 2 s. Headless runs are **not** throttled, and 60 Hz is full speed for this game.

Use `python tools/hd_probe.py --pack <dir>` (debug build) to print per-10-s deltas of the HD texture counters:

- `composition_builds`
- `gl_uploads`
- `decode_evictions`
- and others

## Profiling

The exe ships with a COFF symbol table, so a very small sampling profiler is enough:

```sh
toolchain/bin/clang -O2 tools/sampler.c -o tools/sampler.exe -lpsapi -lwinmm
tools/sampler.exe <pid> 20 > samples.txt          # pid from Task Manager while racing
python tools/sampler_report.py nascar-rumble-recomp/build-nopgxp/NascarRumble_Recompiled.exe samples.txt 25
```

## What was slow and what fixed it

| Cause | Symptom | Fix |
|---|---|---|
| 4x pack = 1.9 GB decoded, over the 512 MiB preload cap | constant decode/evict churn | `finalize --scale 2` |
| Draws straddling many small dumped crops | 3,000–6,000 per-draw CPU compositions per second | `finalize --merge`, plus runtime fast path (`gpu_hd_textures.cpp`) |
| VRAM-write invalidation scanning every tracked rect | about 12% CPU | occupancy-grid early-out (`duckstation_texture_pack.cpp`) |
| PGXP geometry precision | about 23% CPU in races | `-DNASCAR_PGXP=OFF` build |
| General | — | PGO (`tools/pgo_build.sh`) |

The result was about **50–60 fps** in headless demo races, against 10–16 before.

Other tips:

- **Little GPU headroom:** keep `PSX_SUPERSAMPLE=1` and try a fixed `PSX_INTERNAL_RESOLUTION` such as `4x` instead of `display`.
- **Polygon wobble bothers you and your CPU is fast:** use the PGXP launcher.
- **What's left on the CPU:** the rest of the frame time is the emulated game itself, the software rasterizer path (about 10%), GL driver work, and HD texture matching (about 5–7%).
