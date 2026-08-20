from __future__ import annotations

from .models import Server


def normalize(text: str, case_sensitive: bool = False) -> str:
    value = " ".join(str(text or "").split())
    return value if case_sensitive else value.casefold()


def server_matches(server: Server, targets: list[str], case_sensitive: bool = False) -> bool:
    haystack = normalize(server.searchable_text, case_sensitive)
    return any(normalize(t, case_sensitive) in haystack for t in targets if t.strip())


def find_server(
    servers: list[Server],
    query: str,
    case_sensitive: bool = False,
) -> Server | None:
    """按 ID、显示名或任意可搜索文本查找服务器；先精确后模糊。"""
    q = query.strip()
    if not q:
        return None

    normalized = normalize(q, case_sensitive)
    for server in servers:
        if normalize(server.id, case_sensitive) == normalized:
            return server
        if normalize(server.name, case_sensitive) == normalized:
            return server

    matches = [
        server
        for server in servers
        if normalized in normalize(server.searchable_text, case_sensitive)
    ]
    return matches[0] if matches else None
