# 参同契（Cangtongqi）

Claude Code Skills 仓库 - RSS 日报和卡片生成工具集

## 包含的 Skills

### rss-daily-report
从 OPML 格式的 RSS 订阅源抓取 24 小时内更新的文章，访问原文获取完整内容，然后由 Agent 生成 300-500 字中文摘要、分类和编者观察，最终输出格式化的 Markdown 日报。

### rss-daily-to-cards
将 Markdown 格式的 RSS 日报转换为适合小红书/小绿书的 3:4 比例网页卡片。采用杂志风印刷质感设计，支持合欢红+银白配色、噪点滤镜、深色模式穿插等视觉效果。

## 安装方式

本仓库支持两种安装方式，选择最适合你的：

### 方式 1：Vercel Skills CLI（推荐，跨平台）

适用于 Claude、Cursor、Windsurf 等 40+ AI 编码助手。

```bash
# 安装
npx skills add BubblePtr/cantongqi

# 更新
npx skills update

# 查看已安装的 skills
npx skills list
```

### 方式 2：Claude Code 插件市场

仅适用于 Claude Code。

```bash
# 添加市场
/plugin marketplace add BubblePtr/cantongqi

# 安装插件
/plugin install cangtongqi-skills@cangtongqi

# 更新插件
/plugin update cangtongqi-skills
```

## 使用

安装后，skills 会自动在 AI 编码助手中可用。根据你的需求，AI 会自动触发相应的 skill。

## 许可证

MIT
