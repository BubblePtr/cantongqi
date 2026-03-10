#!/usr/bin/env python3
"""
RSS 日报格式验证器
验证生成的日报是否符合规范，如不符合则返回错误信息
"""

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class ValidationError:
    """验证错误信息"""
    section: str
    message: str
    severity: str  # 'error', 'warning'


@dataclass
class ArticleSection:
    """文章段落解析结果"""
    title: str
    category: str
    content: str
    link: str
    word_count: int


class ReportValidator:
    """日报格式验证器"""

    # 规范要求
    MIN_SUMMARY_WORDS = 300
    MAX_SUMMARY_WORDS = 500
    REQUIRED_SECTIONS = ["今日数据", "编者观察"]

    def __init__(self, content: str):
        self.content = content
        self.errors: List[ValidationError] = []

    def _count_chinese_words(self, text: str) -> int:
        """
        计算中文字数
        - 中文字符算 1 字
        - 英文单词算 1 字
        - 数字和标点不算
        """
        # 移除 Markdown 标记
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # 链接
        text = re.sub(r'[#*_`]', '', text)  # Markdown 标记

        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

        # 统计英文单词
        english_words = len(re.findall(r'[a-zA-Z]+', text))

        return chinese_chars + english_words

    def validate_structure(self) -> bool:
        """验证整体结构"""
        # 检查标题格式
        title_pattern = r'^# \d{4}-\d{2}-\d{2} - .+日报$'
        if not re.search(title_pattern, self.content, re.MULTILINE):
            self.errors.append(ValidationError(
                section="标题",
                message="标题格式应为: # YYYY-MM-DD - XXX日报",
                severity="error"
            ))

        # 检查引言
        intro_pattern = r'^> .+信源资讯汇总 \| 共 \d+ 条更新$'
        if not re.search(intro_pattern, self.content, re.MULTILINE):
            self.errors.append(ValidationError(
                section="引言",
                message="引言格式应为: > XXX信源资讯汇总 | 共 N 条更新",
                severity="error"
            ))

        # 检查必需段落（支持带表情符号的标题）
        for section in self.REQUIRED_SECTIONS:
            # 检查是否包含段落名（可能前面有表情符号）
            if section not in self.content:
                self.errors.append(ValidationError(
                    section="结构",
                    message=f"缺少必需段落: {section}",
                    severity="error"
                ))

        # 检查页脚
        if "本日报由 AI 自动生成" not in self.content:
            self.errors.append(ValidationError(
                section="页脚",
                message="缺少页脚信息",
                severity="warning"
            ))

        return len([e for e in self.errors if e.severity == "error"]) == 0

    def parse_articles(self) -> List[ArticleSection]:
        """解析所有文章段落"""
        articles = []

        # 分割内容为各个段落
        sections = self.content.split('\n---\n')

        for section in sections:
            lines = section.strip().split('\n')
            if len(lines) < 4:
                continue

            # 查找标题行 (## 开头)
            title_line = None
            category_line = None
            content_lines = []
            link = ""

            for i, line in enumerate(lines):
                if line.startswith('## ') and not line.startswith('## 📊') and not line.startswith('## 💡'):
                    title_line = line[3:].strip()  # 移除 "## "
                elif line.startswith('**分类：') and line.endswith('**'):
                    # 提取 "分类：XXX" -> "XXX"
                    category_line = line[5:-2]  # 移除 "**分类：" 和 "**"
                elif line.startswith('[阅读原文](') and line.endswith(')'):
                    # 提取链接: [阅读原文](https://...)
                    link_start = line.find('(') + 1
                    link = line[link_start:-1]
                elif title_line and category_line and not link and line:
                    content_lines.append(line)

            if title_line and category_line and content_lines:
                content = '\n'.join(content_lines)
                word_count = self._count_chinese_words(content)

                articles.append(ArticleSection(
                    title=title_line,
                    category=category_line,
                    content=content,
                    link=link,
                    word_count=word_count
                ))

        return articles

    def validate_articles(self, articles: List[ArticleSection]) -> bool:
        """验证每篇文章的规范"""
        valid = True

        for article in articles:
            # 检查字数
            if article.word_count < self.MIN_SUMMARY_WORDS:
                self.errors.append(ValidationError(
                    section=f"文章: {article.title[:30]}...",
                    message=f"简介字数不足: {article.word_count} 字 (要求 {self.MIN_SUMMARY_WORDS}-{self.MAX_SUMMARY_WORDS} 字)",
                    severity="error"
                ))
                valid = False

            if article.word_count > self.MAX_SUMMARY_WORDS:
                self.errors.append(ValidationError(
                    section=f"文章: {article.title[:30]}...",
                    message=f"简介字数过多: {article.word_count} 字 (要求 {self.MIN_SUMMARY_WORDS}-{self.MAX_SUMMARY_WORDS} 字)",
                    severity="warning"
                ))

            # 检查分类
            valid_categories = ["AI", "人工智能", "编程", "开发", "技术", "Web", "开源",
                              "安全", "产品", "创业", "设计", "数据", "科学", "数学", "思考", "其他"]
            if article.category not in valid_categories:
                self.errors.append(ValidationError(
                    section=f"文章: {article.title[:30]}...",
                    message=f"无效的分类: {article.category}",
                    severity="warning"
                ))

            # 检查链接
            if not article.link.startswith(('http://', 'https://')):
                self.errors.append(ValidationError(
                    section=f"文章: {article.title[:30]}...",
                    message=f"无效的链接: {article.link}",
                    severity="error"
                ))
                valid = False

        return valid

    def validate(self) -> Tuple[bool, List[ValidationError]]:
        """
        执行完整验证
        返回: (是否通过, 错误列表)
        """
        # 验证整体结构
        structure_valid = self.validate_structure()

        # 解析并验证文章
        articles = self.parse_articles()
        if not articles:
            self.errors.append(ValidationError(
                section="内容",
                message="未找到任何文章段落",
                severity="error"
            ))
            return False, self.errors

        articles_valid = self.validate_articles(articles)

        return structure_valid and articles_valid, self.errors

    def get_validation_report(self) -> str:
        """生成验证报告"""
        is_valid, errors = self.validate()

        lines = []
        lines.append("=" * 50)
        lines.append("日报格式验证报告")
        lines.append("=" * 50)
        lines.append(f"验证结果: {'通过' if is_valid else '未通过'}")
        lines.append(f"文章数量: {len(self.parse_articles())}")
        lines.append("-" * 50)

        if errors:
            errors_list = [e for e in errors if e.severity == "error"]
            warnings_list = [e for e in errors if e.severity == "warning"]

            if errors_list:
                lines.append(f"\n错误 ({len(errors_list)}):")
                for i, err in enumerate(errors_list, 1):
                    lines.append(f"  {i}. [{err.section}] {err.message}")

            if warnings_list:
                lines.append(f"\n警告 ({len(warnings_list)}):")
                for i, warn in enumerate(warnings_list, 1):
                    lines.append(f"  {i}. [{warn.section}] {warn.message}")
        else:
            lines.append("\n所有检查项均通过！")

        return "\n".join(lines)


def main():
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("用法: python validate_report.py <日报文件路径>")
        sys.exit(1)

    report_path = Path(sys.argv[1])
    if not report_path.exists():
        print(f"错误: 文件不存在 {report_path}")
        sys.exit(1)

    content = report_path.read_text(encoding='utf-8')
    validator = ReportValidator(content)

    print(validator.get_validation_report())

    is_valid, _ = validator.validate()
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
