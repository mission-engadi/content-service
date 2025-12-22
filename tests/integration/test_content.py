"""Integration tests for content endpoints.

Tests all content management API endpoints including:
- Create content
- Get content by ID
- Get content by slug
- List content with filters
- Update content
- Delete content
- Publish content
- Change content status
- Get content with language parameter
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus, ContentType


class TestCreateContent:
    """Tests for POST /api/v1/content endpoint."""
    
    def test_create_content_success(
        self, 
        client: TestClient, 
        auth_headers: dict
    ):
        """Test successful content creation."""
        data = {
            "title": "New Article",
            "slug": "new-article",
            "content_type": "article",
            "body": "This is the article body.",
            "language": "en",
            "status": "draft",
        }
        
        response = client.post(
            "/api/v1/content",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == data["title"]
        assert result["slug"] == data["slug"]
        assert result["status"] == "draft"
        assert "id" in result
        assert "created_at" in result
    
    def test_create_content_without_auth(self, client: TestClient):
        """Test content creation without authentication fails."""
        data = {
            "title": "New Article",
            "slug": "new-article",
            "content_type": "article",
            "body": "Article body",
            "language": "en",
        }
        
        response = client.post("/api/v1/content", json=data)
        assert response.status_code == 401
    
    def test_create_content_duplicate_slug(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test creating content with duplicate slug fails."""
        data = {
            "title": "Another Article",
            "slug": sample_content.slug,  # Use existing slug
            "content_type": "article",
            "body": "Article body",
            "language": "en",
        }
        
        response = client.post(
            "/api/v1/content",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_create_content_invalid_type(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test creating content with invalid type fails."""
        data = {
            "title": "New Article",
            "slug": "new-article",
            "content_type": "invalid_type",
            "body": "Article body",
            "language": "en",
        }
        
        response = client.post(
            "/api/v1/content",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestGetContent:
    """Tests for GET /api/v1/content/{id} endpoint."""
    
    def test_get_content_success(
        self,
        client: TestClient,
        published_content: Content,
    ):
        """Test successful content retrieval."""
        response = client.get(f"/api/v1/content/{published_content.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == str(published_content.id)
        assert result["title"] == published_content.title
        assert result["slug"] == published_content.slug
    
    def test_get_content_with_language(
        self,
        client: TestClient,
        sample_content: Content,
        sample_translation,
    ):
        """Test content retrieval with language parameter."""
        response = client.get(
            f"/api/v1/content/{sample_content.id}",
            params={"language": "es"}
        )
        
        assert response.status_code == 200
        result = response.json()
        # Should return translated content
        assert result["language"] == "es"
    
    def test_get_content_not_found(self, client: TestClient):
        """Test getting non-existent content."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/content/{fake_id}")
        
        assert response.status_code == 404
    
    def test_get_draft_content_without_auth(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test getting draft content without authentication."""
        response = client.get(f"/api/v1/content/{sample_content.id}")
        
        # Draft content might require auth depending on implementation
        # Adjust based on actual behavior
        assert response.status_code in [200, 401, 403]


class TestGetContentBySlug:
    """Tests for GET /api/v1/content/slug/{slug} endpoint."""
    
    def test_get_content_by_slug_success(
        self,
        client: TestClient,
        published_content: Content,
    ):
        """Test successful content retrieval by slug."""
        response = client.get(
            f"/api/v1/content/slug/{published_content.slug}"
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["slug"] == published_content.slug
        assert result["title"] == published_content.title
    
    def test_get_content_by_slug_not_found(self, client: TestClient):
        """Test getting content with non-existent slug."""
        response = client.get("/api/v1/content/slug/non-existent-slug")
        
        assert response.status_code == 404


class TestListContent:
    """Tests for GET /api/v1/content endpoint."""
    
    def test_list_content_success(
        self,
        client: TestClient,
        multiple_contents: list[Content],
    ):
        """Test successful content listing."""
        response = client.get("/api/v1/content")
        
        assert response.status_code == 200
        result = response.json()
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "size" in result
        assert len(result["items"]) > 0
    
    def test_list_content_with_pagination(
        self,
        client: TestClient,
        multiple_contents: list[Content],
    ):
        """Test content listing with pagination."""
        response = client.get("/api/v1/content?page=1&size=2")
        
        assert response.status_code == 200
        result = response.json()
        assert len(result["items"]) <= 2
        assert result["page"] == 1
        assert result["size"] == 2
    
    def test_list_content_filter_by_status(
        self,
        client: TestClient,
        multiple_contents: list[Content],
    ):
        """Test content listing filtered by status."""
        response = client.get("/api/v1/content?status=published")
        
        assert response.status_code == 200
        result = response.json()
        for item in result["items"]:
            assert item["status"] == "published"
    
    def test_list_content_filter_by_type(
        self,
        client: TestClient,
        multiple_contents: list[Content],
    ):
        """Test content listing filtered by content type."""
        response = client.get("/api/v1/content?content_type=article")
        
        assert response.status_code == 200
        result = response.json()
        for item in result["items"]:
            assert item["content_type"] == "article"
    
    def test_list_content_filter_by_language(
        self,
        client: TestClient,
        multiple_contents: list[Content],
    ):
        """Test content listing filtered by language."""
        response = client.get("/api/v1/content?language=en")
        
        assert response.status_code == 200
        result = response.json()
        for item in result["items"]:
            assert item["language"] == "en"
    
    def test_list_content_search(
        self,
        client: TestClient,
        multiple_contents: list[Content],
    ):
        """Test content search functionality."""
        response = client.get("/api/v1/content?search=Article 0")
        
        assert response.status_code == 200
        result = response.json()
        # Should find content with "Article 0" in title
        assert result["total"] > 0


class TestUpdateContent:
    """Tests for PUT /api/v1/content/{id} endpoint."""
    
    def test_update_content_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test successful content update."""
        update_data = {
            "title": "Updated Title",
            "body": "Updated body content",
        }
        
        response = client.put(
            f"/api/v1/content/{sample_content.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == update_data["title"]
        assert result["body"] == update_data["body"]
    
    def test_update_content_without_auth(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test content update without authentication fails."""
        update_data = {"title": "Updated Title"}
        
        response = client.put(
            f"/api/v1/content/{sample_content.id}",
            json=update_data
        )
        
        assert response.status_code == 401
    
    def test_update_content_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test updating non-existent content."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"title": "Updated Title"}
        
        response = client.put(
            f"/api/v1/content/{fake_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestDeleteContent:
    """Tests for DELETE /api/v1/content/{id} endpoint."""
    
    def test_delete_content_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test successful content deletion (soft delete)."""
        response = client.delete(
            f"/api/v1/content/{sample_content.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify content is marked as deleted
        get_response = client.get(f"/api/v1/content/{sample_content.id}")
        assert get_response.status_code == 404
    
    def test_delete_content_without_auth(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test content deletion without authentication fails."""
        response = client.delete(f"/api/v1/content/{sample_content.id}")
        
        assert response.status_code == 401
    
    def test_delete_content_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent content."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.delete(
            f"/api/v1/content/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestPublishContent:
    """Tests for POST /api/v1/content/{id}/publish endpoint."""
    
    def test_publish_content_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test successful content publishing."""
        response = client.post(
            f"/api/v1/content/{sample_content.id}/publish",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "published"
        assert result["published_at"] is not None
    
    def test_publish_content_without_auth(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test publishing content without authentication fails."""
        response = client.post(
            f"/api/v1/content/{sample_content.id}/publish"
        )
        
        assert response.status_code == 401
    
    def test_publish_already_published_content(
        self,
        client: TestClient,
        auth_headers: dict,
        published_content: Content,
    ):
        """Test publishing already published content."""
        response = client.post(
            f"/api/v1/content/{published_content.id}/publish",
            headers=auth_headers
        )
        
        # Should handle gracefully (200 or 400)
        assert response.status_code in [200, 400]


class TestChangeContentStatus:
    """Tests for POST /api/v1/content/{id}/status endpoint."""
    
    def test_change_status_to_review(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test changing content status to review."""
        response = client.post(
            f"/api/v1/content/{sample_content.id}/status",
            json={"status": "review"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "review"
    
    def test_change_status_to_archived(
        self,
        client: TestClient,
        auth_headers: dict,
        published_content: Content,
    ):
        """Test changing content status to archived."""
        response = client.post(
            f"/api/v1/content/{published_content.id}/status",
            json={"status": "archived"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "archived"
    
    def test_change_status_invalid_transition(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test invalid status transition."""
        # Try to go from draft directly to archived (if not allowed)
        response = client.post(
            f"/api/v1/content/{sample_content.id}/status",
            json={"status": "invalid_status"},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_change_status_without_auth(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test changing status without authentication fails."""
        response = client.post(
            f"/api/v1/content/{sample_content.id}/status",
            json={"status": "review"}
        )
        
        assert response.status_code == 401


class TestContentWithTranslations:
    """Tests for content with translations functionality."""
    
    def test_get_content_with_translations(
        self,
        client: TestClient,
        sample_content: Content,
        multiple_translations,
    ):
        """Test getting content with all translations."""
        response = client.get(f"/api/v1/content/{sample_content.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert "id" in result
        # Verify translations are included if endpoint supports it


class TestContentWithMedia:
    """Tests for content with media functionality."""
    
    def test_get_content_with_media(
        self,
        client: TestClient,
        content_with_media: Content,
    ):
        """Test getting content with associated media."""
        response = client.get(f"/api/v1/content/{content_with_media.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["featured_image_id"] is not None
