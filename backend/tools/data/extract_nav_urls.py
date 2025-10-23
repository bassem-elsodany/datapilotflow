#!/usr/bin/env python3
"""
Extract all URLs from nav.json, deduplicate by keeping only the 'latest' version for each base path.
If 'latest' does not exist, keep the highest version. Output to nav_urls_prefixed.txt (no @ at the beginning).
"""
import re
from pathlib import Path
from urllib.parse import urlparse

NAV_FILE = Path("config/nav.json")
OUT_FILE = Path("nav_urls_prefixed.txt")
PREFIX = "https://docs.mulesoft.com/"

if not NAV_FILE.exists():
    print("nav.json not found!")
    exit(1)

with open(NAV_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Regex to find all url values - handles both quoted and unquoted property names
url_pattern = re.compile(r'(?:"url"|url)\s*:\s*"([^"]+)"')
urls = url_pattern.findall(content)

prefixed_urls = []
for url in urls:
    # Remove any leading slashes
    clean_url = url.lstrip('/')
    # Only prefix if not already absolute
    if url.startswith('http'):
        full_url = url
    else:
        full_url = PREFIX + clean_url
    prefixed_urls.append(full_url)

# Deduplicate: keep only 'latest' version for each base path
# If no 'latest', keep the highest version
from collections import defaultdict
import re

def extract_base_and_version(url):
    # Match /<product>/<version>/... or /<product>/latest/...
    m = re.match(r'(https://docs\.mulesoft\.com/[^/]+/)([^/]+)/(.+)', url)
    if m:
        base = m.group(1)
        version = m.group(2)
        rest = m.group(3)
        return base, version, rest
    return url, None, None

url_groups = defaultdict(list)
for url in prefixed_urls:
    base, version, rest = extract_base_and_version(url)
    if version and rest:
        group_key = base + rest  # group by product and path, ignore version
        url_groups[group_key].append((version, url))
    else:
        # URLs without versioning, just keep as is
        url_groups[url].append((None, url))

final_urls = set()
for group, versions in url_groups.items():
    # Prefer 'latest'
    latest = [u for v, u in versions if v == 'latest']
    if latest:
        final_urls.add(latest[0])
    else:
        # If no 'latest', pick the highest version (lexicographically)
        non_null_versions = [(v, u) for v, u in versions if v]
        if non_null_versions:
            # Sort by version string descending
            highest = sorted(non_null_versions, key=lambda x: x[0], reverse=True)[0][1]
            final_urls.add(highest)
        else:
            # No version, just add
            final_urls.add(versions[0][1])

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    for url in sorted(final_urls):
        f.write(url + '\n')

print(f"Extracted {len(final_urls)} deduplicated URLs to {OUT_FILE}") 