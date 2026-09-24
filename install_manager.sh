#!/usr/bin/env bash
set -e

COMFYUI_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing ComfyUI-Manager dependencies..."

python -m pip install -r "$COMFYUI_DIR/manager_requirements.txt"

echo "ComfyUI-Manager dependencies installed."