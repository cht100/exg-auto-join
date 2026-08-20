from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

from .browser import select_page
from .config import (
    DEFAULT_MODES,
    DEFAULT_PROFILE_DIR,
    DEFAULT_URL,
    SERVER_LIST_API,
    resolve_modes,
)
from .log import configure_logging, log
from .watcher import watch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="EXG 僵尸逃跑服务器自动加入：支持关键词自动加入，或监控指定服务器等空位。"
    )
    parser.add_argument("--url", default=DEFAULT_URL, help=f"服务器列表地址，默认：{DEFAULT_URL}")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--target",
        action="append",
        default=None,
        help="自动加入模式：要匹配的关键词，可多次传入。默认：obj3",
    )
    group.add_argument(
        "--server",
        default=None,
        help="监控指定服务器：名称/ID 关键词，出现空位立即加入",
    )

    parser.add_argument(
        "--mode",
        action="append",
        default=None,
        help=(
            "只检测的服务器模式，可多次传入。支持前缀（cs2ze）或中文（僵尸逃跑），"
            f"默认：{', '.join(DEFAULT_MODES)}"
        ),
    )
    parser.add_argument("--join-text", default="加入", help="加入按钮文字，默认：加入")
    parser.add_argument("--interval", type=float, default=1.0, help="轮询间隔秒数，默认：1.0")
    parser.add_argument(
        "--post-click-wait",
        type=float,
        default=60.0,
        help="点击后保持浏览器等待秒数，默认：60",
    )
    parser.add_argument("--reload-every", type=float, default=0.0, help="每 N 秒强制刷新页面，0 禁用")
    parser.add_argument("--case-sensitive", action="store_true", help="关键词/服务器名区分大小写")
    parser.add_argument(
        "--allow-full",
        action="store_true",
        help="自动加入模式也点击已满服务器（默认只点有空位的）",
    )
    parser.add_argument("--dry-run", action="store_true", help="只报告不点击")
    parser.add_argument("--scan-scroll", action="store_true", help="未命中时缓慢滚动扫描页面")
    parser.add_argument("--headless", action="store_true", help="无头浏览器运行")
    parser.add_argument(
        "--profile-dir",
        default=str(DEFAULT_PROFILE_DIR),
        help=f"浏览器 profile 目录，默认：{DEFAULT_PROFILE_DIR}",
    )
    parser.add_argument(
        "--cdp-url",
        default=None,
        help="连接已开远程调试的浏览器，例如 http://127.0.0.1:9222",
    )
    parser.add_argument(
        "--channel",
        default="auto",
        help=(
            "浏览器 channel：auto 自动找本机 Chrome/Edge，chrome 指定 Chrome，"
            "msedge 指定 Edge，空字符串使用内置 Chromium。默认：auto"
        ),
    )
    parser.add_argument("--api-url", default=SERVER_LIST_API, help="服务器列表 JSON 接口")
    parser.add_argument("--api-timeout", type=float, default=10.0, help="接口请求超时秒数")
    return parser


def _split_keywords(values: list[str]) -> list[str]:
    parts: list[str] = []
    for value in values:
        for part in value.replace("，", ",").replace("；", ",").replace(";", ",").split(","):
            part = part.strip()
            if part:
                parts.append(part)
    return parts


def _finalize_args(args: argparse.Namespace) -> argparse.Namespace:
    args.modes = resolve_modes(args.mode)
    if args.target:
        cleaned: list[str] = []
        dropped: list[str] = []
        for target in _split_keywords(args.target):
            if len(target) >= 2:
                cleaned.append(target)
            else:
                dropped.append(target)
        if dropped:
            log(f"忽略过短关键词（至少2个字符）：{', '.join(dropped)}")
        args.target = cleaned
    if not args.server and not args.target:
        args.target = ["obj3"]

    if args.interval < 0.2:
        log("轮询间隔过小，已调整为 0.2 秒")
        args.interval = 0.2
    return args


async def _run(args: argparse.Namespace) -> int:
    try:
        from playwright.async_api import Error as PlaywrightError
        from playwright.async_api import async_playwright
    except ModuleNotFoundError:
        log("缺少依赖 playwright")
        log("安装：python -m pip install -r requirements.txt")
        log("浏览器：python -m playwright install chromium")
        return 1

    args = _finalize_args(args)

    async with async_playwright() as p:
        if args.cdp_url:
            log(f"连接已有浏览器：{args.cdp_url}")
            browser = await p.chromium.connect_over_cdp(args.cdp_url)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await select_page(context, args.url)
            await watch(page, args)
            return 0

        profile_dir = Path(args.profile_dir).resolve()
        profile_dir.mkdir(parents=True, exist_ok=True)

        launch_options: dict[str, Any] = {
            "user_data_dir": str(profile_dir),
            "headless": args.headless,
            "args": ["--no-first-run", "--disable-blink-features=AutomationControlled"],
        }
        channel_arg = (args.channel or "").strip().lower()

        if channel_arg == "":
            # 明确要求内置 Chromium
            log("使用 Playwright 内置 Chromium")
            context = await p.chromium.launch_persistent_context(**launch_options)
        elif channel_arg != "auto":
            # 用户明确指定某个 channel
            opts = {**launch_options, "channel": channel_arg}
            try:
                context = await p.chromium.launch_persistent_context(**opts)
            except PlaywrightError as exc:
                log(f"无法启动 channel '{channel_arg}'，回退到内置 Chromium：{exc}")
                context = await p.chromium.launch_persistent_context(**launch_options)
        else:
            # 自动模式：优先本机 Chrome，其次 Edge，最后内置 Chromium
            launched = False
            for channel in ("chrome", "msedge"):
                opts = {**launch_options, "channel": channel}
                try:
                    log(f"尝试使用本机 {channel} 浏览器")
                    context = await p.chromium.launch_persistent_context(**opts)
                    launched = True
                    break
                except PlaywrightError as exc:
                    log(f"未找到 {channel}，尝试下一个：{exc}")
            if not launched:
                log("未找到 Chrome/Edge，使用 Playwright 内置 Chromium")
                context = await p.chromium.launch_persistent_context(**launch_options)

        try:
            page = await select_page(context, args.url)
            await watch(page, args)
        finally:
            await context.close()

    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        log("已停止")
        return 130


if __name__ == "__main__":
    sys.exit(main())
