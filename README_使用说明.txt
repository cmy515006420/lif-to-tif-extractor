LIF 转 TIF 提取器 / LIF to TIFF Extractor

平台 / Platform
- 仅支持 macOS / macOS only
- 首次允许后，启动脚本会自动清除本软件文件夹的 macOS 下载隔离标记，减少反复授权弹窗。
- After the first macOS approval, the launcher automatically removes the quarantine flag from this app folder to avoid repeated prompts.
- 启动脚本每次会检查 Python 依赖，缺失或版本过旧时自动准备到本机 vendor 文件夹。
- The launcher checks Python dependencies each time and installs or updates them into the local vendor folder when needed.

启动 / Launch
1. 双击 start_lif_to_tif.command
2. 如果 macOS 阻止打开，请到“系统设置 > 隐私与安全性”点击“仍要打开 / Open Anyway”，之后脚本会自动清除本文件夹的下载隔离标记。
3. 点击“打开 LIF / Open LIF”选择 .lif 文件
4. 点击“选择输出文件夹 / Choose Output Folder”设置导出位置

First Launch on macOS
- If macOS blocks start_lif_to_tif.command as an unidentified developer, open System Settings > Privacy & Security, click Open Anyway, then confirm Open.
- After that first approval, the launcher removes the quarantine flag from this app folder so internal files should not need repeated approvals.

主要功能 / Main Features
- 选择任意 Leica .lif 文件 / Open any Leica .lif file
- 按 LIF 内部拍摄时间排序 / Sort series by acquisition time stored in the LIF
- 每个 series 单独建文件夹 / Put each series in its own folder
- 按实际通道数动态生成 C1、C2、C3、C4... / Dynamically create C1, C2, C3, C4... for however many channels are in the LIF
- 原始单通道输出到 Raw/C1、Raw/C2...，保留原始位深且不应用显示增强 / Raw single-channel TIFFs are exported to Raw/C1, Raw/C2... with original bit depth and no display adjustment
- 调整后的显示图输出到 C1、C2...，混合通道输出到 Merged 文件夹 / Adjusted display TIFFs are exported to C1, C2... and merged images to Merged
- 每个通道可独立调颜色、是否参与 Merged、黑场、白场、Gamma、亮度和对比度 / Per-channel color, include-in-merged, black point, white point, gamma, brightness, and contrast
- 可预览 Merged 或单独 C1/C2/C3 / Preview Merged or individual C1/C2/C3 channels
- 支持 time-lapse / 小视频 LIF：界面可用 Frame 滑条、上一帧、下一帧、播放/暂停查看 t001... / Supports time-lapse LIF files with frame slider, previous/next frame, and play/pause preview for t001...
- time-lapse 导出保留逐帧 TIFF，并额外生成通道和 Merged 的预览 GIF/AVI / Time-lapse export keeps ordered frame TIFFs and also writes preview GIF/AVI movies for channels and merged views
- 视频速度默认自动：优先参考 LIF 时间戳，否则按帧数估算；也可手动设置 FPS / Movie speed is automatic by default: LIF timestamps first, frame-count estimate otherwise; manual FPS is also available
- 可选 Merged 合成方式 Max 或 Additive / Choose Max or Additive merge mode
- 可设置自动调节参数并一键自动调节当前图或全部图 / Configurable auto adjustment for the current image or all images
- 支持中英双语界面 / Chinese and English UI
- 大文件预览只缓存缩小图，导出逐个 series、逐个通道处理 / Preview uses downsampled images; export processes series and channels one by one

自动调节 / Auto Adjustment
- 背景百分位 / Background %: 默认 0.5，作为黑场估计
- 信号百分位 / Signal %: 默认 99.8，作为白场估计
- 目标亮度 / Target Max: 默认 230，避免导出过曝
- 自动调节全部图后，仍然可以逐张继续手动修改；最终导出会使用每张图的最新参数。
- After auto-adjusting all images, you can still manually tune any image; final export uses the latest per-image settings.

导出方式 / Export Modes
- 导出当前图 / Export Current: only export the selected series
- 一次预览导出全部 / Preview Once, Export All: apply the current full channel settings to all series
- 按各图参数导出全部 / Export All With Per-Image Settings: preview and tune each series, then export all with each series' latest saved settings

输出结构 / Output Structure
提取出的tif/日期/顺序_时间_图名/Raw/C1
提取出的tif/日期/顺序_时间_图名/Raw/C2
提取出的tif/日期/顺序_时间_图名/C1
提取出的tif/日期/顺序_时间_图名/C2
提取出的tif/日期/顺序_时间_图名/C3
提取出的tif/日期/顺序_时间_图名/Merged

投稿和复核注意 / Publication and Review Notes
- Raw 文件夹中的 TIFF 不应用亮度、对比度、Gamma 或颜色映射，适合归档、复核和定量分析。
- C1、C2... 和 Merged 文件夹中的 TIFF 是显示/排版图，会应用界面中的最新显示参数。
- time-lapse 的逐帧 TIFF 文件名包含 t001、t002...，可在 Fiji/ImageJ 中作为 image sequence 连续查看。
- GIF/AVI 是预览动态，方便分享和快速检查；正式分析和投稿原始数据请保留 Raw TIFF 与记录表。
- 提取记录_*.csv 会记录每个文件的类型、z/t/m index、FPS、FPS 来源、显示参数和输出路径。
- TIFFs under Raw do not apply brightness, contrast, gamma, or color mapping; use them for archiving, review, and quantitative analysis.
- TIFFs under C1, C2... and Merged are display/layout images using the latest UI adjustments.
- Time-lapse frame TIFFs are named with t001, t002... and can be opened as an image sequence in Fiji/ImageJ.
- GIF/AVI files are preview movies for sharing and quick inspection; keep Raw TIFFs and the manifest for formal analysis and publication records.
- 提取记录_*.csv records file type, z/t/m index, FPS, FPS source, display parameters, and output path.

安全说明 / Safety Notes
- 本仓库不包含测试图片、显微图原始数据或导出结果。
- This repository does not include test images, microscopy source data, or exported results.
- .gitignore 已排除 .lif、.tif、.avi、.gif、.mp4、.mov、记录表、testlif、提取出的tif、测试输出和缓存。
- The .gitignore excludes .lif, .tif, .avi, .gif, .mp4, .mov, manifest tables, testlif, exported TIFF folders, test output, and caches.
- 本项目文件夹中不要提交显微图原始数据或导出图片。
- Do not commit microscopy source data or exported images.
