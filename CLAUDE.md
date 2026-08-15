# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 NoneBot2 的 QQ 机器人，提供物理实验图片查询功能，支持精确匹配和 AI 模糊匹配。彩蛋插件提供迪士尼角色、教师图片查询和随机文本功能。

## 开发命令

```bash
uv sync              # 安装依赖（依赖在 pyproject.toml / uv.lock）
uv run bot.py        # 运行机器人（OneBot v11 适配器）
uv run pyright       # 静态类型检查（pyrightconfig.json 指向 .venv）
```

无测试框架。改动后用 `uv run pyright` + 实际命令验证。

## 命令

| 命令 | 说明 |
|------|------|
| `大雾1 <实验名>` | 查询物理实验图片，精确/AI模糊匹配 |
| `大雾1 ls` | 列出所有关键词 |
| `大雾1 help` | 帮助信息 |
| `大雾2 <实验名>` | 查询二级大雾题库（考试题目图片），精确/AI模糊匹配 |
| `大雾2 ls` | 列出所有关键词 |
| `大雾2 help` | 帮助信息 |
| `彩蛋 <角色/教师>` | 彩蛋查询 |
| `彩蛋 ls` | 列出所有彩蛋关键词 |

## 项目架构

```
RzyL/
├── bot.py                    # 入口：init + 注册 OneBot v11 + load_plugins("src/plugins")
├── pyproject.toml            # 项目配置，依赖 nonebot2 / alconna / onebot.v11 / aiohttp
├── .env.secret.temple        # 复制为 .env.secret 后填入真实密钥
├── src/
│   ├── asserts/              # 扁平资源目录（图片 + 关键词 JSON）
│   │   ├── dawu/             #   物理实验图片 + keywords.json（实验关键词）
│   │   ├── dawu2/            #   二级大雾题库图片（27实验，每实验一张）+ keywords.json
│   │   ├── easter_egg/       #   彩蛋图片/子目录 + keywords.json
│   │   └── factor/           #   教师照片（*.jpg，文件名即教师姓名）
│   └── plugins/
│       ├── dawu/             # 主插件（大雾1）
│       ├── dawu2/            # 题库插件（大雾2），与 dawu 同构
│       ├── easter_egg/       # 彩蛋插件
│       └── echo/             # 示例插件（大部分代码被注释）
```

资源加载统一用 `Path(__file__).parent.parent.parent / "asserts" / ...` 定位，图片路径常用 `Path.cwd() / "src" / "asserts" / ...`。

## 主插件 dawu —— 核心机制

- **命令解析**：Alconna，`大雾1 <name>`，`priority=0, block=True`，`rule=check_group`。
- **群组过滤**：`config.py` 从 `dawu_allowed_groups` 读取允许群列表（逗号分隔字符串），留空则全部放行。
- **关键词匹配**：`KEYWORDS` 从 `asserts/dawu/keywords.json` 加载（英文键 → 中文别名列表）。`find_keywords` 对输入做子串/别名包含匹配，同一输入可命中多个键。
- **AI 回退**：精确匹配失败时调用 `ai_match`（`ai_match.py`），`asyncio.Semaphore(8)` 限并发，调用 OpenAI 兼容 `/chat/completions`，返回英文键列表或 `NONE`。配置键 `base_url` / `api_key` / `model_think`。
- **速率限制**：按 `user_id` 每 60 秒最多 10 次。
- **联动彩蛋**：`require("src.plugins.easter_egg")` + 直接 `from src.plugins.easter_egg import try_load_random_text`；发送查询结果后有概率追加随机一言/小问题。
- **缺失图片**：若命中关键词但 `{keyword}.jpg` 不存在，会返回缺失文件名提示。

## 题库插件 dawu2 —— 与 dawu 同构

- 与 `dawu` 完全同构（命令 `大雾2 <name>`，`priority=0, block=True`，复用精确匹配 + AI 回退 + 限速 + 群组过滤 + 彩蛋联动 + 缺失图提示）。
- 资源：`asserts/dawu2/keywords.json`（27 个英文键 → 中文别名）；图片 `asserts/dawu2/{键}.jpg`，由 `二级大雾题库/二级大雾题库.pdf`（40 页）按实验切片而来——单页实验直接渲染，跨页实验（如非平衡电桥 17–18、医学物理 38–39）纵向拼接成一张长图。
- 群组配置键为 `dawu2_allowed_groups`（独立于 `dawu_allowed_groups`）。AI 回退共用同一套 `base_url`/`api_key`/`model_think`。
- 切图脚本：`scripts/slice_dawu2.py`（用 `pdftoppm` + PIL 拼接，键→页范围硬编码于脚本中，重新切片需先在本地用 XeLaTeX 编译 `二级大雾题库/main.tex` 生成 PDF）。

## 彩蛋插件 easter_egg

- **亮蛋查询**：`彩蛋 <name>`，`priority=1`（低于主插件）。从 `asserts/easter_egg/keywords.json` 加载 `EASTER_EGG_KEYWORDS`。
- **图片查找**：`get_easter_egg_image_path` 先看 `asserts/easter_egg/<keyword>/` 子目录（目录内随机选一张），再按多种扩展名（jpg/jpeg/png/gif/webp/bmp/tiff）探测单文件。子目录存在于 `CrazyThursday` / `Nico` / `bxh` / `cj` / `cjx` / `pjw`。
- **复合彩蛋**：`COMPOUND_KEYWORDS` 把单键映射到多个子目标，如 `four_sages → [曲广媛, 李恒一, 郭玉刚, 蔡俊]`，从 `asserts/factor/` 目录（`FACTOR_IMAGE_DIR`）加载对应教师照片。
- **`factor.py`**：从 `asserts/factor/` 目录扫描文件名得到教师姓名列表，提供 `find_factor_teachers` / `get_factor_image_path`。**注意：当前只有备份文件 `__init__1.py` 引用它，正式 `__init__.py` 用的是上面硬编码的 `COMPOUND_KEYWORDS` + `_find_factor_image`**——二者是同一功能的两种实现，改动前先确认以哪个为准。
- **随机文本**（`random_text.py`）：`load_random_text` 按星期概率（周二/五 0.5，其余 0.2）加 40% 概率返回 `sentences.txt` 随机一话，或 `question.txt` 随机一问。`try_load_random_text` 是其 import 别名。

## 配置与安全

- 复制 `.env.secret.temple` → `.env.secret`，填入 `BASE_URL` / `API_KEY` / `MODEL_CHAT` / `MODEL_THINK` / `MODEL_LITE` / `DAWU_ALLOWED_GROUPS` / `DAWU2_ALLOWED_GROUPS`。
- `.env.secret` 和 `.venv` 已被 .gitignore 忽略，永不提交真实密钥。注意 `pyright.config` 指向 `.venv`。

## 已知的遗留/不一致（改动时留意）

- `src/asserts/easter_egg/keywords_girlfriend.json` 与顶层 `src/asserts/keywords.json`（含 AI 大模型关键词 GLM/Qwen/Gemini/Grok/Claude/DeepSeek/ChatGPT）**未被任何插件代码引用**，属疑似遗留数据。
- `src/plugins/easter_egg/__init__1.py` 是旧版备份，与正式 `__init__.py` 并行存在。
- 顶层 `二级大雾题库/` 目录是 LaTeX 题库源码（`main.tex` + `elegantbook.cls` + 各实验 `.tex`），其编译产物 `二级大雾题库.pdf` 是 `dawu2` 图片的来源；`scripts/slice_dawu2.py` 负责切片。源码本身非运行时代码。