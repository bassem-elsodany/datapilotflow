"""
Tests for Confluence XHTML to Markdown conversion.

Tests the ConfluenceMarkdownConverter and related conversion functions
to ensure proper handling of Confluence content.
"""

import pytest

from datapilotflow.processors.confluence.confluence_markdown_converter import (
    ConfluenceMarkdownConverter,
    convert_confluence_xhtml_to_markdown,
)


class TestBasicMarkdownConversion:
    """Test basic XHTML to Markdown conversion."""

    def test_convert_empty_content(self):
        """Test conversion of empty content."""
        result = convert_confluence_xhtml_to_markdown("")
        assert result == ""

    def test_convert_whitespace_only(self):
        """Test conversion of whitespace-only content."""
        result = convert_confluence_xhtml_to_markdown("   \n  \n  ")
        assert result == ""

    def test_convert_simple_paragraph(self):
        """Test conversion of simple paragraph."""
        xhtml = "<p>Hello World</p>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "Hello World" in result

    def test_convert_bold_text(self):
        """Test conversion of bold text."""
        xhtml = "<p>Hello <strong>World</strong></p>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "**World**" in result

    def test_convert_italic_text(self):
        """Test conversion of italic text."""
        xhtml = "<p>Hello <em>World</em></p>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "*World*" in result

    def test_convert_mixed_formatting(self):
        """Test conversion of mixed formatting."""
        xhtml = "<p>This is <strong>bold</strong> and <em>italic</em> text.</p>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "**bold**" in result
        assert "*italic*" in result


class TestHeadingConversion:
    """Test heading conversion."""

    def test_convert_h1(self):
        """Test conversion of H1 heading."""
        xhtml = "<h1>Title</h1>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "# Title" in result

    def test_convert_h2(self):
        """Test conversion of H2 heading."""
        xhtml = "<h2>Subtitle</h2>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "## Subtitle" in result

    def test_convert_h3(self):
        """Test conversion of H3 heading."""
        xhtml = "<h3>Section</h3>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "### Section" in result


class TestListConversion:
    """Test list conversion."""

    def test_convert_unordered_list(self):
        """Test conversion of unordered list."""
        xhtml = "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "- Item 3" in result

    def test_convert_ordered_list(self):
        """Test conversion of ordered list."""
        xhtml = "<ol><li>First</li><li>Second</li><li>Third</li></ol>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "1. First" in result
        assert "2. Second" in result
        assert "3. Third" in result


class TestTableConversion:
    """Test table conversion."""

    def test_convert_simple_table(self):
        """Test conversion of simple table."""
        xhtml = """
        <table>
            <tr><th>Header 1</th><th>Header 2</th></tr>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "Header 1" in result
        assert "Header 2" in result
        assert "Cell 1" in result
        assert "Cell 2" in result
        # Markdown tables use pipes
        assert "|" in result

    def test_convert_table_with_colspan(self):
        """Test conversion of table with colspan."""
        xhtml = """
        <table>
            <tr><th colspan="2">Wide Header</th></tr>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "Cell 1" in result
        assert "Cell 2" in result

    def test_convert_table_with_rowspan(self):
        """Test conversion of table with rowspan."""
        xhtml = """
        <table>
            <tr><td rowspan="2">Tall Cell</td><td>Cell 1</td></tr>
            <tr><td>Cell 2</td></tr>
        </table>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        # Should handle rowspan without errors
        assert len(result) > 0


class TestCodeConversion:
    """Test code block conversion."""

    def test_convert_inline_code(self):
        """Test conversion of inline code."""
        xhtml = "<p>Use <code>function_name()</code> to call the function.</p>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "`function_name()`" in result

    def test_convert_code_block(self):
        """Test conversion of code block."""
        xhtml = """
        <pre><code>
def hello():
    print("Hello World")
        </code></pre>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "```" in result
        assert "hello()" in result

    def test_convert_code_block_with_language(self):
        """Test conversion of code block with language."""
        xhtml = """
        <pre><code class="language-python">
def greet(name):
    return f"Hello {name}"
        </code></pre>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "```python" in result or "```" in result


class TestLinkConversion:
    """Test link conversion."""

    def test_convert_simple_link(self):
        """Test conversion of simple link."""
        xhtml = '<p>Visit <a href="https://example.com">Example</a></p>'
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "[Example](https://example.com)" in result or "Example" in result

    def test_convert_link_with_title(self):
        """Test conversion of link with title."""
        xhtml = '<p><a href="https://github.com" title="GitHub">GitHub</a></p>'
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "GitHub" in result


class TestConfluenceMacros:
    """Test Confluence-specific macro conversion."""

    def test_convert_info_macro(self):
        """Test conversion of info macro to alert."""
        xhtml = """
        <div data-macro-name="info">
            <div class="confluence-information-macro-body">
                <p>This is important information</p>
            </div>
        </div>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "important" in result.lower() or "[!" in result

    def test_convert_warning_macro(self):
        """Test conversion of warning macro."""
        xhtml = """
        <div data-macro-name="warning">
            <div class="confluence-information-macro-body">
                <p>This is a warning</p>
            </div>
        </div>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        # Should not raise an error
        assert len(result) >= 0

    def test_convert_expand_container(self):
        """Test conversion of expand container."""
        xhtml = """
        <div class="expand-container">
            <span class="expand-control-text">Click to expand</span>
            <div class="expand-content">
                <p>Hidden content</p>
            </div>
        </div>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        # Should contain details element or expanded content
        assert "details" in result or "Hidden content" in result


class TestComplexContent:
    """Test conversion of complex Confluence content."""

    def test_convert_complex_page(self):
        """Test conversion of complex page with multiple elements."""
        xhtml = """
        <h1>Page Title</h1>
        <p>Introduction paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
        <h2>Section 1</h2>
        <p>Section content with a <a href="https://example.com">link</a>.</p>
        <ul>
            <li>Bullet point 1</li>
            <li>Bullet point 2</li>
        </ul>
        <h2>Code Example</h2>
        <pre><code>print("Hello")</code></pre>
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>Item 1</td><td>100</td></tr>
        </table>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "Page Title" in result
        assert "Section 1" in result
        assert len(result) > 100

    def test_convert_page_with_all_formats(self):
        """Test conversion of page using all formatting options."""
        xhtml = """
        <h1>Complete Test</h1>
        <p>Paragraph with <strong>bold</strong>, <em>italic</em>, and <code>code</code>.</p>
        <blockquote>A quote</blockquote>
        <pre><code>code block</code></pre>
        <ul><li>Item 1</li></ul>
        <ol><li>Ordered 1</li></ol>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "Complete Test" in result
        assert len(result) > 50


class TestErrorHandling:
    """Test error handling in conversion."""

    def test_convert_malformed_html(self):
        """Test conversion of malformed HTML."""
        xhtml = "<p>Unclosed paragraph <strong>bold text</p></strong>"
        # Should not raise an error
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert isinstance(result, str)

    def test_convert_none_input(self):
        """Test conversion with None input."""
        with pytest.raises((AttributeError, ValueError, TypeError)):
            convert_confluence_xhtml_to_markdown(None)

    def test_convert_very_large_content(self):
        """Test conversion of very large content."""
        xhtml = "<p>Large content: " + ("word " * 10000) + "</p>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert len(result) > 0

    def test_convert_special_characters(self):
        """Test conversion with special characters."""
        xhtml = "<p>Special chars: &lt; &gt; &amp; &quot; &apos;</p>"
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert len(result) > 0


class TestWhitespaceHandling:
    """Test whitespace handling in conversion."""

    def test_remove_excessive_blank_lines(self):
        """Test that excessive blank lines are removed."""
        xhtml = """
        <p>Line 1</p>
        <p>Line 2</p>
        <p>Line 3</p>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        # Should not have excessive blank lines
        assert "\n\n\n" not in result

    def test_preserve_necessary_whitespace(self):
        """Test that necessary whitespace is preserved."""
        xhtml = """
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <p>Paragraph after list</p>
        """
        result = convert_confluence_xhtml_to_markdown(xhtml)
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Paragraph after list" in result


class TestMarkdownConverterClass:
    """Test the ConfluenceMarkdownConverter class directly."""

    def test_converter_initialization(self):
        """Test converter initialization."""
        converter = ConfluenceMarkdownConverter()
        assert converter is not None
        assert isinstance(converter, ConfluenceMarkdownConverter)

    def test_converter_with_options(self):
        """Test converter with custom options."""
        converter = ConfluenceMarkdownConverter(bullets="*")
        assert converter is not None

    def test_converter_simple_conversion(self):
        """Test simple conversion using converter class."""
        converter = ConfluenceMarkdownConverter()
        result = converter.convert("<p>Test content</p>")
        assert "Test content" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
