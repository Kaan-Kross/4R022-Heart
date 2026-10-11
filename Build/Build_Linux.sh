#!/usr/bin/env bash
# 4R022 Heart - Linux one-click build (no Python needed) / Linux tek tikla build (Python gerekmez)
# Copyright (c) 2026 4R022 / Kaan Kross - 4R022 Heart License
cd "$(dirname "$0")" || exit 1
bash scripts/build_unix.sh "$@"
