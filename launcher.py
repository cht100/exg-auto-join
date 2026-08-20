#!/usr/bin/env python3
"""PyInstaller 打包入口：无参数打开图形界面，有参数进入命令行监控模式。"""

import sys


def main() -> int:
    if len(sys.argv) > 1:
        from exg_auto_join.cli import main as cli_main

        return cli_main()

    from exg_auto_join.gui import main as gui_main

    gui_main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
