#!/usr/bin/env python3
"""
生成中文格式化的 RSS 日报 Markdown 文件
流程：RSS → 时效过滤 → 抓取全文 → Agent 处理 → 生成日报
"""

import argparse
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
import time

sys.path.insert(0, str(Path(__file__).parent))

from parse_opml import parse_opml
from fetch_rss import fetch_all_feeds
from fetch_article import fetch_article


def print_progress_bar(iteration: int, total: int, prefix: str = '', suffix: str = '', length: int = 50):
    """
    打印进度条
    """
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='', flush=True)
    if iteration == total:
        print()  # 完成后换行


def get_default_opml_path() -> str:
    """
    获取内置的默认 OPML 文件路径
    优先使用 assets 目录下的文件
    """
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    # 尝试找到 assets 目录下的 OPML 文件
    assets_dir = script_dir.parent / "assets"

    if assets_dir.exists():
        opml_files = list(assets_dir.glob("*.opml"))
        if opml_files:
            return str(opml_files[0])

    # 如果找不到，返回空字符串
    return ""


def generate_raw_data(
    opml_path: Optional[str] = None,
    hours: int = 24,
    output_json: Optional[str] = None,
    max_articles: int = 20
) -> str:
    """
    抓取 RSS 并获取文章全文，保存为 JSON 供 Agent 处理

    Args:
        opml_path: OPML 文件路径，如不指定则使用内置数据源

    Returns:
        JSON 文件路径
    """
    # 如果没有指定 OPML 路径，使用内置的
    if not opml_path:
        opml_path = get_default_opml_path()
        if not opml_path:
            print("错误: 未找到内置的 OPML 数据源，请手动指定 OPML 文件路径")
            return ""
        print(f"使用内置数据源: {opml_path}")
    else:
        print(f"使用指定数据源: {opml_path}")

    print(f"正在解析 OPML 文件...")
    feeds = parse_opml(opml_path)
    print(f"找到 {len(feeds)} 个订阅源")

    print(f"正在抓取最近 {hours} 小时的文章...")
    articles = fetch_all_feeds(feeds, hours=hours)
    print(f"找到 {len(articles)} 篇候选文章")

    if not articles:
        print("没有找到新文章")
        return ""

    # 限制文章数量（避免处理过多）
    articles = articles[:max_articles]
    print(f"将处理前 {len(articles)} 篇文章")

    # 抓取每篇文章的完整内容
    articles_data = []
    total_articles = len(articles)

    print(f"\n开始抓取 {total_articles} 篇文章全文...")
    print("-" * 60)

    for i, article in enumerate(articles, 1):
        # 显示进度条
        title_short = article.title[:40] + "..." if len(article.title) > 40 else article.title
        print_progress_bar(
            i - 1, total_articles,
            prefix=f'[{i}/{total_articles}]',
            suffix=f'正在抓取: {title_short}',
            length=40
        )

        content = fetch_article(article.link, use_trafilatura=True)

        if content and len(content.text) > 100:
            articles_data.append({
                "title": article.title,
                "link": article.link,
                "source": article.source_name,
                "published": article.published.strftime("%Y-%m-%d %H:%M"),
                "content": content.text
            })
            status = f"✓ {len(content.text)} 字"
        else:
            articles_data.append({
                "title": article.title,
                "link": article.link,
                "source": article.source_name,
                "published": article.published.strftime("%Y-%m-%d %H:%M"),
                "content": article.summary or "[无法获取全文]"
            })
            status = "✗ 失败，使用 RSS 摘要"

        # 更新进度条显示完成状态
        print_progress_bar(
            i, total_articles,
            prefix=f'[{i}/{total_articles}]',
            suffix=f'{status}',
            length=40
        )

        # 避免请求过快
        time.sleep(0.5)

    print("-" * 60)
    print(f"✓ 全文抓取完成: 成功 {len([a for a in articles_data if len(a['content']) > 1000])} 篇")

    # 保存为 JSON
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if output_json:
        json_path = Path(output_json)
    else:
        json_path = Path(f"{today}_articles_raw.json")

    json_path.write_text(
        json.dumps({
            "date": today,
            "article_count": len(articles_data),
            "articles": articles_data
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n✓ 原始数据已保存: {json_path}")
    return str(json_path)


def filter_articles(
    raw_json_path: str,
    output_json: Optional[str] = None,
    min_content_length: int = 500
) -> str:
    """
    过滤文章：移除内容过短的文章（< min_content_length 字符）

    Returns:
        过滤后的 JSON 文件路径
    """
    data = json.loads(Path(raw_json_path).read_text(encoding="utf-8"))
    articles = data["articles"]

    before = len(articles)
    filtered = [a for a in articles if len(a.get("content", "")) >= min_content_length]
    removed = before - len(filtered)

    print(f"过滤前: {before} 篇")
    print(f"移除内容 < {min_content_length} 字的文章: {removed} 篇")
    print(f"过滤后: {len(filtered)} 篇")

    today = data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    if output_json:
        json_path = Path(output_json)
    else:
        json_path = Path(f"{today}_articles_filtered.json")

    json_path.write_text(
        json.dumps(
            {"date": today, "article_count": len(filtered), "articles": filtered},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n✓ 过滤后数据已保存: {json_path}")

    if len(filtered) > 10:
        print(f"\n⚠️  文章数量 ({len(filtered)}) > 10，需要 subagent 评分筛选")
        print("下一步：Agent 读取以下文件，对每篇文章评分（1-10），选出最优 10 篇：")
        print(f"  输入: {json_path}")
        print(f"  输出: {today}_articles_top10.json")
        print("\n评分维度：技术深度(1-10) + 信息价值(1-10) + 话题热度(1-10)，取综合分最高的 10 篇")
    else:
        print(f"\n下一步：Agent 读取 {json_path} 生成摘要、分类、编者观察")

    return str(json_path)


def generate_report_from_json(json_path: str, agent_result_path: str, output_md: Optional[str] = None):
    """
    基于 Agent 处理结果生成最终日报
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 读取 Agent 处理结果
    agent_result = json.loads(Path(agent_result_path).read_text(encoding="utf-8"))

    # 分类表情符号
    category_icons = {
        "AI": "🤖", "编程": "💻", "Web": "🌐", "开源": "📦",
        "安全": "🔒", "产品": "📱", "创业": "🚀", "设计": "🎨",
        "数据": "📊", "其他": "📄"
    }

    # 生成 Markdown
    md = f"# {today} - AI热点日报\n\n"
    md += f"> AI热点信源资讯汇总 | 共 {len(agent_result['articles'])} 条更新\n\n"
    md += "---\n\n"

    # 按分类分组
    categorized = {}
    for article in agent_result['articles']:
        cat = article.get('category', '其他')
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(article)

    # 按优先级排序
    priority = ["AI", "编程", "Web", "开源", "安全", "创业", "产品", "数据", "其他"]
    sorted_categories = sorted(categorized.keys(),
                               key=lambda x: priority.index(x) if x in priority else 999)

    # 生成文章内容
    for category in sorted_categories:
        for article in categorized[category]:
            icon = category_icons.get(category, "📄")
            md += f"## {icon} {article['title']}\n\n"
            md += f"**分类：{category}**\n\n"
            md += f"{article['summary']}\n\n"
            md += f"[阅读原文]({article['link']})\n\n"
            md += "---\n\n"

    # 今日数据
    md += "## 📊 今日数据\n\n"
    md += f"- **{len(agent_result['articles'])}** 篇精选阅读\n\n"
    md += f"- **{len(categorized)}** 个分类：{', '.join(sorted_categories)}\n\n"

    # 编者观察（来自 Agent）
    md += "## 💡 编者观察\n\n"
    md += f"{agent_result.get('editor_note', '今日信源呈现了多样化的技术话题。')}\n\n"

    md += "---\n\n"
    md += "*本日报由 AI 自动生成*\n"

    # 保存 Markdown
    if output_md:
        md_path = Path(output_md)
    else:
        md_path = Path(f"{today} AI热点日报.md")

    md_path.write_text(md, encoding="utf-8")
    print(f"✓ Markdown 日报已生成: {md_path}")

    # 同时保存 JSON 格式
    json_out = {
        "date": today,
        "article_count": len(agent_result["articles"]),
        "categories": sorted_categories,
        "articles": agent_result["articles"],
        "editor_note": agent_result.get("editor_note", ""),
    }
    json_report_path = md_path.with_suffix(".json")
    json_report_path.write_text(json.dumps(json_out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ JSON 日报已生成: {json_report_path}")

    return str(md_path)


def main():
    parser = argparse.ArgumentParser(description="生成 RSS 日报")
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # 子命令: fetch - 抓取原始数据
    fetch_parser = subparsers.add_parser('fetch', help='抓取文章全文并保存为 JSON')
    fetch_parser.add_argument("opml_path", nargs='?', default=None, help="OPML 文件路径（可选，默认使用内置数据源）")
    fetch_parser.add_argument("--hours", type=int, default=24, help="时间窗口（小时）")
    fetch_parser.add_argument("-o", "--output", help="输出 JSON 文件路径")
    fetch_parser.add_argument("--max-articles", type=int, default=20, help="最大文章数量")

    # 子命令: filter - 过滤内容过短的文章
    filter_parser = subparsers.add_parser('filter', help='过滤内容过短的文章（< 500 字）')
    filter_parser.add_argument("raw_json", help="原始数据 JSON 路径")
    filter_parser.add_argument("--min-length", type=int, default=500, help="最小内容长度（字符数，默认 500）")
    filter_parser.add_argument("-o", "--output", help="输出 JSON 文件路径")

    # 子命令: generate - 基于 Agent 结果生成日报
    gen_parser = subparsers.add_parser('generate', help='基于 Agent 处理结果生成日报')
    gen_parser.add_argument("json_path", help="原始数据 JSON 路径")
    gen_parser.add_argument("agent_result", help="Agent 处理结果 JSON 路径")
    gen_parser.add_argument("-o", "--output", help="输出 Markdown 文件路径")

    args = parser.parse_args()

    if args.command == 'fetch':
        json_path = generate_raw_data(
            args.opml_path,
            hours=args.hours,
            output_json=args.output,
            max_articles=args.max_articles
        )
        if json_path:
            print(f"\n下一步：运行 filter 命令过滤短文章")
            print(f"  python {sys.argv[0]} filter {json_path}")

    elif args.command == 'filter':
        filter_articles(args.raw_json, output_json=args.output, min_content_length=args.min_length)

    elif args.command == 'generate':
        output_path = generate_report_from_json(args.json_path, args.agent_result, args.output)
        print(f"\n日报已生成: {output_path}")

    else:
        parser.print_help()
        print("\n使用示例:")
        print(f"  1. 抓取数据: python {sys.argv[0]} fetch hn-popular-blogs-2025.opml")
        print(f"  2. Agent 处理: 读取生成的 JSON，生成摘要/分类/编者观察")
        print(f"  3. 生成日报: python {sys.argv[0]} generate raw.json agent_result.json")


if __name__ == "__main__":
    main()
