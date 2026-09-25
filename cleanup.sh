#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT_DIR="$SCRIPT_DIR/input"
OUTPUT_DIR="$SCRIPT_DIR/output"

echo "ComfyUI directory: $SCRIPT_DIR"
echo "Cleaning up ComfyUI input/output images and videos..."

for dir in "$INPUT_DIR" "$OUTPUT_DIR"; do
    if [ -d "$dir" ]; then
        find "$dir" \
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
    else
        echo "Skip: directory does not exist: $dir"
    fi
done

echo "Cleanup complete."
