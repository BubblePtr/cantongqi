#!/usr/bin/env python3
"""
解析 OPML 文件，提取 RSS 订阅源信息
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List


@dataclass
class FeedSource:
    """RSS 订阅源信息"""
    title: str
    xml_url: str
    html_url: str
    text: str


def parse_opml(opml_path: str) -> List[FeedSource]:
    """
    解析 OPML 文件，返回所有 RSS 订阅源列表

    Args:
        opml_path: OPML 文件路径

    Returns:
        FeedSource 对象列表
    """
    tree = ET.parse(opml_path)
    root = tree.getroot()

    feeds = []
    for outline in root.findall('.//outline[@type="rss"]'):
        feed = FeedSource(
            title=outline.get('title', ''),
            xml_url=outline.get('xmlUrl', ''),
            html_url=outline.get('htmlUrl', ''),
            text=outline.get('text', '')
        )
        feeds.append(feed)

    return feeds


def main():
    import sys
    if len(sys.argv) < 2:
        print("用法: python parse_opml.py <opml文件路径>")
        sys.exit(1)

    feeds = parse_opml(sys.argv[1])
    print(f"共找到 {len(feeds)} 个 RSS 订阅源:")
    for feed in feeds:
        print(f"- {feed.title}: {feed.xml_url}")


if __name__ == "__main__":
    main()
