LIF 转 TIF 提取器 / LIF to TIFF Extractor

平台 / Platform
- 仅支持 macOS / macOS only
- 第一次启动会自动安装 Python 依赖到本机 vendor 文件夹。
- On first launch, Python dependencies are installed into the local vendor folder.

启动 / Launch
1. 双击 start_lif_to_tif.command
2. 点击“打开 LIF / Open LIF”选择 .lif 文件
3. 点击“选择输出文件夹 / Choose Output Folder”设置导出位置

主要功能 / Main Features
- 选择任意 Leica .lif 文件 / Open any Leica .lif file
- 按 LIF 内部拍摄时间排序 / Sort series by acquisition time stored in the LIF
- 每个 series 单独建文件夹 / Put each series in its own folder
- 按实际通道数动态生成 C1、C2、C3、C4... / Dynamically create C1, C2, C3, C4... for however many channels are in the LIF
- 混合通道输出到 Merged 文件夹 / Export merged image into the Merged folder
- 每个通道可独立调颜色、是否参与 Merged、黑场、白场、Gamma、亮度和对比度 / Per-channel color, include-in-merged, black point, white point, gamma, brightness, and contrast
- 可预览 Merged 或单独 C1/C2/C3 / Preview Merged or individual C1/C2/C3 channels
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
提取出的tif/日期/顺序_时间_图名/C1
提取出的tif/日期/顺序_时间_图名/C2
提取出的tif/日期/顺序_时间_图名/C3
提取出的tif/日期/顺序_时间_图名/Merged

安全说明 / Safety Notes
- 本仓库不包含测试图片、显微图原始数据或导出结果。
- This repository does not include test images, microscopy source data, or exported results.
- .gitignore 已排除 .lif、.tif、testlif、提取出的tif、测试输出和缓存。
- The .gitignore excludes .lif, .tif, testlif, exported TIFF folders, test output, and caches.
- 本项目文件夹中不要提交显微图原始数据或导出图片。
- Do not commit microscopy source data or exported images.
