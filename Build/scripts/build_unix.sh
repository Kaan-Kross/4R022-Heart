#!/usr/bin/env bash
# 4R022 Heart - macOS / Linux build.  NO Python installation required.
# Copyright (c) 2026 4R022 / Kaan Kross - 4R022 Heart License
#
# 1. downloads "uv" (one small standalone tool) into Build/.tools
# 2. uv downloads a private Python 3.12 and creates Build/.venv
# 3. installs PySide6 + PyInstaller there
# 4. builds the app (folder build = instant start-up; macOS = .app bundle)
# 5. self-tests it and packs Release/4R022-Heart-vX.Y.Z-<os>-<arch>.(zip|tar.gz)
#
# Options: --onefile (Linux only)  --skip-test  --clean-env  --keep-work
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
BUILD="$ROOT/Build"; TOOLS="$BUILD/.tools"; VENV="$BUILD/.venv"
WORK="$BUILD/work"; DIST="$BUILD/dist"; RELEASE="$ROOT/Release"

ONEFILE=0; SKIPTEST=0; CLEAN=0; KEEPWORK=0
for a in "$@"; do
  case "$a" in
    --onefile) ONEFILE=1;; --skip-test) SKIPTEST=1;; --clean-env) CLEAN=1;; --keep-work) KEEPWORK=1;;
    -h|--help) sed -n '2,13p' "$0"; exit 0;;
    *) echo "Unknown option: $a"; exit 2;;
  esac
done

say()  { printf '\033[35m[4R022]\033[0m %s\n' "$*"; }
fail() { printf '\033[31m[4R022][ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

OS="$(uname -s)"; MACHINE="$(uname -m)"
case "$OS" in
  Darwin) OSN="macos"; case "$MACHINE" in arm64) TRIPLE="aarch64-apple-darwin"; ARCH="arm64";; *) TRIPLE="x86_64-apple-darwin"; ARCH="x64";; esac;;
  Linux)  OSN="linux"; case "$MACHINE" in aarch64|arm64) TRIPLE="aarch64-unknown-linux-gnu"; ARCH="arm64";; *) TRIPLE="x86_64-unknown-linux-gnu"; ARCH="x64";; esac;;
  *) fail "Unsupported system: $OS";;
esac
[ "$OSN" = "macos" ] && ONEFILE=0

VER="$(sed -n 's/^__version__ *= *"\(.*\)"/\1/p' "$ROOT/Main/Main.py" | head -n1)"
[ -n "$VER" ] || fail "Could not read the version from Main/Main.py"

echo "================================================================"
echo "  4R022 Heart v$VER  |  $OSN $ARCH  |  automatic build"
echo "================================================================"

fetch() {  # fetch URL OUTPUT
  if command -v curl >/dev/null 2>&1; then curl -fsSL "$1" -o "$2"
  elif command -v wget >/dev/null 2>&1; then wget -q "$1" -O "$2"
  else fail "curl or wget is required to download the build tools."; fi
}

# Linux: runtime libraries Qt needs (Debian/Ubuntu family) - only installs what is missing
if [ "$OSN" = "linux" ] && command -v apt-get >/dev/null 2>&1 && command -v dpkg >/dev/null 2>&1; then
  PKGS="libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xfixes0 libpulse0 libdbus-1-3 libfontconfig1"
  MISSING=""; for p in $PKGS; do dpkg -s "$p" >/dev/null 2>&1 || MISSING="$MISSING $p"; done
  if [ -n "$MISSING" ]; then
    SUDO=""; [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo"
    say "Installing missing Qt runtime libraries:$MISSING"
    $SUDO apt-get update -y >/dev/null 2>&1 || true
    $SUDO apt-get install -y $MISSING || say "(some libraries could not be installed - continuing)"
  fi
fi

# 1 - bootstrap uv
if command -v uv >/dev/null 2>&1; then UV="$(command -v uv)"
else
  UV="$TOOLS/uv"
  if [ ! -x "$UV" ]; then
    say "Downloading the uv bootstrapper (no admin rights needed)..."
    mkdir -p "$TOOLS"
    fetch "https://github.com/astral-sh/uv/releases/latest/download/uv-$TRIPLE.tar.gz" "$TOOLS/uv.tar.gz"
    tar -xzf "$TOOLS/uv.tar.gz" -C "$TOOLS"
    F="$(find "$TOOLS" -type f -name uv -perm -u+x | head -n1)"
    [ -n "$F" ] || fail "uv was not found in the downloaded archive."
    [ "$F" = "$UV" ] || cp "$F" "$UV"
    chmod +x "$UV"; rm -rf "$TOOLS/uv.tar.gz" "$TOOLS"/uv-"$TRIPLE"
  fi
fi
export UV_CACHE_DIR="$BUILD/.cache/uv" UV_PYTHON_INSTALL_DIR="$TOOLS/python" UV_PYTHON_PREFERENCE=only-managed UV_LINK_MODE=copy

# 2 - private Python + venv
[ "$CLEAN" = 1 ] && rm -rf "$VENV"
PY="$VENV/bin/python"
if [ ! -x "$PY" ]; then
  say "Creating a private Python 3.12 environment (downloaded automatically)..."
  "$UV" venv "$VENV" --python 3.12
fi

# 3 - dependencies
say "Installing dependencies (PySide6, PyInstaller)..."
"$UV" pip install --python "$PY" -r "$BUILD/requirements.txt" -r "$BUILD/requirements-build.txt"

# 4 - build
rm -rf "$WORK" "$DIST"
export HEART_ONEFILE="$ONEFILE"
say "Building the application (a few minutes)..."
"$PY" -m PyInstaller --noconfirm --clean --distpath "$DIST" --workpath "$WORK" "$BUILD/4R022-Heart.spec"

if   [ "$OSN" = "macos" ]; then EXE="$DIST/4R022-Heart.app/Contents/MacOS/4R022-Heart"
elif [ "$ONEFILE" = 1 ];   then EXE="$DIST/4R022-Heart"
else                            EXE="$DIST/4R022-Heart/4R022-Heart"; fi
[ -x "$EXE" ] || fail "Built executable not found: $EXE"

# 5 - self-test
if [ "$SKIPTEST" = 0 ]; then
  say "Running the built-in self-test..."
  mkdir -p "$WORK"; LOG="$WORK/selftest.log"; RC=0
  QT_QPA_PLATFORM=offscreen "$EXE" --selftest --log "$LOG" || RC=$?
  [ -f "$LOG" ] && sed 's/^/   /' "$LOG"
  [ "$RC" = 0 ] || fail "Self-test failed (exit code $RC). Use --skip-test to package anyway."
fi

# 6 - package
BASE="4R022-Heart-v$VER-$OSN-$ARCH"; STAGE="$RELEASE/$BASE"
rm -rf "$STAGE"; mkdir -p "$STAGE"
if [ "$OSN" = "macos" ]; then
  cp -R "$DIST/4R022-Heart.app" "$STAGE/"; APPDIR="$STAGE"
elif [ "$ONEFILE" = 1 ]; then
  cp "$DIST/4R022-Heart" "$STAGE/"; APPDIR="$STAGE"
else
  cp -R "$DIST/4R022-Heart" "$STAGE/4R022-Heart"; APPDIR="$STAGE/4R022-Heart"
fi
cp "$ROOT/Assets/Config/4R022-Heart.settings.json" "$APPDIR/"
cp "$ROOT/LICENSE" "$ROOT/README.md" "$STAGE/"; cp "$ROOT/Docs/NOTICE.md" "$STAGE/"
if [ "$OSN" = "macos" ]; then
  OUT="$RELEASE/$BASE.zip"; rm -f "$OUT"
  ditto -c -k --sequesterRsrc --keepParent "$STAGE" "$OUT"
else
  OUT="$RELEASE/$BASE.tar.gz"; rm -f "$OUT"
  tar -C "$RELEASE" -czf "$OUT" "$BASE"
fi
rm -rf "$STAGE"
[ "$KEEPWORK" = 1 ] || rm -rf "$WORK" "$DIST"
SIZE="$(du -h "$OUT" | cut -f1)"
echo; say "DONE  ->  $OUT  ($SIZE)"
