#!/usr/bin/env python3
"""Small local app for converting Leica LIF files to sorted TIFF folders."""

from __future__ import annotations

import csv
import queue
import re
import subprocess
import sys
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

APP_DIR = Path(__file__).resolve().parent
VENDOR_DIR = APP_DIR / "vendor"
if VENDOR_DIR.exists():
    sys.path.insert(0, str(VENDOR_DIR))

import numpy as np
from PIL import Image, ImageTk
from readlif.reader import LifFile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
PREVIEW_SIZE = 720

LUT_RGB = {
    "red": (1.0, 0.0, 0.0),
    "green": (0.0, 1.0, 0.0),
    "blue": (0.0, 0.0, 1.0),
    "cyan": (0.0, 1.0, 1.0),
    "magenta": (1.0, 0.0, 1.0),
    "yellow": (1.0, 1.0, 0.0),
    "white": (1.0, 1.0, 1.0),
    "gray": (1.0, 1.0, 1.0),
    "grey": (1.0, 1.0, 1.0),
}
LUT_CHOICES = ("Green", "Red", "Blue", "Cyan", "Magenta", "Yellow", "White", "Gray")
MERGE_MODES = ("Max", "Additive")

STRINGS = {
    "zh": {
        "app_title": "LIF 转 TIF 提取器",
        "open_lif": "打开 LIF",
        "choose_output": "选择输出文件夹",
        "open_output": "打开输出文件夹",
        "export_current": "导出当前图",
        "export_all_current": "一次预览导出全部",
        "export_all_per_image": "按各图参数导出全部",
        "apply_adjustments": "导出时应用亮度/对比度",
        "apply_all_adjustments": "导出时应用所有调节",
        "reset_current": "重置当前参数",
        "reset_all": "重置全部参数",
        "cancel_export": "取消导出",
        "auto_levels": "自动拉伸当前图",
        "auto_all": "自动调节全部图",
        "language": "Language / 语言",
        "no_lif": "未选择 LIF",
        "output": "输出:",
        "preview_area": "预览区",
        "select_preview": "选择左侧图像预览",
        "preview_mode": "预览模式:",
        "merge_mode": "Merged 合成:",
        "auto_settings": "自动调节参数",
        "low_percentile": "背景百分位",
        "high_percentile": "信号百分位",
        "target_max": "目标亮度",
        "merged": "Merged",
        "channel_adjustments": "通道调整",
        "include_merged": "参与 Merged",
        "color": "颜色",
        "seq": "顺序",
        "time": "拍摄时间",
        "name": "名称",
        "channels": "通道",
        "size": "尺寸",
        "status_start": "选择一个 .lif 文件开始",
        "reading_meta": "正在读取 LIF 元数据...",
        "read_done": "已读取 {count} 个图像/series",
        "series_loaded": "共 {count} 个图像/series，已按拍摄时间排序",
        "read_failed_title": "读取失败",
        "read_failed": "无法读取这个 LIF 文件:\n{error}",
        "loading_preview": "正在加载预览...",
        "preview_done": "预览已更新",
        "preview_failed_title": "预览失败",
        "preview_failed": "无法预览这个图像:\n{error}",
        "brightness": "亮度",
        "contrast": "对比度",
        "gamma": "Gamma",
        "black": "黑场",
        "white": "白场",
        "no_selected_title": "没有选择图像",
        "no_selected": "先在左侧选择一个图像。",
        "no_lif_title": "没有 LIF",
        "no_lif_msg": "先打开一个 .lif 文件。",
        "exporting_label": "正在导出{label}...",
        "exporting_progress": "正在导出: {done}/{total}",
        "export_done_status": "导出完成: {count} 个 TIFF 记录",
        "export_done_title": "导出完成",
        "export_done_msg": "已导出到:\n{output}\n\n记录数: {count}\n记录表:\n{manifest}",
        "cancelled_status": "导出已取消",
        "cancelled_title": "导出已取消",
        "cancelled_msg": "已停止导出。\n已写出的文件保留在:\n{output}",
        "export_failed": "导出失败",
        "current_reset": "当前图参数已重置",
        "all_reset": "全部参数已重置",
        "auto_current_done": "当前图已自动调节",
        "auto_all_done": "全部图已自动调节: {count} 个 series",
        "auto_running": "正在自动调节全部图...",
        "cancelling": "正在取消，等待当前文件写完...",
        "current_image": "当前图",
        "all_images": "全部图像",
        "unknown_time": "unknown time",
    },
    "en": {
        "app_title": "LIF to TIFF Extractor",
        "open_lif": "Open LIF",
        "choose_output": "Choose Output Folder",
        "open_output": "Open Output Folder",
        "export_current": "Export Current",
        "export_all_current": "Preview Once, Export All",
        "export_all_per_image": "Export All With Per-Image Settings",
        "apply_adjustments": "Apply Brightness/Contrast on Export",
        "apply_all_adjustments": "Apply All Adjustments on Export",
        "reset_current": "Reset Current",
        "reset_all": "Reset All",
        "cancel_export": "Cancel Export",
        "auto_levels": "Auto Levels Current",
        "auto_all": "Auto Adjust All",
        "language": "Language / 语言",
        "no_lif": "No LIF selected",
        "output": "Output:",
        "preview_area": "Preview",
        "select_preview": "Select an image on the left to preview",
        "preview_mode": "Preview Mode:",
        "merge_mode": "Merged Mode:",
        "auto_settings": "Auto Adjustment Settings",
        "low_percentile": "Background %",
        "high_percentile": "Signal %",
        "target_max": "Target Max",
        "merged": "Merged",
        "channel_adjustments": "Channel Adjustments",
        "include_merged": "Include in Merged",
        "color": "Color",
        "seq": "Order",
        "time": "Acquired",
        "name": "Name",
        "channels": "Channels",
        "size": "Size",
        "status_start": "Choose a .lif file to start",
        "reading_meta": "Reading LIF metadata...",
        "read_done": "Loaded {count} images/series",
        "series_loaded": "{count} images/series loaded and sorted by acquisition time",
        "read_failed_title": "Read Failed",
        "read_failed": "Cannot read this LIF file:\n{error}",
        "loading_preview": "Loading preview...",
        "preview_done": "Preview updated",
        "preview_failed_title": "Preview Failed",
        "preview_failed": "Cannot preview this image:\n{error}",
        "brightness": "Brightness",
        "contrast": "Contrast",
        "gamma": "Gamma",
        "black": "Black",
        "white": "White",
        "no_selected_title": "No Image Selected",
        "no_selected": "Select an image on the left first.",
        "no_lif_title": "No LIF",
        "no_lif_msg": "Open a .lif file first.",
        "exporting_label": "Exporting {label}...",
        "exporting_progress": "Exporting: {done}/{total}",
        "export_done_status": "Export complete: {count} TIFF records",
        "export_done_title": "Export Complete",
        "export_done_msg": "Exported to:\n{output}\n\nRecords: {count}\nManifest:\n{manifest}",
        "cancelled_status": "Export cancelled",
        "cancelled_title": "Export Cancelled",
        "cancelled_msg": "Export stopped.\nAlready written files remain in:\n{output}",
        "export_failed": "Export Failed",
        "current_reset": "Current settings reset",
        "all_reset": "All settings reset",
        "auto_current_done": "Current image auto-adjusted",
        "auto_all_done": "All images auto-adjusted: {count} series",
        "auto_running": "Auto-adjusting all images...",
        "cancelling": "Cancelling after the current file finishes...",
        "current_image": "current image",
        "all_images": "all images",
        "unknown_time": "unknown time",
    },
}


@dataclass(frozen=True)
class SeriesRecord:
    lif_index: int
    name: str
    acquired_at: datetime | None
    channel_luts: tuple[str, ...]
    size_label: str
    dims: tuple[int, int, int, int, int]


class ExportCancelled(Exception):
    pass


def safe_name(value: str) -> str:
    value = re.sub(r"[^\w .()+-]+", "_", value, flags=re.UNICODE).strip()
    value = re.sub(r"\s+", " ", value)
    return value or "untitled"


def parse_filetime_hex(value: str) -> datetime | None:
    try:
        ticks_100ns = int(value, 16)
    except ValueError:
        return None
    return FILETIME_EPOCH + timedelta(microseconds=ticks_100ns / 10)


def image_elements(lif: LifFile):
    return [e for e in lif.xml_root.iter("Element") if e.find("./Data/Image") is not None]


def first_timestamp(element) -> datetime | None:
    timestamp_list = element.find("./Data/Image/TimeStampList")
    if timestamp_list is None or not timestamp_list.text:
        return None
    for token in timestamp_list.text.split():
        parsed = parse_filetime_hex(token)
        if parsed is not None:
            return parsed.astimezone()
    return None


def channel_luts(element) -> tuple[str, ...]:
    channels = element.findall("./Data/Image/ImageDescription/Channels/ChannelDescription")
    return tuple((channel.attrib.get("LUTName") or "Gray") for channel in channels)


def sort_key(record: SeriesRecord):
    if record.acquired_at is None:
        return (1, datetime.max.replace(tzinfo=timezone.utc), record.lif_index)
    return (0, record.acquired_at, record.lif_index)


def rgb_for_lut(lut_name: str) -> tuple[float, float, float]:
    return LUT_RGB.get(lut_name.strip().lower(), (1.0, 1.0, 1.0))


def to_uint8_display(
    array: np.ndarray,
    brightness: float = 1.0,
    contrast: float = 1.0,
    gamma: float = 1.0,
    black: float = 0.0,
    white: float = 255.0,
) -> np.ndarray:
    array = np.asarray(array)
    if array.dtype == np.uint8:
        display = array.astype(np.float32)
    elif np.issubdtype(array.dtype, np.integer):
        max_value = np.iinfo(array.dtype).max
        display = (array.astype(np.float32) / max_value) * 255.0 if max_value > 0 else 0.0
    else:
        display = array.astype(np.float32)
    black = max(0.0, min(254.0, float(black)))
    white = max(black + 1.0, min(255.0, float(white)))
    display = np.clip((display - black) * (255.0 / (white - black)), 0, 255)
    gamma = max(0.05, float(gamma))
    if abs(gamma - 1.0) > 0.001:
        display = np.power(display / 255.0, 1.0 / gamma) * 255.0
    display = (display - 127.5) * contrast + 127.5
    return np.clip(display * brightness, 0, 255).astype(np.uint8)


def colorize(
    gray: np.ndarray,
    lut_name: str,
    brightness: float = 1.0,
    contrast: float = 1.0,
    gamma: float = 1.0,
    black: float = 0.0,
    white: float = 255.0,
) -> np.ndarray:
    display = to_uint8_display(gray, brightness, contrast, gamma, black, white)
    color = np.asarray(rgb_for_lut(lut_name), dtype=np.float32)
    return np.clip(display[..., None].astype(np.float32) * color, 0, 255).astype(np.uint8)


def merge_colored(channels: list[np.ndarray], mode: str) -> np.ndarray | None:
    if not channels:
        return None
    if mode == "Additive":
        total = np.zeros_like(channels[0], dtype=np.uint16)
        for channel in channels:
            total += channel.astype(np.uint16)
        return np.clip(total, 0, 255).astype(np.uint8)
    merged = np.zeros_like(channels[0], dtype=np.uint8)
    for channel in channels:
        merged = np.maximum(merged, channel)
    return merged


def write_tiff(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(array).save(path, format="TIFF", compression="tiff_lzw")


def requested_dims_for(image, z: int, t: int, m: int) -> dict[int, int]:
    dims = {}
    if image.dims.z > 1:
        dims[3] = z
    if image.dims.t > 1:
        dims[4] = t
    if image.dims.m > 1:
        dims[10] = m
    return dims


def plane_suffix(image, z: int, t: int, m: int) -> str:
    parts = []
    if image.dims.z > 1:
        parts.append(f"z{z + 1:03d}")
    if image.dims.t > 1:
        parts.append(f"t{t + 1:03d}")
    if image.dims.m > 1:
        parts.append(f"m{m + 1:03d}")
    return "_" + "_".join(parts) if parts else ""


def iter_planes(image):
    for t in range(int(image.dims.t)):
        for z in range(int(image.dims.z)):
            for m in range(int(image.dims.m)):
                yield z, t, m


def make_preview_plane_array(image, channel: int) -> np.ndarray:
    plane = image.get_plane(c=channel)
    plane.thumbnail((PREVIEW_SIZE, PREVIEW_SIZE), Image.Resampling.BOX)
    return np.asarray(plane)


def compute_auto_parameters(plane: np.ndarray, low_percent: float, high_percent: float, target: float) -> tuple[float, float, float]:
    base = to_uint8_display(plane, 1.0, 1.0, 1.0, 0.0, 255.0).astype(np.float32)
    low_percent = max(0.0, min(99.0, float(low_percent)))
    high_percent = max(low_percent + 0.1, min(100.0, float(high_percent)))
    target = max(1.0, min(255.0, float(target)))
    black = float(np.percentile(base, low_percent))
    white = float(np.percentile(base, high_percent))
    if white <= black + 1.0:
        white = min(255.0, black + 1.0)
    brightness = target / 255.0
    return black, white, brightness


def discover_records(lif: LifFile) -> list[SeriesRecord]:
    elements = image_elements(lif)
    images = list(lif.get_iter_image())
    if len(elements) != len(images):
        raise RuntimeError("LIF XML image count does not match readable image count.")

    records: list[SeriesRecord] = []
    for idx, (image, element) in enumerate(zip(images, elements)):
        dims = (int(image.dims.x), int(image.dims.y), int(image.dims.z), int(image.dims.t), int(image.dims.m))
        size_label = f"{dims[0]}x{dims[1]}"
        if dims[2] > 1 or dims[3] > 1 or dims[4] > 1:
            size_label += f" z{dims[2]} t{dims[3]} m{dims[4]}"
        records.append(
            SeriesRecord(
                lif_index=idx,
                name=image.name,
                acquired_at=first_timestamp(element),
                channel_luts=channel_luts(element),
                size_label=size_label,
                dims=dims,
            )
        )
    return sorted(records, key=sort_key)


def expected_tiff_count(records_with_sequence: Iterable[tuple[int, SeriesRecord]]) -> int:
    total = 0
    for _sequence, record in records_with_sequence:
        _x, _y, z, t, m = record.dims
        channel_count = max(1, len(record.channel_luts))
        total += (channel_count + 1) * z * t * m
    return total


def export_records(
    lif_path: Path,
    records_with_sequence: Iterable[tuple[int, SeriesRecord]],
    output_root: Path,
    manifest_path: Path,
    brightness_by_index: dict[int, list[float]],
    contrast_by_index: dict[int, list[float]],
    gamma_by_index: dict[int, list[float]],
    black_by_index: dict[int, list[float]],
    white_by_index: dict[int, list[float]],
    include_merged_by_index: dict[int, list[bool]],
    lut_by_index: dict[int, list[str]],
    apply_adjustments: bool,
    merge_mode: str = "Max",
    progress_callback=None,
    cancel_event: threading.Event | None = None,
) -> int:
    lif = LifFile(str(lif_path))
    manifest_rows = []
    written_count = 0

    for sequence, record in records_with_sequence:
        if cancel_event is not None and cancel_event.is_set():
            raise ExportCancelled()
        image = lif.get_image(record.lif_index)
        brightness = brightness_by_index.get(record.lif_index, [1.0] * image.channels)
        contrast = contrast_by_index.get(record.lif_index, [1.0] * image.channels)
        gamma = gamma_by_index.get(record.lif_index, [1.0] * image.channels)
        black = black_by_index.get(record.lif_index, [0.0] * image.channels)
        white = white_by_index.get(record.lif_index, [255.0] * image.channels)
        include_merged = include_merged_by_index.get(record.lif_index, [True] * image.channels)
        lut_values = lut_by_index.get(record.lif_index, list(record.channel_luts))
        date_folder = record.acquired_at.strftime("%Y%m%d") if record.acquired_at else "unknown_time"
        time_label = record.acquired_at.strftime("%H%M%S") if record.acquired_at else "unknown"
        datetime_label = record.acquired_at.strftime("%Y%m%d_%H%M%S") if record.acquired_at else "unknown_time"
        series_folder = output_root / date_folder / f"{sequence:03d}_{time_label}_{safe_name(record.name)}"

        for z, t, m in iter_planes(image):
            suffix = plane_suffix(image, z, t, m)
            requested = requested_dims_for(image, z, t, m)
            merged_channels = []

            for channel_index in range(image.channels):
                if cancel_event is not None and cancel_event.is_set():
                    raise ExportCancelled()
                original_lut = record.channel_luts[channel_index] if channel_index < len(record.channel_luts) else "Gray"
                lut_name = lut_values[channel_index] if apply_adjustments and channel_index < len(lut_values) else original_lut
                channel_brightness = brightness[channel_index] if apply_adjustments and channel_index < len(brightness) else 1.0
                channel_contrast = contrast[channel_index] if apply_adjustments and channel_index < len(contrast) else 1.0
                channel_gamma = gamma[channel_index] if apply_adjustments and channel_index < len(gamma) else 1.0
                channel_black = black[channel_index] if apply_adjustments and channel_index < len(black) else 0.0
                channel_white = white[channel_index] if apply_adjustments and channel_index < len(white) else 255.0
                channel_include_merged = (
                    include_merged[channel_index] if apply_adjustments and channel_index < len(include_merged) else True
                )
                plane = np.asarray(image.get_plane(c=channel_index, requested_dims=requested))
                colored = colorize(
                    plane,
                    lut_name,
                    channel_brightness,
                    channel_contrast,
                    channel_gamma,
                    channel_black,
                    channel_white,
                )

                if channel_include_merged:
                    merged_channels.append(colored)

                channel_name = f"C{channel_index + 1}"
                filename = f"{datetime_label}_{safe_name(record.name)}-c{channel_index + 1}{suffix}.tif"
                output_path = series_folder / channel_name / filename
                write_tiff(output_path, colored)
                written_count += 1
                if progress_callback is not None:
                    progress_callback(written_count)
                manifest_rows.append(
                    {
                        "sequence": f"{sequence:03d}",
                        "lif_file": str(lif_path),
                        "lif_index": str(record.lif_index),
                        "series_name": record.name,
                        "acquired_at": record.acquired_at.isoformat() if record.acquired_at else "",
                        "kind": channel_name,
                        "lut": lut_name,
                        "include_merged": str(channel_include_merged),
                        "black": f"{channel_black:.1f}",
                        "white": f"{channel_white:.1f}",
                        "gamma": f"{channel_gamma:.2f}",
                        "brightness": f"{channel_brightness:.2f}",
                        "contrast": f"{channel_contrast:.2f}",
                        "path": str(output_path),
                    }
                )

            merged = merge_colored(merged_channels, merge_mode)
            if merged is not None:
                filename = f"{datetime_label}_{safe_name(record.name)}-merged{suffix}.tif"
                output_path = series_folder / "Merged" / filename
                write_tiff(output_path, merged)
                written_count += 1
                if progress_callback is not None:
                    progress_callback(written_count)
                manifest_rows.append(
                    {
                        "sequence": f"{sequence:03d}",
                        "lif_file": str(lif_path),
                        "lif_index": str(record.lif_index),
                        "series_name": record.name,
                        "acquired_at": record.acquired_at.isoformat() if record.acquired_at else "",
                        "kind": "Merged",
                        "lut": "+".join(record.channel_luts),
                        "include_merged": "merged",
                        "black": "applied" if apply_adjustments else "0.0",
                        "white": "applied" if apply_adjustments else "255.0",
                        "gamma": "applied" if apply_adjustments else "1.00",
                        "brightness": "applied" if apply_adjustments else "1.00",
                        "contrast": "applied" if apply_adjustments else "1.00",
                        "path": str(output_path),
                    }
                )

    with manifest_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "sequence",
                "lif_file",
                "lif_index",
                "series_name",
                "acquired_at",
                "kind",
                "lut",
                "include_merged",
                "black",
                "white",
                "gamma",
                "brightness",
                "contrast",
                "path",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    return len(manifest_rows)


class LifToTifApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.language = "zh"
        self.lang_var = tk.StringVar(value="中文")
        self.preview_mode_var = tk.StringVar(value="Merged")
        self.merge_mode_var = tk.StringVar(value="Max")
        self.auto_low_var = tk.DoubleVar(value=0.5)
        self.auto_high_var = tk.DoubleVar(value=99.8)
        self.auto_target_var = tk.DoubleVar(value=230.0)
        self.root.title(self.t("app_title"))
        self.root.geometry("1600x950")
        self.root.minsize(1450, 800)

        self.lif_path: Path | None = None
        self.lif: LifFile | None = None
        self.records: list[SeriesRecord] = []
        self.current_record: SeriesRecord | None = None
        self.current_planes: list[np.ndarray] = []
        self.brightness_by_index: dict[int, list[float]] = {}
        self.contrast_by_index: dict[int, list[float]] = {}
        self.gamma_by_index: dict[int, list[float]] = {}
        self.black_by_index: dict[int, list[float]] = {}
        self.white_by_index: dict[int, list[float]] = {}
        self.include_merged_by_index: dict[int, list[bool]] = {}
        self.lut_by_index: dict[int, list[str]] = {}
        self.preview_photo = None
        self.worker_queue: queue.Queue = queue.Queue()
        self.export_cancel_event: threading.Event | None = None
        self.export_total = 0

        self.output_var = tk.StringVar(value=str((APP_DIR / "提取出的tif").resolve()))
        self.status_var = tk.StringVar(value=self.t("status_start"))
        self.path_var = tk.StringVar(value=self.t("no_lif"))
        self.apply_brightness_var = tk.BooleanVar(value=True)
        self.include_merged_vars: list[tk.BooleanVar] = []
        self.lut_vars: list[tk.StringVar] = []
        self.black_vars: list[tk.DoubleVar] = []
        self.white_vars: list[tk.DoubleVar] = []
        self.gamma_vars: list[tk.DoubleVar] = []
        self.brightness_vars: list[tk.DoubleVar] = []
        self.contrast_vars: list[tk.DoubleVar] = []
        self.slider_frame: ttk.Frame | None = None
        self.slider_canvas: tk.Canvas | None = None
        self.preview_wrap: ttk.Frame | None = None

        self.build_ui()
        self.root.after(150, self.poll_worker_queue)

    def t(self, key: str, **kwargs) -> str:
        text = STRINGS.get(self.language, STRINGS["zh"]).get(key, key)
        return text.format(**kwargs) if kwargs else text

    def build_ui(self) -> None:
        self.root.title(self.t("app_title"))
        toolbar = ttk.Frame(self.root, padding=(12, 10))
        toolbar.pack(fill=tk.X)

        row1 = ttk.Frame(toolbar)
        row1.pack(fill=tk.X)
        ttk.Button(row1, text=self.t("open_lif"), command=self.open_lif).pack(side=tk.LEFT)
        ttk.Button(row1, text=self.t("choose_output"), command=self.choose_output).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(row1, text=self.t("open_output"), command=self.open_output_folder).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(row1, text=self.t("language")).pack(side=tk.LEFT, padx=(18, 6))
        lang_box = ttk.Combobox(row1, textvariable=self.lang_var, values=("中文", "English"), width=10, state="readonly")
        lang_box.pack(side=tk.LEFT)
        lang_box.bind("<<ComboboxSelected>>", self.on_language_changed)

        row2 = ttk.Frame(toolbar)
        row2.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(row2, text=self.t("export_current"), command=self.export_current).pack(side=tk.LEFT)
        ttk.Button(row2, text=self.t("export_all_current"), command=self.export_all_with_current).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(row2, text=self.t("export_all_per_image"), command=self.export_all_per_image).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Checkbutton(row2, text=self.t("apply_all_adjustments"), variable=self.apply_brightness_var).pack(
            side=tk.LEFT, padx=(18, 0)
        )
        ttk.Button(row2, text=self.t("reset_current"), command=self.reset_current_adjustments).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(row2, text=self.t("reset_all"), command=self.reset_all_adjustments).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(row2, text=self.t("auto_levels"), command=self.auto_levels_current).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(row2, text=self.t("auto_all"), command=self.auto_levels_all).pack(side=tk.LEFT, padx=(8, 0))
        self.cancel_button = ttk.Button(row2, text=self.t("cancel_export"), command=self.cancel_export, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=(8, 0))

        path_bar = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        path_bar.pack(fill=tk.X)
        ttk.Label(path_bar, textvariable=self.path_var).pack(anchor=tk.W)
        output_row = ttk.Frame(path_bar)
        output_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(output_row, text=self.t("output")).pack(side=tk.LEFT)
        ttk.Entry(output_row, textvariable=self.output_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        main = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main, width=430)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        right = ttk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0))

        columns = ("seq", "time", "name", "channels", "size")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("seq", text=self.t("seq"))
        self.tree.heading("time", text=self.t("time"))
        self.tree.heading("name", text=self.t("name"))
        self.tree.heading("channels", text=self.t("channels"))
        self.tree.heading("size", text=self.t("size"))
        self.tree.column("seq", width=44, anchor=tk.CENTER, stretch=False)
        self.tree.column("time", width=130, stretch=False)
        self.tree.column("name", width=125)
        self.tree.column("channels", width=48, anchor=tk.CENTER, stretch=False)
        self.tree.column("size", width=78, stretch=False)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_record)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        right_main = ttk.Frame(right)
        right_main.pack(fill=tk.BOTH, expand=True)
        right_main.grid_rowconfigure(0, weight=1)
        right_main.grid_columnconfigure(0, weight=1)
        right_main.grid_columnconfigure(1, weight=0)

        preview_wrap = ttk.Frame(right_main)
        preview_wrap.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))
        self.preview_wrap = preview_wrap

        controls_wrap = ttk.LabelFrame(right_main, text=self.t("channel_adjustments"), padding=(10, 8))
        controls_wrap.grid(row=0, column=1, sticky=tk.NS)
        controls_wrap.configure(width=390)
        controls_wrap.grid_propagate(False)

        self.preview_label = ttk.Label(preview_wrap, text=self.t("preview_area"), anchor=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        preview_wrap.bind("<Configure>", lambda _event=None: self.render_preview())

        self.info_var = tk.StringVar(value="")
        ttk.Label(controls_wrap, textvariable=self.info_var).pack(fill=tk.X, pady=(0, 6))

        preview_mode_row = ttk.Frame(controls_wrap)
        preview_mode_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(preview_mode_row, text=self.t("preview_mode")).grid(row=0, column=0, sticky=tk.W, padx=(0, 6), pady=2)
        self.preview_mode_combo = ttk.Combobox(
            preview_mode_row,
            textvariable=self.preview_mode_var,
            values=("Merged",),
            width=12,
            state="readonly",
        )
        self.preview_mode_combo.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.preview_mode_combo.bind("<<ComboboxSelected>>", lambda _event=None: self.render_preview())
        ttk.Label(preview_mode_row, text=self.t("merge_mode")).grid(row=1, column=0, sticky=tk.W, padx=(0, 6), pady=2)
        self.merge_mode_combo = ttk.Combobox(
            preview_mode_row,
            textvariable=self.merge_mode_var,
            values=MERGE_MODES,
            width=10,
            state="readonly",
        )
        self.merge_mode_combo.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.merge_mode_combo.bind("<<ComboboxSelected>>", lambda _event=None: self.render_preview())

        auto_box = ttk.LabelFrame(controls_wrap, text=self.t("auto_settings"), padding=(8, 4))
        auto_box.pack(fill=tk.X, pady=(0, 6))
        for row_index, (label_key, var, width) in enumerate((
            ("low_percentile", self.auto_low_var, 6),
            ("high_percentile", self.auto_high_var, 6),
            ("target_max", self.auto_target_var, 6),
        )):
            ttk.Label(auto_box, text=self.t(label_key)).grid(row=row_index, column=0, sticky=tk.W, padx=(0, 6), pady=2)
            ttk.Spinbox(
                auto_box,
                from_=0.0,
                to=255.0 if label_key == "target_max" else 100.0,
                increment=0.1,
                textvariable=var,
                width=width,
            ).grid(
                row=row_index, column=1, sticky=tk.W, pady=2
            )

        slider_area = ttk.Frame(controls_wrap)
        slider_area.pack(fill=tk.BOTH, expand=True)
        self.slider_canvas = tk.Canvas(slider_area, highlightthickness=0)
        slider_scroll = ttk.Scrollbar(slider_area, orient=tk.VERTICAL, command=self.slider_canvas.yview)
        self.slider_canvas.configure(yscrollcommand=slider_scroll.set)
        self.slider_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        slider_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.slider_frame = ttk.Frame(self.slider_canvas, padding=(0, 4))
        slider_window = self.slider_canvas.create_window((0, 0), window=self.slider_frame, anchor=tk.NW)
        self.slider_frame.bind(
            "<Configure>", lambda _event=None: self.slider_canvas.configure(scrollregion=self.slider_canvas.bbox("all"))
        )
        self.slider_canvas.bind(
            "<Configure>", lambda event: self.slider_canvas.itemconfigure(slider_window, width=event.width)
        )

        bottom = ttk.Frame(self.root, padding=(12, 0, 12, 10))
        bottom.pack(fill=tk.X)
        self.progress = ttk.Progressbar(bottom, mode="indeterminate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(bottom, textvariable=self.status_var, width=48, anchor=tk.E).pack(side=tk.RIGHT, padx=(12, 0))

        if self.records:
            self.populate_tree()
            if self.current_record is not None:
                iid = str(self.current_record.lif_index)
                if iid in self.tree.get_children():
                    self.tree.selection_set(iid)
                    self.tree.focus(iid)
                self.update_preview_modes()
                self.build_sliders(self.current_record, max(1, len(self.current_planes)))
                self.render_preview()
                self.update_info_text()
        elif self.current_record is None:
            self.preview_label.configure(text=self.t("preview_area"))

    def on_language_changed(self, _event=None) -> None:
        self.language = "en" if self.lang_var.get() == "English" else "zh"
        current_status = self.status_var.get()
        for child in self.root.winfo_children():
            child.destroy()
        if self.lif_path is None:
            self.path_var.set(self.t("no_lif"))
        if current_status in {STRINGS["zh"]["status_start"], STRINGS["en"]["status_start"]}:
            self.status_var.set(self.t("status_start"))
        self.build_ui()

    def open_lif(self) -> None:
        initial = str(APP_DIR)
        if self.lif_path is not None:
            initial = str(self.lif_path.parent)
        filename = filedialog.askopenfilename(
            title=self.t("open_lif"),
            initialdir=initial,
            filetypes=[("Leica LIF", "*.lif"), ("All files", "*.*")],
        )
        if not filename:
            return

        self.set_busy(self.t("reading_meta"))
        self.root.update_idletasks()
        try:
            lif_path = Path(filename).resolve()
            lif = LifFile(str(lif_path))
            records = discover_records(lif)
        except Exception as exc:
            self.clear_busy()
            messagebox.showerror(self.t("read_failed_title"), self.t("read_failed", error=exc))
            return

        self.lif_path = lif_path
        self.lif = lif
        self.records = records
        self.current_record = None
        self.current_planes = []
        self.brightness_by_index.clear()
        self.contrast_by_index.clear()
        self.gamma_by_index.clear()
        self.black_by_index.clear()
        self.white_by_index.clear()
        self.include_merged_by_index.clear()
        self.lut_by_index.clear()
        self.path_var.set(f"LIF: {lif_path}")
        self.output_var.set(str((lif_path.parent / "提取出的tif").resolve()))
        self.populate_tree()
        self.clear_sliders()
        self.preview_mode_var.set("Merged")
        self.preview_label.configure(image="", text=self.t("select_preview"))
        self.info_var.set(self.t("series_loaded", count=len(records)))
        self.clear_busy(self.t("read_done", count=len(records)))

        if records:
            first = self.tree.get_children()[0]
            self.tree.selection_set(first)
            self.tree.focus(first)
            self.load_record(records[0])

    def populate_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for sequence, record in enumerate(self.records, start=1):
            time_text = record.acquired_at.strftime("%Y-%m-%d %H:%M:%S") if record.acquired_at else "unknown"
            self.tree.insert(
                "",
                tk.END,
                iid=str(record.lif_index),
                values=(f"{sequence:03d}", time_text, record.name, len(record.channel_luts), record.size_label),
            )

    def on_select_record(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection or self.lif is None:
            return
        lif_index = int(selection[0])
        record = next((item for item in self.records if item.lif_index == lif_index), None)
        if record is None:
            return
        self.load_record(record)

    def load_record(self, record: SeriesRecord) -> None:
        assert self.lif is not None
        self.set_busy(self.t("loading_preview"))
        self.root.update_idletasks()
        try:
            image = self.lif.get_image(record.lif_index)
            self.current_planes = [self.make_preview_plane(image, c) for c in range(image.channels)]
            self.current_record = record
            self.ensure_channel_settings(record, image.channels)
            self.update_preview_modes()
            self.build_sliders(record, image.channels)
            self.render_preview()
            self.update_info_text()
            self.clear_busy(self.t("preview_done"))
        except Exception as exc:
            self.clear_busy()
            messagebox.showerror(self.t("preview_failed_title"), self.t("preview_failed", error=exc))

    def make_preview_plane(self, image, channel: int) -> np.ndarray:
        return make_preview_plane_array(image, channel)

    def ensure_channel_settings(self, record: SeriesRecord, channels: int) -> None:
        def extend_float(mapping: dict[int, list[float]], default: float) -> None:
            values = mapping.setdefault(record.lif_index, [])
            while len(values) < channels:
                values.append(default)
            del values[channels:]

        extend_float(self.brightness_by_index, 1.0)
        extend_float(self.contrast_by_index, 1.0)
        extend_float(self.gamma_by_index, 1.0)
        extend_float(self.black_by_index, 0.0)
        extend_float(self.white_by_index, 255.0)

        include_values = self.include_merged_by_index.setdefault(record.lif_index, [])
        while len(include_values) < channels:
            include_values.append(True)
        del include_values[channels:]

        lut_values = self.lut_by_index.setdefault(record.lif_index, [])
        while len(lut_values) < channels:
            idx = len(lut_values)
            lut_values.append(record.channel_luts[idx] if idx < len(record.channel_luts) else "Gray")
        del lut_values[channels:]

    def update_preview_modes(self) -> None:
        if self.current_record is None:
            values = ("Merged",)
        else:
            values = ("Merged",) + tuple(f"C{i + 1}" for i in range(len(self.current_record.channel_luts)))
        if hasattr(self, "preview_mode_combo"):
            self.preview_mode_combo.configure(values=values)
        if self.preview_mode_var.get() not in values:
            self.preview_mode_var.set("Merged")

    def update_info_text(self) -> None:
        if self.current_record is None:
            self.info_var.set("")
            return
        when = self.current_record.acquired_at.strftime("%Y-%m-%d %H:%M:%S") if self.current_record.acquired_at else self.t("unknown_time")
        self.info_var.set(
            f"{self.current_record.name} | {when} | {len(self.current_record.channel_luts)} {self.t('channels')} | {self.current_record.size_label}"
        )

    def build_sliders(self, record: SeriesRecord, channels: int) -> None:
        self.clear_sliders()
        self.ensure_channel_settings(record, channels)
        brightness = self.brightness_by_index[record.lif_index]
        contrast = self.contrast_by_index[record.lif_index]
        gamma = self.gamma_by_index[record.lif_index]
        black = self.black_by_index[record.lif_index]
        white = self.white_by_index[record.lif_index]
        include_merged = self.include_merged_by_index[record.lif_index]
        lut_values = self.lut_by_index[record.lif_index]
        for idx in range(channels):
            lut = lut_values[idx]
            box = ttk.LabelFrame(self.slider_frame, text=f"C{idx + 1} {lut}", padding=(8, 4))
            box.pack(fill=tk.X, pady=3)

            top_row = ttk.Frame(box)
            top_row.pack(fill=tk.X, pady=(0, 2))
            include_var = tk.BooleanVar(value=include_merged[idx])
            include_var.trace_add("write", lambda *_args, channel=idx: self.on_adjustment_changed(channel))
            self.include_merged_vars.append(include_var)
            ttk.Checkbutton(top_row, text=self.t("include_merged"), variable=include_var).pack(side=tk.LEFT)

            ttk.Label(top_row, text=self.t("color")).pack(side=tk.LEFT, padx=(10, 4))
            lut_var = tk.StringVar(value=lut)
            self.lut_vars.append(lut_var)
            lut_combo = ttk.Combobox(top_row, textvariable=lut_var, values=LUT_CHOICES, width=10, state="readonly")
            lut_combo.pack(side=tk.LEFT)
            lut_combo.bind("<<ComboboxSelected>>", lambda _event=None, channel=idx: self.on_adjustment_changed(channel))

            self.black_vars.append(
                self.add_adjustment_row(box, self.t("black"), black[idx], 0.0, 254.0, 1.0, "black", idx)
            )
            self.white_vars.append(
                self.add_adjustment_row(box, self.t("white"), white[idx], 1.0, 255.0, 1.0, "white", idx)
            )
            self.gamma_vars.append(
                self.add_adjustment_row(box, self.t("gamma"), gamma[idx], 0.1, 5.0, 0.05, "gamma", idx)
            )
            self.brightness_vars.append(
                self.add_adjustment_row(box, self.t("brightness"), brightness[idx], 0.0, 5.0, 0.05, "brightness", idx)
            )
            self.contrast_vars.append(
                self.add_adjustment_row(box, self.t("contrast"), contrast[idx], 0.0, 5.0, 0.05, "contrast", idx)
            )

    def add_adjustment_row(
        self,
        parent,
        label_text: str,
        value: float,
        min_value: float,
        max_value: float,
        step: float,
        kind: str,
        channel: int,
    ) -> tk.DoubleVar:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(row, text=label_text, width=8).pack(side=tk.LEFT)
        var = tk.DoubleVar(value=value)
        ttk.Button(row, text="-", width=3, command=lambda: self.nudge_adjustment(kind, channel, -step)).pack(side=tk.LEFT)
        tk.Scale(
            row,
            from_=min_value,
            to=max_value,
            resolution=step,
            orient=tk.HORIZONTAL,
            variable=var,
            showvalue=False,
            length=150,
            width=16,
            sliderlength=26,
            command=lambda _value: self.on_adjustment_changed(channel),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
        suffix = "x" if kind in {"brightness", "contrast", "gamma"} else ""
        value_label = ttk.Label(row, text=f"{value:.2f}{suffix}", width=7)
        value_label.pack(side=tk.LEFT)
        ttk.Button(row, text="+", width=3, command=lambda: self.nudge_adjustment(kind, channel, step)).pack(side=tk.LEFT)
        var._value_label = value_label
        var._value_suffix = suffix
        return var

    def clear_sliders(self) -> None:
        self.include_merged_vars.clear()
        self.lut_vars.clear()
        self.black_vars.clear()
        self.white_vars.clear()
        self.gamma_vars.clear()
        self.brightness_vars.clear()
        self.contrast_vars.clear()
        if self.slider_frame is not None:
            for child in self.slider_frame.winfo_children():
                child.destroy()

    def on_adjustment_changed(self, channel: int) -> None:
        if self.current_record is None:
            return
        self.ensure_channel_settings(self.current_record, len(self.brightness_vars))
        brightness = self.brightness_by_index.setdefault(self.current_record.lif_index, [1.0] * len(self.brightness_vars))
        contrast = self.contrast_by_index.setdefault(self.current_record.lif_index, [1.0] * len(self.contrast_vars))
        gamma = self.gamma_by_index.setdefault(self.current_record.lif_index, [1.0] * len(self.gamma_vars))
        black = self.black_by_index.setdefault(self.current_record.lif_index, [0.0] * len(self.black_vars))
        white = self.white_by_index.setdefault(self.current_record.lif_index, [255.0] * len(self.white_vars))
        include_merged = self.include_merged_by_index.setdefault(self.current_record.lif_index, [True] * len(self.include_merged_vars))
        lut_values = self.lut_by_index.setdefault(self.current_record.lif_index, list(self.current_record.channel_luts))
        if channel < len(brightness):
            brightness[channel] = float(self.brightness_vars[channel].get())
        if channel < len(contrast):
            contrast[channel] = float(self.contrast_vars[channel].get())
        if channel < len(gamma):
            gamma[channel] = float(self.gamma_vars[channel].get())
        if channel < len(black):
            black[channel] = float(self.black_vars[channel].get())
        if channel < len(white):
            white[channel] = max(float(self.white_vars[channel].get()), black[channel] + 1.0)
            if float(self.white_vars[channel].get()) != white[channel]:
                self.white_vars[channel].set(white[channel])
        if channel < len(include_merged):
            include_merged[channel] = bool(self.include_merged_vars[channel].get())
        if channel < len(lut_values):
            lut_values[channel] = self.lut_vars[channel].get()
        self.update_value_labels()
        self.render_preview()

    def nudge_adjustment(self, kind: str, channel: int, delta: float) -> None:
        vars_by_kind = {
            "brightness": self.brightness_vars,
            "contrast": self.contrast_vars,
            "gamma": self.gamma_vars,
            "black": self.black_vars,
            "white": self.white_vars,
        }
        vars_for_kind = vars_by_kind.get(kind, [])
        if channel >= len(vars_for_kind):
            return
        max_value = 255.0 if kind in {"black", "white"} else 5.0
        min_value = 0.1 if kind == "gamma" else 0.0
        value = max(min_value, min(max_value, float(vars_for_kind[channel].get()) + delta))
        vars_for_kind[channel].set(round(value, 2))
        self.on_adjustment_changed(channel)

    def update_value_labels(self) -> None:
        for var in self.black_vars + self.white_vars + self.gamma_vars + self.brightness_vars + self.contrast_vars:
            label = getattr(var, "_value_label", None)
            if label is not None:
                suffix = getattr(var, "_value_suffix", "")
                value = float(var.get())
                label.configure(text=f"{value:.2f}{suffix}" if suffix else f"{value:.1f}")

    def render_preview(self) -> None:
        if self.current_record is None or not self.current_planes:
            return
        brightness = self.brightness_by_index.get(self.current_record.lif_index, [1.0] * len(self.current_planes))
        contrast = self.contrast_by_index.get(self.current_record.lif_index, [1.0] * len(self.current_planes))
        gamma = self.gamma_by_index.get(self.current_record.lif_index, [1.0] * len(self.current_planes))
        black = self.black_by_index.get(self.current_record.lif_index, [0.0] * len(self.current_planes))
        white = self.white_by_index.get(self.current_record.lif_index, [255.0] * len(self.current_planes))
        include_merged = self.include_merged_by_index.get(self.current_record.lif_index, [True] * len(self.current_planes))
        lut_values = self.lut_by_index.get(self.current_record.lif_index, list(self.current_record.channel_luts))
        mode = self.preview_mode_var.get()
        if mode.startswith("C"):
            try:
                idx = int(mode[1:]) - 1
            except ValueError:
                idx = 0
            idx = max(0, min(idx, len(self.current_planes) - 1))
            lut = lut_values[idx] if idx < len(lut_values) else "Gray"
            brightness_value = brightness[idx] if idx < len(brightness) else 1.0
            contrast_value = contrast[idx] if idx < len(contrast) else 1.0
            gamma_value = gamma[idx] if idx < len(gamma) else 1.0
            black_value = black[idx] if idx < len(black) else 0.0
            white_value = white[idx] if idx < len(white) else 255.0
            preview = colorize(self.current_planes[idx], lut, brightness_value, contrast_value, gamma_value, black_value, white_value)
        else:
            merged_channels = []
            for idx, plane in enumerate(self.current_planes):
                if idx < len(include_merged) and not include_merged[idx]:
                    continue
                lut = lut_values[idx] if idx < len(lut_values) else "Gray"
                brightness_value = brightness[idx] if idx < len(brightness) else 1.0
                contrast_value = contrast[idx] if idx < len(contrast) else 1.0
                gamma_value = gamma[idx] if idx < len(gamma) else 1.0
                black_value = black[idx] if idx < len(black) else 0.0
                white_value = white[idx] if idx < len(white) else 255.0
                colored = colorize(plane, lut, brightness_value, contrast_value, gamma_value, black_value, white_value)
                merged_channels.append(colored)
            merged = merge_colored(merged_channels, self.merge_mode_var.get())
            if merged is None:
                return
            preview = merged
        image = Image.fromarray(preview)
        target_width = PREVIEW_SIZE
        target_height = PREVIEW_SIZE
        if self.preview_wrap is not None:
            target_width = max(120, self.preview_wrap.winfo_width() - 12)
            target_height = max(120, self.preview_wrap.winfo_height() - 12)
        image.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(image)
        self.preview_label.configure(image=self.preview_photo, text="")

    def choose_output(self) -> None:
        folder = filedialog.askdirectory(title=self.t("choose_output"), initialdir=str(Path(self.output_var.get()).parent))
        if folder:
            self.output_var.set(str(Path(folder).resolve()))

    def open_output_folder(self) -> None:
        folder = Path(self.output_var.get()).expanduser().resolve()
        folder.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(folder)], check=False)

    def reset_current_adjustments(self) -> None:
        if self.current_record is None:
            return
        channels = len(self.current_planes) if self.current_planes else max(1, len(self.current_record.channel_luts))
        self.ensure_channel_settings(self.current_record, channels)
        self.brightness_by_index[self.current_record.lif_index] = [1.0] * channels
        self.contrast_by_index[self.current_record.lif_index] = [1.0] * channels
        self.gamma_by_index[self.current_record.lif_index] = [1.0] * channels
        self.black_by_index[self.current_record.lif_index] = [0.0] * channels
        self.white_by_index[self.current_record.lif_index] = [255.0] * channels
        self.include_merged_by_index[self.current_record.lif_index] = [True] * channels
        self.lut_by_index[self.current_record.lif_index] = [
            self.current_record.channel_luts[i] if i < len(self.current_record.channel_luts) else "Gray"
            for i in range(channels)
        ]
        for var in self.brightness_vars + self.contrast_vars + self.gamma_vars:
            var.set(1.0)
        for var in self.black_vars:
            var.set(0.0)
        for var in self.white_vars:
            var.set(255.0)
        for var in self.include_merged_vars:
            var.set(True)
        for idx, var in enumerate(self.lut_vars):
            var.set(self.lut_by_index[self.current_record.lif_index][idx])
        self.update_value_labels()
        self.render_preview()
        self.status_var.set(self.t("current_reset"))

    def reset_all_adjustments(self) -> None:
        self.brightness_by_index.clear()
        self.contrast_by_index.clear()
        self.gamma_by_index.clear()
        self.black_by_index.clear()
        self.white_by_index.clear()
        self.include_merged_by_index.clear()
        self.lut_by_index.clear()
        if self.current_record is not None:
            self.reset_current_adjustments()
        self.status_var.set(self.t("all_reset"))

    def auto_parameters_for_plane(self, plane: np.ndarray) -> tuple[float, float, float]:
        return compute_auto_parameters(
            plane,
            float(self.auto_low_var.get()),
            float(self.auto_high_var.get()),
            float(self.auto_target_var.get()),
        )

    def apply_auto_to_record(self, record: SeriesRecord, planes: list[np.ndarray]) -> None:
        channels = len(planes)
        self.ensure_channel_settings(record, channels)
        black_values = []
        white_values = []
        brightness_values = []
        for plane in planes:
            black, white, brightness = self.auto_parameters_for_plane(plane)
            black_values.append(black)
            white_values.append(white)
            brightness_values.append(brightness)
        self.black_by_index[record.lif_index] = black_values
        self.white_by_index[record.lif_index] = white_values
        self.brightness_by_index[record.lif_index] = brightness_values
        self.contrast_by_index[record.lif_index] = [1.0] * channels
        self.gamma_by_index[record.lif_index] = [1.0] * channels

    def refresh_current_controls_from_settings(self) -> None:
        if self.current_record is None:
            return
        idx = self.current_record.lif_index
        mappings = (
            (self.black_vars, self.black_by_index.get(idx, [])),
            (self.white_vars, self.white_by_index.get(idx, [])),
            (self.gamma_vars, self.gamma_by_index.get(idx, [])),
            (self.brightness_vars, self.brightness_by_index.get(idx, [])),
            (self.contrast_vars, self.contrast_by_index.get(idx, [])),
        )
        for vars_list, values in mappings:
            for channel, value in enumerate(values[: len(vars_list)]):
                vars_list[channel].set(value)
        for channel, value in enumerate(self.include_merged_by_index.get(idx, [])[: len(self.include_merged_vars)]):
            self.include_merged_vars[channel].set(value)
        for channel, value in enumerate(self.lut_by_index.get(idx, [])[: len(self.lut_vars)]):
            self.lut_vars[channel].set(value)
        self.update_value_labels()

    def auto_levels_current(self) -> None:
        if self.current_record is None or not self.current_planes:
            messagebox.showinfo(self.t("no_selected_title"), self.t("no_selected"))
            return
        self.apply_auto_to_record(self.current_record, self.current_planes)
        self.refresh_current_controls_from_settings()
        self.render_preview()
        self.status_var.set(self.t("auto_current_done"))

    def auto_levels_all(self) -> None:
        if self.lif_path is None or not self.records:
            messagebox.showinfo(self.t("no_lif_title"), self.t("no_lif_msg"))
            return
        self.export_total = len(self.records)
        self.export_cancel_event = threading.Event()
        auto_params = (
            float(self.auto_low_var.get()),
            float(self.auto_high_var.get()),
            float(self.auto_target_var.get()),
        )
        self.set_exporting(self.t("auto_running"), self.export_total)
        thread = threading.Thread(
            target=self.auto_levels_all_worker,
            args=(self.lif_path, list(self.records), auto_params, self.export_cancel_event),
            daemon=True,
        )
        thread.start()

    def auto_levels_all_worker(
        self,
        lif_path: Path,
        records: list[SeriesRecord],
        auto_params: tuple[float, float, float],
        cancel_event: threading.Event,
    ) -> None:
        try:
            lif = LifFile(str(lif_path))
            results = {
                "brightness": {},
                "contrast": {},
                "gamma": {},
                "black": {},
                "white": {},
                "include": {},
                "lut": {},
            }
            for index, record in enumerate(records, start=1):
                if cancel_event.is_set():
                    raise ExportCancelled()
                image = lif.get_image(record.lif_index)
                planes = [make_preview_plane_array(image, c) for c in range(image.channels)]
                black_values = []
                white_values = []
                brightness_values = []
                for plane in planes:
                    black, white, brightness = compute_auto_parameters(plane, *auto_params)
                    black_values.append(black)
                    white_values.append(white)
                    brightness_values.append(brightness)
                channels = image.channels
                results["brightness"][record.lif_index] = brightness_values
                results["contrast"][record.lif_index] = [1.0] * channels
                results["gamma"][record.lif_index] = [1.0] * channels
                results["black"][record.lif_index] = black_values
                results["white"][record.lif_index] = white_values
                results["include"][record.lif_index] = self.include_merged_by_index.get(record.lif_index, [True] * channels)
                results["lut"][record.lif_index] = self.lut_by_index.get(record.lif_index, list(record.channel_luts))
                self.worker_queue.put(("auto_progress", index))
            self.worker_queue.put(("auto_ok", results, len(records)))
        except ExportCancelled:
            self.worker_queue.put(("cancelled", Path(self.output_var.get()).expanduser().resolve()))
        except Exception:
            self.worker_queue.put(("error", traceback.format_exc()))

    def export_current(self) -> None:
        if self.current_record is None:
            messagebox.showinfo(self.t("no_selected_title"), self.t("no_selected"))
            return
        sequence = self.records.index(self.current_record) + 1
        self.start_export([(sequence, self.current_record)], self.t("current_image"))

    def export_all_with_current(self) -> None:
        if not self.records:
            messagebox.showinfo(self.t("no_lif_title"), self.t("no_lif_msg"))
            return
        records_with_sequence = list(enumerate(self.records, start=1))
        self.start_export(records_with_sequence, self.t("all_images"), use_current_adjustments=True)

    def export_all_per_image(self) -> None:
        if not self.records:
            messagebox.showinfo(self.t("no_lif_title"), self.t("no_lif_msg"))
            return
        records_with_sequence = list(enumerate(self.records, start=1))
        self.start_export(records_with_sequence, self.t("all_images"), use_current_adjustments=False)

    def preview_then_export_all(self) -> None:
        if not self.records:
            messagebox.showinfo(self.t("no_lif_title"), self.t("no_lif_msg"))
            return
        if self.current_record is None:
            first = self.tree.get_children()[0]
            self.tree.selection_set(first)
            self.tree.focus(first)
            self.root.update_idletasks()
        self.export_all_with_current()

    def start_export(
        self,
        records_with_sequence: list[tuple[int, SeriesRecord]],
        label: str,
        use_current_adjustments: bool = False,
    ) -> None:
        if self.lif_path is None:
            messagebox.showinfo(self.t("no_lif_title"), self.t("no_lif_msg"))
            return
        output_root = Path(self.output_var.get()).expanduser().resolve()
        apply_adjustments = bool(self.apply_brightness_var.get())
        output_root.mkdir(parents=True, exist_ok=True)
        manifest_path = output_root / f"提取记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        adjustment_maps = self.export_adjustment_maps(
            records_with_sequence, use_current_adjustments
        )
        self.export_total = expected_tiff_count(records_with_sequence)
        self.export_cancel_event = threading.Event()

        self.set_exporting(self.t("exporting_label", label=label), self.export_total)
        thread = threading.Thread(
            target=self.export_worker,
            args=(
                self.lif_path,
                records_with_sequence,
                output_root,
                manifest_path,
                *adjustment_maps,
                apply_adjustments,
                self.merge_mode_var.get(),
                self.export_cancel_event,
            ),
            daemon=True,
        )
        thread.start()

    def export_adjustment_maps(
        self, records_with_sequence: list[tuple[int, SeriesRecord]], use_current_adjustments: bool
    ):
        if not use_current_adjustments or self.current_record is None:
            return (
                {key: list(value) for key, value in self.brightness_by_index.items()},
                {key: list(value) for key, value in self.contrast_by_index.items()},
                {key: list(value) for key, value in self.gamma_by_index.items()},
                {key: list(value) for key, value in self.black_by_index.items()},
                {key: list(value) for key, value in self.white_by_index.items()},
                {key: list(value) for key, value in self.include_merged_by_index.items()},
                {key: list(value) for key, value in self.lut_by_index.items()},
            )

        current_brightness = [float(var.get()) for var in self.brightness_vars] or [1.0]
        current_contrast = [float(var.get()) for var in self.contrast_vars] or [1.0]
        current_gamma = [float(var.get()) for var in self.gamma_vars] or [1.0]
        current_black = [float(var.get()) for var in self.black_vars] or [0.0]
        current_white = [float(var.get()) for var in self.white_vars] or [255.0]
        current_include = [bool(var.get()) for var in self.include_merged_vars] or [True]
        current_luts = [var.get() for var in self.lut_vars] or ["Gray"]
        brightness_by_index: dict[int, list[float]] = {}
        contrast_by_index: dict[int, list[float]] = {}
        gamma_by_index: dict[int, list[float]] = {}
        black_by_index: dict[int, list[float]] = {}
        white_by_index: dict[int, list[float]] = {}
        include_by_index: dict[int, list[bool]] = {}
        lut_by_index: dict[int, list[str]] = {}
        for _sequence, record in records_with_sequence:
            channel_count = max(1, len(record.channel_luts))
            brightness_values = []
            contrast_values = []
            gamma_values = []
            black_values = []
            white_values = []
            include_values = []
            lut_values = []
            for channel_index in range(channel_count):
                brightness_values.append(
                    current_brightness[channel_index] if channel_index < len(current_brightness) else 1.0
                )
                contrast_values.append(current_contrast[channel_index] if channel_index < len(current_contrast) else 1.0)
                gamma_values.append(current_gamma[channel_index] if channel_index < len(current_gamma) else 1.0)
                black_values.append(current_black[channel_index] if channel_index < len(current_black) else 0.0)
                white_values.append(current_white[channel_index] if channel_index < len(current_white) else 255.0)
                include_values.append(current_include[channel_index] if channel_index < len(current_include) else True)
                lut_values.append(
                    current_luts[channel_index]
                    if channel_index < len(current_luts)
                    else (record.channel_luts[channel_index] if channel_index < len(record.channel_luts) else "Gray")
                )
            brightness_by_index[record.lif_index] = brightness_values
            contrast_by_index[record.lif_index] = contrast_values
            gamma_by_index[record.lif_index] = gamma_values
            black_by_index[record.lif_index] = black_values
            white_by_index[record.lif_index] = white_values
            include_by_index[record.lif_index] = include_values
            lut_by_index[record.lif_index] = lut_values
        return (
            brightness_by_index,
            contrast_by_index,
            gamma_by_index,
            black_by_index,
            white_by_index,
            include_by_index,
            lut_by_index,
        )

    def export_worker(
        self,
        lif_path: Path,
        records_with_sequence: list[tuple[int, SeriesRecord]],
        output_root: Path,
        manifest_path: Path,
        brightness_by_index: dict[int, list[float]],
        contrast_by_index: dict[int, list[float]],
        gamma_by_index: dict[int, list[float]],
        black_by_index: dict[int, list[float]],
        white_by_index: dict[int, list[float]],
        include_merged_by_index: dict[int, list[bool]],
        lut_by_index: dict[int, list[str]],
        apply_adjustments: bool,
        merge_mode: str,
        cancel_event: threading.Event,
    ) -> None:
        try:
            def progress_callback(done: int) -> None:
                self.worker_queue.put(("progress", done))

            count = export_records(
                lif_path,
                records_with_sequence,
                output_root,
                manifest_path,
                brightness_by_index,
                contrast_by_index,
                gamma_by_index,
                black_by_index,
                white_by_index,
                include_merged_by_index,
                lut_by_index,
                apply_adjustments,
                merge_mode,
                progress_callback=progress_callback,
                cancel_event=cancel_event,
            )
            self.worker_queue.put(("ok", count, output_root, manifest_path))
        except ExportCancelled:
            self.worker_queue.put(("cancelled", output_root))
        except Exception:
            self.worker_queue.put(("error", traceback.format_exc()))

    def poll_worker_queue(self) -> None:
        try:
            message = self.worker_queue.get_nowait()
        except queue.Empty:
            self.root.after(150, self.poll_worker_queue)
            return

        if message[0] == "progress":
            _, done = message
            self.progress.configure(value=done)
            total = self.export_total or 0
            self.status_var.set(self.t("exporting_progress", done=done, total=total))
        elif message[0] == "auto_progress":
            _, done = message
            self.progress.configure(value=done)
            total = self.export_total or 0
            self.status_var.set(self.t("exporting_progress", done=done, total=total))
        elif message[0] == "auto_ok":
            _, results, count = message
            self.brightness_by_index.update(results["brightness"])
            self.contrast_by_index.update(results["contrast"])
            self.gamma_by_index.update(results["gamma"])
            self.black_by_index.update(results["black"])
            self.white_by_index.update(results["white"])
            self.include_merged_by_index.update(results["include"])
            self.lut_by_index.update(results["lut"])
            if self.current_record is not None:
                self.refresh_current_controls_from_settings()
                self.render_preview()
            self.clear_busy(self.t("auto_all_done", count=count))
        elif message[0] == "ok":
            _, count, output_root, manifest_path = message
            self.clear_busy(self.t("export_done_status", count=count))
            messagebox.showinfo(
                self.t("export_done_title"),
                self.t("export_done_msg", output=output_root, count=count, manifest=manifest_path),
            )
        elif message[0] == "cancelled":
            _, output_root = message
            self.clear_busy(self.t("cancelled_status"))
            messagebox.showinfo(self.t("cancelled_title"), self.t("cancelled_msg", output=output_root))
        else:
            _, error_text = message
            self.clear_busy(self.t("export_failed"))
            messagebox.showerror(self.t("export_failed"), error_text)
        self.root.after(150, self.poll_worker_queue)

    def set_busy(self, text: str) -> None:
        self.status_var.set(text)
        self.progress.configure(mode="indeterminate")
        self.progress.start(10)

    def set_exporting(self, text: str, total: int) -> None:
        self.status_var.set(text)
        self.progress.stop()
        self.progress.configure(mode="determinate", maximum=max(1, total), value=0)
        self.cancel_button.configure(state=tk.NORMAL)

    def clear_busy(self, text: str | None = None) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)
        self.cancel_button.configure(state=tk.DISABLED)
        self.export_cancel_event = None
        if text is not None:
            self.status_var.set(text)

    def cancel_export(self) -> None:
        if self.export_cancel_event is not None:
            self.export_cancel_event.set()
            self.status_var.set(self.t("cancelling"))


def main() -> int:
    root = tk.Tk()
    style = ttk.Style(root)
    if "aqua" in style.theme_names():
        style.theme_use("aqua")
    LifToTifApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
