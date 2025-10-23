#!/usr/bin/env python3
"""
Extract Links from MuleSoft Navigation Data.

This script handles BOTH JavaScript and JSON formats automatically,
extracts URLs, selects latest versions, and outputs to a text file.

ONE SCRIPT - DOES EVERYTHING.
"""

import json
import re
import subprocess
import sys
import tempfile
from functools import cmp_to_key
from pathlib import Path
from typing import Dict, List

import click
from loguru import logger


def is_valid_json(file_path: Path) -> bool:
    """Check if file is valid JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except:
        return False


def convert_js_to_json_with_node(js_file: Path) -> Path:
    """
    Convert JavaScript file to JSON using Node.js.

    Args:
        js_file: Path to JavaScript file

    Returns:
        Path to temporary JSON file
    """
    logger.info(f"Converting JavaScript to JSON using Node.js...")

    # Create temporary file for JSON output
    temp_json = Path(tempfile.mktemp(suffix=".json"))

    # Node.js command to convert
    node_cmd = f"""
    const fs = require('fs');
    const data = eval(fs.readFileSync('{js_file}', 'utf8'));
    fs.writeFileSync('{temp_json}', JSON.stringify(data, null, 2));
    """

    try:
        result = subprocess.run(
            ["node", "-e", node_cmd], capture_output=True, text=True, check=True
        )
        logger.info(f"✅ Converted to JSON successfully")
        return temp_json
    except subprocess.CalledProcessError as e:
        logger.error(f"Node.js conversion failed: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.error("Node.js not found! Please install Node.js")
        raise


def parse_navigation_file(file_path: Path) -> List[Dict]:
    """
    Parse navigation file (auto-detects JavaScript or JSON).

    Args:
        file_path: Path to the file

    Returns:
        List of navigation items
    """
    logger.info(f"Reading file: {file_path}")

    # Try to parse as JSON first
    if is_valid_json(file_path):
        logger.info("File is valid JSON, parsing directly...")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"✅ Parsed {len(data)} items from JSON")
        return data

    # If not valid JSON, convert from JavaScript
    logger.info("File is JavaScript format, converting to JSON...")
    temp_json_file = convert_js_to_json_with_node(file_path)

    try:
        with open(temp_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"✅ Parsed {len(data)} items after conversion")
        return data
    finally:
        # Clean up temp file
        if temp_json_file.exists():
            temp_json_file.unlink()


def has_latest_urls(version: Dict) -> bool:
    """Check if a version object contains URLs with '/latest/'."""
    sets = version.get("sets", [])
    for set_item in sets:
        if "url" in set_item and "/latest/" in set_item["url"]:
            return True
        items = set_item.get("items", [])
        for item in items:
            if "url" in item and "/latest/" in item["url"]:
                return True
    return False


def compare_versions(v1: str, v2: str) -> int:
    """Compare two version strings."""

    def parse_version(v):
        match = re.match(r"^([\d\.]+)", v)
        if match:
            return [int(x) for x in match.group(1).split(".")]
        return [0]

    nums1 = parse_version(v1)
    nums2 = parse_version(v2)

    for i in range(max(len(nums1), len(nums2))):
        n1 = nums1[i] if i < len(nums1) else 0
        n2 = nums2[i] if i < len(nums2) else 0

        if n1 > n2:
            return 1
        elif n1 < n2:
            return -1

    return 0


def select_latest_version(item_name: str, versions: List[Dict]) -> Dict:
    """Select the latest version from a list of versions."""
    if not versions:
        return None

    # Look for a version with '/latest/' URLs
    for version in versions:
        if has_latest_urls(version):
            logger.debug(f"Item '{item_name}': selected version with '/latest/' URLs")
            return version

    # No '/latest/' found, select highest version number
    sorted_versions = sorted(
        versions,
        key=cmp_to_key(
            lambda v1, v2: compare_versions(
                v1.get("version", "0"), v2.get("version", "0")
            )
        ),
        reverse=True,
    )

    selected = sorted_versions[0]
    logger.debug(
        f"Item '{item_name}': selected highest version {selected.get('version')}"
    )
    return selected


def extract_urls_from_version(version: Dict) -> List[str]:
    """Extract all URLs from a version object."""
    urls = []

    sets = version.get("sets", [])
    for set_item in sets:
        if "url" in set_item:
            urls.append(set_item["url"])

        items = set_item.get("items", [])
        for item in items:
            if "url" in item:
                urls.append(item["url"])

    return urls


def extract_urls(data: List[Dict], latest_only: bool = True) -> List[str]:
    """Extract URLs from navigation data."""
    all_urls = []

    for item in data:
        item_name = item.get("name", "unknown")
        versions = item.get("versions", [])

        if not versions:
            logger.warning(f"Item '{item_name}' has no versions")
            continue

        if latest_only:
            selected_version = select_latest_version(item_name, versions)
            if selected_version:
                urls = extract_urls_from_version(selected_version)
                all_urls.extend(urls)
                logger.debug(
                    f"Item '{item_name}': extracted {len(urls)} URLs from version {selected_version.get('version')}"
                )
        else:
            for version in versions:
                urls = extract_urls_from_version(version)
                all_urls.extend(urls)
            logger.debug(
                f"Item '{item_name}': extracted URLs from all {len(versions)} versions"
            )

    return all_urls


def deduplicate_urls(urls: List[str]) -> List[str]:
    """Remove duplicate URLs while preserving order."""
    seen = set()
    unique_urls = []

    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    duplicates_removed = len(urls) - len(unique_urls)
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate URLs")

    return unique_urls


def create_full_urls(paths: List[str], base_url: str) -> List[str]:
    """Convert relative paths to full URLs."""
    base_url = base_url.rstrip("/")

    full_urls = []
    for path in paths:
        if not path.startswith("/"):
            path = "/" + path

        full_url = base_url + path
        full_urls.append(full_url)

    return full_urls


def write_urls_to_file(urls: List[str], output_file: Path):
    """Write URLs to a text file, one per line."""
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")

        logger.info(f"Successfully wrote {len(urls)} URLs to {output_file}")

    except Exception as e:
        logger.error(f"Error writing to file {output_file}: {e}")
        raise


@click.command()
@click.option(
    "--input-file",
    "-i",
    type=click.Path(exists=True, path_type=Path),
    default="data/ms-site-navigation-data.js",
    help="Path to the navigation data file (JavaScript or JSON)",
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    default="data/mulesoft_urls.txt",
    help="Path to the output text file",
)
@click.option(
    "--base-url",
    "-b",
    default="https://docs.mulesoft.com",
    help="Base URL to prepend to relative paths",
)
@click.option(
    "--latest-only",
    "-l",
    is_flag=True,
    default=False,
    help="Only include latest version of each item",
)
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Enable verbose logging"
)
def main(
    input_file: Path, output_file: Path, base_url: str, latest_only: bool, verbose: bool
):
    """
    Extract documentation links from MuleSoft navigation data.

    ONE SCRIPT - handles JavaScript OR JSON automatically.
    Converts, parses, extracts, and outputs URLs.

    Examples:
        # Latest versions only (RECOMMENDED)
        python extract_mulesoft_links.py --latest-only

        # All versions
        python extract_mulesoft_links.py

        # Custom files
        python extract_mulesoft_links.py -i data.js -o urls.txt --latest-only
    """
    # Configure logging
    logger.remove()
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr, level=log_level, format="{time:HH:mm:ss} | {level:<8} | {message}"
    )

    logger.info("=" * 80)
    logger.info("MuleSoft Documentation Link Extractor")
    logger.info("=" * 80)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Latest only: {latest_only}")
    logger.info("-" * 80)

    try:
        # Step 1: Parse file (auto-converts JavaScript to JSON if needed)
        logger.info("Step 1: Parsing navigation data...")
        data = parse_navigation_file(input_file)

        # Step 2: Extract URLs
        if latest_only:
            logger.info("Step 2: Extracting URLs from latest/highest versions...")
        else:
            logger.info("Step 2: Extracting URLs from all versions...")

        paths = extract_urls(data, latest_only=latest_only)
        logger.info(f"Extracted {len(paths)} URLs from navigation data")

        # Step 3: Remove duplicates
        logger.info("Step 3: Removing duplicates...")
        paths = deduplicate_urls(paths)

        # Step 4: Create full URLs
        logger.info("Step 4: Creating full URLs...")
        full_urls = create_full_urls(paths, base_url)

        # Step 5: Sort URLs
        logger.info("Step 5: Sorting URLs...")
        full_urls.sort()

        # Step 6: Write to output file
        logger.info("Step 6: Writing URLs to file...")
        write_urls_to_file(full_urls, output_file)

        logger.info("-" * 80)
        logger.info(f"✅ Success! Generated {len(full_urls)} URLs")
        logger.info(f"📄 Output file: {output_file}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Failed to process: {e}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
