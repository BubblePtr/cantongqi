---
name: rss-daily-to-cards
description: 将 Markdown 格式的 RSS 日报转换为适合小红书/小绿书的 3:4 比例网页卡片。采用杂志风印刷质感设计，支持合欢红+银白配色、噪点滤镜、深色模式穿插等视觉效果。集成 Playwright 自动截图，一键生成 PNG 图片。
---

# RSS 日报转社交媒体卡片

## 概述

本技能将 Markdown 格式的 RSS 精选日报转换为杂志风格的社交媒体卡片。采用瑞士主义排版、合欢红+银白配色、印刷质感噪点滤镜，每张卡片都具备高端纸媒的视觉效果。

**设计特点**：
- **色彩策略**：合欢红 #E07563 + 银白 #F1F0EC
- **印刷质感**：全局噪点滤镜 + 深邃悬浮阴影
- **字体栈**：Oswald（数字/英文）+ Noto Serif SC（标题）+ Noto Sans SC（正文）
- **深色穿插**：每3-4张卡片自动插入一张 Dark Mode 卡片
- **破格封面**：非对称色块切割设计
- **统一页头**：所有卡片页头格式一致（分类标签 + 日期 + 副标题）

**品牌信息**：
- **主标题**：第九比特的 AI 日报
- **副标题**：每日精选
- **Twitter**：@ninthbit_ai

## 输入格式要求

```markdown
# YYYY-MM-DD - 日报标题

---

## 🔥 小节标题（每篇文章一个独立小节）

**分类：文章分类**

文章内容，支持完整的 Markdown 格式...

---

## 📊 今日数据

统计数据内容...

## 💡 编者观察

编者按内容...
```

## 字数规范

| 字号 | 建议字数 | 说明 |
|------|----------|------|
| 20px | 300-500 字 | 当前配置，最佳视觉效果 |

## 使用方式

### 前提：安装依赖

首次使用需要安装依赖（在 Skill 目录下执行一次）：

```bash
# 进入 Skill 目录
cd ~/.claude/skills/rss-daily-to-cards/

# 安装依赖
uv venv
uv pip install -r requirements.txt
uv run playwright install chromium
```

### 生成卡片

必须先激活 skill 目录下的 venv，再调用脚本（`uv run --project` 无法正确找到 Playwright）：

```bash
# 激活 skill 的 venv，然后用绝对路径调用脚本
cd ~/.claude/skills/rss-daily-to-cards && source .venv/bin/activate && \
  python scripts/generate_cards.py "/绝对路径/{日期} AI热点日报.json" -o /绝对路径/cards_output
```

输入文件为 `rss-daily-report` 生成的 JSON 日报（`{日期} AI热点日报.json`），不再使用 Markdown 文件。

输出：`cards_output/card_01.png`, `cards_output/card_02.png` ...

### 快捷方式（可选）

可以创建别名方便使用：

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
alias rss-to-cards='uv run ~/.claude/skills/rss-daily-to-cards/scripts/generate_cards.py'

# 之后可以直接使用
rss-to-cards "你的日报.md" -o output
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `-o, --output` | 输出目录（默认：`output/`） |
| `--keep-html` | 保留中间 HTML 文件 |
| `--no-screenshot` | 跳过自动截图（仅生成 HTML） |
| `--cleanup` | 仅清理历史中间文件 |
| `--width` / `--height` | 截图尺寸（默认 900x1200，输出 2x 高清图） |

### 完整示例

```bash
# 假设你在 ~/Documents/rss/ 目录下
pwd
# ~/Documents/rss/

ls
# 2024-01-15.md

# 生成卡片（使用绝对路径调用 Skill）
uv run ~/.claude/skills/rss-daily-to-cards/scripts/generate_cards.py "2024-01-15.md" -o cards

# 查看输出
ls cards/
# card_01.png  card_02.png  card_03.png ...
```

## 卡片结构

### 页头格式（统一）
所有卡片页头采用统一格式：

```
┌─────────────────────────────────────┐
│ [分类标签]              2026-02-17  │
│                        每日精选     │
├─────────────────────────────────────┤
│                                     │
│           卡片内容区域              │
│                                     │
├─────────────────────────────────────┤
│ 1 / 6                        @ninthbit_ai │
└─────────────────────────────────────┘
```

### 卡片类型

1. **封面卡片**（第 1 张）：破格设计，非对称色块，大标题"第九比特的 AI 日报"
2. **内容卡片**（第 2-N+1 张）：交替浅色/深色模式
3. **深色穿插**：每3-4张卡片自动插入 Dark Mode 卡片

### 页脚信息
- 左侧：页码（当前页 / 总页数）
- 右侧：Twitter X 图标 + @ninthbit_ai

## 资源文件

- `assets/style.css` - 杂志风样式（含噪点滤镜、深色模式、统一页头样式）
- `scripts/generate_cards.py` - 主脚本：生成 HTML + 自动截图 + 清理临时文件
- `scripts/export_images.py` - （可选）独立的高清图片导出脚本

## 依赖安装

### 方式一：使用 uv（推荐，Mac 友好）

```bash
# 1. 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt

# 2. 安装 Playwright 浏览器（仅需一次）
uv run playwright install chromium
```

### 方式二：使用 pip3（需要虚拟环境）

```bash
# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或: .venv\Scripts\activate  # Windows

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 安装 Playwright 浏览器
playwright install chromium
```

## 运行脚本

```bash
# 使用 uv 运行（推荐）
uv run python scripts/generate_cards.py "RSS日报.md" -o output

# 或激活虚拟环境后运行
source .venv/bin/activate
python scripts/generate_cards.py "RSS日报.md" -o output
```
