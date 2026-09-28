# 无畏契约抢码器

桌面小工具：框选抖音等直播画面中的房间码，OCR 识别后直接复制。当前按常见格式 `3 位大写字母 + 3 位数字` 过滤，例如 `SDF345`。

## 下载 Windows 版

打开仓库右侧的 **Releases**，下载最新版 `QiangMa_Portable.zip`，解压后运行 `QiangMa.exe`。便携版无需安装 Python。首次启动或识别时可能需要等待 OCR 模型加载。

## 安装与运行

源码运行需要 Windows 和 Python 3。在克隆后的项目目录中打开 PowerShell，执行：

```powershell
.\install.ps1
py -3 main.py
```

首次识别会加载随 exe 打包的 RapidOCR 模型，不需要上传直播画面。使用时点击“选择识别区域”，拖出房间码所在区域；可以立即识别，也可以开启自动识别。

## 生成 exe

```powershell
.\install.ps1 -BuildExe
```

输出：`dist\QiangMa.exe`。打包后的程序首次启动也会在本机缓存 OCR 模型。生成便携版压缩包时，将 exe 复制到项目上级目录并运行 `py -3 make_release.py`。

## 注意

程序只读取用户主动框选的屏幕区域，不自动访问账号、弹幕或直播平台接口。识别结果应人工确认后再粘贴。
