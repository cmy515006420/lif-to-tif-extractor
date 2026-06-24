# LIF 转 TIF 提取器 / LIF to TIFF Extractor

本工具用于把 Leica `.lif` 共聚焦文件按拍摄时间整理并导出为普通 TIFF。目前仅支持 macOS。

This tool converts Leica `.lif` confocal files into sorted TIFF folders. It currently supports macOS only.

## 平台 / Platform

- macOS only / 仅支持 macOS
- 启动脚本会在本机自动准备 Python 依赖到 `vendor/`，该目录不会上传到 GitHub。
- The launcher installs Python dependencies into the local `vendor/` folder when needed; `vendor/` is not uploaded to GitHub.

## 使用 / Usage

1. 双击 `start_lif_to_tif.command`
2. 点击 `打开 LIF / Open LIF`
3. 设置输出文件夹
4. 预览并调整每个通道的亮度、对比度
5. 导出当前图，或批量导出全部

## 功能 / Features

- 按 LIF 内部拍摄时间排序 / Sort by acquisition time
- 每个 series 一个文件夹 / One folder per series
- 按实际通道数动态生成 `C1`、`C2`、`C3`、`C4`... / Dynamically create `C1`, `C2`, `C3`, `C4`... for all channels
- 混合图输出到 `Merged` / Merged TIFFs in `Merged`
- 每个通道独立调颜色、是否参与 Merged、黑场、白场、Gamma、亮度和对比度 / Per-channel color, include-in-merged, black point, white point, gamma, brightness, and contrast
- 可预览 `Merged` 或单独通道 / Preview merged or individual channels
- 可选 `Max` 或 `Additive` 合成 / Choose `Max` or `Additive` merge mode
- 可设置自动调节参数，一键自动调节当前图或全部图 / Configurable auto adjustment for current image or all images
- 中英双语界面 / Chinese and English UI
- 大文件友好：预览使用缩小图，导出逐通道处理 / Large-file friendly preview and export

## 自动调节 / Auto Adjustment

默认自动调节会把每个通道的背景百分位设为黑场、信号百分位设为白场，并把目标亮度控制在不过曝的范围。自动调节全部图后，仍然可以逐张继续手动修改；最终导出会使用每张图最新保存的参数。

By default, auto adjustment estimates each channel's black point from the background percentile, white point from the signal percentile, and keeps target brightness below saturation. After auto-adjusting all images, you can still manually tune any image; final export uses the latest saved settings for each image.

## 数据安全 / Data Safety

本仓库不包含测试图片、显微图原始数据或导出结果。`.gitignore` 已排除 `.lif`、`.tif`、`testlif/`、导出目录、测试输出、缓存和本地依赖。

This repository does not include test images, microscopy source data, or exported results. The `.gitignore` excludes `.lif`, `.tif`, `testlif/`, exported folders, test output, caches, and local dependencies.

## 许可 / License

MIT License.
