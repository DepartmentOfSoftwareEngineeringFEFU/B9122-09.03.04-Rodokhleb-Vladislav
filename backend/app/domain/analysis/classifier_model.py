import torch
from typing import List, Tuple, Optional
import numpy as np
from PIL import Image
import cv2
from pathlib import Path
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

from ...config import settings
from .models import Detection


class ClassifierModel:
    def __init__(self, confidence_threshold: float = 0.35, text_threshold: float = 0.25, verbose: bool = False):
        self.model_path = "models/classifier_model"
        self.confidence_threshold = confidence_threshold
        self.text_threshold = text_threshold
        self.verbose = verbose
        self.model = None
        self.processor = None
        self.device = None
        self._ensure_model_exists()
        self._load_model()

    def _ensure_model_exists(self):
        model_dir = Path(self.model_path)
        config_file = model_dir / "config.json"

        if config_file.exists():
            print(f"Модель доступна локально: {self.model_path}")
            return
        else:
            raise RuntimeError(f"Модель не найдена. Ошибка!!")

    def _load_model(self):
        try:
            print(f"Loading model from {self.model_path}...")

            if torch.cuda.is_available():
                self.device = "cuda"
                print(f"Using device: GPU ({torch.cuda.get_device_name(0)})")
            else:
                self.device = "cpu"
                print("Using device: CPU (CUDA not available)")

            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                local_files_only=True
            )
            self.model = AutoModelForZeroShotObjectDetection.from_pretrained(
                self.model_path,
                local_files_only=True
            ).to(self.device)

            self.model.eval()

            print(f"Model loaded on {self.device}")

        except Exception as e:
            print(f"Failed to load model: {e}")
            raise

    def _format_keywords(self, keywords: List[str]) -> List[str]:
        return [kw.strip().lower() + "." for kw in keywords if kw.strip()]

    def detect(self, frame: np.ndarray, keywords: List[str], frame_info: str = "") -> List[Detection]:
        if self.model is None:
            raise RuntimeError("Model not loaded")

        formatted_keywords = self._format_keywords(keywords)
        text_query = " ".join(formatted_keywords)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        inputs = self.processor(
            images=pil_image,
            text=text_query,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        height, width = frame.shape[:2]

        try:
            results = self.processor.post_process_grounded_object_detection(
                outputs,
                inputs.input_ids,
                box_threshold=self.confidence_threshold,
                text_threshold=self.text_threshold,
                target_sizes=[(height, width)]
            )
        except TypeError:
            results = self.processor.post_process_grounded_object_detection(
                outputs=outputs,
                input_ids=inputs.input_ids,
                box_threshold=self.confidence_threshold,
                text_threshold=self.text_threshold,
                target_sizes=[(height, width)]
            )

        detections = []

        if results and len(results) > 0:
            if isinstance(results, list):
                result = results[0]
            else:
                result = results

            boxes = result.get("boxes", [])
            scores = result.get("scores", [])
            labels = result.get("labels", [])

            for box, score, label in zip(boxes, scores, labels):
                if isinstance(box, torch.Tensor):
                    box = box.tolist()
                x1, y1, x2, y2 = box
                norm_bbox = (x1 / width, y1 / height, x2 / width, y2 / height)
                clean_label = label.rstrip('.') if label.endswith('.') else label

                detections.append(Detection(
                    bbox=norm_bbox,
                    confidence=float(score),
                    label=clean_label
                ))

        if self.verbose and detections:
            det_str = ", ".join([f"{d.label}({d.confidence:.2f})" for d in detections])
            print(f"   {frame_info} Model detected: {det_str}")

        return detections

    def detect_simple(self, frame: np.ndarray, keywords: List[str]) -> List[Tuple[str, float, Tuple]]:
        detections = self.detect(frame, keywords)
        return [(d.label, d.confidence, d.bbox) for d in detections]

    def batch_detect(
        self,
        frames: List[Tuple[float, np.ndarray]],
        keywords: List[str]
    ) -> List[Tuple[float, List[Detection]]]:
        results = []
        for timestamp, frame in frames:
            detections = self.detect(frame, keywords, frame_info=f"[{timestamp:.2f}s]")
            results.append((timestamp, detections))
        return results