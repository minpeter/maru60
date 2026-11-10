#!/bin/sh
# Run after: docker build -f tools/kicad9.Dockerfile -t maru60-kicad:9.0.2 .
set -eu
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
exec docker run --rm --network none --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$repo_root,dst=/workspace" \
    --workdir /workspace \
    maru60-kicad:9.0.2 sh -c '
        scratch=$(mktemp -d)
        trap '\''rm -rf "$scratch"'\'' EXIT
        export HOME="$scratch/home" XDG_CONFIG_HOME="$scratch/config"
        export XDG_CACHE_HOME="$scratch/cache" XDG_DATA_HOME="$scratch/data"
        export XDG_STATE_HOME="$scratch/state" XDG_RUNTIME_DIR="$scratch/runtime"
        mkdir -p "$HOME" "$XDG_RUNTIME_DIR"
        chmod 700 "$XDG_RUNTIME_DIR"
        "$@"
    ' sh "$@"
