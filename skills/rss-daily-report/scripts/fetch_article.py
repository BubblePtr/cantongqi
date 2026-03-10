#!/usr/bin/env python3
"""
抓取文章全文内容
支持使用 trafilatura（推荐）或标准库
"""

import urllib.request
import urllib.error
import re
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class ArticleContent:
    """文章内容"""
    title: str
    url: str
    text: str
    author: Optional[str] = None
    published: Optional[str] = None


def clean_html(html: str) -> str:
    """基础 HTML 清理"""
    # 移除 script 和 style
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # 移除导航、侧边栏等
    html = re.sub(r'<(nav|header|footer|aside|sidebar)[^>]*>.*?</\1>', '', html,
                  flags=re.DOTALL | re.IGNORECASE)

    # 提取正文标签内容
    text = ''
    for tag in ['article', 'main', 'div[class*="content"]', 'div[class*="post"]', 'div[class*="entry"]']:
        pattern = f'<{tag}[^>]*>(.*?)</{tag.split("[")[0]}>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        if matches:
            text = max(matches, key=len)  # 取最长的匹配
            break

    if not text:
        # 如果没有找到特定标签，尝试 body
        match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)

    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)

    # 解码 HTML 实体
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&amp;', '&').replace('&quot;', '"')
    text = text.replace('&apos;', "'").replace('&nbsp;', ' ')

    # 清理空白
    text = ' '.join(text.split())

    return text.strip()


def fetch_article_stdlib(url: str, timeout: int = 30) -> Optional[ArticleContent]:
    """
    使用标准库抓取文章内容
    返回文章正文或 None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()

        # 尝试多种编码
        for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin1']:
            try:
                html = data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            html = data.decode('utf-8', errors='ignore')

        # 提取标题
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "无标题"

        # 清理标题中的 HTML 实体
        title = title.replace('&lt;', '<').replace('&gt;', '>')
        title = title.replace('&amp;', '&').replace('&quot;', '"')

        # 提取正文
        text = clean_html(html)

        # 限制长度（避免太大）
        if len(text) > 20000:
            text = text[:20000] + "..."

        return ArticleContent(title=title, url=url, text=text)

    except Exception as e:
        print(f"  抓取失败 {url}: {e}")
        return None


def fetch_article_trafilatura(url: str, timeout: int = 30) -> Optional[ArticleContent]:
    """
    使用 trafilatura 抓取文章（效果更好）
    如果未安装 trafilatura，自动回退到标准库
    """
    try:
        import trafilatura

        downloaded = trafilatura.fetch_url(url, timeout=timeout)
        if not downloaded:
            return None

        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if not text:
            return None

        # 提取标题
        from trafilatura.metadata import extract_metadata
        metadata = extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else "无标题"

        return ArticleContent(
            title=title,
            url=url,
            text=text,
            author=metadata.author if metadata else None,
            published=metadata.date if metadata else None
        )

    except ImportError:
        print("  trafilatura 未安装，使用标准库抓取")
        return fetch_article_stdlib(url, timeout)
    except Exception as e:
        print(f"  trafilatura 失败，回退到标准库: {e}")
        return fetch_article_stdlib(url, timeout)


def fetch_article(url: str, use_trafilatura: bool = True, timeout: int = 30) -> Optional[ArticleContent]:
    """
    抓取文章内容

    Args:
        url: 文章链接
        use_trafilatura: 是否尝试使用 trafilatura（效果更好）
        timeout: 超时时间

    Returns:
        ArticleContent 或 None
    """
    if use_trafilatura:
        return fetch_article_trafilatura(url, timeout)
    else:
        return fetch_article_stdlib(url, timeout)


def main():
    import sys

    if len(sys.argv) < 2:
        print("用法: python fetch_article.py <文章URL> [--no-trafilatura]")
        sys.exit(1)

    url = sys.argv[1]
    use_trafilatura = '--no-trafilatura' not in sys.argv

    print(f"正在抓取: {url}")
    content = fetch_article(url, use_trafilatura=use_trafilatura)

    if content:
        print(f"\n标题: {content.title}")
        print(f"作者: {content.author or '未知'}")
        print(f"发布时间: {content.published or '未知'}")
        print(f"\n正文前 500 字:\n{content.text[:500]}...")
    else:
        print("抓取失败")


if __name__ == "__main__":
    main()
