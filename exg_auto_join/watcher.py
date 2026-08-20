from __future__ import annotations

import asyncio
import time
from typing import Any

from . import api, matching
from .browser import (
    click_match,
    ensure_page_ready,
    find_join_button,
    scan_scroll_once,
    wait_for_server_rows,
)
from .config import mode_title
from .log import log
from .models import Server


async def _fetch_servers(args: Any) -> list[Server]:
    return await asyncio.to_thread(api.fetch_servers, args.api_url, args.api_timeout)


def _allowed_sections(args: Any) -> list[str]:
    return [mode_title(mode) for mode in args.modes]


def _should_log(args: Any, key: str, interval: float = 10.0) -> bool:
    now = time.monotonic()
    if now - getattr(args, key, 0.0) >= interval:
        setattr(args, key, now)
        return True
    return False


async def _handle_auto_join(page: Any, args: Any, servers: list[Server]) -> bool:
    targets = [target for target in (args.target or ["obj3"]) if target.strip()]

    # 关键词按优先级处理：第一个有匹配的关键词生效，后面的关键词只在前面的完全没有匹配时才考虑
    for target in targets:
        matched = [
            server
            for server in servers
            if server.mode in args.modes
            and matching.server_matches(server, [target], args.case_sensitive)
        ]
        if not matched:
            continue

        candidates = matched if args.allow_full else [server for server in matched if not server.is_full]
        if not candidates:
            if _should_log(args, "_last_full_log"):
                full = ", ".join(f"{server.name}({server.players_text})" for server in matched[:3])
                log(f"关键词 [{target}] 匹配到但暂满：{full}；等待空位")
            return False

        if args.dry_run:
            if _should_log(args, "_last_dry_log", 3.0):
                server = candidates[0]
                log(f"命中关键词 [{target}]：{server.name}（{server.players_text}）")
            return False

        for server in candidates:
            result = await find_join_button(
                page,
                server.name,
                args.join_text,
                _allowed_sections(args),
                args.case_sensitive,
            )
            if not result.get("matched"):
                continue

            log(f"命中关键词 [{target}]：{server.name}（{server.players_text}）")
            await click_match(page, result)
            log(f"已点击加入，等待 {args.post_click_wait:g}s 交给浏览器/游戏处理")
            await asyncio.sleep(max(args.post_click_wait, 0))
            return True

        if _should_log(args, "_last_missing_row_log", 5.0):
            names = "、".join(server.name for server in candidates[:3])
            log(f"关键词 [{target}] 已匹配但 DOM 未找到对应行：{names}")
        return False

    return False


async def _handle_monitor(page: Any, args: Any, servers: list[Server]) -> bool:
    candidates = [server for server in servers if server.mode in args.modes]
    server = matching.find_server(candidates, args.server, args.case_sensitive)

    if server is None:
        if _should_log(args, "_last_not_found_log"):
            log(f"未找到服务器：{args.server}（当前仅监控 {', '.join(args.modes)}）")
        return False

    if server.is_full:
        if _should_log(args, "_last_full_warn"):
            log(f"{server.name} 已满（{server.players_text}），等待空位…")
        return False

    if args.dry_run:
        if _should_log(args, "_last_dry_log", 3.0):
            log(f"{server.name} 出现空位（{server.players_text}），立即加入")
        return False

    log(f"{server.name} 出现空位（{server.players_text}），立即加入")

    result = await find_join_button(
        page,
        server.name,
        args.join_text,
        _allowed_sections(args),
        args.case_sensitive,
    )
    if not result.get("matched"):
        if _should_log(args, "_last_missing_row_log", 5.0):
            log(f"服务器有空位但 DOM 未找到对应行：{server.name}；{result.get('reason', '')}")
        return False

    await click_match(page, result)
    log(f"已点击加入，等待 {args.post_click_wait:g}s 交给浏览器/游戏处理")
    await asyncio.sleep(max(args.post_click_wait, 0))
    return True


async def watch(page: Any, args: Any) -> None:
    await wait_for_server_rows(page)

    if args.server:
        log(f"监控指定服务器：{args.server}")
    else:
        log(f"自动加入关键词：{', '.join(args.target or ['obj3'])}")
    log(f"仅检测模式：{', '.join(args.modes)}（页面分区：{', '.join(_allowed_sections(args))}）")
    log(f"页面：{args.url}；轮询间隔：{args.interval:g}s")
    if args.dry_run:
        log("dry-run 模式：只报告匹配，不点击")

    last_reload = time.monotonic()
    last_status = time.monotonic()

    while True:
        try:
            await ensure_page_ready(page, args.url)

            if args.reload_every > 0 and time.monotonic() - last_reload >= args.reload_every:
                log("重新加载页面")
                await page.reload(wait_until="domcontentloaded", timeout=60_000)
                await wait_for_server_rows(page)
                last_reload = time.monotonic()

            servers = await _fetch_servers(args)
            clicked = (
                await _handle_monitor(page, args, servers)
                if args.server
                else await _handle_auto_join(page, args, servers)
            )

            if clicked:
                # 已成功点击加入，保持浏览器一段时间交给游戏/Steam 后自动结束
                return

            if args.scan_scroll:
                await scan_scroll_once(page)

            now = time.monotonic()
            if now - last_status >= 10:
                ze_servers = [s for s in servers if s.mode in args.modes]
                if args.server:
                    target = matching.find_server(ze_servers, args.server, args.case_sensitive)
                    detail = (
                        f"；{target.name} {'已满' if target.is_full else '有空位'}"
                        if target
                        else "；未找到目标服务器"
                    )
                else:
                    targets = [t for t in (args.target or ["obj3"]) if t.strip()]
                    active_target = None
                    matched_target: list[Server] = []
                    for target in targets:
                        matched_target = [
                            s
                            for s in ze_servers
                            if matching.server_matches(s, [target], args.case_sensitive)
                        ]
                        if matched_target:
                            active_target = target
                            break
                    if active_target:
                        pending = sum(1 for s in matched_target if s.is_full)
                        detail = (
                            f"；当前优先级 [{active_target}] 匹配 {len(matched_target)} 台，"
                            f"其中 {pending} 台已满"
                        )
                    else:
                        detail = "；暂无关键词匹配"
                log(f"监控中；僵尸逃跑服务器 {len(ze_servers)} 台{detail}")
                last_status = now

            await asyncio.sleep(args.interval)
        except RuntimeError as exc:
            log(f"页面不可用，自动退出：{exc}")
            return
        except Exception as exc:  # 网络抖动、页面临时异常等均不退出
            log(f"运行异常，重试：{exc}")
            await asyncio.sleep(max(args.interval, 2.0))
