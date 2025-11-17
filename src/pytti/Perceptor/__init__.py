import torch
from clip import clip
from pytti import vram_usage_mode

CLIP_PERCEPTORS = None

# this should probably be a method on the multiperceptor guide
@vram_usage_mode("CLIP")
def init_clip(clip_models, device=None):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Validate clip_models is not empty
    if not clip_models or len(clip_models) == 0:
        raise ValueError("clip_models must contain at least one model name")

    global CLIP_PERCEPTORS
    # Always reinitialize - this allows model switching and fixes empty list bugs
    CLIP_PERCEPTORS = [
        clip.load(model, jit=False)[0]
        .eval()
        .requires_grad_(False)
        .to(device, memory_format=torch.channels_last)
        for model in clip_models
    ]

    # Validate that models were actually loaded
    if not CLIP_PERCEPTORS or len(CLIP_PERCEPTORS) == 0:
        raise RuntimeError("Failed to load any CLIP models")


def free_clip():
    global CLIP_PERCEPTORS
    CLIP_PERCEPTORS = None
