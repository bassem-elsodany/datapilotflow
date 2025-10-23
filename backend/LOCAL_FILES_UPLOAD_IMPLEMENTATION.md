# Local Files Upload Implementation

## Overview

Implemented complete file upload flow for knowledge source configurations with local files. Files are uploaded to `inbound/{config_id}/` folder and stored with the configuration record.

---

## Architecture

### Flow Diagram

```
User uploads files in wizard
        ↓
Frontend stores File objects
        ↓
User clicks "Create Configuration"
        ↓
Frontend sends FormData with:
  - config_data (JSON string)
  - files (actual File objects)
        ↓
Backend POST /knowledge/sources/with-files
        ↓
Create config record → Get config.id
        ↓
Create directory: inbound/{config.id}/
        ↓
Save files to inbound/{config.id}/{uuid}.{ext}
        ↓
Update config with file paths
        ↓
Return config with file metadata
        ↓
Job processor reads from inbound/{config.id}/
```

---

## Backend Changes

### 1. New API Endpoint

**File:** `src/api/routers/knowledge/knowledge_source_router.py`

**Added imports:**
```python
import uuid
from pathlib import Path
import aiofiles
from fastapi import UploadFile, File, Form
```

**New endpoint:**
```python
@router.post("/with-files", response_model=KnowledgeSourceConfig, status_code=status.HTTP_201_CREATED)
async def create_knowledge_source_config_with_files(
    config_data: str = Form(..., description="JSON string of KnowledgeSourceConfigCreate"),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    service: KnowledgeSourceService = Depends(get_knowledge_source_service),
):
    """
    Create a new knowledge source configuration with file uploads.

    This endpoint is used for local_files content source type.
    Files are uploaded to inbound/{config_id}/ directory and paths are stored in the config.
    """
```

**What it does:**
1. Parses JSON config_data from form field
2. Creates config record first to get the ID
3. Creates `inbound/{config.id}/` directory
4. Saves each file with UUID-based filename
5. Updates config with file metadata (paths, sizes, types)
6. Returns complete config with file info

**Route:** `POST /api/v1/knowledge/sources/with-files`

---

### 2. File Storage Structure

```
inbound/
  └── {config_id}/
      ├── {uuid-1}.md
      ├── {uuid-2}.md
      ├── {uuid-3}.html
      └── {uuid-4}.pdf
```

**Benefits:**
- ✅ Each config has isolated directory
- ✅ No filename collisions (UUID-based)
- ✅ Easy cleanup (delete config → delete folder)
- ✅ Easy job processing (read from single folder)

---

## Frontend Changes

### 1. New API Hook

**File:** `dashboard/src/api/resources/knowledge-sources.ts`

**Added:**
```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

export const useCreateKnowledgeSourceConfigWithFiles = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ configData, files }: {
      configData: KnowledgeSourceConfigCreate,
      files: File[]
    }) => {
      const formData = new FormData();
      formData.append('config_data', JSON.stringify(configData));

      files.forEach((file) => {
        formData.append('files', file);
      });

      const response = await fetch(`${apiEndpoints.knowledgeSources.configs}/with-files`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create configuration with files');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-source-configs'] });
    },
  });
};
```

---

### 2. Wizard Component Changes

**File:** `dashboard/src/pages/dashboard/management/knowledge-sources/config-create/index.tsx`

**Added state for actual File objects:**
```typescript
const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
```

**Added hook:**
```typescript
const createConfigWithFilesMutation = useCreateKnowledgeSourceConfigWithFiles();
```

**Updated file drop handler:**
```typescript
const handleLocalFilesDrop = (e: React.DragEvent) => {
  const files = Array.from(e.dataTransfer.files);

  // Store actual File objects for upload
  setUploadedFiles(files);

  // Create metadata for form display
  const localFiles = files.map((file) => ({
    file_id: `file_${Date.now()}_${index}`,
    original_filename: file.name,
    file_path: '', // Will be set after upload
    file_type: file.name.split('.').pop()?.toLowerCase(),
    file_size: file.size,
    upload_timestamp: new Date().toISOString(),
  }));

  form.setFieldValue('local_files', localFiles);
};
```

**Updated FileInput onChange:**
```typescript
<FileInput
  onChange={(files) => {
    const fileList = Array.from(files);

    // Store actual File objects for upload
    setUploadedFiles(fileList);

    // Create metadata for display
    const localFiles = fileList.map((file) => ({
      // ... same as drag&drop
    }));

    form.setFieldValue('local_files', localFiles);
  }}
/>
```

**Updated handleSubmit:**
```typescript
const handleSubmit = async (values) => {
  // Clean up config data
  const cleanedValues = { ...values };
  delete cleanedValues.local_files; // Files uploaded separately

  // Use different endpoint based on content_source_type
  if (values.content_source_type === 'local_files' && uploadedFiles.length > 0) {
    console.log('📤 Uploading files with config');

    await createConfigWithFilesMutation.mutateAsync({
      configData: cleanedValues,
      files: uploadedFiles
    });
  } else {
    console.log('📤 Creating config without files');

    await createConfigMutation.mutateAsync({
      variables: cleanedValues
    });
  }
};
```

---

## File Metadata Structure

### Before Upload (Frontend Display)
```typescript
{
  file_id: "file_1234567890_0",
  original_filename: "document.md",
  file_path: "",  // Empty - will be set by backend
  file_type: "md",
  file_size: 12345,
  upload_timestamp: "2025-10-22T10:30:00.000Z"
}
```

### After Upload (Stored in Config)
```python
{
  "file_id": "uuid-generated-by-backend",
  "original_filename": "document.md",
  "file_path": "inbound/config-123/abc-def-ghi.md",  // Full path
  "file_type": "md",
  "file_size": 12345,
  "upload_timestamp": "2025-10-22T10:30:00.000Z"
}
```

---

## Testing

### Test Case 1: Markdown Files Upload
1. Navigate to create config wizard
2. Select "Local Files" → "Markdown Files"
3. Upload 3 markdown files via drag & drop
4. Fill in configuration name
5. Click "Next" → Click "Create Configuration"
6. **Expected:**
   - Files uploaded to `inbound/{config_id}/`
   - Config created with file metadata
   - Success notification shown
   - Redirected to configs list

### Test Case 2: Mixed File Types Upload
1. Select "Local Files" → "HTML Files"
2. Upload mix of .html, .htm files
3. Navigate through wizard steps
4. Create configuration
5. **Expected:**
   - All files uploaded to same `inbound/{config_id}/` folder
   - Each file has UUID-based name
   - Config stores all file paths

### Test Case 3: Web Scraping (No Files)
1. Select "Web Scraping" → "Website"
2. Enter URL and configure
3. Create configuration
4. **Expected:**
   - Uses standard endpoint (POST /knowledge/sources)
   - No files uploaded
   - Config created normally

---

## Error Handling

### Backend Errors

**Invalid JSON in config_data:**
```json
{
  "detail": "Invalid JSON in config_data: ..."
}
```
**Status:** 400 Bad Request

**File save failure:**
```json
{
  "detail": "Failed to upload files: ..."
}
```
**Status:** 500 Internal Server Error

### Frontend Errors

**No files uploaded:**
- Validation blocks submission
- Shows: "Please upload files before proceeding"

**Upload failed:**
- Shows notification with error message
- Keeps user on form (doesn't navigate away)

---

## Job Processing Integration

### How Jobs Read Files

**When job starts:**
```python
# In job processor
config = get_knowledge_source_config(config_id)

if config.content_source_type == 'local_files':
    # Read files from inbound folder
    for file_info in config.local_files:
        file_path = Path(file_info['file_path'])

        with open(file_path, 'r') as f:
            content = f.read()

        # Process content based on file_type
        if file_info['file_type'] == 'md':
            # Process markdown
        elif file_info['file_type'] == 'html':
            # Process HTML
        # ... etc
```

**Benefits:**
- ✅ Files already on disk (no download needed)
- ✅ Config has all file metadata
- ✅ Clear file paths for processing
- ✅ Easy to add new file types

---

## Next Steps

### Required for Job Processing

1. **Update Job Processor** to read from `inbound/{config_id}/`
   - Check `config.content_source_type`
   - If `'local_files'`, read from `config.local_files` array
   - Process each file based on `file_type`

2. **Add File Type Handlers**
   - Markdown: Already supported
   - HTML: Extract text or use existing HTML processor
   - PDF: Use PDF extraction library
   - DOCX: Use python-docx or similar
   - TXT: Read as plain text

3. **Error Handling**
   - Missing files
   - Corrupted files
   - Unsupported formats

---

## File Storage Configuration

### Current Settings

Files stored in: `inbound/{config_id}/`

**Configurable via environment:**
```python
# In config.py (if needed)
INBOUND_DIR: str = Field(
    default="./inbound",
    description="Directory for uploaded configuration files"
)
```

---

## Security Considerations

### File Upload Safety

✅ **UUID-based filenames** - Prevents path traversal attacks
✅ **File extension validation** - Frontend limits to `.html,.htm,.md,.markdown,.pdf,.docx,.txt`
✅ **Isolated directories** - Each config has own folder
✅ **Authentication required** - `current_user: User = Depends(get_current_user)`

### Recommended Additions

- [ ] File size limits (per file and total)
- [ ] MIME type validation on backend
- [ ] Virus scanning for uploaded files
- [ ] Disk quota per user/config

---

## API Documentation

### POST /api/v1/knowledge/sources/with-files

**Request:**
```
Content-Type: multipart/form-data

config_data: {
  "name": "My Config",
  "description": "...",
  "content_source_type": "local_files",
  "scraping_mode": "markdown_files",
  ...
}
files: [File, File, File]
```

**Response:**
```json
{
  "id": "config-123",
  "name": "My Config",
  "content_source_type": "local_files",
  "scraping_mode": "markdown_files",
  "local_files": [
    {
      "file_id": "abc-def",
      "original_filename": "doc1.md",
      "file_path": "inbound/config-123/uuid-1.md",
      "file_type": "md",
      "file_size": 12345,
      "upload_timestamp": "2025-10-22T10:30:00.000Z"
    }
  ],
  ...
}
```

---

## Summary

### What Was Implemented

1. ✅ **Backend endpoint** - POST /knowledge/sources/with-files
2. ✅ **File storage** - inbound/{config_id}/ directory structure
3. ✅ **Frontend hook** - useCreateKnowledgeSourceConfigWithFiles()
4. ✅ **Wizard integration** - Store File objects, use correct endpoint
5. ✅ **File metadata** - Full file info stored in config
6. ✅ **Error handling** - Frontend validation + backend error handling

### What's Next

- **Job processor** needs to be updated to read from inbound folder
- **File type handlers** for HTML, PDF, DOCX, TXT
- **File validation** (size limits, MIME types, virus scanning)
- **Cleanup logic** (delete files when config deleted)

---

**Last Updated:** 2025-10-22
**Status:** ✅ COMPLETE - Ready for job processor integration
**Files Modified:**
- Backend: `knowledge_source_router.py`
- Frontend: `knowledge-sources.ts`, `config-create/index.tsx`

**Documentation:**
- This file: Complete implementation guide
- Wizard fixes: WIZARD_ALL_FIXES_COMPLETE.md
- Form submission: WIZARD_FINAL_FIX_SUBMISSION.md
