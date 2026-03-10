---
name: rss-daily-report
description: 从 OPML 格式的 RSS 订阅源抓取 24 小时内更新的文章，访问原文获取完整内容，然后由 Agent 生成 300-500 字中文摘要、分类和编者观察，最终输出格式化的 Markdown 日报。适用于需要从 RSS 订阅源生成高质量中文日报的场景。
---

# RSS 日报生成器

从 OPML 文件定义的 RSS 订阅源抓取更新，访问原文获取完整内容，由 Agent 生成中文摘要和分类，输出结构化 Markdown 日报。

## 路径初始化（必须第一步执行）

skill 加载时会显示 `Base directory for this skill: /path/to/skill`，将该路径存为变量供后续所有命令使用：

```bash
SKILL_DIR="<skill 加载时显示的 Base directory 路径>"
# 例：SKILL_DIR="/Users/void/.claude/skills/rss-daily-report"
```

后续所有脚本调用均使用 `$SKILL_DIR/scripts/generate_report.py`，不得硬编码绝对路径。

## 工作流程

```
OPML → RSS 抓取 → 时效过滤 → 原文抓取 → 内容过滤 → [评分筛选] → 摘要生成 → 双格式输出
```

1. **fetch**: 抓取文章全文，保存为 `{日期}_articles_raw.json`
2. **filter**: 过滤内容 < 500 字的文章，保存为 `{日期}_articles_filtered.json`
3. **[评分 subagent]**: 若文章数 > 10，用 subagent 评分，取最优 10 篇，保存为 `{日期}_articles_top10.json`
4. **[摘要 subagent]**: 用 subagent 为每篇文章生成中文摘要、分类、编者观察，保存为 `agent_result.json`
5. **generate**: 生成最终 `{日期} AI热点日报.md` 和 `{日期} AI热点日报.json`

## 输出规范

### 文件名格式
- `{日期} AI热点日报.md` (例: `2026-02-17 AI热点日报.md`)

### 内容结构
1. **标题**: `# YYYY-MM-DD - AI热点日报`
2. **引言**: `> AI热点信源资讯汇总 | 共 N 条更新`
3. **文章列表**: 每篇包含
   - 标题（带分类表情符号）
   - 分类标签（AI、编程、Web、开源、安全、产品、创业、数据、其他）
   - **中文简介（300-500字）**
   - 原文链接
4. **今日数据**: 统计信息
5. **编者观察**: 编辑观点总结
6. **页脚**: 数据源信息

### 中文摘要要求（Agent 生成）

**字数要求**:
- 每篇文章摘要：300-500 个中文字符
- 字数计算方法：纯中文字符数（不含标点、空格、英文单词）

**内容要求**:
1. 基于文章全文，提炼核心观点和关键信息
2. 用流畅的中文撰写，避免直译腔
3. 包含：文章主题、主要观点、关键细节、价值/意义
4. 不要只是翻译，要组织和重构信息

**分类选择**（必须为每篇文章选择一项）:
AI、编程、Web、开源、安全、产品、创业、数据、其他

**编者观察要求**（100-200 字）:
- 总结今日文章的整体趋势和主题
- 指出最有价值或最值得关注的内容
- 给出编辑观点

## 使用方法

### 数据源说明

本 skill **内置了 RSS 数据源**，无需额外指定 OPML 文件即可运行。内置数据源位于 `assets/` 目录下。

如需使用自定义 OPML 文件，可在 `fetch` 命令后指定路径。

### 步骤 1: 抓取文章数据

**使用内置数据源（推荐）:**
```bash
uvx --with feedparser python "$SKILL_DIR/scripts/generate_report.py" fetch
```

选项：
- `--hours 48`: 抓取 48 小时内的文章
- `--max-articles 20`: 最多处理 20 篇文章（默认）
- `-o output.json`: 指定输出文件名

输出：`{日期}_articles_raw.json`

### 步骤 2: 过滤短文章

```bash
uvx --with feedparser python "$SKILL_DIR/scripts/generate_report.py" filter {日期}_articles_raw.json
```

选项：
- `--min-length 500`: 最小内容长度（默认 500 字符）
- `-o output.json`: 指定输出文件名

输出：`{日期}_articles_filtered.json`，并提示是否需要评分筛选。

### 步骤 3: [条件] 评分筛选（文章数 > 10 时）

若过滤后文章数仍 > 10，Agent 读取 filtered JSON，对每篇文章按以下维度评分（各 1-10 分）：
- **技术深度**：内容是否有深度、有原创见解
- **信息价值**：对读者是否有实用价值
- **话题热度**：是否涉及当前热点话题

取综合分最高的 10 篇，保存为：

```json
{
  "date": "2026-02-18",
  "article_count": 10,
  "articles": [
    {
      "title": "文章标题",
      "link": "原文链接",
      "source": "来源",
      "published": "发布时间",
      "content": "正文内容",
      "score": 27,
      "score_detail": {"技术深度": 9, "信息价值": 9, "话题热度": 9}
    }
  ]
}
```

文件名：`{日期}_articles_top10.json`

### 步骤 4: 摘要生成（subagent）

Agent 读取 filtered/top10 JSON（取文章数较少的那个），为每篇文章生成摘要。

**重要：每次只处理 3-5 篇文章**，避免上下文过长导致超时。将结果合并后保存为 `agent_result.json`：

```json
{
  "articles": [
    {
      "title": "原文标题",
      "category": "AI",
      "summary": "300-500字中文摘要...",
      "link": "原文链接"
    }
  ],
  "editor_note": "编者观察内容（100-200字）..."
}
```

### 步骤 5: 生成最终日报

```bash
uvx --with feedparser python "$SKILL_DIR/scripts/generate_report.py" generate \
  {日期}_articles_filtered.json agent_result.json \
  -o "{日期} AI热点日报.md"
```

同时输出：
- `{日期} AI热点日报.md` — Markdown 格式
- `{日期} AI热点日报.json` — JSON 格式（自动生成，与 .md 同名）

## 脚本说明

### generate_report.py

**fetch**: 抓取 RSS 和文章全文
```bash
uvx --with feedparser python "$SKILL_DIR/scripts/generate_report.py" fetch [opml_path] [--hours 24] [--max-articles 20]
```

**filter**: 过滤内容过短的文章
```bash
uvx --with feedparser python "$SKILL_DIR/scripts/generate_report.py" filter {日期}_articles_raw.json [--min-length 500]
```

**generate**: 基于 Agent 处理结果生成日报（同时输出 .md 和 .json）
```bash
uvx --with feedparser python "$SKILL_DIR/scripts/generate_report.py" generate articles_filtered.json agent_result.json [-o output.md]
```

### fetch_article.py

文章全文抓取工具：

```bash
# 测试抓取单篇文章
python "$SKILL_DIR/scripts/fetch_article.py" "https://example.com/article"
```

### validate_report.py

格式验证器：

```bash
python "$SKILL_DIR/scripts/validate_report.py" "2026-02-18 AI热点日报.md"
```

验证项：
- 标题、引言格式
- 必需段落完整性
- 每篇文章 300-500 字
- 分类有效性
- 链接格式

## 完整示例

```bash
# 0. 初始化路径变量（从 skill 加载时显示的 Base directory 获取）
SKILL_DIR="/Users/void/.claude/skills/rss-daily-report"  # 替换为实际路径

# 1. 抓取文章数据
uvx --with feedparser python "$SKILL_DIR/scripts/generate_report.py" fetch
# 输出: 2026-02-18_articles_raw.json

# 2. 过滤短文章
uvx --with feedparser python "$SKILL_DIR/scripts/generate_report.py" filter 2026-02-18_articles_raw.json
# 输出: 2026-02-18_articles_filtered.json
# 若文章数 > 10，Agent 进行评分筛选，输出: 2026-02-18_articles_top10.json

# 3. Agent 生成摘要（每次处理 3-5 篇，分批完成）
# 保存为: agent_result.json

# 4. 生成最终日报
uvx --with feedparser python "$SKILL_DIR/scripts/generate_report.py" generate \
  2026-02-18_articles_filtered.json agent_result.json \
  -o "2026-02-18 AI热点日报.md"
# 同时输出: 2026-02-18 AI热点日报.md 和 2026-02-18 AI热点日报.json

# 5. 验证格式
uvx --with feedparser python "$SKILL_DIR/scripts/validate_report.py" "2026-02-18 AI热点日报.md"
```
uvx --with feedparser python scripts/validate_report.py "2026-02-18 AI热点日报.md"
```

## 依赖安装

```bash
# 使用 uv（推荐）
uvx --with feedparser python scripts/generate_report.py fetch

# 可选：安装 trafilatura 以获得更好的正文提取效果
uv pip install trafilatura
```

## 注意事项

1. **原文抓取限制**: 部分网站可能有反爬虫机制，抓取失败时会回退到 RSS 摘要
2. **文章数量**: 默认最多处理 20 篇文章
3. **字数检查**: 使用 validate_report.py 验证字数是否符合要求
4. **生成 agent_result.json 时禁止直接写 JSON 文本**: 摘要内容含有双引号时会破坏 JSON 结构。必须用 Python 构建数据结构再 `json.dump()` 输出，示例：

```python
import json

articles = [{"title": "...", "summary": "含「引号」的摘要", "category": "AI", "link": "..."}]
data = {"articles": articles, "editor_note": "..."}

with open("agent_result.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```
