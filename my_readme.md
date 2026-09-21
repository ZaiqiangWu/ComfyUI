conda create -n comfyui python=3.12 -y
conda activate comfyui


python -m pip install \
    torch==2.7.1 \
    torchvision==0.22.1 \
    torchaudio==2.7.1 \
    --index-url https://download.pytorch.org/whl/cu118



