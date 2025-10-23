# Knowledge Source Wizard - Quick Reference 🚀

## TL;DR - Step Flows by Content Type

### 📝 Markdown Files (FASTEST - 2 Steps!)
```
┌──────────────────┐
│ 1. Upload Files  │ ← Upload ready markdown files
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Review        │ ← Preview and create!
└──────────────────┘

Time: ~30 seconds
Steps: 2
Why: Markdown is already in final format - no conversion needed!
```

---

### 📄 HTML Files (4 Steps)
```
┌──────────────────┐
│ 1. Upload Files  │ ← Upload HTML files
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Filter        │ ← Set CSS selectors (optional)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 3. Generate      │ ← Choose output format
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 4. Review        │ ← Preview and create
└──────────────────┘

Time: ~1-2 minutes
Steps: 4
Why: HTML needs filtering and format conversion
```

---

### 📑 PDF/DOCX/TXT Files (3 Steps)
```
┌──────────────────┐
│ 1. Upload Files  │ ← Upload documents
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Generate      │ ← Configure processing
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 3. Review        │ ← Preview and create
└──────────────────┘

Time: ~1 minute
Steps: 3
Why: Documents need extraction and format conversion
```

---

### 🌐 Web Scraping (FULL - 5 Steps)
```
┌──────────────────┐
│ 1. Basic Info    │ ← Name, URL, mode
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Domains       │ ← Allow/block domains
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 3. Filter        │ ← CSS selectors
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 4. Generate      │ ← Output format
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. Review        │ ← Preview and create
└──────────────────┘

Time: ~3-5 minutes
Steps: 5
Why: Full web crawling needs all controls
```

---

## 🎯 Decision Tree

```
Select Content Source Type
        │
        ├─ Web Scraping?
        │       │
        │       └─→ 5 steps (full pipeline)
        │
        └─ Local Files?
                │
                ├─ Markdown?
                │       │
                │       └─→ 2 steps (minimal - FASTEST!)
                │
                ├─ HTML?
                │       │
                │       └─→ 4 steps (filter + generate)
                │
                └─ PDF/DOCX/TXT?
                        │
                        └─→ 3 steps (generate + review)
```

---

## 📊 Comparison Table

| Source Type | Steps | Domain Filter | Content Filter | Generation | Time |
|-------------|-------|---------------|----------------|------------|------|
| Markdown Files | **2** | ❌ | ❌ | ❌ | ~30s |
| PDF Files | 3 | ❌ | ❌ | ✅ | ~1m |
| DOCX Files | 3 | ❌ | ❌ | ✅ | ~1m |
| TXT Files | 3 | ❌ | ❌ | ✅ | ~1m |
| HTML Files | 4 | ❌ | ✅ | ✅ | ~2m |
| Web Scraping | 5 | ✅ | ✅ | ✅ | ~5m |

**Legend:**
- ✅ = Step included
- ❌ = Step skipped
- **Bold** = Fastest option

---

## 💡 Tips

### For Markdown Users (FASTEST!)
```
🚀 Uploading markdown files?

✅ Just 2 steps!
✅ No conversion needed!
✅ No CSS selectors!
✅ Go straight to preview!

Perfect for: Documentation, notes, pre-formatted content
```

### For HTML Users
```
📄 Uploading HTML files?

✅ Set CSS selectors to extract main content
✅ Choose output format (HTML or Markdown)
✅ Preview before creating

Perfect for: Saved web pages, HTML exports
```

### For Document Users
```
📑 Uploading PDF/DOCX/TXT?

✅ Configure how to process documents
✅ Choose output format
✅ Preview extraction

Perfect for: Reports, articles, text files
```

### For Web Scrapers
```
🌐 Scraping websites?

✅ Full control over crawling
✅ Domain filtering for focused crawls
✅ CSS selectors for content extraction
✅ Format conversion options

Perfect for: Documentation sites, blogs, knowledge bases
```

---

## 🎨 Visual Flow

### Markdown Flow (Optimal!)
```
📝 Upload → ✅ Review = DONE! 🎉
```

### HTML Flow
```
📄 Upload → 🎯 Filter → ⚙️ Generate → ✅ Review
```

### Document Flow
```
📑 Upload → ⚙️ Generate → ✅ Review
```

### Web Scraping Flow
```
🌐 Config → 🚧 Domains → 🎯 Filter → ⚙️ Generate → ✅ Review
```

---

## 🚀 Quick Start Examples

### Example 1: Upload Markdown Docs
```bash
1. Click "Create Configuration"
2. Select "Local Files" → "Markdown Files"
3. Upload your .md files
4. Click Next → Review → Create
5. Done in 30 seconds! ✨
```

### Example 2: Upload HTML Files
```bash
1. Click "Create Configuration"
2. Select "Local Files" → "HTML Files"
3. Upload your .html files
4. (Optional) Set CSS selector like "article" or "main"
5. Choose output format
6. Review → Create
7. Done in 1-2 minutes!
```

### Example 3: Scrape Documentation Site
```bash
1. Click "Create Configuration"
2. Select "Web Scraping" → "Website Crawler"
3. Enter base URL (e.g., https://docs.example.com)
4. Set allowed domains (e.g., docs.example.com)
5. Set CSS selectors (e.g., .content, article)
6. Choose output format (usually Markdown)
7. Review → Create
8. Done in 3-5 minutes!
```

---

## 📋 Checklist by Type

### ✅ Markdown Files
- [ ] Name your config
- [ ] Upload .md files
- [ ] Review → Create
- **Total time: 30 seconds**

### ✅ HTML Files
- [ ] Name your config
- [ ] Upload .html files
- [ ] (Optional) Set CSS selectors
- [ ] Choose output format
- [ ] Review → Create
- **Total time: 1-2 minutes**

### ✅ PDF/DOCX/TXT
- [ ] Name your config
- [ ] Upload documents
- [ ] Configure generation
- [ ] Review → Create
- **Total time: 1 minute**

### ✅ Web Scraping
- [ ] Name your config
- [ ] Enter URL and mode
- [ ] Configure domain filters
- [ ] Set CSS selectors
- [ ] Choose output format
- [ ] Review → Create
- **Total time: 3-5 minutes**

---

## 🎯 Key Takeaways

1. **Markdown = Fastest** (2 steps, ~30 seconds)
2. **Documents = Quick** (3 steps, ~1 minute)
3. **HTML = Moderate** (4 steps, ~2 minutes)
4. **Web Scraping = Full** (5 steps, ~5 minutes)

**Choose markdown when possible for fastest setup!** 🚀

---

**Last Updated:** 2025-10-21
**Version:** 2.0 (Adaptive Steps)
