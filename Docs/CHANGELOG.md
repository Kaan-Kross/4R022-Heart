# 📝 Changelog / Değişiklik Günlüğü

All notable changes to **4R022 Heart** are documented here. Format: [Keep a Changelog](https://keepachangelog.com), versioning: [SemVer](https://semver.org).
**4R022 Heart**'taki tüm önemli değişiklikler burada tutulur.

> 🇬🇧 English first, 🇹🇷 Türkçe her sürümün altında. · Legend / Simgeler: ✨ Added · 🔄 Changed · 🐞 Bug fixes · ⚡ Performance · 🛠️ Build · 📚 Docs · 🔒 License/Legal

---

## [1.2.0] — 2026-10-10 · "Light Writer" / "Işık Yazarı"

### ✨ Added / Eklenenler
- **New "4R022 PRESENTS" opening:** every letter is pre-rendered and writes itself in with a stagger, a light sweep crosses the title, hairlines with glowing ends expand like the logo, a soft light blooms behind it; exactly **3 s fully visible**, then the letters dissolve outward.
  *Yeni açılış: harfler tek tek yazılır, ışık başlığın üzerinden süpürür, logodaki gibi ince çizgiler açılır; tam 3 sn görünür, sonra harfler dışa doğru dağılır.*
- **"Written by light" text reveal:** phrases are wiped on with a glowing head (right-to-left for Arabic) instead of a plain fade.
  *Yazılar parlayan bir uçla "yazılır" (Arapça sağdan sola).*
- **Ember outro:** phrases dissolve with a wipe and release rising embers; the outline retracts with comet heads; a new **closing card "4R022 HEART"** fades in before the final fade.
  *Yazılar silinirken közlere dönüşür, çizgi kuyruklu yıldız uçlarıyla geri çekilir, yeni "4R022 HEART" kapanış kartı gelir.*
- Third shockwave ring, twinkling **sparkle field** and softer light breathing.
- **Performance profiles** (`high` / `balanced` / `low` / `auto`), `--fps`, `--primary-only`, `--no-music`, `--music`, `--full-repaint`.
- **Settings file** `4R022-Heart.settings.json` (no command line needed).
- `--selftest` (internal health check used by the build) and `--screenshot DIR` (offscreen frame rendering).
- **Automatic screenshot workflow** (`.github/workflows/screenshots.yml`).
- README rewritten: previews, badges, settings, performance profiles, build guide, FAQ.

### 🔄 Changed / Değişenler
- Timeline is now **~49 s** (was ~48.5 s): the longer opening shifts the heart start to 5.8 s. Hold stays **exactly 20 s**.
- Heartbeat now moves text **positions** only; text bitmaps are never scaled (crisp at every beat).
- Repository layout: only `README.md` and `LICENSE` stay in the root; community files live in `.github/`, documents in `Docs/`, build tooling in `Build/`.
- `NOTICE.md` moved to `Docs/NOTICE.md`; license text updated (closing card is now a Brand Element).
- Release packages are **folder builds** by default; settings file ships next to the app.

### 🐞 Bug fixes / Hata düzeltmeleri
- **Text drift and misalignment fixed.** Phrases were centred by their *bounding box*, so words with descenders ("Seni seviyorum", "Jeg elsker dig") sat higher/lower than their row-mates. Every phrase now sits on a **shared baseline** inside a fixed-height bitmap.
  *Yazı kayması giderildi: kelimeler artık satır içinde ortak taban çizgisine oturuyor.*
- **No more sub-pixel shimmer:** phrase positions are snapped to device pixels; the scale-in animation (which blurred text and shifted its centre) was replaced by a wipe reveal.
- **Slow start (5–10 s) fixed:** caused by the single-file EXE unpacking itself at every launch → default build is now onedir; asset preparation is incremental and runs behind the opening animation; QtMultimedia is loaded lazily after the first frame.
- **Disk footprint reduced:** unused Qt modules, plugins, translations and software-OpenGL are excluded from the build; only the music and the app icon are bundled as assets.
- Portrait / unusual displays: UI sizes are now derived from a safe unit so the title never clips (carried from 1.1, re-verified on 8 resolutions).
- Audio can no longer delay or crash start-up: it is created after the first frames and every failure falls back to silent mode.
- A broken settings file is ignored instead of stopping the show.

### ⚡ Performance improvement statement / Performans geliştirme bildirgesi
| Area | Before (1.1) | Now (1.2.0) |
|---|---|---|
| Launch | single-file EXE unpacked itself every start | folder build, nothing to unpack |
| Start-up work | all assets built before the window showed | incremental, ≤ ~6 ms per frame, behind the intro |
| Repainting | full-screen repaint every frame, every monitor | **dirty rectangles** only (heart area + particles + sparkles); full repaint only when needed and every 5 s as self-heal |
| GC | normal garbage collection | collector frozen during the show (no pauses) |
| Quality | fixed | auto-selected profile; **steps down automatically** if frames drop |
| Frame cap | fixed | follows the display (max 60 unless you raise it) |
| Text drawing | scaled bitmaps every beat | unscaled bitmaps, only positions move |
| Disk | full Qt payload | trimmed Qt payload |

Verification performed on the render engine: layout (30 phrases, no overlaps, inside screen) on **8 resolutions** from 1280×720 to 3840×2160, portrait and ultra-wide; **1,000+ frames** painted across the full timeline without errors; dirty-rectangle coverage checked on every frame for all three profiles (0 uncovered changes). Real-world frame rates depend on your hardware — please report numbers in an issue.

### 🛠️ Build
- **No Python required:** `Build/Build_*.bat|.command|.sh` download `uv` and a private Python 3.12, create an isolated environment, install dependencies, build with PyInstaller (`Build/4R022-Heart.spec`), self-test the result and package it. `Build.py` is gone.
- Windows file properties (version, copyright) are embedded; macOS `.app` bundle with identifier `com.4r022.heart`.
- CI builds Windows, macOS and Linux with the same scripts.

---

## [1.1.0] — 2026-10-10 · "Everywhere" / "Her Yerde"

### ✨ Added
- Automatic **cross-platform build system** (Windows / macOS / Linux) with one-click launchers, PyInstaller packaging, icons generated from the logo.
- GitHub Actions workflow building all three platforms.
- **4R022 Heart License (4R022-HL 1.0):** sharing with friends/family/partner allowed, **brand removal forbidden**; `NOTICE`, `CONTRIBUTING`, `CODE_OF_CONDUCT`, `SECURITY`, issue/PR templates, bilingual README.
- `--windowed` test mode, `--version`, resource lookup for packaged builds.
- Graceful **silent fallback** when no audio device exists; Wayland → X11 preference on Linux.

### 🔄 Changed
- Music loop now uses a **2 s crossfade** (the track is 24 s, the scene needs ~43 s) with a soft restart.
- Vietnamese phrase shortened to "Anh yêu em".

### 🐞 Bug fixes
- Portrait monitors: inner phrases could not be placed at all → sizing now follows the heart size.
- Outer phrases could touch the heart outline near the cleft → boxes are pushed outward until they clear it.

---

## [1.0.0] — 2026-10-10 · "First Light" / "İlk Işık"

### ✨ Added
- Cinematic scene: opening → heart outline drawing → outer phrases → inner fill → ignition → 20 s hold → erase → exit.
- **"I love you" in 30 languages** with per-language fonts and automatic overlap-free layout.
- **Multi-monitor** full screen on every display with one shared clock; hidden cursor; ESC to quit.
- Music starting with the heart drawing and fading out; rising mini hearts, heartbeat, shockwave.
