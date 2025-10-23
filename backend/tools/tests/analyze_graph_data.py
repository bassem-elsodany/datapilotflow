#!/usr/bin/env python3
"""
Script to analyze and visualize extracted graph data from documentation crawling.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import sys

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger


def load_graph_data(output_dir: Path = Path("crawl_output")) -> Dict[str, Any]:
    """Load all graph data files."""
    try:
        with open(output_dir / "graph_pages.json", 'r', encoding='utf-8') as f:
            pages = json.load(f)
        
        with open(output_dir / "graph_links.json", 'r', encoding='utf-8') as f:
            links = json.load(f)
        
        with open(output_dir / "graph_hierarchies.json", 'r', encoding='utf-8') as f:
            hierarchies = json.load(f)
        
        with open(output_dir / "graph_summary.json", 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        return {
            "pages": pages,
            "links": links,
            "hierarchies": hierarchies,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error loading graph data: {e}")
        return {}


def analyze_hierarchy(hierarchy: Dict[str, Any]) -> None:
    """Analyze and display hierarchy structure."""
    logger.info(f"=== HIERARCHY ANALYSIS ===")
    logger.info(f"Page: {hierarchy['title']}")
    logger.info(f"URL: {hierarchy['url']}")
    logger.info(f"Depth: {hierarchy['depth']}")
    logger.info(f"Total headers: {len(hierarchy['structure'])}")
    
    # Group headers by level
    headers_by_level = defaultdict(list)
    for header in hierarchy['structure']:
        headers_by_level[header['level']].append(header)
    
    logger.info(f"\nHeader distribution:")
    for level in sorted(headers_by_level.keys()):
        count = len(headers_by_level[level])
        logger.info(f"  H{level}: {count} headers")
    
    # Show hierarchy tree
    logger.info(f"\nHierarchy tree:")
    current_level = 0
    for header in hierarchy['structure']:
        indent = "  " * (header['level'] - 1)
        logger.info(f"{indent}• {header['text']} (H{header['level']})")
    
    # Find main sections (H2 headers)
    main_sections = [h for h in hierarchy['structure'] if h['level'] == 2]
    logger.info(f"\nMain sections ({len(main_sections)}):")
    for section in main_sections:
        logger.info(f"  • {section['text']}")


def analyze_links(links: List[Dict[str, Any]]) -> None:
    """Analyze and display link structure."""
    logger.info(f"\n=== LINK ANALYSIS ===")
    logger.info(f"Total links: {len(links)}")
    
    # Group links by destination domain
    domain_links = defaultdict(list)
    for link in links:
        from urllib.parse import urlparse
        domain = urlparse(link['to_url']).netloc
        domain_links[domain].append(link)
    
    logger.info(f"\nLinks by domain:")
    for domain, domain_link_list in domain_links.items():
        logger.info(f"  {domain}: {len(domain_link_list)} links")
    
    # Find most linked pages
    link_counts = defaultdict(int)
    for link in links:
        link_counts[link['to_url']] += 1
    
    logger.info(f"\nMost linked pages:")
    sorted_links = sorted(link_counts.items(), key=lambda x: x[1], reverse=True)
    for url, count in sorted_links[:10]:
        # Find the link text for this URL
        link_text = next((link['to_text'] for link in links if link['to_url'] == url), "Unknown")
        logger.info(f"  • {link_text} ({count} links) - {url}")


def analyze_pages(pages: Dict[str, Any]) -> None:
    """Analyze and display page structure."""
    logger.info(f"\n=== PAGE ANALYSIS ===")
    logger.info(f"Total pages: {len(pages)}")
    
    for url, page_data in pages.items():
        logger.info(f"\nPage: {page_data['title']}")
        logger.info(f"URL: {url}")
        logger.info(f"  Headers: {len(page_data['headers'])}")
        logger.info(f"  Internal links: {len(page_data['internal_links'])}")
        logger.info(f"  Code blocks: {len(page_data['code_blocks'])}")
        logger.info(f"  Breadcrumbs: {len(page_data['breadcrumbs'])}")
        
        # Show code block languages
        if page_data['code_blocks']:
            languages = defaultdict(int)
            for code_block in page_data['code_blocks']:
                languages[code_block['language']] += 1
            
            logger.info(f"  Code languages:")
            for lang, count in languages.items():
                logger.info(f"    • {lang}: {count} blocks")


def generate_graph_insights(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate insights from graph data."""
    insights = {
        "total_pages": len(graph_data.get("pages", {})),
        "total_links": len(graph_data.get("links", [])),
        "total_hierarchies": len(graph_data.get("hierarchies", [])),
        "avg_headers_per_page": 0,
        "avg_links_per_page": 0,
        "avg_code_blocks_per_page": 0,
        "most_common_languages": [],
        "link_density": 0,
        "hierarchy_depth": 0
    }
    
    pages = graph_data.get("pages", {})
    if pages:
        total_headers = sum(len(page.get("headers", [])) for page in pages.values())
        total_links = sum(len(page.get("internal_links", [])) for page in pages.values())
        total_code_blocks = sum(len(page.get("code_blocks", [])) for page in pages.values())
        
        insights["avg_headers_per_page"] = total_headers / len(pages)
        insights["avg_links_per_page"] = total_links / len(pages)
        insights["avg_code_blocks_per_page"] = total_code_blocks / len(pages)
        
        # Most common code languages
        languages = defaultdict(int)
        for page in pages.values():
            for code_block in page.get("code_blocks", []):
                languages[code_block.get("language", "unknown")] += 1
        
        insights["most_common_languages"] = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Hierarchy depth
    hierarchies = graph_data.get("hierarchies", [])
    if hierarchies:
        insights["hierarchy_depth"] = max(h.get("depth", 0) for h in hierarchies)
    
    return insights


def main():
    """Main analysis function."""
    logger.info("🔍 Graph Data Analysis")
    logger.info("=" * 50)
    
    # Load graph data
    graph_data = load_graph_data()
    
    if not graph_data:
        logger.error("No graph data found. Run the extraction first.")
        return
    
    # Display summary
    summary = graph_data.get("summary", {})
    logger.info(f"📊 Summary:")
    logger.info(f"  Pages: {summary.get('total_pages', 0)}")
    logger.info(f"  Links: {summary.get('total_links', 0)}")
    logger.info(f"  Hierarchies: {summary.get('total_hierarchies', 0)}")
    
    # Analyze hierarchies
    hierarchies = graph_data.get("hierarchies", [])
    for hierarchy in hierarchies:
        analyze_hierarchy(hierarchy)
    
    # Analyze links
    links = graph_data.get("links", [])
    analyze_links(links)
    
    # Analyze pages
    pages = graph_data.get("pages", {})
    analyze_pages(pages)
    
    # Generate insights
    insights = generate_graph_insights(graph_data)
    
    logger.info(f"\n=== INSIGHTS ===")
    logger.info(f"Average headers per page: {insights['avg_headers_per_page']:.1f}")
    logger.info(f"Average links per page: {insights['avg_links_per_page']:.1f}")
    logger.info(f"Average code blocks per page: {insights['avg_code_blocks_per_page']:.1f}")
    logger.info(f"Maximum hierarchy depth: {insights['hierarchy_depth']}")
    
    if insights["most_common_languages"]:
        logger.info(f"Most common code languages:")
        for lang, count in insights["most_common_languages"]:
            logger.info(f"  • {lang}: {count} blocks")
    
    logger.info(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    main() 