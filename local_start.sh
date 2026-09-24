#!/usr/bin/env bash

cleaned=0

cleanup() {
    if [ "$cleaned" -eq 1 ]; then
        return
    fi
    cleaned=1

    echo
    echo "Cleaning up ComfyUI input/output images and videos..."

    find "$PWD/input" "$PWD/output" \
        -type f \
        \( -iname "*.png" \
        -o -iname "*.jpg" \
        -o -iname "*.jpeg" \
        -o -iname "*.webp" \
        -o -iname "*.gif" \
        -o -iname "*.mp4" \
        -o -iname "*.webm" \
        -o -iname "*.mov" \
        -o -iname "*.avi" \
        -o -iname "*.mkv" \) \
        -print \
        -delete

    echo "Cleanup complete."
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

python main.py \
    --listen 127.0.0.1 \
    --port 8188 \
    --enable-manager