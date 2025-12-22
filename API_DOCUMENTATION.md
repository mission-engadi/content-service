# Content Service API Documentation

Complete API reference for the Content Service with 25 endpoints.

## Base URL

```
http://localhost:8002/api/v1
```

## Authentication

Most write operations require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Token Claims

Tokens should include:
- `sub`: User ID (UUID)
- `email`: User email
- `roles`: Array of user roles (e.g., ["user"], ["admin", "user"])

## Response Formats

All responses use JSON format with consistent structures:

**Success Response:**
```json
{
  "id": "uuid",
  "field": "value",
  "created_at": "2024-12-22T10:00:00",
  "updated_at": "2024-12-22T10:00:00"
}
```

**Error Response:**
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

**Paginated Response:**
```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

## Content Endpoints

### 1. Create Content

**POST** `/content`

Create new content item.

**Authentication:** Required

**Request Body:**
```json
{
  "title": "Article Title",
  "slug": "article-title",
  "content_type": "article",
  "body": "Article content...",
  "language": "en",
  "status": "draft",
  "meta_description": "Description",
  "tags": ["tag1", "tag2"],
  "category_id": "uuid" 
}
```

**Response:** 201 Created
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Article Title",
  "slug": "article-title",
  "content_type": "article",
  "status": "draft",
  "author_id": "author-uuid",
  "created_at": "2024-12-22T10:00:00",
  "updated_at": "2024-12-22T10:00:00"
}
```

**Content Types:**
- `article`: Article/blog post
- `lesson`: Educational lesson
- `video`: Video content
- `resource`: Downloadable resource
- `page`: Static page

**Status Values:**
- `draft`: Work in progress
- `review`: Submitted for review
- `published`: Live content
- `archived`: No longer active

---

### 2. Get Content by ID

**GET** `/content/{id}`

Retrieve content by ID. Supports optional language parameter for translated content.

**Authentication:** Not required

**Query Parameters:**
- `language` (optional): Language code (en, es, fr, pt-br)

**Response:** 200 OK
```json
{
  "id": "uuid",
  "title": "Article Title",
  "slug": "article-title",
  "content_type": "article",
  "body": "Content...",
  "status": "published",
  "language": "en",
  "author_id": "uuid",
  "published_at": "2024-12-22T10:00:00",
  "featured_image_id": "uuid",
  "meta_description": "Description",
  "tags": ["tag1"],
  "created_at": "2024-12-22T10:00:00"
}
```

---

### 3. Get Content by Slug

**GET** `/content/slug/{slug}`

Retrieve content by URL slug.

**Authentication:** Not required

**Response:** 200 OK (same as Get Content by ID)

---

### 4. List Content

**GET** `/content`

List content with filters and pagination.

**Authentication:** Not required

**Query Parameters:**
- `page` (default: 1): Page number
- `size` (default: 20): Items per page
- `status`: Filter by status (draft, review, published, archived)
- `content_type`: Filter by type (article, lesson, video, resource, page)
- `language`: Filter by language code
- `author_id`: Filter by author
- `search`: Search in title and body
- `tags`: Filter by tags (comma-separated)

**Response:** 200 OK
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Article 1",
      "slug": "article-1",
      "status": "published"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

---

### 5. Update Content

**PUT** `/content/{id}`

Update content fields.

**Authentication:** Required

**Request Body:** (all fields optional)
```json
{
  "title": "Updated Title",
  "body": "Updated content...",
  "meta_description": "New description",
  "tags": ["updated", "tags"],
  "featured_image_id": "uuid"
}
```

**Response:** 200 OK (updated content object)

---

### 6. Delete Content

**DELETE** `/content/{id}`

Soft delete content (marks as deleted).

**Authentication:** Required

**Response:** 204 No Content

---

### 7. Publish Content

**POST** `/content/{id}/publish`

Publish content (changes status to published, sets published_at).

**Authentication:** Required

**Response:** 200 OK
```json
{
  "id": "uuid",
  "status": "published",
  "published_at": "2024-12-22T10:00:00"
}
```

---

### 8. Change Content Status

**POST** `/content/{id}/status`

Change content workflow status.

**Authentication:** Required

**Request Body:**
```json
{
  "status": "review"
}
```

**Valid Transitions:**
- draft → review
- draft → published
- review → published
- review → draft
- published → archived

**Response:** 200 OK (updated content object)

---

## Translation Endpoints

### 9. Create Translation

**POST** `/content/{id}/translations`

Create translation for content.

**Authentication:** Required

**Request Body:**
```json
{
  "language": "es",
  "title": "Título en Español",
  "body": "Contenido en español...",
  "meta_description": "Descripción",
  "meta_keywords": ["palabra1", "palabra2"]
}
```

**Supported Languages:**
- `en`: English
- `es`: Spanish
- `fr`: French
- `pt-br`: Portuguese (Brazil)

**Response:** 201 Created
```json
{
  "id": "uuid",
  "content_id": "parent-content-uuid",
  "language": "es",
  "title": "Título en Español",
  "status": "pending",
  "created_at": "2024-12-22T10:00:00"
}
```

---

### 10. List Translations

**GET** `/content/{id}/translations`

List all translations for content.

**Authentication:** Not required

**Response:** 200 OK
```json
[
  {
    "id": "uuid",
    "language": "es",
    "title": "Spanish Title",
    "status": "completed"
  },
  {
    "id": "uuid",
    "language": "fr",
    "title": "French Title",
    "status": "in_progress"
  }
]
```

---

### 11. Get Translation by Language

**GET** `/content/{id}/translations/{language}`

Get specific translation by language code.

**Authentication:** Not required

**Response:** 200 OK
```json
{
  "id": "uuid",
  "content_id": "uuid",
  "language": "es",
  "title": "Spanish Title",
  "body": "Spanish content...",
  "status": "completed",
  "translator_id": "uuid",
  "created_at": "2024-12-22T10:00:00"
}
```

---

### 12. Get Translation by ID

**GET** `/translations/{id}`

Get translation by its ID.

**Authentication:** Not required

**Response:** 200 OK (same as Get Translation by Language)

---

### 13. Update Translation

**PUT** `/translations/{id}`

Update translation content.

**Authentication:** Required

**Request Body:** (all fields optional)
```json
{
  "title": "Updated Title",
  "body": "Updated content...",
  "meta_description": "Updated description"
}
```

**Response:** 200 OK (updated translation object)

---

### 14. Delete Translation

**DELETE** `/translations/{id}`

Delete a translation.

**Authentication:** Required

**Response:** 204 No Content

---

### 15. Change Translation Status

**POST** `/translations/{id}/status`

Change translation workflow status.

**Authentication:** Required

**Request Body:**
```json
{
  "status": "in_progress"
}
```

**Translation Status Workflow:**
- `pending`: Waiting to be translated
- `in_progress`: Being translated
- `completed`: Translation finished
- `reviewed`: Reviewed and approved

**Valid Transitions:**
- pending → in_progress
- in_progress → completed
- completed → reviewed
- Any → pending (restart workflow)

**Response:** 200 OK (updated translation object)

---

### 16. Get Available Languages

**GET** `/content/{id}/languages`

Get all available languages for content.

**Authentication:** Not required

**Response:** 200 OK
```json
{
  "original": "en",
  "translations": [
    {
      "language": "es",
      "language_name": "Spanish",
      "status": "completed"
    },
    {
      "language": "fr",
      "language_name": "French",
      "status": "in_progress"
    }
  ],
  "total_translations": 2,
  "missing_languages": ["pt-br"]
}
```

---

### 17. Bulk Create Translations

**POST** `/content/{id}/translations/bulk`

Create multiple translations at once.

**Authentication:** Required

**Request Body:**
```json
{
  "translations": [
    {
      "language": "es",
      "title": "Spanish Title",
      "body": "Spanish content..."
    },
    {
      "language": "fr",
      "title": "French Title",
      "body": "French content..."
    }
  ]
}
```

**Response:** 201 Created
```json
{
  "created": [
    {
      "id": "uuid",
      "language": "es",
      "status": "pending"
    },
    {
      "id": "uuid",
      "language": "fr",
      "status": "pending"
    }
  ],
  "failed": [],
  "total_created": 2
}
```

---

## Media Endpoints

### 18. Upload Media

**POST** `/media/upload`

Upload media file.

**Authentication:** Required

**Request:** Multipart form data
```
file: <binary file>
title: "Image Title" (optional)
alt_text: "Alt text" (optional)
caption: "Caption" (optional)
description: "Description" (optional)
```

**File Size Limits:**
- Images: 10MB
- Videos: 100MB
- Audio: 50MB
- Documents: 20MB

**Response:** 201 Created
```json
{
  "id": "uuid",
  "filename": "abc123_image.png",
  "original_filename": "image.png",
  "file_path": "/uploads/2024/12/abc123_image.png",
  "file_size": 102400,
  "mime_type": "image/png",
  "media_type": "image",
  "uploaded_by": "user-uuid",
  "width": 1920,
  "height": 1080,
  "url": "http://localhost:8002/uploads/2024/12/abc123_image.png",
  "created_at": "2024-12-22T10:00:00"
}
```

**Media Types:**
- `image`: PNG, JPG, GIF, WebP
- `video`: MP4, WebM, MOV
- `audio`: MP3, WAV, OGG
- `document`: PDF, DOC, DOCX, TXT

---

### 19. Upload Media for Content

**POST** `/media/content/{id}/upload`

Upload media directly associated with content.

**Authentication:** Required

**Request:** Same as Upload Media

**Response:** 201 Created (includes content_id field)
```json
{
  "id": "uuid",
  "content_id": "content-uuid",
  "filename": "abc123_image.png",
  ...
}
```

---

### 20. Get Media

**GET** `/media/{id}`

Get media metadata.

**Authentication:** Not required

**Response:** 200 OK
```json
{
  "id": "uuid",
  "filename": "abc123_image.png",
  "original_filename": "image.png",
  "file_size": 102400,
  "mime_type": "image/png",
  "media_type": "image",
  "title": "Image Title",
  "alt_text": "Alt text",
  "caption": "Caption",
  "width": 1920,
  "height": 1080,
  "url": "http://localhost:8002/uploads/2024/12/abc123_image.png",
  "uploaded_by": "user-uuid",
  "created_at": "2024-12-22T10:00:00"
}
```

---

### 21. Download Media

**GET** `/media/{id}/download`

Download media file.

**Authentication:** Not required

**Response:** 200 OK (binary file with appropriate Content-Type header)

---

### 22. List Media for Content

**GET** `/media/content/{id}/media`

List all media associated with content.

**Authentication:** Not required

**Response:** 200 OK
```json
[
  {
    "id": "uuid",
    "filename": "image1.png",
    "media_type": "image"
  },
  {
    "id": "uuid",
    "filename": "video1.mp4",
    "media_type": "video"
  }
]
```

---

### 23. List All Media

**GET** `/media`

List all media with filters and pagination.

**Authentication:** Not required

**Query Parameters:**
- `page` (default: 1): Page number
- `size` (default: 20): Items per page
- `media_type`: Filter by type (image, video, audio, document)
- `uploaded_by`: Filter by uploader UUID
- `content_id`: Filter by associated content

**Response:** 200 OK
```json
{
  "items": [
    {
      "id": "uuid",
      "filename": "image.png",
      "media_type": "image",
      "file_size": 102400
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

---

### 24. Update Media

**PUT** `/media/{id}`

Update media metadata (not the file itself).

**Authentication:** Required (must be uploader)

**Request Body:** (all fields optional)
```json
{
  "title": "Updated Title",
  "alt_text": "Updated alt text",
  "caption": "Updated caption",
  "description": "Updated description"
}
```

**Response:** 200 OK (updated media object)

---

### 25. Delete Media

**DELETE** `/media/{id}`

Delete media file and database record.

**Authentication:** Required (must be uploader)

**Response:** 204 No Content

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 204 | No Content - Deletion successful |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Duplicate resource |
| 413 | Payload Too Large - File too big |
| 415 | Unsupported Media Type - Invalid file type |
| 422 | Validation Error - Invalid data format |
| 500 | Internal Server Error - Server error |

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production use.

## Examples

### Create and Publish Content

```bash
# 1. Create content
curl -X POST http://localhost:8002/api/v1/content \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Article",
    "slug": "my-article",
    "content_type": "article",
    "body": "Article content...",
    "language": "en"
  }'

# 2. Publish content
curl -X POST http://localhost:8002/api/v1/content/{id}/publish \
  -H "Authorization: Bearer $TOKEN"
```

### Create Translation Workflow

```bash
# 1. Create translation
curl -X POST http://localhost:8002/api/v1/content/{id}/translations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "es",
    "title": "Mi Artículo",
    "body": "Contenido del artículo..."
  }'

# 2. Update status to in_progress
curl -X POST http://localhost:8002/api/v1/translations/{translation_id}/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# 3. Update translation content
curl -X PUT http://localhost:8002/api/v1/translations/{translation_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "body": "Contenido actualizado..."
  }'

# 4. Mark as completed
curl -X POST http://localhost:8002/api/v1/translations/{translation_id}/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

### Upload and Associate Media

```bash
# 1. Upload media for content
curl -X POST http://localhost:8002/api/v1/media/content/{content_id}/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@image.png" \
  -F "title=Article Image" \
  -F "alt_text=Description of image"

# 2. Get media details
curl http://localhost:8002/api/v1/media/{media_id}
```

---

## Interactive Documentation

For interactive API exploration, visit:
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

---

**Last Updated:** December 22, 2024
**API Version:** v1
**Service:** Content Service
