#!/usr/bin/env python3

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


# ------------------------------------------------------------
# Known ComfyUI loader -> (model directory, widget index)
# ------------------------------------------------------------

LOADERS = {
    "VAELoader": ("vae", 0),
    "UNETLoader": ("diffusion_models", 0),
    "CLIPLoader": ("text_encoders", 0),
    "UpscaleModelLoader": ("upscale_models", 0),
    "CheckpointLoaderSimple": ("checkpoints", 0),
    "LoraLoader": ("loras", 0),

    # This workflow
    "UltralyticsDetectorProvider": ("ultralytics", 0),

    # SeedVR2
    "SeedVR2LoadDiTModel": ("seedvr2", 0),
    "SeedVR2LoadVAEModel": ("seedvr2", 0),
}


def human_size(n):
    units = ["B", "KB", "MB", "GB", "TB"]
    n = float(n)

    for unit in units:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024

    return f"{n:.2f} PB"


def basename(name):
    """
    ComfyUI may store things like:

        ComfyUI\\Moody-Krea-Mix-v7.safetensors

    Return only actual filename.
    """

    return name.replace("\\", "/").split("/")[-1]


# ------------------------------------------------------------
# Recursively collect nodes
# ------------------------------------------------------------

def collect_nodes(obj, result=None):

    if result is None:
        result = []

    if isinstance(obj, dict):

        # Looks like a workflow node
        if (
            "type" in obj
            and "widgets_values" in obj
            and isinstance(obj.get("type"), str)
        ):
            result.append(obj)

        for value in obj.values():
            collect_nodes(value, result)

    elif isinstance(obj, list):

        for value in obj:
            collect_nodes(value, result)

    return result


# ------------------------------------------------------------
# Extract actual selected models
# ------------------------------------------------------------

def extract_required_models(workflow):

    nodes = collect_nodes(workflow)

    models = {}

    for node in nodes:

        node_type = node.get("type")

        if node_type not in LOADERS:
            continue

        directory, widget_index = LOADERS[node_type]

        widgets = node.get("widgets_values", [])

        if not isinstance(widgets, list):
            continue

        if len(widgets) <= widget_index:
            continue

        value = widgets[widget_index]

        if not isinstance(value, str):
            continue

        if not (
            value.lower().endswith(".safetensors")
            or value.lower().endswith(".pth")
            or value.lower().endswith(".pt")
            or value.lower().endswith(".ckpt")
            or value.lower().endswith(".bin")
        ):
            continue

        filename = basename(value)

        key = (directory, filename)

        models[key] = {
            "name": filename,
            "original_name": value,
            "directory": directory,
            "node_type": node_type,
            "node_id": node.get("id"),
            "url": None,
            "url_source": None,
        }

    return models


# ------------------------------------------------------------
# Extract properties.models metadata
# ------------------------------------------------------------

def extract_metadata_models(workflow):

    result = []

    def walk(obj):

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

                        if name and url:

                            result.append({
                                "name": basename(name),
                                "url": url,
                                "directory": directory,
                            })

            for value in obj.values():
                walk(value)

        elif isinstance(obj, list):

            for value in obj:
                walk(value)

    walk(workflow)

    return result


# ------------------------------------------------------------
# Extract Markdown links
# ------------------------------------------------------------

def extract_markdown_links(workflow):

    links = []

    nodes = collect_nodes(workflow)

    # Markdown:
    #
    # [filename](https://...)
    #
    pattern = re.compile(
        r'\[([^\]]+)\]\((https?://[^)\s]+)\)'
    )

    for node in nodes:

        if node.get("type") not in (
            "MarkdownNote",
            "Note",
        ):
            continue

        widgets = node.get("widgets_values", [])

        if not isinstance(widgets, list):
            continue

        for value in widgets:

            if not isinstance(value, str):
                continue

            for label, url in pattern.findall(value):

                links.append({
                    "label": label.strip(),
                    "url": url.strip(),
                })

    return links


# ------------------------------------------------------------
# Match URL
# ------------------------------------------------------------

def attach_urls(required, metadata, markdown_links):

    for model in required.values():

        filename = model["name"]

        # ------------------------------------------------
        # 1. Exact properties.models match
        # ------------------------------------------------

        for item in metadata:

            if item["name"].lower() == filename.lower():

                model["url"] = item["url"]
                model["url_source"] = "properties.models"

                break

        if model["url"]:
            continue

        # ------------------------------------------------
        # 2. Exact Markdown label match
        # ------------------------------------------------

        for item in markdown_links:

            label = basename(item["label"])

            if label.lower() == filename.lower():

                model["url"] = item["url"]
                model["url_source"] = "markdown"

                break

        if model["url"]:
            continue

        # ------------------------------------------------
        # 3. URL basename match
        # ------------------------------------------------

        for item in markdown_links:

            url_name = basename(
                urlparse(item["url"]).path
            )

            if url_name.lower() == filename.lower():

                model["url"] = item["url"]
                model["url_source"] = "markdown-url"

                break


# ------------------------------------------------------------
# Resolve ComfyUI target path
# ------------------------------------------------------------

def target_path(models_root, model):

    directory = model["directory"]

    original = model["original_name"].replace("\\", "/")

    # Preserve subdirectory specified by node, e.g.
    #
    # ComfyUI\\xxx.safetensors
    #
    parts = original.split("/")

    if len(parts) > 1:

        subdir = Path(*parts[:-1])

        return (
            models_root
            / directory
            / subdir
            / model["name"]
        )

    return (
        models_root
        / directory
        / model["name"]
    )


# ------------------------------------------------------------
# Download with resume
# ------------------------------------------------------------

def download(url, destination):

    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = Path(str(destination) + ".part")

    existing = (
        temp.stat().st_size
        if temp.exists()
        else 0
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    if existing:
        headers["Range"] = f"bytes={existing}-"

    request = urllib.request.Request(
        url,
        headers=headers,
    )

    print(f"URL: {url}")
    print(f"Destination: {destination}")

    if existing:
        print(
            f"Resuming from "
            f"{human_size(existing)}"
        )

    response = urllib.request.urlopen(request)

    status = getattr(response, "status", 200)

    if existing and status == 200:

        print(
            "Server ignored Range. "
            "Restarting download."
        )

        existing = 0
        mode = "wb"

    else:

        mode = "ab" if existing else "wb"

    length = response.headers.get(
        "Content-Length"
    )

    total = (
        int(length) + existing
        if length
        else None
    )

    downloaded = existing

    with open(temp, mode) as f:

        while True:

            chunk = response.read(
                8 * 1024 * 1024
            )

            if not chunk:
                break

            f.write(chunk)

            downloaded += len(chunk)

            if total:

                percent = (
                    downloaded
                    / total
                    * 100
                )

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
                    f"\r"
                    f"{human_size(downloaded)}",
                    end="",
                    flush=True,
                )

    print()

    temp.replace(destination)

    print("Download complete.")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "workflow",
        help="ComfyUI workflow JSON",
    )

    parser.add_argument(
        "--comfyui",
        default=".",
        help="ComfyUI root directory",
    )

    parser.add_argument(
        "--list",
        action="store_true",
    )

    args = parser.parse_args()

    workflow_path = Path(
        args.workflow
    ).resolve()

    comfyui = Path(
        args.comfyui
    ).resolve()

    models_root = comfyui / "models"

    with open(
        workflow_path,
        encoding="utf-8",
    ) as f:

        workflow = json.load(f)

    required = extract_required_models(
        workflow
    )

    metadata = extract_metadata_models(
        workflow
    )

    markdown_links = extract_markdown_links(
        workflow
    )

    attach_urls(
        required,
        metadata,
        markdown_links,
    )

    print()
    print(
        f"Required models: "
        f"{len(required)}"
    )
    print()

    missing = []

    for model in required.values():

        target = target_path(
            models_root,
            model,
        )

        exists = target.exists()

        status = (
            "OK"
            if exists
            else "MISSING"
        )

        print(
            f"[{status}] "
            f"{model['name']}"
        )

        print(
            f"    node: "
            f"{model['node_type']} "
            f"(id={model['node_id']})"
        )

        print(
            f"    path: {target}"
        )

        if model["url"]:

            print(
                f"    url: "
                f"{model['url']}"
            )

            print(
                f"    source: "
                f"{model['url_source']}"
            )

        else:

            print(
                "    url: NOT FOUND"
            )

        print()

        if not exists:
            missing.append(
                (model, target)
            )

    if args.list:
        return

    downloadable = [
        x
        for x in missing
        if x[0]["url"]
    ]

    unresolved = [
        x
        for x in missing
        if not x[0]["url"]
    ]

    if unresolved:

        print("=" * 70)
        print(
            "Missing models with no "
            "download URL:"
        )
        print("=" * 70)

        for model, target in unresolved:

            print(
                f"- {model['name']}"
            )

            print(
                f"  node: "
                f"{model['node_type']}"
            )

            print(
                f"  expected: {target}"
            )

        print()

    if not downloadable:

        print(
            "No downloadable missing "
            "models found."
        )

        return

    print("=" * 70)

    print(
        f"Downloading "
        f"{len(downloadable)} model(s)"
    )

    print("=" * 70)

    for i, (model, target) in enumerate(
        downloadable,
        1,
    ):

        print()

        print(
            f"[{i}/{len(downloadable)}] "
            f"{model['name']}"
        )

        try:

            download(
                model["url"],
                target,
            )

        except KeyboardInterrupt:

            print()
            print(
                "Interrupted. Partial "
                "download kept."
            )

            sys.exit(130)

        except Exception as e:

            print()
            print(
                f"ERROR: {e}"
            )

    print()
    print("Finished.")


if __name__ == "__main__":
    main()