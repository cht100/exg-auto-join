from __future__ import annotations

from typing import Any

from .log import log


async def select_page(context: Any, url: str):
    for page in context.pages:
        if "darkrp.cn/servers" in page.url or page.url == url:
            return page

    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    return page


async def ensure_page_ready(page: Any, url: str) -> None:
    if page.is_closed():
        raise RuntimeError("browser page was closed")

    if not page.url or page.url == "about:blank":
        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        return

    if "darkrp.cn/servers" not in page.url:
        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)


async def wait_for_server_rows(page: Any, timeout_ms: int = 10_000) -> None:
    try:
        await page.locator("tr.el-table__row, .server-item").first.wait_for(
            state="visible", timeout=timeout_ms
        )
    except Exception:
        # 页面可能暂时没有服务器卡片/表格；由上层循环重试
        pass


async def find_join_button(
    page: Any,
    server_name: str,
    join_text: str = "加入",
    allowed_sections: list[str] | None = None,
    case_sensitive: bool = False,
) -> dict[str, Any]:
    """在页面 DOM 中找到指定服务器的“加入”按钮，返回可点击信息。"""
    allowed = allowed_sections or []
    payload = {
        "serverName": server_name,
        "joinText": join_text,
        "allowedSections": allowed,
        "caseSensitive": case_sensitive,
    }

    return await page.evaluate(
        """
        async ({ serverName, joinText, allowedSections, caseSensitive }) => {
          const normalize = (value) => {
            const text = String(value || "").replace(/\\s+/g, " ").trim();
            return caseSensitive ? text : text.toLowerCase();
          };

          const wantedName = normalize(serverName);
          const wantedJoin = normalize(joinText);
          const wantedSections = allowedSections.map(normalize).filter(Boolean);

          const visible = (el) => {
            if (!el || !el.isConnected) return false;
            const style = window.getComputedStyle(el);
            if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity) === 0) {
              return false;
            }
            const rect = el.getBoundingClientRect();
            return rect.width > 1 && rect.height > 1;
          };

          const rawTextOf = (el) => String(el.innerText || el.textContent || el.value || el.getAttribute("aria-label") || "")
            .replace(/\\s+/g, " ")
            .trim();
          const textOf = (el) => normalize(rawTextOf(el));

          const sectionForRow = (row) => {
            const table = row.closest(".el-table");
            let node = table || row;
            while (node) {
              for (let prev = node.previousElementSibling; prev; prev = prev.previousElementSibling) {
                const title = prev.matches?.(".server-type-title")
                  ? prev
                  : prev.querySelector?.(".server-type-title");
                if (title && visible(title)) return rawTextOf(title);
              }
              node = node.parentElement;
            }
            return "";
          };

          const joinSelector = [
            "button",
            "a",
            "[role='button']",
            "input[type='button']",
            "input[type='submit']",
            ".btn",
            ".button"
          ].join(",");

          const tableRows = Array.from(document.querySelectorAll("tr.el-table__row")).filter(visible);
          const cardRows = Array.from(document.querySelectorAll(".server-item")).filter(visible);
          const rows = tableRows.length ? tableRows : cardRows;

          for (const row of rows) {
            const section = sectionForRow(row);
            if (wantedSections.length && !wantedSections.includes(normalize(section))) continue;

            const rawRowText = rawTextOf(row);
            const rowText = normalize(rawRowText);
            const firstCell = row.querySelector("td .cell");
            const nameEl = row.querySelector(".server-item-inner p, .server-item-topbar p, p");
            const cellText = firstCell
              ? normalize(rawTextOf(firstCell))
              : nameEl
                ? normalize(rawTextOf(nameEl))
                : "";
            const rowMatches = cellText ? cellText === wantedName : rowText.includes(wantedName);
            if (!rowMatches) continue;

            const joinButton = Array.from(row.querySelectorAll(joinSelector))
              .find((el) => visible(el) && textOf(el).includes(wantedJoin));
            if (!joinButton) continue;

            joinButton.scrollIntoView({ block: "center", inline: "center" });
            await new Promise((resolve) => setTimeout(resolve, 80));

            const marker = `auto-join-${Date.now()}-${Math.random().toString(36).slice(2)}`;
            joinButton.setAttribute("data-auto-join-marker", marker);
            const buttonRect = joinButton.getBoundingClientRect();

            return {
              matched: true,
              marker,
              section,
              rowText: rawRowText.slice(0, 220),
              buttonCenter: {
                x: Math.round(buttonRect.left + buttonRect.width / 2),
                y: Math.round(buttonRect.top + buttonRect.height / 2)
              }
            };
          }

          return {
            matched: false,
            reason: `server row not found or join button missing: ${serverName}`,
            inspectedCount: rows.length
          };
        }
        """,
        payload,
    )


async def click_match(page: Any, result: dict[str, Any]) -> None:
    marker = result.get("marker")
    center = result.get("buttonCenter") or {}

    try:
        await page.bring_to_front()
    except Exception:
        pass

    if marker:
        locator = page.locator(f"[data-auto-join-marker='{marker}']")
        try:
            await locator.click(timeout=5_000)
            return
        except Exception as exc:
            log(f"locator click failed, falling back to coordinate click: {exc}")

    x = center.get("x")
    y = center.get("y")
    if isinstance(x, int) and isinstance(y, int):
        await page.mouse.click(x, y)
        return

    raise RuntimeError("matched a server, but could not determine the join button position")


async def scan_scroll_once(page: Any) -> None:
    await page.evaluate(
        """
        () => {
          const step = Math.max(240, Math.floor(window.innerHeight * 0.65));
          const maxY = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
          const nextY = window.scrollY >= maxY - 5 ? 0 : Math.min(maxY, window.scrollY + step);
          window.scrollTo({ top: nextY, behavior: "instant" });
        }
        """
    )
