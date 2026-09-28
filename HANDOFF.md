# 交接

当前已完成第一版可运行闭环，项目位于 `C:\Users\49929\Desktop\workspace\codex\qiangma`。

运行 `install.ps1` 安装依赖，运行 `py -3 main.py` 启动；运行 `install.ps1 -BuildExe` 生成 `dist\QiangMa.exe`。

下一步应在真实直播间验证识别率，并按主播房间码的字体、颜色和布局继续调整预处理或候选规则。

当前过滤规则是 3 位大写字母 + 3 位数字；如规则变化，修改 `main.py` 顶部的 `CODE_RE` 并重新打包。

GitHub 仓库：`https://github.com/kob-ux/无畏契约抢码器`。源码位于仓库根目录，便携版 `QiangMa_Portable.zip` 作为 Release 附件发布；`build/`、`dist/` 和本地 exe 不进入 Git 历史。
