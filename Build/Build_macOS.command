#!/usr/bin/env bash
# 4R022 Heart - macOS one-click build, double-click to run (no Python needed)
# macOS tek tikla build, cift tikla (Python gerekmez)
# Copyright (c) 2026 4R022 / Kaan Kross - 4R022 Heart License
cd "$(dirname "$0")" || exit 1
bash scripts/build_unix.sh "$@"
RC=$?
echo
if [ "$RC" -eq 0 ]; then echo "Build finished. See the 'Release' folder. / Build tamam, 'Release' klasorune bakin."
else echo "BUILD FAILED / BUILD BASARISIZ (code $RC)"; fi
read -r -p "Press Enter to close... / Kapatmak icin Enter..."
exit $RC
