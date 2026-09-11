"""Hailo AI accelerator hooks for on-device vision inference."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from nestweaver.perception.pipeline import Detection, FrameBundle


@dataclass
class HailoModelSpec:
    hef_path: str
    input_name: str = "input"
    labels: tuple[str, ...] = ("bottle", "cup", "remote", "toy", "person", "pet")
    score_threshold: float = 0.45


class VisionAccelerator(ABC):
    @abstractmethod
    def load(self, spec: HailoModelSpec) -> None: ...

    @abstractmethod
    def infer(self, frame: FrameBundle) -> Iterable[Detection]: ...

    @abstractmethod
    def close(self) -> None: ...


class StubHailoAccelerator(VisionAccelerator):
    """CPU stub used when HailoRT is not installed (dev laptops / CI)."""

    def __init__(self) -> None:
        self._spec: HailoModelSpec | None = None
        self._loaded = False

    def load(self, spec: HailoModelSpec) -> None:
        self._spec = spec
        self._loaded = True

    def infer(self, frame: FrameBundle) -> Iterable[Detection]:
        if not self._loaded or self._spec is None:
            raise RuntimeError("Hailo model not loaded")
        # Mirror sim heuristic with configurable threshold
        return [
            Detection(
                label="bottle",
                confidence=max(self._spec.score_threshold, 0.71),
                bbox_xywh=(300.0, 200.0, 40.0, 120.0),
            )
        ]

    def close(self) -> None:
        self._loaded = False


class HailoAccelerator(VisionAccelerator):
    """Thin wrapper around HailoRT — import guarded for non-Hailo hosts.

    On a Pi 5 + Hailo Hat / M.2 module, install HailoRT and place compiled
    HEF networks under ``configs/robots/models/``. Then construct this class
    instead of :class:`StubHailoAccelerator`.
    """

    def __init__(self) -> None:
        self._spec: HailoModelSpec | None = None
        self._device: Any = None
        self._network_group: Any = None

    def load(self, spec: HailoModelSpec) -> None:
        try:
            from hailo_platform import (  # type: ignore
                HEF,
                ConfigureParams,
                FormatType,
                HailoStreamInterface,
                VDevice,
            )
        except ImportError as exc:
            raise RuntimeError(
                "HailoRT Python bindings not found. Use StubHailoAccelerator on "
                "dev machines, or install HailoRT on the robot SBC."
            ) from exc
        self._spec = spec
        self._device = VDevice()
        hef = HEF(spec.hef_path)
        params = ConfigureParams.create_from_hef(hef, interface=HailoStreamInterface.PCIe)
        self._network_group = self._device.configure(hef, params)[0]
        self._FormatType = FormatType  # stash for infer

    def infer(self, frame: FrameBundle) -> Iterable[Detection]:
        if self._network_group is None or self._spec is None:
            raise RuntimeError("Hailo network not configured")
        # Production: preprocess RGB → model input, run async infer, decode boxes.
        # Until HEF I/O is wired, fall back to the CPU stub shape for integration tests.
        _ = frame.rgb
        stub = StubHailoAccelerator()
        stub.load(self._spec)
        return list(stub.infer(frame))

    def close(self) -> None:
        self._network_group = None
        self._device = None


def create_accelerator(prefer_hailo: bool = True) -> VisionAccelerator:
    if prefer_hailo:
        try:
            import hailo_platform  # noqa: F401

            return HailoAccelerator()
        except ImportError:
            pass
    return StubHailoAccelerator()
