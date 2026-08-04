#!/usr/bin/env bash
set -e

COMFYUI_DIR="$(cd "$(dirname "$0")" && pwd)"
CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
MANAGER_DIR="$CUSTOM_NODES_DIR/ComfyUI-Manager"

mkdir -p "$CUSTOM_NODES_DIR"

if [ -d "$MANAGER_DIR/.git" ]; then
    echo "ComfyUI-Manager 已存在，正在更新..."
    git -C "$MANAGER_DIR" pull
else
    echo "正在安装 ComfyUI-Manager..."
    git clone https://github.com/Comfy-Org/ComfyUI-Manager.git "$MANAGER_DIR"
fi

echo "完成：$MANAGER_DIR"
echo "请重启 ComfyUI。"
