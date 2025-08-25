#!/usr/bin/env bash
set -euxo pipefail
# System libraries required for CI on Ubuntu
# - wx runtime: libnotify4, libsdl2-2.0-0

export DEBIAN_FRONTEND=noninteractive

sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    libnotify4 \
    libsdl2-2.0-0