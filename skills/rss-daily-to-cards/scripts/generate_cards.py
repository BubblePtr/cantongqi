#!/usr/bin/env python3
"""
RSS 日报卡片生成器
将 JSON 格式的 RSS 日报转换为 3:4 比例的网页卡片
输入：agent_result.json 或 {日期} AI热点日报.json
"""

import json
import sys
import argparse
import shutil
import tempfile
import asyncio
from pathlib import Path
from datetime import datetime
from html import escape

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# 个人品牌配置
BRAND_CONFIG = {
    "name": "第九比特的 AI 日报",
    "tagline": "AI 启蒙小伙伴",
    "twitter_id": "@ninthbit_ai",
    "subtitle": "每日精选"
}

TWITTER_X_ICON = '''<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'''


def load_json(path: Path) -> dict:
    """加载 JSON 日报，统一为内部格式"""
    raw = json.loads(path.read_text(encoding="utf-8"))
    articles = raw.get("articles", [])
    count = raw.get("article_count", len(articles))
    cats = raw.get("categories", list({a.get("category", "") for a in articles}))
    stats_items = [
        f"{count} 篇精选阅读",
        f"{len(cats)} 个分类：{', '.join(cats)}"
    ]
    return {
        "date": raw.get("date", datetime.now().strftime("%Y-%m-%d")),
        "editor_note": raw.get("editor_note", ""),
        "stats": stats_items,
        "articles": articles,
    }


def render_paragraphs(text: str) -> str:
    """将纯文本（\\n\\n 分段）渲染为 HTML 段落"""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "\n".join(f"<p>{escape(p)}</p>" for p in paras)


async def export_cards_to_images(html_path: Path, output_dir: Path, card_width: int = 900, card_height: int = 1200):
    """使用 Playwright 导出所有卡片为图片"""
    if not PLAYWRIGHT_AVAILABLE:
        print("警告：Playwright 未安装，跳过自动截图")
        print("请运行: pip install playwright && playwright install chromium")
        return []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": card_width, "height": card_height},
            device_scale_factor=2
        )
        page = await context.new_page()
        await page.goto(f"file://{html_path.absolute()}", wait_until="networkidle")

        cards = await page.query_selector_all(".card")
        print(f"找到 {len(cards)} 张卡片，开始截图...")
        output_dir.mkdir(parents=True, exist_ok=True)

        exported = []
        for i, card in enumerate(cards, 1):
            await asyncio.sleep(0.3)
            out = output_dir / f"card_{i:02d}.png"
            await card.screenshot(path=str(out))
            exported.append(out)
            print(f"已导出: {out}")

        await context.close()
        await browser.close()
    return exported


def generate_cover_card(data: dict, page_num: int, total_pages: int) -> str:
    """生成封面卡片"""
    date_str = data["date"]
    twitter_id = BRAND_CONFIG["twitter_id"]

    editor_html = ""
    if data.get("editor_note"):
        editor_html = f'''
            <div class="editor-note">
                <h3>编者观察</h3>
                <div class="content-text">{render_paragraphs(data["editor_note"])}</div>
            </div>'''

    stats_html = ""
    if data.get("stats"):
        items_html = "".join(f"<li>{escape(item)}</li>" for item in data["stats"])
        stats_html = f'''
            <div class="stats-section">
                <h3>今日数据</h3>
                <div class="content-text"><ul>{items_html}</ul></div>
            </div>'''

    return f'''
    <div class="card cover-card">
        <div class="card-header">
            <span class="category-tag">精选日报</span>
            <div class="header-info">
                <div class="header-date">{date_str}</div>
                <div class="header-subtitle">{BRAND_CONFIG["subtitle"]}</div>
            </div>
        </div>
        <div class="card-content">
            <h1 class="main-title">{BRAND_CONFIG["name"]}</h1>
            <div class="subtitle">每日科技资讯精选</div>
            {editor_html}
            {stats_html}
        </div>
        <div class="card-footer">
            <div class="page-number"><span class="current">{page_num}</span> / {total_pages}</div>
            <div class="footer-social">
                <span class="twitter-icon">{TWITTER_X_ICON}</span>
                <span class="twitter-id">{twitter_id}</span>
            </div>
        </div>
    </div>'''


def generate_article_card(article: dict, page_num: int, total_pages: int, date_str: str = "", dark_mode: bool = False) -> str:
    """生成文章卡片"""
    title = escape(article.get("title", ""))
    category = escape(article.get("category", "其他"))
    summary = render_paragraphs(article.get("summary", ""))
    link = article.get("link", "")
    dark_class = "dark-mode" if dark_mode else ""
    twitter_id = BRAND_CONFIG["twitter_id"]

    title_html = f'<h2 class="article-title">{title}</h2>' if title else ""
    link_html = f'<p class="read-more">阅读原文：{escape(link)}</p>' if link else ""

    return f'''
    <div class="card {dark_class}">
        <div class="card-header">
            <span class="category-tag">{category}</span>
            <div class="header-info">
                <div class="header-date">{date_str}</div>
                <div class="header-subtitle">{BRAND_CONFIG["subtitle"]}</div>
            </div>
        </div>
        <div class="card-content">
            {title_html}
            <div class="content-text article-body">
                {summary}
                {link_html}
            </div>
        </div>
        <div class="card-footer">
            <div class="page-number"><span class="current">{page_num}</span> / {total_pages}</div>
            <div class="footer-social">
                <span class="twitter-icon">{TWITTER_X_ICON}</span>
                <span class="twitter-id">{twitter_id}</span>
            </div>
        </div>
    </div>'''


def generate_html(data: dict) -> str:
    """生成完整 HTML"""
    articles = data.get("articles", [])
    total_pages = len(articles) + 1
    date_str = data.get("date", "")

    dark_positions = set(range(3, len(articles), 4))

    cards = [generate_cover_card(data, 1, total_pages)]
    for idx, article in enumerate(articles, start=2):
        is_dark = (idx - 2) in dark_positions
        cards.append(generate_article_card(article, idx, total_pages, date_str=date_str, dark_mode=is_dark))

    css_path = Path(__file__).parent.parent / "assets" / "style.css"
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{date_str} - 社交媒体卡片</title>
    <style>
{css}
    </style>
</head>
<body>
    <div class="card-container">
{''.join(cards)}
    </div>
</body>
</html>'''


def main():
    import argparse, shutil, tempfile, sys

    parser = argparse.ArgumentParser(description="将 JSON 日报转换为社交媒体卡片")
    parser.add_argument("input_file", help="输入的 JSON 文件（agent_result.json 或 {日期} AI热点日报.json）")
    parser.add_argument("-o", "--output", default="output", help="输出目录（默认: output）")
    parser.add_argument("--keep-html", action="store_true", help="保留中间 HTML 文件")
    parser.add_argument("--no-screenshot", action="store_true", help="跳过自动截图")
    parser.add_argument("--width", type=int, default=900)
    parser.add_argument("--height", type=int, default=1200)
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"错误：找不到文件 {args.input_file}")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_json(input_path)
    print(f"加载 {len(data['articles'])} 篇文章")
    print(f"生成 {len(data['articles']) + 1} 张卡片")

    html = generate_html(data)
    temp_dir = Path(tempfile.mkdtemp(prefix="rss_cards_"))
    print(f"创建临时工作目录: {temp_dir}")

    try:
        temp_html = temp_dir / "cards.html"
        temp_html.write_text(html, encoding="utf-8")
        print(f"临时 HTML 已生成: {temp_html}")

        if args.keep_html:
            html_out = output_dir / "cards.html"
            html_out.write_text(html, encoding="utf-8")
            print(f"HTML 已保存: {html_out}")

        if not args.no_screenshot and PLAYWRIGHT_AVAILABLE:
            print("\n开始自动截图...")
            asyncio.run(export_cards_to_images(temp_html, output_dir, args.width, args.height))
            print(f"\n图片已保存到: {output_dir}")
        elif not args.no_screenshot:
            print("\n警告：Playwright 未安装，跳过自动截图")
            print("请运行: pip install playwright && playwright install chromium")
    finally:
        shutil.rmtree(temp_dir)
        print(f"清理临时工作目录: {temp_dir}")

    print("\n处理完成！")


if __name__ == "__main__":
    import asyncio
    main()
