#!/usr/bin/env bash
set -e

COMFYUI_DIR="$(cd "$(dirname "$0")" && pwd)"
CUSTOM_NODES_DIR="$COMFYUI_DIR/custom_nodes"
RGTHREE_DIR="$CUSTOM_NODES_DIR/rgthree-comfy"

mkdir -p "$CUSTOM_NODES_DIR"

if [ -d "$RGTHREE_DIR/.git" ]; then
    echo "rgthree-comfy 已存在，正在更新..."
    git -C "$RGTHREE_DIR" pull
else
    echo "正在安装 rgthree-comfy..."
    git clone https://github.com/rgthree/rgthree-comfy.git "$RGTHREE_DIR"
fi

echo "完成：$RGTHREE_DIR"
echo "请重启 ComfyUI。"
