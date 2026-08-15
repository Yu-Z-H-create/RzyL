# RzyL - 物理实验查询机器人

基于 NoneBot2 的 QQ 机器人，提供物理实验图片查询功能，支持精确匹配和 AI 模糊匹配。

## 功能特性

- **关键词匹配**：支持精确匹配和 AI 模糊匹配物理实验关键词
- **图片查询**：根据关键词返回对应的实验图片（.jpg格式）
- **多关键词支持**：一次查询可返回多个匹配的实验图片
- **智能回退**：精确匹配失败时自动使用 AI 进行模糊匹配
- **随机语言**：有概率发送随机一言或小问题，增加互动趣味
- **速率限制**：每用户每分钟最多10次请求，防止滥用

## 安装

1. 克隆项目
2. 安装依赖：
   ```bash
   uv sync
   ```

## 配置

复制 `.env.secret.temple` 为 `.env.secret` 并填写配置：

```env
# AI API配置（必需）
BASE_URL=https://api.longcat.chat/openai
API_KEY=your_api_key
MODEL_THINK=your_think_model

# 可选配置
# 允许使用插件的群聊ID列表，留空表示所有群聊可用
DAWU_ALLOWED_GROUPS=[]  # 例如: [123456789, 987654321]
```

## 使用方法

### 基本命令

| 命令 | 说明 |
|------|------|
| `大雾1 <实验名称>` | 查询实验图片 |
| `大雾1 ls` | 查看所有可用关键词 |
| `大雾1 help` | 查看帮助信息 |

### 示例

```
大雾1 杨氏模量        # 返回杨氏模量实验图片
大雾1 示波器          # 返回示波器使用图片
大雾1 光电            # 返回光电效应图片
大雾1 物理实验        # AI 模糊匹配相关实验
```

## 项目结构

```
RzyL/
├── bot.py                      # 机器人入口
├── pyproject.toml              # 项目配置
├── .env                        # 环境变量
├── .env.secret                 # 敏感配置（API密钥等）
├── .env.secret.temple          # 配置模板
├── src/
│   ├── plugins/
│   │   ├── dawu/              # 主插件
│   │   │   ├── __init__.py    # 主逻辑、命令处理
│   │   │   ├── config.py      # 配置、群组过滤
│   │   │   ├── keywords.py    # 关键词加载器
│   │   │   ├── keywords.json  # 关键词定义
│   │   │   ├── ai_match.py    # AI 匹配
│   │   │   ├── random_text.py # 随机文本加载
│   │   │   ├── sentences.txt  # 随机一言
│   │   │   └── question.txt   # 小问题
│   │   └── echo/              # Echo插件示例
│   └── asserts/dawu/          # 实验图片（.jpg）
└── CLAUDE.md                  # Claude Code 指南
```

## 技术栈

- **框架**：NoneBot2
- **适配器**：OneBot v11
- **命令解析**：Alconna
- **HTTP客户端**：aiohttp（异步）
- **AI 匹配**：OpenAI 兼容 API

## 开发

运行机器人：
```bash
uv run bot.py
```

类型检查：
```bash
uv run pyright
```

## 许可证

MIT
