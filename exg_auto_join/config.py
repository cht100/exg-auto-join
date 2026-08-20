from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # PyInstaller 打包后：数据/日志放在 exe 同目录，资源从临时解包目录读取
    PROJECT_ROOT = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    RESOURCE_DIR = PROJECT_ROOT

DEFAULT_URL = "https://darkrp.cn/servers"
SERVER_LIST_API = "https://list.darkrp.cn:9000/ServerList/CurrentStatus"

DEFAULT_PROFILE_DIR = PROJECT_ROOT / "data" / "profile"
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "auto_join.log"
ICON_PATH = RESOURCE_DIR / "assets" / "darkrp.ico"

# 服务器 ID 前缀 -> 页面分区标题
MODE_TITLES = {
    "cs2home": "挂机大厅",
    "cs2zepve": "PVE模式",
    "cs2ze": "僵尸逃跑",
    "cs2ph": "躲猫猫",
    "cs2mg": "娱乐闯关",
}

DEFAULT_MODES = ("cs2ze",)


def mode_title(mode: str) -> str:
    """把模式前缀（cs2ze）或中文标题转成页面分区标题。"""
    mode = mode.strip()
    if mode in MODE_TITLES:
        return MODE_TITLES[mode]
    if mode in MODE_TITLES.values():
        return mode
    return mode


def resolve_modes(values: list[str] | None) -> list[str]:
    """把用户传入的模式（前缀或中文名）统一成前缀列表。"""
    if not values:
        return list(DEFAULT_MODES)

    modes: list[str] = []
    for value in values:
        value = value.strip()
        if value in MODE_TITLES:
            modes.append(value)
        elif value in MODE_TITLES.values():
            modes.append(next(key for key, title in MODE_TITLES.items() if title == value))
        else:
            modes.append(value)
    return list(dict.fromkeys(modes)) or list(DEFAULT_MODES)
