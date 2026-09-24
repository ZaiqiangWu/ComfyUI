#!/usr/bin/env python3

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


def human_size(n):
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(n)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024


def find_models(obj, result=None):
    """
    Recursively find:

        properties: {
            models: [
                {
                    name: "...",
                    url: "...",
                    directory: "..."
                }
            ]
        }

    Works with normal nodes and subgraph nodes.
    """

    if result is None:
        result = {}

    if isinstance(obj, dict):

        properties = obj.get("properties")

        if isinstance(properties, dict):
            models = properties.get("models")

            if isinstance(models, list):
                for model in models:

                    if not isinstance(model, dict):
                        continue

                    name = model.get("name")
                    url = model.get("url")
                    directory = model.get("directory")

                    if not name or not url:
                        continue

                    # Avoid duplicates
                    key = (directory or "", name)

                    result[key] = {
                        "name": name,
                        "url": url,
                        "directory": directory or "",
                        "hash": model.get("hash"),
                        "hash_type": model.get("hash_type"),
                    }

        # Recursively scan everything, including definitions/subgraphs
        for value in obj.values():
            find_models(value, result)

    elif isinstance(obj, list):
        for item in obj:
            find_models(item, result)

    return result


def download(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    temp_path = Path(str(destination) + ".part")

    # Resume if .part already exists
    existing_size = 0

    if temp_path.exists():
        existing_size = temp_path.stat().st_size

    headers = {}

    if existing_size > 0:
        headers["Range"] = f"bytes={existing_size}-"

    request = urllib.request.Request(
        url,
        headers=headers
    )

    print(f"URL: {url}")
    print(f"Destination: {destination}")

    if existing_size:
        print(f"Resuming from {human_size(existing_size)}")

    try:
        response = urllib.request.urlopen(request)

        status = getattr(response, "status", None)

        # Server ignored Range → restart download
        if existing_size and status == 200:
            print("Server does not support resume. Restarting download.")
            existing_size = 0
            mode = "wb"
        else:
            mode = "ab" if existing_size else "wb"

        total_header = response.headers.get("Content-Length")

        if total_header:
            total = int(total_header) + existing_size
        else:
            total = None

        downloaded = existing_size

        with open(temp_path, mode) as f:

            while True:

                chunk = response.read(8 * 1024 * 1024)

                if not chunk:
                    break

                f.write(chunk)

                downloaded += len(chunk)

                if total:
                    percent = downloaded / total * 100

                    print(
                        f"\r"
                        f"{human_size(downloaded)} / "
                        f"{human_size(total)} "
                        f"({percent:.1f}%)",
                        end="",
                        flush=True,
                    )
                else:
                    print(
                        f"\r{human_size(downloaded)}",
                        end="",
                        flush=True,
                    )

        print()

        temp_path.rename(destination)

        print("Download complete.")

    except KeyboardInterrupt:

        print()
        print("Download interrupted.")
        print(f"Partial file kept at: {temp_path}")
        print("Run the script again to resume.")

        raise


def main():

    parser = argparse.ArgumentParser(
        description="Download models required by a ComfyUI workflow."
    )

    parser.add_argument(
        "workflow",
        help="ComfyUI workflow JSON file",
    )

    parser.add_argument(
        "--comfyui",
        default=".",
        help="ComfyUI root directory (default: current directory)",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Only list required models",
    )

    args = parser.parse_args()

    workflow_path = Path(args.workflow).expanduser().resolve()
    comfyui_dir = Path(args.comfyui).expanduser().resolve()

    models_root = comfyui_dir / "models"

    if not workflow_path.exists():
        print(f"Workflow not found: {workflow_path}")
        sys.exit(1)

    if not models_root.exists():
        print(f"ComfyUI models directory not found:")
        print(models_root)
        sys.exit(1)

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    models = find_models(workflow)

    if not models:
        print("No downloadable model metadata found in workflow.")
        print()
        print("Expected metadata:")
        print("""
"properties": {
    "models": [
        {
            "name": "model.safetensors",
            "url": "https://...",
            "directory": "diffusion_models"
        }
    ]
}
""")
        sys.exit(0)

    print()
    print(f"Found {len(models)} model(s):")
    print()

    missing = []

    for model in models.values():

        directory = model["directory"]

        # Some official workflows use:
        #
        #   "directory": "models/checkpoints"
        #
        # while others use:
        #
        #   "directory": "checkpoints"
        #
        # Normalize both.

        directory_path = Path(directory)

        if (
            directory_path.parts
            and directory_path.parts[0] == "models"
        ):
            directory_path = Path(*directory_path.parts[1:])

        target = models_root / directory_path / model["name"]

        exists = target.exists()

        status = "OK" if exists else "MISSING"

        print(f"[{status}] {model['name']}")
        print(f"         directory: {directory}")
        print(f"         path:      {target}")
        print(f"         url:       {model['url']}")
        print()

        if not exists:
            missing.append((model, target))

    if args.list:
        return

    if not missing:

        print("All required models are already installed.")
        return

    print("=" * 70)
    print(f"{len(missing)} model(s) need to be downloaded.")
    print("=" * 70)

    for index, (model, target) in enumerate(missing, 1):

        print()
        print(
            f"[{index}/{len(missing)}] "
            f"{model['name']}"
        )
        print("-" * 70)

        try:
            download(
                model["url"],
                target,
            )

        except KeyboardInterrupt:
            sys.exit(130)

        except Exception as e:
            print()
            print(f"ERROR: {e}")
            print()
            print("Skipping this model.")

    print()
    print("=" * 70)
    print("Finished.")
    print("=" * 70)


if __name__ == "__main__":
    main()
