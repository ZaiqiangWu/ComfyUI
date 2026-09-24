#!/usr/bin/env bash
set -e

COMFYUI_DIR="$(cd "$(dirname "$0")" && pwd)"
CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
MANAGER_DIR="$CUSTOM_NODES_DIR/ComfyUI-Manager"

mkdir -p "$CUSTOM_NODES_DIR"

if [ -d "$MANAGER_DIR/.git" ]; then
    echo "ComfyUI-Manager already exists. Updating..."
    git -C "$MANAGER_DIR" pull
else
    echo "Installing ComfyUI-Manager..."
    git clone https://github.com/Comfy-Org/ComfyUI-Manager.git "$MANAGER_DIR"
fi

echo "Installing ComfyUI Manager dependencies..."

python -m pip install -r "$COMFYUI_DIR/manager_requirements.txt"

if [ -f "$MANAGER_DIR/requirements.txt" ]; then
    python -m pip install -r "$MANAGER_DIR/requirements.txt"
fi

echo "ComfyUI-Manager installation complete."
echo "Please restart ComfyUI."