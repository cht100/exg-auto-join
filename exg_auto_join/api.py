from __future__ import annotations

import json
import urllib.request
from typing import Any

from .config import SERVER_LIST_API
from .models import Server


def fetch_servers(url: str = SERVER_LIST_API, timeout: float = 10.0) -> list[Server]:
    """从 EXG 公开接口拉取服务器列表。"""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = json.load(response)
    return parse_servers(payload)


def parse_servers(payload: Any) -> list[Server]:
    servers: list[Server] = []
    for item in payload or []:
        server = item.get("Server") or {}
        status = item.get("Status") or {}
        servers.append(
            Server(
                id=str(server.get("Id") or ""),
                name=str(server.get("DisplayNameCN") or server.get("DisplayName") or ""),
                display_name=str(server.get("DisplayName") or ""),
                full_title=str(status.get("FullTitle") or ""),
                region=str(server.get("Region") or ""),
                map_name=str(status.get("Map") or ""),
                map_name_cn=str(status.get("MapDisplayName") or ""),
                difficulty=str(status.get("MapDifficulty") or ""),
                current_players=int(status.get("CurrentPlayers") or 0),
                max_players=int(status.get("MaxPlayers") or 0),
                ip=str(server.get("Ip") or ""),
                port=int(server.get("Port") or 0),
            )
        )
    return servers
