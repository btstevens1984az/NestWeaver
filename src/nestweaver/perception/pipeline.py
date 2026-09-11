"""Depth-camera perception pipeline outline (RealSense-class sensors)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Intrinsics:
    fx: float
    fy: float
    cx: float
    cy: float
    width: int = 640
    height: int = 480


@dataclass
class Detection:
    label: str
    confidence: float
    bbox_xywh: tuple[float, float, float, float]
    depth_m: float | None = None
    xyz_m: tuple[float, float, float] | None = None


@dataclass
class FrameBundle:
    """RGB + aligned depth (+ optional Hailo tensor metadata)."""

    rgb: Any  # numpy array HxWx3 uint8 when available
    depth_m: Any  # numpy array HxW float32 meters
    intrinsics: Intrinsics
    timestamp_s: float
    detections: list[Detection] = field(default_factory=list)


class DepthCamera(ABC):
    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def capture(self) -> FrameBundle: ...


class SimulatedDepthCamera(DepthCamera):
    """Synthetic frames for CI and desktop demos."""

    def __init__(self, width: int = 640, height: int = 480) -> None:
        self.width = width
        self.height = height
        self._running = False
        self.intrinsics = Intrinsics(
            fx=600.0, fy=600.0, cx=width / 2, cy=height / 2, width=width, height=height
        )

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def capture(self) -> FrameBundle:
        if not self._running:
            raise RuntimeError("Camera not started")
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("numpy required for SimulatedDepthCamera") from exc
        rgb = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        rgb[:, :] = (40, 55, 70)
        # Fake bottle blob
        rgb[200:320, 300:340] = (30, 140, 220)
        depth = np.full((self.height, self.width), 1.8, dtype=np.float32)
        depth[200:320, 300:340] = 0.85
        import time

        return FrameBundle(
            rgb=rgb,
            depth_m=depth,
            intrinsics=self.intrinsics,
            timestamp_s=time.time(),
        )


class PerceptionPipeline:
    """Detect → project → track outline. Hailo hook optional."""

    def __init__(self, camera: DepthCamera, detector=None) -> None:
        self.camera = camera
        self.detector = detector

    def start(self) -> None:
        self.camera.start()

    def stop(self) -> None:
        self.camera.stop()

    def step(self) -> FrameBundle:
        frame = self.camera.capture()
        if self.detector is not None:
            frame.detections = list(self.detector.infer(frame))
        else:
            frame.detections = self._heuristic_bottle(frame)
        for det in frame.detections:
            if det.depth_m is None:
                det.depth_m = self._median_depth(frame, det.bbox_xywh)
            det.xyz_m = self._deproject(frame.intrinsics, det.bbox_xywh, det.depth_m)
        return frame

    @staticmethod
    def _heuristic_bottle(frame: FrameBundle) -> list[Detection]:
        # Center-ish blue blob proxy for sim frames
        return [
            Detection(
                label="bottle",
                confidence=0.72,
                bbox_xywh=(300.0, 200.0, 40.0, 120.0),
            )
        ]

    @staticmethod
    def _median_depth(frame: FrameBundle, bbox: tuple[float, float, float, float]) -> float:
        x, y, w, h = bbox
        depth = frame.depth_m
        if depth is None:
            return 1.0
        x0, y0 = int(x), int(y)
        x1, y1 = int(x + w), int(y + h)
        try:
            import numpy as np

            patch = depth[y0:y1, x0:x1]
            if patch.size == 0:
                return 1.0
            return float(np.median(patch))
        except Exception:
            return 1.0

    @staticmethod
    def _deproject(
        K: Intrinsics, bbox: tuple[float, float, float, float], depth_m: float | None
    ) -> tuple[float, float, float]:
        x, y, w, h = bbox
        u = x + w / 2.0
        v = y + h / 2.0
        z = depth_m or 1.0
        X = (u - K.cx) * z / K.fx
        Y = (v - K.cy) * z / K.fy
        return (X, Y, z)
