#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


# 脚本所在目录作为 ComfyUI 根目录
COMFYUI_PATH = Path(__file__).resolve().parent


MODEL_DIR_MAP = {
    "checkpoints": "models/checkpoints",
    "configs": "models/configs",
    "diffusion_models": "models/diffusion_models",
    "vae": "models/vae",
    "vae_approx": "models/vae_approx",
    "clip": "models/clip",
    "text_encoders": "models/text_encoders",
    "clip_vision": "models/clip_vision",
    "style_models": "models/style_models",
    "diffusers": "models/diffusers",
    "loras": "models/loras",
    "controlnet": "models/controlnet",
    "gligen": "models/gligen",
    "upscale_models": "models/upscale_models",
    "latent_upscale_models": "models/latent_upscale_models",
    "embeddings": "models/embeddings",
    "hypernetworks": "models/hypernetworks",
    "photomaker": "models/photomaker",
    "model_patches": "models/model_patches",
    "audio_encoders": "models/audio_encoders",
    "background_removal": "models/background_removal",
    "frame_interpolation": "models/frame_interpolation",
    "geometry_estimation": "models/geometry_estimation",
    "optical_flow": "models/optical_flow",
    "detection": "models/detection",
}


# 一些方便输入的别名
MODEL_TYPE_ALIASES = {
    "checkpoint": "checkpoints",
    "checkpoints": "checkpoints",

    "unet": "diffusion_models",
    "diffusion": "diffusion_models",
    "diffusion_model": "diffusion_models",
    "diffusion_models": "diffusion_models",

    "vae": "vae",
    "vae_approx": "vae_approx",

    "clip": "clip",

    "text_encoder": "text_encoders",
    "text_encoders": "text_encoders",

    "clip_vision": "clip_vision",

    "lora": "loras",
    "loras": "loras",

    "controlnet": "controlnet",

    "upscale": "upscale_models",
    "upscaler": "upscale_models",
    "upscale_models": "upscale_models",

    "embedding": "embeddings",
    "embeddings": "embeddings",
}


def convert_url(url):
    """
    Hugging Face:
        /blob/ -> /resolve/
    """

    if "/blob/" in url:
        url = url.replace("/blob/", "/resolve/")

    return url


def detect_type_from_url(url):
    """
    只根据 URL 路径判断模型类型。

    不根据文件名猜。

    例如：
        .../loras/xxx.safetensors
        .../vae/xxx.safetensors
        .../text_encoders/xxx.safetensors
    """

    parsed = urlparse(url)

    parts = [
        part.lower()
        for part in parsed.path.strip("/").split("/")
    ]

    for part in parts:

        # 正式目录名
        if part in MODEL_DIR_MAP:
            return part

        # URL 中也可能出现 alias
        if part in MODEL_TYPE_ALIASES:
            return MODEL_TYPE_ALIASES[part]

    return None


def normalize_model_type(value):
    """
    将用户输入转换为正式 model type。
    """

    value = value.strip().lower()

    if value in MODEL_TYPE_ALIASES:
        return MODEL_TYPE_ALIASES[value]

    return None


def choose_model_type():
    """
    URL 无法判断时，交互式选择。
    """

    choices = list(MODEL_DIR_MAP.keys())

    print()
    print("Cannot determine model type from URL.")
    print()
    print("Please select model type:")
    print()

    for i, model_type in enumerate(choices, 1):

        print(
            f"  {i:2d}. "
            f"{model_type:<20} "
            f"-> {MODEL_DIR_MAP[model_type]}"
        )

    print()
    print("   0. Cancel")
    print()

    while True:

        value = input("Select [0-%d]: " % len(choices)).strip()

        try:
            index = int(value)

        except ValueError:
            print("Please enter a number.")
            continue

        if index == 0:
            print("Cancelled.")
            sys.exit(0)

        if 1 <= index <= len(choices):
            return choices[index - 1]

        print("Invalid selection.")


def parse_filename(url):

    parsed = urlparse(url)

    parts = parsed.path.strip("/").split("/")

    if not parts:
        raise ValueError("Cannot determine filename from URL")

    return parts[-1]


def download(url, out_dir, filename):

    os.makedirs(
        out_dir,
        exist_ok=True,
    )

    out_path = os.path.join(
        out_dir,
        filename,
    )

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
                f"Authorization: Bearer {token}",
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
                f"Authorization: Bearer {token}",
            ]

        cmd.append(url)

    print()
    print("=" * 70)
    print("Downloading")
    print(url)
    print()
    print("Save to")
    print(out_path)
    print("=" * 70)
    print()

    subprocess.check_call(cmd)

    print()
    print("Done.")


def print_usage():

    print("Usage:")
    print()
    print("  Auto detect:")
    print("    python download_comfy.py <URL>")
    print()
    print("  Explicit model type:")
    print("    python download_comfy.py <URL> <TYPE>")
    print()
    print("Examples:")
    print()
    print("  python download_comfy.py URL loras")
    print("  python download_comfy.py URL lora")
    print("  python download_comfy.py URL vae")
    print("  python download_comfy.py URL diffusion_models")
    print("  python download_comfy.py URL unet")
    print("  python download_comfy.py URL text_encoders")


def main():

    if len(sys.argv) not in (2, 3):

        print_usage()
        sys.exit(1)

    url = convert_url(
        sys.argv[1]
    )

    filename = parse_filename(url)

    # ========================================================
    # Priority 1:
    # 显式指定类型
    # ========================================================

    if len(sys.argv) == 3:

        requested_type = sys.argv[2]

        model_type = normalize_model_type(
            requested_type
        )

        if model_type is None:

            print(
                f"Unknown model type: "
                f"{requested_type}"
            )

            print()
            print("Available types:")
            print()

            for key in MODEL_DIR_MAP:
                print(f"  {key}")

            sys.exit(1)

        detection_source = "explicit"

    # ========================================================
    # Priority 2:
    # URL 路径判断
    # ========================================================

    else:

        model_type = detect_type_from_url(
            url
        )

        if model_type is not None:

            detection_source = "URL path"

        # ====================================================
        # Priority 3:
        # 交互式选择
        # ====================================================

        else:

            model_type = choose_model_type()

            detection_source = "manual selection"

    out_dir = os.path.join(
        COMFYUI_PATH,
        MODEL_DIR_MAP[model_type],
    )

    print()
    print(f"File           : {filename}")
    print(f"Model type     : {model_type}")
    print(f"Detected by    : {detection_source}")
    print(
        f"Target folder  : "
        f"{MODEL_DIR_MAP[model_type]}"
    )

    download(
        url,
        out_dir,
        filename,
    )


if __name__ == "__main__":
    main()
