from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Server:
    id: str
    name: str
    display_name: str
    full_title: str
    region: str
    map_name: str
    map_name_cn: str
    difficulty: str
    current_players: int
    max_players: int
    ip: str
    port: int

    @property
    def mode(self) -> str:
        # 站点按 id 去掉末尾两位数字得到模式前缀，例如 cs2ze06 -> cs2ze
        return self.id[:-2] if len(self.id) > 2 else self.id

    @property
    def is_full(self) -> bool:
        return self.current_players >= self.max_players

    @property
    def players_text(self) -> str:
        return f"{self.current_players}/{self.max_players}"

    @property
    def searchable_text(self) -> str:
        return " ".join(
            filter(
                None,
                (
                    self.name,
                    self.display_name,
                    self.full_title,
                    self.map_name,
                    self.map_name_cn,
                    self.difficulty,
                ),
            )
        )
