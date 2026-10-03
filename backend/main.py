"""FastAPI backend serving CIFAR-10 predictions and Grad-CAM explanations
for the per-epoch models trained in logic/src/experiment.ipynb."""

import base64
import io
from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torchvision as tv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

CACHE_DIR = Path(__file__).resolve().parent.parent / "logic" / "src" / ".cache"
MODEL_DIR = CACHE_DIR / "models"
EPOCHS = sorted(int(p.stem.split("_")[-1]) for p in MODEL_DIR.glob("model_epoch_*.pt"))
GALLERY_SIZE = 16
THUMB_SIZE = 128

dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class SimpleCNN(nn.Module):
    def __init__(self, in_channels=3, num_classes=10, input_size=(32, 32)):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.fc1 = nn.Linear(64 * 8 * 8, 512)
        self.fc2 = nn.Linear(512, num_classes)
        self.input_size = input_size

    def forward(self, x):
        assert x.shape[2:] == self.input_size
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = x.view(-1, 64 * 8 * 8)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return torch.log_softmax(x, dim=1)


test_ds = tv.datasets.CIFAR10(root=str(CACHE_DIR), train=False, download=True)
classes = test_ds.classes
to_tensor = tv.transforms.ToTensor()


@lru_cache(maxsize=None)
def load_model(epoch: int) -> SimpleCNN:
    if epoch not in EPOCHS:
        raise HTTPException(404, f"No model for epoch {epoch}")
    model = SimpleCNN().to(dev)
    state_dict = torch.load(MODEL_DIR / f"model_epoch_{epoch}.pt", map_location=dev)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def get_sample(index: int) -> tuple[torch.Tensor, int, Image.Image]:
    if not 0 <= index < len(test_ds):
        raise HTTPException(404, f"No sample {index}")
    img, label = test_ds[index]
    return to_tensor(img).unsqueeze(0).to(dev), label, img


def encode_image(img: Image.Image, size: int = THUMB_SIZE) -> str:
    buf = io.BytesIO()
    img.resize((size, size), Image.NEAREST).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def encode_array(arr: np.ndarray, size: int = THUMB_SIZE) -> str:
    return encode_image(Image.fromarray(arr), size)


def predict(model: SimpleCNN, input_tensor: torch.Tensor) -> dict:
    with torch.no_grad():
        log_probs = model(input_tensor)[0]
        probs = log_probs.exp()
    predicted = int(probs.argmax().item())
    return {
        "predicted_class": predicted,
        "predicted_label": classes[predicted],
        "predicted_prob": float(probs[predicted].item()),
        "probs": [float(p) for p in probs.tolist()],
    }


def normalize(arr: np.ndarray) -> np.ndarray:
    lo, hi = arr.min(), arr.max()
    return (arr - lo) / (hi - lo) if hi > lo else np.zeros_like(arr)


def cam_for(model: SimpleCNN, input_tensor: torch.Tensor, target_class: int) -> np.ndarray:
    target_layers = [model.conv1, model.conv2]
    with GradCAM(model=model, target_layers=target_layers) as cam:
        grayscale_cam = cam(input_tensor=input_tensor, targets=[ClassifierOutputTarget(target_class)])
    return grayscale_cam[0]


class MetaResponse(BaseModel):
    epochs: list[int]
    classes: list[str]


class Sample(BaseModel):
    index: int
    label: int
    label_name: str
    thumbnail: str


class EpochPrediction(BaseModel):
    epoch: int
    predicted_class: int
    predicted_label: str
    predicted_prob: float
    true_class_prob: float
    probs: list[float]


class PredictionsResponse(BaseModel):
    true_class: int
    true_label: str
    predictions: list[EpochPrediction]


class GradCamSide(BaseModel):
    epoch: int
    cam: str
    predicted_class: int
    predicted_label: str
    predicted_prob: float
    probs: list[float]


class GradCamResponse(BaseModel):
    true_class: int
    true_label: str
    original: str
    epoch_a: GradCamSide
    epoch_b: GradCamSide
    diff: str


app = FastAPI(title="How They Learn API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/meta")
def meta() -> MetaResponse:
    return MetaResponse(epochs=EPOCHS, classes=classes)


@app.get("/api/samples")
def samples() -> list[Sample]:
    step = max(1, len(test_ds) // GALLERY_SIZE)
    out = []
    for index in range(0, len(test_ds), step)[:GALLERY_SIZE]:
        _, label, img = get_sample(index)
        out.append(
            {
                "index": index,
                "label": label,
                "label_name": classes[label],
                "thumbnail": encode_image(img, size=64),
            }
        )
    return out


@app.get("/api/predictions/{index}")
def predictions(index: int) -> PredictionsResponse:
    input_tensor, label, _ = get_sample(index)
    out = []
    for epoch in EPOCHS:
        model = load_model(epoch)
        pred = predict(model, input_tensor)
        out.append(
            {
                "epoch": epoch,
                "true_class_prob": pred["probs"][label],
                **pred,
            }
        )
    return {"true_class": label, "true_label": classes[label], "predictions": out}


@app.get("/api/gradcam")
def gradcam(index: int, epoch_a: int, epoch_b: int) -> GradCamResponse:
    input_tensor, label, img = get_sample(index)
    rgb = np.asarray(img.resize((THUMB_SIZE, THUMB_SIZE), Image.NEAREST), dtype=np.float32) / 255.0

    model_a, model_b = load_model(epoch_a), load_model(epoch_b)
    cam_a = cam_for(model_a, input_tensor, label)
    cam_b = cam_for(model_b, input_tensor, label)
    cam_a_up = np.array(Image.fromarray(cam_a).resize((THUMB_SIZE, THUMB_SIZE)))
    cam_b_up = np.array(Image.fromarray(cam_b).resize((THUMB_SIZE, THUMB_SIZE)))
    diff_up = normalize(cam_b_up - cam_a_up)

    return {
        "true_class": label,
        "true_label": classes[label],
        "original": encode_image(img),
        "epoch_a": {
            "epoch": epoch_a,
            "cam": encode_array(show_cam_on_image(rgb, cam_a_up, use_rgb=True)),
            **predict(model_a, input_tensor),
        },
        "epoch_b": {
            "epoch": epoch_b,
            "cam": encode_array(show_cam_on_image(rgb, cam_b_up, use_rgb=True)),
            **predict(model_b, input_tensor),
        },
        "diff": encode_array(show_cam_on_image(rgb, diff_up, use_rgb=True)),
    }
