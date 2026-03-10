#!/usr/bin/env python3
"""
抓取 RSS 订阅源，获取 24 小时内的更新
"""

import feedparser
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import List, Optional
import time


@dataclass
class Article:
    """文章信息"""
    title: str
    link: str
    published: datetime
    summary: str
    source_name: str
    source_url: str


def parse_date(entry) -> Optional[datetime]:
    """解析文章发布时间"""
    # 尝试不同的日期字段
    date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']

    for field in date_fields:
        if hasattr(entry, field) and getattr(entry, field):
            parsed = getattr(entry, field)
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue

    return None


def fetch_feed(xml_url: str, source_name: str, source_url: str, hours: int = 24) -> List[Article]:
    """
    抓取单个 RSS 订阅源，返回指定时间内的文章

    Args:
        xml_url: RSS feed URL
        source_name: 订阅源名称
        source_url: 订阅源网站 URL
        hours: 时间窗口（小时），默认 24 小时

    Returns:
        Article 列表
    """
    try:
        feed = feedparser.parse(xml_url)
        articles = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        for entry in feed.entries:
            pub_date = parse_date(entry)

            # 如果没有日期，跳过这篇文章
            if not pub_date:
                continue

            # 只保留时间窗口内的文章
            if pub_date >= cutoff_time:
                article = Article(
                    title=entry.get('title', '无标题'),
                    link=entry.get('link', ''),
                    published=pub_date,
                    summary=entry.get('summary', entry.get('description', '')),
                    source_name=source_name,
                    source_url=source_url
                )
                articles.append(article)

        return articles

    except Exception as e:
        print(f"抓取 {source_name} 时出错: {e}")
        return []


def fetch_all_feeds(feeds: List, hours: int = 24, delay: float = 1.0) -> List[Article]:
    """
    批量抓取多个 RSS 订阅源

    Args:
        feeds: FeedSource 对象列表
        hours: 时间窗口（小时）
        delay: 请求间隔（秒），避免请求过快

    Returns:
        所有文章的列表，按发布时间倒序排列
    """
    all_articles = []

    for feed in feeds:
        print(f"正在抓取: {feed.title}...")
        articles = fetch_feed(feed.xml_url, feed.title, feed.html_url, hours)
        all_articles.extend(articles)

        if delay > 0:
            time.sleep(delay)

    # 按发布时间倒序排列
    all_articles.sort(key=lambda x: x.published, reverse=True)

    return all_articles


def main():
    import sys
    from parse_opml import parse_opml

    if len(sys.argv) < 2:
        print("用法: python fetch_rss.py <opml文件路径> [小时数]")
        sys.exit(1)

    opml_path = sys.argv[1]
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24

    feeds = parse_opml(opml_path)
    articles = fetch_all_feeds(feeds, hours=hours)

    print(f"\n共找到 {len(articles)} 篇 {hours} 小时内的文章:\n")

    for article in articles:
        print(f"标题: {article.title}")
        print(f"来源: {article.source_name}")
        print(f"时间: {article.published.strftime('%Y-%m-%d %H:%M')}")
        print(f"链接: {article.link}")
        print("-" * 50)


if __name__ == "__main__":
    main()
