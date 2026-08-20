# EXG 僵尸逃跑自动加入

一个轻量的浏览器自动化脚本：直接读取 EXG 服务器列表接口和页面 DOM，另开浏览器后台监控 **僵尸逃跑** 模式下的服务器，再也不用为挤不进obj而烦恼呐~（后台开着cs2，直接秒进，让你成为EXG最快的靓仔）

支持两种模式：

1. **自动加入**：在所有僵尸逃跑服务器里匹配关键词（服务器名 / 地图名等），一旦命中且有空位就点击“加入”。
2. **监控指定服务器**：指定一个服务器 ID 或地图名，持续监控；当它出现空位时立刻点击“加入”。

## 特性

- 只检测 `僵尸逃跑`（`cs2ze`），自动忽略挂机大厅、PVE、躲猫猫、娱乐闯关等其他模式。
- 默认只在有空位时加入；`--allow-full` 可恢复“满员也点”的旧行为（莫非你能挤掉别人？我也不知道这个功能有啥用）。
- 多个关键词按优先级匹配：先找第一个关键词，有匹配就锁定该关键词；第一个完全没有匹配时才用第二个，以此类推。
- 关键词至少 2 个字符，过短的关键词会自动忽略，避免一两个字符误匹配一大堆服务器。
- 成功点击“加入”后，会保持浏览器约 60 秒用于拉起 Steam/游戏，然后自动结束并关闭浏览器（其实应该点击了就可以了）。
- 登录状态保存在独立浏览器 profile（`data/profile`），首次登录一次即可。
- 日志每次启动自动滚动到 `auto_join.log.1`，新日志从空文件开始；单个日志超过 1MB 会自动轮转，最多保留 3 份历史。


## 1.安装

需要先安装 Python 3.10 或更高版本。

```powershell
# 必装：Python 依赖（Playwright 等）
python -m pip install -r requirements.txt
```

如果电脑上没有 Chrome 也没有 Edge，才需要额外安装 Playwright 内置浏览器：

```powershell
python -m playwright install chromium
```

> 脚本默认 `--channel auto`：优先使用本机 Chrome，没有 Chrome 就尝试 Edge，都没有才用 Playwright 内置 Chromium。


### 2.图形界面（推荐）

推荐先生成桌面快捷方式，之后直接双击使用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\create_desktop_shortcut.ps1
```

执行后会在桌面生成 **“僵尸逃跑自动加入”** 快捷方式（使用 EXG 图标），双击即可打开图形界面。

也可以不生成快捷方式，直接运行：

```powershell
python .\auto_join.pyw
```

界面里可以选择：

- 自动加入（输入多个关键词，用英文逗号 `,` 分隔；按输入顺序优先匹配）
- 监控指定服务器（输入服务器 ID 或地图名，如 `#7`、`孤注一掷`）

点击“开始监控”后会在后台运行，日志写入 `logs\auto_join.log`。


## 快速开始（当然如果你只想要懒人操作）

> 也可以直接下载 Release 里的 `EXG-AutoJoin.exe`，双击运行即可。


### 命令行

```powershell
# 自动加入：匹配所有僵尸逃跑服务器中的关键词，有空位才点
python .\auto_join.py --target sisy --target obj

# 也可以一次传入多个，用英文逗号分隔，按顺序优先匹配
python .\auto_join.py --target "obj,一线生机"

# 监控指定服务器，出现空位立即加入
python .\auto_join.py --server "ZE装备 #7"

# 按服务器 ID 监控
python .\auto_join.py --server cs2ze07

# 只报告不点击
python .\auto_join.py --target obj --dry-run

# 强制刷新页面（列表长期不更新时使用）
python .\auto_join.py --target obj --reload-every 120
```


## 常用参数

| 参数 | 说明 |
| --- | --- |
| `--target TEXT` | 自动加入关键词，可多次传入 |
| `--server TEXT` | 监控指定服务器名称/ID |
| `--mode MODE` | 模式前缀或中文名，可多次传入，默认 `cs2ze`（僵尸逃跑） |
| `--interval SEC` | 轮询间隔，默认 `1.0` 秒 |
| `--post-click-wait SEC` | 点击后保持浏览器等待，默认 `60` 秒 |
| `--allow-full` | 自动加入时也点击已满服务器 |
| `--scan-scroll` | 页面滚动扫描（懒加载时更稳） |
| `--dry-run` | 只报告不点击 |
| `--headless` | 无头浏览器运行 |
| `--channel NAME` | 浏览器：`auto`（默认）、`chrome`、`msedge`，空字符串用内置 Chromium |
| `--cdp-url URL` | 连接已开远程调试的 Chrome |
| `--profile-dir DIR` | 浏览器 profile 目录，默认 `data\profile` |

## 连接到现有浏览器

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="$env:TEMP\chrome-auto-join"
python .\auto_join.py --target obj --cdp-url http://127.0.0.1:9222
```

注意：必须是带 `--remote-debugging-port=9222` 启动的浏览器。

## 目录结构

```text
auto_join/
├── auto_join.py             # 命令行入口
├── auto_join.pyw            # 图形界面入口
├── exg_auto_join/           # 核心代码包
│   ├── api.py               # 服务器列表接口
│   ├── browser.py           # Playwright DOM 操作
│   ├── cli.py               # 命令行参数与启动
│   ├── config.py            # 路径 / 模式配置
│   ├── gui.py               # Tkinter 图形界面
│   ├── matching.py          # 关键词 / 服务器匹配
│   ├── models.py            # 服务器数据模型
│   ├── watcher.py           # 监控主循环
│   └── log.py               # 日志输出
├── assets/darkrp.ico        # 应用图标（darkrp.cn favicon）
├── create_desktop_shortcut.ps1  # 生成桌面快捷方式
├── data/profile/            # 浏览器登录态（自动生成）
├── logs/auto_join.log       # 运行日志（自动生成，自动滚动）
├── requirements.txt
└── pyproject.toml
```
