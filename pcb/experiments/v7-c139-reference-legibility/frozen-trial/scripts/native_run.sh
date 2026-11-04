#!/bin/bash
set -euo pipefail
ROOT=/tmp/v7-buck-three-labels-4765
R=$(mktemp -d "$ROOT/runtime.XXXXXX")
chmod 700 "$R"
for d in config cache data state runtime; do mkdir "$R/$d"; chmod 700 "$R/$d"; done
export XDG_CONFIG_HOME="$R/config" XDG_CACHE_HOME="$R/cache" XDG_DATA_HOME="$R/data" XDG_STATE_HOME="$R/state" XDG_RUNTIME_DIR="$R/runtime"
export QT_QPA_PLATFORM=offscreen
exec "$@"
