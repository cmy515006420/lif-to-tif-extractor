# LIF 转 TIF 提取器 / LIF to TIFF Extractor

本工具用于把 Leica `.lif` 共聚焦文件按拍摄时间整理并导出为 TIFF、time-lapse 预览视频和可追溯记录表。目前仅支持 macOS。

This tool converts Leica `.lif` confocal files into sorted TIFF folders, time-lapse preview movies, and traceable manifest records. It currently supports macOS only.

## 平台 / Platform

- macOS only / 仅支持 macOS
- 首次允许后，启动脚本会自动清除本软件文件夹的 macOS 下载隔离标记，减少反复授权弹窗。
- After the first macOS approval, the launcher automatically removes the quarantine flag from this app folder to avoid repeated prompts.
- 启动脚本会在本机自动准备 Python 依赖到 `vendor/`，该目录不会上传到 GitHub。
- The launcher installs Python dependencies into the local `vendor/` folder when needed; `vendor/` is not uploaded to GitHub.

## 使用 / Usage

1. 双击 `start_lif_to_tif.command`
2. 如果 macOS 阻止打开，请到 `系统设置 > 隐私与安全性` 点击 `仍要打开 / Open Anyway`，之后脚本会自动清除本文件夹的下载隔离标记。
3. 点击 `打开 LIF / Open LIF`
4. 设置输出文件夹
5. 预览并调整每个通道的亮度、对比度
6. 导出当前图，或批量导出全部

1. Double-click `start_lif_to_tif.command`
2. If macOS blocks it, go to `System Settings > Privacy & Security` and click `Open Anyway`. After that first approval, the launcher clears the download quarantine flag for this folder.
3. Click `Open LIF`
4. Choose an output folder
5. Preview and adjust channel brightness/contrast
6. Export the current image or batch export all images

## 功能 / Features

- 按 LIF 内部拍摄时间排序 / Sort by acquisition time
- 每个 series 一个文件夹 / One folder per series
- 按实际通道数动态生成 `C1`、`C2`、`C3`、`C4`... / Dynamically create `C1`, `C2`, `C3`, `C4`... for all channels
- 原始单通道输出到 `Raw/C1`、`Raw/C2`...，保留原始位深且不应用显示增强 / Raw single-channel TIFFs in `Raw/C1`, `Raw/C2`... with original bit depth and no display adjustment
- 调整后的显示图输出到 `C1`、`C2`...，混合图输出到 `Merged` / Adjusted display TIFFs in `C1`, `C2`..., and merged TIFFs in `Merged`
- 每个通道独立调颜色、是否参与 Merged、黑场、白场、Gamma、亮度和对比度 / Per-channel color, include-in-merged, black point, white point, gamma, brightness, and contrast
- 可预览 `Merged` 或单独通道 / Preview merged or individual channels
- 支持 time-lapse / 小视频 LIF：界面可用 Frame 滑条、上一帧、下一帧、播放/暂停查看 `t001...` / Supports time-lapse LIF files with frame slider, previous/next frame, and play/pause preview for `t001...`
- time-lapse 导出保留逐帧 TIFF，并额外生成通道和 Merged 的预览 GIF/AVI / Time-lapse export keeps ordered frame TIFFs and also writes preview GIF/AVI movies for channels and merged views
- 视频速度默认自动：优先参考 LIF 时间戳，否则按帧数估算；也可手动设置 FPS / Movie speed is automatic by default: LIF timestamps first, frame-count estimate otherwise; manual FPS is also available
- 可选 `Max` 或 `Additive` 合成 / Choose `Max` or `Additive` merge mode
- 可设置自动调节参数，一键自动调节当前图或全部图 / Configurable auto adjustment for current image or all images
- 中英双语界面 / Chinese and English UI
- 大文件友好：预览使用缩小图，导出逐通道处理 / Large-file friendly preview and export

## 自动调节 / Auto Adjustment

默认自动调节会把每个通道的背景百分位设为黑场、信号百分位设为白场，并把目标亮度控制在不过曝的范围。自动调节全部图后，仍然可以逐张继续手动修改；最终导出会使用每张图最新保存的参数。

By default, auto adjustment estimates each channel's black point from the background percentile, white point from the signal percentile, and keeps target brightness below saturation. After auto-adjusting all images, you can still manually tune any image; final export uses the latest saved settings for each image.

## 输出和投稿注意 / Output and Publication Notes

- `Raw/` 内的 TIFF 不应用亮度、对比度、Gamma 或颜色映射，适合归档、复核和定量分析。
- `C1`、`C2`... 和 `Merged` 内的 TIFF 是显示/排版用图，会应用界面中的最新显示参数。
- time-lapse 的逐帧 TIFF 文件名包含 `t001`、`t002`...，可在 Fiji/ImageJ 中作为 image sequence 连续查看。
- GIF/AVI 是预览动态，方便分享和快速检查；正式分析和投稿原始数据请保留 Raw TIFF 与记录表。
- `提取记录_*.csv` 会记录每个文件的类型、z/t/m index、FPS、FPS 来源、显示参数和输出路径。

- TIFFs under `Raw/` do not apply brightness, contrast, gamma, or color mapping; use them for archiving, review, and quantitative analysis.
- TIFFs under `C1`, `C2`... and `Merged` are display/layout images using the latest UI adjustments.
- Time-lapse frame TIFFs are named with `t001`, `t002`... and can be opened as an image sequence in Fiji/ImageJ.
- GIF/AVI files are preview movies for sharing and quick inspection; keep Raw TIFFs and the manifest for formal analysis and publication records.
- `提取记录_*.csv` records file type, z/t/m index, FPS, FPS source, display parameters, and output path.

## 数据安全 / Data Safety

本仓库不包含测试图片、显微图原始数据或导出结果。`.gitignore` 已排除 `.lif`、`.tif`、`testlif/`、导出目录、测试输出、缓存和本地依赖。

This repository does not include test images, microscopy source data, or exported results. The `.gitignore` excludes `.lif`, `.tif`, `testlif/`, exported folders, test output, caches, and local dependencies.

## 许可 / License

MIT License.
