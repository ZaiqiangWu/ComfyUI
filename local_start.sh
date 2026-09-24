#!/usr/bin/env bash

cleanup() {
    echo
    echo "Cleaning up ComfyUI input/output images..."

    find ./input ./output \
        -type f \
        \( -iname "*.png" \
        -o -iname "*.jpg" \
        -o -iname "*.jpeg" \
        -o -iname "*.webp" \
        -o -iname "*.gif" \) \
        -delete

    echo "Cleanup complete."
}

trap cleanup EXIT

python main.py \
  --listen 127.0.0.1 \
  --port 8188 \
  --enable-manager
