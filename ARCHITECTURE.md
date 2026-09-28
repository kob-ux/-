# 架构

`main.py` 是单文件 Tkinter 桌面应用：

- `RegionOverlay`：全屏透明框选层，返回屏幕坐标。
- `capture`：优先使用 mss 截取区域，Pillow 作为回退。
- `preprocess`：放大、灰度、锐化，提高小字体识别率。
- `RapidOCR`：本地 OCR，不把直播画面上传到服务端。
- `extract_code`：清洗 OCR 字符，只接受 `AAA999`（3 位大写字母 + 3 位数字）候选码，降低直播画面杂字造成的误识别。
- Tkinter 主线程：展示结果、复制剪贴板、自动识别定时器。

自动识别只会重复读取当前已选区域；区域改变时重新框选即可。
