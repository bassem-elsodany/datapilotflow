"""
Confluence XHTML to Markdown Converter.

This module provides conversion of Confluence XHTML storage format to Markdown.
Adapted from https://github.com/Spenhouet/confluence-markdown-exporter

Features:
- Convert Confluence XHTML storage format to clean Markdown
- Handle Confluence macros (info, warning, tip, note, etc.)
- Handle tables with colspan/rowspan
- Handle expandable content
- Preserve code blocks and inline code
- Support for attachments and links
"""

import re
from typing import List, Set, cast

from bs4 import BeautifulSoup, Tag
from loguru import logger
from markdownify import ATX, MarkdownConverter
from tabulate import tabulate


def _get_int_attr(cell: Tag, attr: str, default: str = "1") -> int:
    """Get integer attribute from a tag."""
    val = cell.get(attr, default)
    if isinstance(val, list):
        val = val[0] if val else default
    try:
        return int(str(val))
    except (ValueError, TypeError):
        return int(default)


def _make_empty_cell() -> Tag:
    """Create an empty table cell."""
    return Tag(name="td")


def _pad_table_rows(rows: List[List[Tag]]) -> List[List[Tag]]:
    """
    Pad table rows to handle rowspan and colspan for markdown conversion.

    This function handles complex table structures with rowspan and colspan
    by padding rows with empty cells to maintain proper alignment.
    """
    padded: List[List[Tag]] = []
    occ: dict = {}

    for r, row in enumerate(rows):
        if not row:
            continue
        cur: List[Tag] = []
        c = 0

        for cell in row:
            while (r, c) in occ:
                cur.append(occ.pop((r, c)))
                c += 1

            rs = _get_int_attr(cell, "rowspan", "1")
            cs = _get_int_attr(cell, "colspan", "1")
            cur.append(cell)

            # Append extra cells for colspan
            if cs > 1:
                cur.extend(_make_empty_cell() for _ in range(1, cs))

            # Mark future cells for rowspan and colspan
            for i in range(rs):
                for j in range(cs):
                    if i or j:
                        occ[(r + i, c + j)] = _make_empty_cell()
            c += cs

        while (r, c) in occ:
            cur.append(occ.pop((r, c)))
            c += 1

        padded.append(cur)

    return padded


class ConfluenceMarkdownConverter(MarkdownConverter):
    """
    Custom Markdown converter for Confluence XHTML storage format.

    This converter extends markdownify's MarkdownConverter to handle
    Confluence-specific elements and macros.
    """

    class Options(MarkdownConverter.DefaultOptions):
        """Configuration options for the converter."""
        bullets = "-"
        heading_style = ATX
        macros_to_ignore: Set[str] = frozenset(["qc-read-and-understood-signature-box"])

    def __init__(self, **options):
        """Initialize the converter with options."""
        super().__init__(**options)
        self.page_properties = {}

    def convert_table(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """
        Convert HTML table to Markdown table format.

        Handles rowspan, colspan, and complex table structures.
        """
        rows = [
            cast(List[Tag], tr.find_all(["td", "th"]))
            for tr in cast(List[Tag], el.find_all("tr"))
            if tr
        ]

        if not rows:
            return ""

        try:
            padded_rows = _pad_table_rows(rows)
            converted = [[self.convert(str(cell)).strip() for cell in row] for row in padded_rows]

            # Check if first row has header cells
            has_header = all(cell.name == "th" for cell in rows[0]) if rows[0] else False

            if has_header and len(converted) > 1:
                return "\n" + tabulate(converted[1:], headers=converted[0], tablefmt="pipe") + "\n"
            elif converted:
                return "\n" + tabulate(converted, tablefmt="pipe") + "\n"
        except Exception as e:
            logger.warning(f"Error converting table: {e}. Falling back to text representation.")
            return text

        return ""

    def convert_th(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """No-op for table header cells - handled by convert_table."""
        return text

    def convert_td(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """No-op for table cells - handled by convert_table."""
        return text

    def convert_div(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """
        Convert div elements, handling Confluence macros and special classes.
        """
        # Handle Confluence macros
        if el.has_attr("data-macro-name"):
            macro_name = str(el.get("data-macro-name", ""))

            if macro_name in self.options.get("macros_to_ignore", frozenset()):
                return ""

            # Handle specific macros
            if macro_name in ["panel", "info", "note", "tip", "warning"]:
                return self._convert_alert(el, text, macro_name)
            elif macro_name == "details":
                return self._convert_page_properties(el, text, parent_tags)
            elif macro_name == "expand-container":
                return self._convert_expand_container(el, text, parent_tags)
            elif macro_name == "toc":
                return self._convert_toc(el, text, parent_tags)
            elif macro_name == "attachments":
                return self._convert_attachments(el, text, parent_tags)

        # Handle special classes
        if "expand-container" in str(el.get("class", "")):
            return self._convert_expand_container(el, text, parent_tags)

        return super().convert_div(el, text, parent_tags)

    def _convert_alert(self, el: BeautifulSoup, text: str, macro_type: str) -> str:
        """
        Convert Confluence alert macros to Markdown GitHub-style alerts.

        Maps Confluence alert types to GitHub alert syntax.
        """
        alert_type_map = {
            "info": "IMPORTANT",
            "panel": "NOTE",
            "tip": "TIP",
            "note": "WARNING",
            "warning": "CAUTION",
        }

        alert_type = alert_type_map.get(macro_type, "NOTE")

        # Extract alert body content
        body_el = el.find("div", class_="confluenceTd")
        if not body_el:
            body_el = el

        content = self.convert(str(body_el))

        # Format as GitHub alert
        lines = content.strip().split("\n")
        formatted_lines = [f"> [!{alert_type}] {lines[0]}"] if lines else [f"> [!{alert_type}]"]
        formatted_lines.extend(f"> {line}" for line in lines[1:])

        return "\n" + "\n".join(formatted_lines) + "\n"

    def _convert_expand_container(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """
        Convert Confluence expandable content to HTML details element.

        Preserves expand/collapse functionality in rendered Markdown.
        """
        # Extract summary text
        summary_element = el.find("span", class_="expand-control-text")
        summary_text = (
            summary_element.get_text().strip() if summary_element else "Click to expand"
        )

        # Extract content
        content_element = el.find("div", class_="expand-content")
        content = (
            self.process_tag(content_element, parent_tags).strip() if content_element else ""
        )

        # Return as HTML details element (preserves functionality)
        return f"\n<details>\n<summary>{summary_text}</summary>\n\n{content}\n\n</details>\n"

    def _convert_page_properties(
        self, el: BeautifulSoup, text: str, parent_tags: List[str]
    ) -> str:
        """
        Extract and format page properties from detail macro.
        """
        rows = [
            cast(List[Tag], tr.find_all(["th", "td"]))
            for tr in cast(List[Tag], el.find_all("tr"))
            if tr
        ]

        if not rows:
            return ""

        for row in rows:
            if len(row) >= 2:
                key = row[0].get_text(strip=True)
                value = self.convert(str(row[1])).strip()
                self.page_properties[key] = value

        return ""

    def _convert_toc(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """
        Handle table of contents macro.

        In Markdown, TOC is typically generated by tools, so we remove it.
        """
        return ""

    def _convert_attachments(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """
        Handle attachments macro.

        Extracts attachment information and formats as links.
        """
        attachments = []
        for link in el.find_all("a"):
            href = link.get("href", "")
            name = link.get_text(strip=True)
            if href and name:
                attachments.append(f"[{name}]({href})")

        if attachments:
            return "\n### Attachments\n\n" + "\n".join(attachments) + "\n"

        return ""

    def convert_span(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """Handle span elements, including macros."""
        if el.has_attr("data-macro-name"):
            macro_name = str(el.get("data-macro-name", ""))
            if macro_name == "jira":
                return self._convert_jira_issue(el, text)

        return text

    def _convert_jira_issue(self, el: BeautifulSoup, text: str) -> str:
        """
        Handle JIRA issue macros.

        Formats JIRA references as links.
        """
        issue_key = el.get("data-jira-key", "")
        if issue_key:
            return f"[{issue_key}](https://jira.atlassian.com/browse/{issue_key})"

        return text

    def convert_code(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """Handle code blocks with language specifications."""
        # Check for language class
        class_list = el.get("class", [])
        language = ""

        if isinstance(class_list, list):
            for cls in class_list:
                if isinstance(cls, str) and cls.startswith("language-"):
                    language = cls.replace("language-", "")
                    break

        code_content = el.get_text()

        if "\n" in code_content:
            # Multi-line code block
            return f"\n```{language}\n{code_content}\n```\n"
        else:
            # Inline code
            return f"`{code_content}`"

    def convert_pre(self, el: BeautifulSoup, text: str, parent_tags: List[str]) -> str:
        """Handle pre blocks for code."""
        code_el = el.find("code")
        if code_el:
            return self.convert_code(code_el, text, parent_tags)

        return f"\n```\n{el.get_text()}\n```\n"


def convert_confluence_xhtml_to_markdown(xhtml_content: str) -> str:
    """
    Convert Confluence XHTML storage format to clean Markdown.

    This function takes raw Confluence XHTML (as returned by the Confluence API)
    and converts it to well-formatted Markdown suitable for embeddings and
    downstream processing.

    Args:
        xhtml_content: Raw XHTML content from Confluence API

    Returns:
        Clean Markdown representation of the content

    Raises:
        ValueError: If content cannot be parsed

    Example:
        >>> xhtml = '<ac:rich-text-body><p>Hello <strong>World</strong></p></ac:rich-text-body>'
        >>> markdown = convert_confluence_xhtml_to_markdown(xhtml)
        >>> print(markdown)
        Hello **World**
    """
    if not xhtml_content or not xhtml_content.strip():
        return ""

    try:
        # Parse XHTML content
        soup = BeautifulSoup(xhtml_content, "html.parser")

        # Create converter instance
        converter = ConfluenceMarkdownConverter()

        # Convert to markdown
        markdown = converter.convert(str(soup))

        # Clean up excessive whitespace
        # Remove multiple blank lines
        markdown = re.sub(r"\n\n\n+", "\n\n", markdown)

        # Strip leading/trailing whitespace
        markdown = markdown.strip()

        logger.debug(f"Successfully converted {len(xhtml_content)} chars of XHTML to Markdown")

        return markdown

    except Exception as e:
        logger.error(f"Error converting Confluence XHTML to Markdown: {e}")
        # Fallback: return plain text extraction
        try:
            soup = BeautifulSoup(xhtml_content, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            logger.warning(f"Fell back to plain text extraction due to: {e}")
            return text
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            raise ValueError(f"Failed to convert Confluence content: {e}") from e
