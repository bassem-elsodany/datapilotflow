# knowledge_metadata.json README

## Purpose
This file documents the structure and usage of the `knowledge_metadata.json` configuration file for SkillPilot knowledge sources.

## url_source Field (for single_page mode)

The `url_source` field allows you to specify where to load URLs from when using `"scraping_mode": "single_page"`.

### Usage
- **file**: Load URLs from a file (one per line, JSON, or CSV)
- **inline**: Provide a list of URLs directly in the config

### Example (file):
```json
"url_source": {
    "type": "file",
    "path": "nav_urls_prefixed.txt",
    "format": "line_by_line"
}
```

### Example (inline):
```json
"url_source": {
    "type": "inline",
    "urls": [
        "https://docs.mulesoft.com/page1",
        "https://docs.mulesoft.com/page2"
    ]
}
```

### Supported Formats
- `line_by_line`: Each line in the file is a URL
- `json`: File contains a JSON array of URLs or an object with a `urls` key
- `csv`: File contains URLs in the first column

## Notes
- The `url_source` field is only required for knowledge sources with `"scraping_mode": "single_page"`.
- For `crawl` mode, the system will crawl starting from the base URL as usual.

---
For more details, see the SkillPilot documentation or contact the maintainers. 