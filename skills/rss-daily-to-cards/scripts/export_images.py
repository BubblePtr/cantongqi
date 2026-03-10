#!/usr/bin/env python3
"""
RSS 日报卡片图片导出器
使用 Playwright 将生成的 HTML 卡片导出为 PNG 图片
"""

import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("错误：需要安装 Playwright")
    print("请运行: pip3 install playwright")
    print("然后运行: playwright install chromium")
    sys.exit(1)


async def export_cards(html_path: Path, output_dir: Path, card_width: int = 900, card_height: int = 1200):
    """导出所有卡片为图片"""

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch()

        # 创建高分辨率页面（2x缩放）
        context = await browser.new_context(
            viewport={"width": card_width, "height": card_height},
            device_scale_factor=2  # 2x 分辨率
        )
        page = await context.new_page()

        # 加载 HTML 文件
        html_url = f"file://{html_path.absolute()}"
        await page.goto(html_url, wait_until="networkidle")

        # 获取所有卡片
        cards = await page.query_selector_all('.card')
        print(f"找到 {len(cards)} 张卡片")

        output_dir.mkdir(parents=True, exist_ok=True)

        for i, card in enumerate(cards, 1):
            # 等待卡片渲染完成
            await asyncio.sleep(0.3)

            # 截图
            output_path = output_dir / f"card_{i:02d}.png"
            await card.screenshot(path=str(output_path))
            print(f"已导出: {output_path}")

        await context.close()
        await browser.close()


def main():
    parser = argparse.ArgumentParser(description="将 HTML 卡片导出为 PNG 图片")
    parser.add_argument("html_file", help="输入的 HTML 文件路径")
    parser.add_argument("-o", "--output", default="cards_output", help="输出目录")
    parser.add_argument("--width", type=int, default=900, help="卡片宽度 (默认: 900)")
    parser.add_argument("--height", type=int, default=1200, help="卡片高度 (默认: 1200)")

    args = parser.parse_args()

    html_path = Path(args.html_file)
    if not html_path.exists():
        print(f"错误：找不到文件 {args.html_file}")
        sys.exit(1)

    output_dir = Path(args.output)

    print(f"正在导出卡片...")
    print(f"来源: {html_path}")
    print(f"输出: {output_dir}")
    print(f"尺寸: {args.width}x{args.height}")
    print()

    # 运行异步导出
    asyncio.run(export_cards(html_path, output_dir, args.width, args.height))

    print(f"\n全部完成！共导出 {len(list(output_dir.glob('*.png')))} 张图片")


if __name__ == "__main__":
    main()
