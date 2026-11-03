# 2. HD texture pack (built from your own disc)

The psxrecomp runtime loads **DuckStation-format** texture replacement packs. This guide builds a pack for NASCAR Rumble entirely from your own disc.

```
your disc ──extract_disc──► disc-extract/ ──dump_raw_blocks──► raw-blocks/   (original texture pages)
debug build + demo mod ──capture_all──► dumps/                               (how the game draws them)
raw-blocks + dumps ──build_pack stage──► pack-work/staged                    (full pages, runtime palettes)
staged ──Real-ESRGAN──► pack-work/upscaled ──ai_gate──► scores
build_pack finalize (--merge --skip-ui --scale 2) ──► texture-packs/SLUS-01068-hd/replacements
```

Run everything from Git Bash in the workspace (`cd /c/NascarPC`), with `pip install pillow numpy` done. Guide 1 must be complete, including the **debug build** and the **demo-track mod**.

## Why it is not a simple "dump and upscale"

1. **Textures come from EA SHOC containers.** The `.TRK` (per track) and `GLBLDATA.PSX` / `FE.TRK` files are chunked containers whose FourCC tags are stored reversed. Textures are `pag` resources: a 4-level mip chain of `PIX4` (4bpp) or `PDAT` (8bpp) image blocks, each followed by a `CLUT`, all uncompressed.
2. **Pack names are hashes of the upload.** DuckStation names (`texupload-P4-<texhash>-<palhash>-…`) use XXH3 of the uploaded VRAM words. The raw `PIX` block on disc hashes the same as the runtime upload, so disc pages can be matched to in-game textures exactly.
3. **The game recolours palettes at runtime** (shading and fog variants), so most palette hashes exist only in-game. That is why in-game **dumps** are needed. Each dump reveals the colours of the palette entries it uses. `build_pack stage` combines all dumps of one texture+palette to rebuild the runtime palette. It then renders the **whole** disc page with that palette, which gives clean edges for the upscaler, instead of upscaling the small cropped dumps.
4. **AI upscaling smears some content.** Real-ESRGAN is great on rock, cliffs and buildings, but it smears foliage, dithering and text. `ai_gate.py` measures how much high-frequency detail survives. Pages below the gate use Lanczos instead.
5. **2D UI looks worse upscaled.** Glyphs thicken and bleed into neighbouring atlas cells, and the native UI is already sharp. `--skip-ui` leaves these at native resolution:
   - the HUD atlas (`*_p09`)
   - the demo logo (`*_p13`)
   - the frontend pages (`FE_p08`, `FE_p09`)
   - text built in VRAM
6. **Performance needs merged, preloaded textures.** Polygons sample UV ranges that straddle many small dumped crops, so the runtime would composite images per draw. `--merge` emits one entry per texture+palette covering the union of its crops. `--scale 2` keeps the decoded pack under the runtime's **512 MiB preload cap**. A 4x pack is about 1.9 GB and makes races stutter badly on a 2 GB iGPU.

## 2.1 Extract the disc and the original texture pages

```sh
python tools/extract_disc.py "C:/Games/NASCAR Rumble/NASCAR Rumble.bin" disc-extract
python tools/dump_raw_blocks.py raw-blocks disc-extract/GLBLDATA.PSX $(find disc-extract/CW -name '*.TRK')

# XXH3 hasher used by build_pack (xxhash.h ships with psxrecomp)
toolchain/bin/clang -O2 -I nascar-rumble-recomp/psxrecomp/runtime/third_party tools/xxh3sum.c -o tools/xxh3sum.exe
```

Optional: `python tools/extract_textures.py textures <file.TRK> …` writes viewable PNGs of every page, which is useful for browsing.

## 2.2 Capture in-game dumps (unattended)

```sh
python tools/capture_all.py --seconds 240 --locations 0-7 --tracks 0-2
```

For each of the 8 locations × 3 tracks, it runs the **debug build** headless and does the following:

1. Sets the demo-track mod to that track.
2. Enables HD texture *dumping* into `build-release/mods/texture-packs/SLUS-01068/dumps`.
3. Idles into the attract demo and records for `--seconds`.
4. Quits cleanly through the debug server.

The full run takes about 1.5–2 hours and produces about 5,400 dumps. Use `--locations` / `--tracks` to rerun individual tracks.

The menus are captured too, from the time spent before each demo starts.

## 2.3 Stage, upscale, score

```sh
python tools/build_pack.py stage raw-blocks nascar-rumble-recomp/build-release/mods/texture-packs/SLUS-01068/dumps pack-work
```

`stage` writes the following into `pack-work`:

- `staged/` (RGB, transparent texels colour-dilated)
- `alpha/`
- `known/` (texels whose palette colour was seen in a dump)
- `jobs.json`

**AI upscale (optional).** Download `realesrgan-ncnn-vulkan-*-windows.zip` from the [Real-ESRGAN releases](https://github.com/xinntao/Real-ESRGAN/releases), unzip it into `upscaler/`, then run:

```sh
upscaler/realesrgan-ncnn-vulkan.exe -i pack-work/staged -o pack-work/upscaled -n realesrgan-x4plus-anime -t 32 -f png
python tools/ai_gate.py pack-work
python tools/compare_sheet.py pack-work compare.png 8     # optional: nearest | lanczos | AI side by side
```

- **Model choice.** `realesrgan-x4plus` needs more VRAM than a 2 GB iGPU has, and fails with `vkAllocateMemory` at any tile size. `x4plus-anime` fits and works well on these textures. Don't use `animevideov3`: it produces maze-like artifacts on dithered PS1 textures.
- **Without a Vulkan GPU,** skip this step. `finalize` falls back to Lanczos for everything.

## 2.4 Finalize the pack

```sh
P=nascar-rumble-recomp/build-release/mods/texture-packs/SLUS-01068-hd
mkdir -p $P
python tools/build_pack.py finalize pack-work $P/replacements \
  --resample lanczos --ai-gate 0.85 --scale 2 --merge --skip-ui
```

| Flag | Effect |
|---|---|
| `--resample lanczos` | Lanczos for pages without an AI result, or that fail the gate |
| `--ai-gate 0.85` | Use AI only when it kept at least 85% of the high-frequency detail (good pages score 0.7–0.95, smeared ones 0.2–0.35) |
| `--scale 2` | Downscale the output to 2× (keeps the pack under the 512 MiB preload cap) |
| `--merge` | One entry per texture+palette (no per-draw compositing). Groups with unseen palette colours are left unmerged. |
| `--skip-ui` | Leave the HUD, frontend and VRAM-built text native |

The result is about 3,100 PNGs and about 120 MB.

## 2.5 Enable the pack

In **each build folder you play from** (`build-nopgxp`, `build-release`), create or edit `mods/state.toml`. Use an absolute path with forward slashes:

```toml
format_version = 2

[[package]]
id = "psx.enhancement.hd-textures"
version = "1.0.0"

[[feature]]
package_id = "psx.enhancement.hd-textures"
id = "hd-textures"
enabled = true
[feature.values]
dump = "false"
replacements = "true"
[feature.resources]
pack = "C:/NascarPC/nascar-rumble-recomp/build-release/mods/texture-packs/SLUS-01068-hd"
```

You can also toggle the HD textures from the launcher's Mods screen.

## 2.6 Check the result

`tools/shot_probe.py` runs the debug build headless and saves hi-res screenshots (`screenshot_hires`) at the times you choose. Use it to compare without the pack and with it:

```sh
python tools/shot_probe.py nopack --pack none --at 40,70,100
python tools/shot_probe.py hd --pack C:/NascarPC/nascar-rumble-recomp/build-release/mods/texture-packs/SLUS-01068-hd --at 40,70,100
```

Screenshots land in `shots/`. Timing differs a little between runs, so a shot may show the menu in one run and the race in another.

**Please don't share the finished pack or the dumps.** They are derived from the game's copyrighted textures. Share the tools and let others build their own from their disc.
