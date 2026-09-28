from __future__ import annotations

import re
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageGrab, ImageTk

try:
    import mss
except ImportError:
    mss = None

try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    from rapidocr_onnxruntime import RapidOCR
except ImportError:
    RapidOCR = None


# 无畏契约主播常用房间码格式：3 位大写字母 + 3 位数字，例如 SDF345。
CODE_RE = re.compile(r"(?<![A-Z0-9])[A-Z]{3}[0-9]{3}(?![A-Z0-9])")


@dataclass
class CaptureRegion:
    left: int
    top: int
    width: int
    height: int


class RegionOverlay(tk.Toplevel):
    def __init__(self, master: tk.Tk, on_selected):
        super().__init__(master)
        self.on_selected = on_selected
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.28)
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        self.canvas = tk.Canvas(self, bg="black", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.start = None
        self.rect = None
        self.bind("<Escape>", lambda _e: self.cancel())
        self.canvas.bind("<ButtonPress-1>", self.begin)
        self.canvas.bind("<B1-Motion>", self.move)
        self.canvas.bind("<ButtonRelease-1>", self.end)
        self.focus_force()

    def begin(self, event):
        self.start = (event.x, event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#00ff88", width=3)

    def move(self, event):
        if self.start and self.rect:
            self.canvas.coords(self.rect, self.start[0], self.start[1], event.x, event.y)

    def end(self, event):
        if not self.start:
            return
        x1, y1 = self.start
        x2, y2 = event.x, event.y
        left, top = min(x1, x2), min(y1, y2)
        width, height = abs(x2 - x1), abs(y2 - y1)
        if width >= 8 and height >= 8:
            self.destroy()
            self.on_selected(CaptureRegion(left, top, width, height))
        else:
            self.cancel()

    def cancel(self):
        self.destroy()
        self.master.deiconify()
        self.master.lift()


class QiangMaApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("无畏契约抢码器")
        self.root.geometry("560x400")
        self.root.minsize(520, 360)
        self.root.attributes("-topmost", True)
        self.region: CaptureRegion | None = None
        self.running = False
        self.last_code = ""
        self.ocr = None
        self.ocr_lock = threading.Lock()
        self.status = tk.StringVar(value="请先选择直播画面中的房间码区域")
        self.interval = tk.DoubleVar(value=1.0)
        self.auto = tk.BooleanVar(value=False)
        self.recognizing = False
        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 14, "pady": 8}
        ttk.Label(self.root, text="无畏契约房间码识别", font=("Microsoft YaHei UI", 17, "bold")).pack(anchor="w", **pad)
        ttk.Label(self.root, text="从抖音/浏览器/桌面直播画面框选房间码，识别结果可直接复制。", foreground="#555").pack(anchor="w", padx=14)

        controls = ttk.Frame(self.root)
        controls.pack(fill="x", padx=14, pady=(18, 8))
        ttk.Button(controls, text="① 选择识别区域", command=self.select_region).pack(side="left")
        ttk.Button(controls, text="② 立即识别", command=self.recognize_once).pack(side="left", padx=8)
        ttk.Checkbutton(controls, text="自动识别", variable=self.auto, command=self.toggle_auto).pack(side="left")

        box = ttk.LabelFrame(self.root, text="识别到的房间码")
        box.pack(fill="x", padx=14, pady=8)
        self.code_entry = ttk.Entry(box, font=("Consolas", 28, "bold"), justify="center")
        self.code_entry.pack(fill="x", padx=12, pady=12)
        self.code_entry.bind("<Return>", lambda _e: self.copy_code())
        ttk.Button(box, text="复制房间码", command=self.copy_code).pack(pady=(0, 12))

        opts = ttk.Frame(self.root)
        opts.pack(fill="x", padx=14, pady=4)
        ttk.Label(opts, text="格式：3 位大写字母 + 3 位数字").pack(side="left")
        ttk.Label(opts, text="自动识别间隔（秒）").pack(side="left", padx=(18, 0))
        ttk.Spinbox(opts, from_=0.5, to=10, increment=0.5, textvariable=self.interval, width=6).pack(side="left", padx=8)
        ttk.Label(self.root, textvariable=self.status, foreground="#1769aa", wraplength=520).pack(anchor="w", padx=14, pady=(12, 4))
        ttk.Label(self.root, text="提示：框选时按 Esc 取消；直播画面越清晰、区域越紧凑，识别越快。", foreground="#777").pack(anchor="w", padx=14)

    def select_region(self):
        self.root.withdraw()
        self.root.after(250, lambda: RegionOverlay(self.root, self.region_selected))

    def region_selected(self, region: CaptureRegion):
        self.region = region
        self.root.deiconify()
        self.root.lift()
        self.status.set(f"已选择区域：{region.width}×{region.height}，可以识别")
        self.recognize_once()

    def capture(self):
        if not self.region:
            raise RuntimeError("请先选择识别区域")
        r = self.region
        if mss:
            with mss.mss() as sct:
                shot = sct.grab({"left": r.left, "top": r.top, "width": r.width, "height": r.height})
                return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
        image = ImageGrab.grab(bbox=(r.left, r.top, r.left + r.width, r.top + r.height))
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    def get_ocr(self):
        if RapidOCR is None:
            raise RuntimeError("未安装 RapidOCR，请先运行 install.ps1")
        with self.ocr_lock:
            if self.ocr is None:
                self.status.set("首次运行正在加载 OCR 模型（约需几秒）…")
                self.ocr = RapidOCR()
        return self.ocr

    def preprocess(self, image):
        # 放大和锐化，适合直播间叠加的小号白字/彩字
        scale = 3 if max(image.shape[:2]) < 900 else 2
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (0, 0), 1.2)
        sharp = cv2.addWeighted(gray, 1.7, blur, -0.7, 0)
        return cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)

    def extract_code(self, texts):
        candidates = []
        cleaned_items = []
        for text, score in texts:
            clean = re.sub(r"[^A-Za-z0-9]", "", text).upper()
            cleaned_items.append((clean, float(score)))
            for match in CODE_RE.finditer(clean):
                value = match.group(0)
                if CODE_RE.fullmatch(value):
                    candidates.append((float(score), value))
        # OCR 可能把字母段和数字段识别成两个文本框，拼接后再检查一次。
        if len(cleaned_items) > 1:
            joined = "".join(item[0] for item in cleaned_items)
            avg_score = sum(item[1] for item in cleaned_items) / len(cleaned_items)
            for match in CODE_RE.finditer(joined):
                candidates.append((avg_score, match.group(0)))
        if not candidates:
            return ""
        candidates.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
        return candidates[0][1]

    def recognize_once(self):
        if not self.region:
            self.status.set("请先选择识别区域")
            return
        if self.recognizing:
            return
        self.recognizing = True
        threading.Thread(target=self._recognize_worker, daemon=True).start()

    def _recognize_worker(self):
        try:
            image = self.preprocess(self.capture())
            ocr = self.get_ocr()
            result, _ = ocr(image)
            texts = []
            if result:
                for item in result:
                    if len(item) >= 3:
                        texts.append((str(item[1]), float(item[2])))
            code = self.extract_code(texts)
            self.root.after(0, lambda: self.show_result(code, texts))
        except Exception as exc:
            message = str(exc)
            self.root.after(0, lambda: self.status.set(f"识别失败：{message}"))
        finally:
            self.root.after(0, lambda: setattr(self, "recognizing", False))

    def show_result(self, code, texts):
        if code:
            self.last_code = code
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, code)
            self.status.set(f"识别成功：{code}（可按按钮复制）")
        else:
            raw = "、".join(t for t, _ in texts[:4]) or "未检测到文字"
            self.status.set(f"没有找到 4-8 位房间码。检测到：{raw}")

    def copy_code(self):
        code = self.code_entry.get().strip()
        if not code:
            self.status.set("当前没有可复制的房间码")
            return
        if pyperclip:
            pyperclip.copy(code)
        else:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
        self.status.set(f"已复制：{code}")

    def toggle_auto(self):
        self.running = self.auto.get()
        if self.running:
            self.status.set("自动识别已开启")
            self.auto_loop()
        else:
            self.status.set("自动识别已暂停")

    def auto_loop(self):
        if not self.running:
            return
        self.recognize_once()
        try:
            delay = max(0.5, float(self.interval.get()))
        except (ValueError, tk.TclError):
            delay = 1.0
        self.root.after(int(delay * 1000), self.auto_loop)


def main():
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass
    QiangMaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
