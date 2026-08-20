from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tkinter import Tk, StringVar, BooleanVar, messagebox
from tkinter import ttk

from .config import ICON_PATH, PROJECT_ROOT


def pythonw_path() -> str:
    current = Path(sys.executable)
    sibling = current.with_name("pythonw.exe")
    return str(sibling if sibling.exists() else current)


def split_targets(raw: str) -> list[str]:
    parts = (
        raw.replace("，", ",")
        .replace("；", ",")
        .replace(";", ",")
        .replace("\n", ",")
        .split(",")
    )
    return [part.strip() for part in parts if part.strip()]


def start_watcher(args: list[str]) -> int:
    creationflags = 0
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags |= subprocess.CREATE_NO_WINDOW
    if hasattr(subprocess, "DETACHED_PROCESS"):
        creationflags |= subprocess.DETACHED_PROCESS

    # 日志由 watcher 进程自己写（带滚动），这里不再重定向 stdout
    process = subprocess.Popen(
        args,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=True,
    )
    return process.pid


class LauncherApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("EXG 僵尸逃跑自动加入")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        try:
            self.root.iconbitmap(str(ICON_PATH))
        except Exception:
            pass

        self.mode = StringVar(value="auto")
        self.targets = StringVar(value="obj,一线生机")
        self.server = StringVar(value="")
        self.allow_full = BooleanVar(value=False)
        self.scan_scroll = BooleanVar(value=True)

        self._build()

    def _build(self) -> None:
        pad = {"padx": 12, "pady": 6}
        frame = ttk.Frame(self.root, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="监控模式", font=("", 11, "bold")).grid(row=0, column=0, sticky="w", **pad)

        self.auto_radio = ttk.Radiobutton(
            frame,
            text="自动加入：在所有僵尸逃跑服务器中匹配关键词",
            variable=self.mode,
            value="auto",
            command=self._sync_mode,
        )
        self.auto_radio.grid(row=1, column=0, sticky="w", padx=12)

        self.targets_entry = ttk.Entry(frame, textvariable=self.targets, width=46)
        self.targets_entry.grid(row=2, column=0, sticky="w", padx=(28, 12))
        ttk.Label(frame, text="关键词（多个用英文逗号 , 分隔，至少2个字符）").grid(row=3, column=0, sticky="w", padx=(28, 12))

        self.server_radio = ttk.Radiobutton(
            frame,
            text="监控指定僵尸逃跑服务器：出现空位立即点击加入",
            variable=self.mode,
            value="server",
            command=self._sync_mode,
        )
        self.server_radio.grid(row=4, column=0, sticky="w", padx=12, pady=(12, 0))

        self.server_entry = ttk.Entry(frame, textvariable=self.server, width=46)
        self.server_entry.grid(row=5, column=0, sticky="w", padx=(28, 12))
        ttk.Label(frame, text="服务器ID/地图名（如：#7 或 孤注一掷）").grid(
            row=6, column=0, sticky="w", padx=(28, 12)
        )

        ttk.Separator(frame, orient="horizontal").grid(row=7, column=0, sticky="ew", pady=10)

        self.allow_full_check = ttk.Checkbutton(
            frame,
            text="自动加入时也点击已满服务器（不推荐）",
            variable=self.allow_full,
        )
        self.allow_full_check.grid(row=8, column=0, sticky="w", padx=12)

        ttk.Checkbutton(
            frame,
            text="页面滚动扫描（列表懒加载时更稳）",
            variable=self.scan_scroll,
        ).grid(row=9, column=0, sticky="w", padx=12)

        buttons = ttk.Frame(frame)
        buttons.grid(row=10, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="开始监控", command=self._on_start).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="退出", command=self.root.destroy).pack(side="left", padx=8)

        self._sync_mode()

    def _sync_mode(self) -> None:
        is_auto = self.mode.get() == "auto"
        state = "normal" if is_auto else "disabled"
        self.targets_entry.configure(state=state)
        self.allow_full_check.configure(state=state)
        self.server_entry.configure(state="normal" if not is_auto else "disabled")

    def _build_args(self) -> list[str] | None:
        if getattr(sys, "frozen", False):
            # 打包成 exe 后，用同一个 exe 的“命令行模式”启动后台监控
            args = [sys.executable, "--post-click-wait", "60"]
        else:
            cli = PROJECT_ROOT / "auto_join.py"
            if not cli.exists():
                messagebox.showerror("自动加入", f"找不到 CLI 脚本：\n{cli}", parent=self.root)
                return None
            args = [pythonw_path(), str(cli), "--post-click-wait", "60"]

        if self.mode.get() == "auto":
            targets = split_targets(self.targets.get())
            if not targets:
                messagebox.showwarning("自动加入", "请输入至少一个关键词。", parent=self.root)
                return None
            for target in targets:
                args.extend(["--target", target])
            if self.allow_full.get():
                args.append("--allow-full")
        else:
            server = self.server.get().strip()
            if not server:
                messagebox.showwarning("自动加入", "请输入要监控的服务器名称或 ID。", parent=self.root)
                return None
            args.extend(["--server", server])

        if self.scan_scroll.get():
            args.append("--scan-scroll")

        return args

    def _on_start(self) -> None:
        args = self._build_args()
        if args is None:
            return

        try:
            start_watcher(args)
        except Exception as exc:
            messagebox.showerror("自动加入", f"启动失败：\n{exc}", parent=self.root)
            return

        # 启动成功后自动关闭窗口，监控在后台运行
        self.root.destroy()

def main() -> None:
    root = Tk()
    LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
