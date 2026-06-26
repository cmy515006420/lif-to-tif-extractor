# LIF 转 TIF 提取器 / LIF to TIFF Extractor

本工具用于把 Leica `.lif` 共聚焦文件按拍摄时间整理并导出为 TIFF、time-lapse 预览视频和可追溯记录表。目前仅支持 macOS。默认采用 publication-safe display normalization：保留 raw 数据，只对显示图应用可追踪 LUT/display range。

This tool converts Leica `.lif` confocal files into sorted TIFF folders, time-lapse preview movies, and traceable manifest records. It currently supports macOS only. The default workflow uses publication-safe display normalization: raw data are preserved, and display exports use traceable LUT/display ranges.

## 平台 / Platform

- macOS only / 仅支持 macOS
- 首次允许后，启动脚本会自动清除本软件文件夹的 macOS 下载隔离标记，减少反复授权弹窗。
- After the first macOS approval, the launcher automatically removes the quarantine flag from this app folder to avoid repeated prompts.
- 启动脚本每次会检查 Python 依赖，缺失或版本过旧时自动准备到 `vendor/`；该目录不会上传到 GitHub。
- The launcher checks Python dependencies each time and installs or updates them into the local `vendor/` folder when needed; `vendor/` is not uploaded to GitHub.

## 使用 / Usage

1. 双击 `start_lif_to_tif.command`
2. 如果 macOS 阻止打开，请到 `系统设置 > 隐私与安全性` 点击 `仍要打开 / Open Anyway`，之后脚本会自动清除本文件夹的下载隔离标记。
3. 点击 `打开 LIF / Open LIF`
4. 设置输出文件夹
5. 在默认 `Publication` 模式下选择 comparison group，预览并调整每个通道的 display range
6. 导出当前图，或批量导出全部

1. Double-click `start_lif_to_tif.command`
2. If macOS blocks it, go to `System Settings > Privacy & Security` and click `Open Anyway`. After that first approval, the launcher clears the download quarantine flag for this folder.
3. Click `Open LIF`
4. Choose an output folder
5. In the default `Publication` mode, choose a comparison group and tune each channel's display range
6. Export the current image or batch export all images

## 功能 / Features

- 按 LIF 内部拍摄时间排序 / Sort by acquisition time
- 每个 series 一个文件夹 / One folder per series
- 按实际通道数动态生成 `C1`、`C2`、`C3`、`C4`... / Dynamically create `C1`, `C2`, `C3`, `C4`... for all channels
- 原始单通道输出到 `Raw/C1`、`Raw/C2`...，保留原始位深且不应用显示增强 / Raw single-channel TIFFs in `Raw/C1`, `Raw/C2`... with original bit depth and no display adjustment
- 调整后的显示图输出到 `C1`、`C2`...，混合图输出到 `Merged` / Adjusted display TIFFs in `C1`, `C2`..., and merged TIFFs in `Merged`
- 每个通道独立调颜色、是否参与 Merged、黑场、白场、Gamma、亮度和对比度 / Per-channel color, include-in-merged, black point, white point, gamma, brightness, and contrast
- 默认 `Publication` 模式按 comparison group + channel + stack/video 统一计算线性 black/white display range / Default `Publication` mode computes a shared linear black/white display range by comparison group + channel + stack/video
- `Preview` 模式可做单张快速预览，导出日志会标记为 preview-only / `Preview` mode can auto-preview individual images; exports are marked preview-only in the log
- 可给当前图设置 comparison group，并一键把当前参数应用到同组 / Assign comparison groups and apply current settings to the whole group
- 可按通道锁定 black/white，防止自动调节覆盖手动确认的 display range / Lock per-channel black/white values so auto adjustment does not overwrite confirmed display ranges
- 可显示 clipping overlay，蓝色表示压到 0，红色表示达到最大显示值 / Optional clipping overlay: blue marks pixels clipped to 0, red marks pixels clipped to display max
- 可预览 `Merged` 或单独通道 / Preview merged or individual channels
- 支持 time-lapse / 小视频 LIF：界面可用 Frame 滑条、上一帧、下一帧、播放/暂停查看 `t001...` / Supports time-lapse LIF files with frame slider, previous/next frame, and play/pause preview for `t001...`
- time-lapse 导出保留逐帧 TIFF，并额外生成通道和 Merged 的预览 GIF/AVI / Time-lapse export keeps ordered frame TIFFs and also writes preview GIF/AVI movies for channels and merged views
- 视频速度默认自动：优先参考 LIF 时间戳，否则按帧数估算；也可手动设置 FPS / Movie speed is automatic by default: LIF timestamps first, frame-count estimate otherwise; manual FPS is also available
- 可选 `Max` 或 `Additive` 合成 / Choose `Max` or `Additive` merge mode
- 可设置 publication-safe 自动范围参数，一键自动调节当前图或全部 comparison groups / Configurable publication-safe auto range for the current image or all comparison groups
- 中英双语界面 / Chinese and English UI
- 大文件友好：预览使用缩小图，导出逐通道处理 / Large-file friendly preview and export

## Publication-Safe Auto Adjustment

默认 `Publication` 模式不会做普通照片增强，不做 CLAHE、histogram equalization、锐化、去噪、局部背景擦除、AI enhancement 或默认 gamma/curve。自动调节只计算线性 display range：

`output = clip((raw - black_point) / (white_point - black_point), 0, 1)`

- `Gamma` 默认保持 `1.0`。
- `Publication` 模式会把额外 brightness、contrast、gamma 固定为 `1.0`；想做单张视觉预览时请切到 `Preview` 模式。
- 同一 comparison group 内，同一 channel 使用同一套 black/white。
- time-lapse / z-stack / 连续帧视频按整个 stack/video 为同一 channel 统一计算 display range，避免逐帧 auto contrast 造成闪烁或掩盖真实强度变化。
- hot pixel 和极亮离群点只在计算 display range 时作为 outlier 处理；raw TIFF 不会被删除或修改。
- 低信号/空白图不会被自动拉亮成假信号，日志会记录 warning。
- 自动调节后仍可手动微调；最终导出会使用每张图/每个视频的最新保存参数。

The default `Publication` mode does not apply ordinary photo enhancement: no CLAHE, histogram equalization, sharpening, denoising, local background removal, AI enhancement, or default gamma/curve. Auto adjustment only computes a linear display range:

`output = clip((raw - black_point) / (white_point - black_point), 0, 1)`

- `Gamma` stays at `1.0` by default.
- `Publication` mode keeps extra brightness, contrast, and gamma fixed at `1.0`; switch to `Preview` mode for individual visual previews.
- The same channel within the same comparison group uses the same black/white range.
- Time-lapse / z-stack / continuous videos use one display range per channel across the whole stack/video, avoiding frame-by-frame auto contrast flicker.
- Hot pixels and extreme outliers are handled only when estimating the display range; raw TIFFs are not removed or modified.
- Low-signal/blank images are not automatically boosted into false signal; warnings are recorded in the log.
- After auto adjustment, you can still tune images manually; final export uses the latest saved settings for each image/video.

## 输出和投稿注意 / Output and Publication Notes

- `Raw/` 内的 TIFF 不应用亮度、对比度、Gamma 或颜色映射，适合归档、复核和定量分析。
- `C1`、`C2`... 和 `Merged` 内的 TIFF 是显示/排版用图，会应用界面中的最新显示参数。
- 定量分析必须使用 `Raw/` 数据；display-adjusted TIFF/PNG/GIF/AVI 只用于展示和排版。
- time-lapse 的逐帧 TIFF 文件名包含 `t001`、`t002`...，可在 Fiji/ImageJ 中作为 image sequence 连续查看。
- GIF/AVI 是预览动态，方便分享和快速检查；正式分析和投稿原始数据请保留 Raw TIFF 与记录表。
- `提取记录_*.csv` 和 `提取记录_*_normalization.json` 会记录原始文件、comparison group、channel、bit depth、raw min/max、black/white、raw black/white、gamma、是否线性 LUT、clipping 百分比、normalization mode、算法版本、软件版本和输出路径。

- TIFFs under `Raw/` do not apply brightness, contrast, gamma, or color mapping; use them for archiving, review, and quantitative analysis.
- TIFFs under `C1`, `C2`... and `Merged` are display/layout images using the latest UI adjustments.
- Quantitative analysis must use `Raw/` data; display-adjusted TIFF/PNG/GIF/AVI files are for presentation/layout only.
- Time-lapse frame TIFFs are named with `t001`, `t002`... and can be opened as an image sequence in Fiji/ImageJ.
- GIF/AVI files are preview movies for sharing and quick inspection; keep Raw TIFFs and the manifest for formal analysis and publication records.
- `提取记录_*.csv` and `提取记录_*_normalization.json` record source file, comparison group, channel, bit depth, raw min/max, black/white, raw black/white, gamma, whether a linear LUT was used, clipping percentages, normalization mode, algorithm version, software version, and output path.

## 数据安全 / Data Safety

本仓库不包含测试图片、显微图原始数据或导出结果。`.gitignore` 已排除 `.lif`、`.tif`、`.avi`、`.gif`、`.mp4`、`.mov`、记录表、`testlif/`、导出目录、测试输出、缓存和本地依赖。

This repository does not include test images, microscopy source data, or exported results. The `.gitignore` excludes `.lif`, `.tif`, `.avi`, `.gif`, `.mp4`, `.mov`, manifest tables, `testlif/`, exported folders, test output, caches, and local dependencies.

## 许可 / License

MIT License.
