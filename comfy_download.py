#!/usr/bin/env python3

import os
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse

# 修改成你的 ComfyUI 路径
COMFYUI_PATH = os.path.expanduser("~/ComfyUI")

MODEL_DIR_MAP = {
    "checkpoints": "models/checkpoints",
    "diffusion_models": "models/diffusion_models",
    "vae": "models/vae",
    "vae_approx": "models/vae_approx",
    "clip": "models/clip",
    "text_encoders": "models/text_encoders",
    "text_encoder": "models/text_encoders",
    "clip_vision": "models/clip_vision",
    "loras": "models/loras",
    "controlnet": "models/controlnet",
    "upscale_models": "models/upscale_models",
    "embeddings": "models/embeddings",
}


def convert_url(url):
    """
    blob -> resolve
    """

    if "/blob/" in url:
        url = url.replace("/blob/", "/resolve/")

    return url


def parse(url):
    """
    提取目录和文件名
    """

    p = urlparse(url)
    parts = p.path.strip("/").split("/")

    filename = parts[-1]

    model_type = None
    for p in parts:
        if p in MODEL_DIR_MAP:
            model_type = p
            break

    if model_type is None:
        model_type = "checkpoints"

    return filename, model_type


def download(url, out_dir, filename):

    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, filename)

    token = os.environ.get("HF_TOKEN")

    if shutil.which("aria2c"):

        cmd = [
            "aria2c",
            "-x16",
            "-s16",
            "-k1M",
            "-c",
            "-o",
            filename,
            "-d",
            out_dir,
        ]

        if token:
            cmd += [
                "--header",
                f"Authorization: Bearer {token}"
            ]

        cmd.append(url)

    else:

        cmd = [
            "wget",
            "-c",
            "-O",
            out_path,
        ]

        if token:
            cmd += [
                "--header",
                f"Authorization: Bearer {token}"
            ]

        cmd.append(url)

    print("=" * 60)
    print("Downloading")
    print(url)
    print()
    print("Save to")
    print(out_path)
    print("=" * 60)

    subprocess.check_call(cmd)

    print("\nDone.")


def main():

    if len(sys.argv) != 2:
        print("Usage:")
        print("python comfy_download.py <huggingface url>")
        return

    url = convert_url(sys.argv[1])

    filename, model_type = parse(url)

    out_dir = os.path.join(
        COMFYUI_PATH,
        MODEL_DIR_MAP[model_type]
    )

    download(url, out_dir, filename)


if __name__ == "__main__":
    main()
