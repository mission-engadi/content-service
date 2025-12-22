"""Integration tests for translation endpoints.

Tests all translation management API endpoints including:
- Create translation
- Get translations for content
- Get translation by language
- Get translation by ID
- Update translation
- Delete translation
- Change translation status
- Get available languages
- Bulk create translations
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content
from app.models.translation import Translation, TranslationStatus


class TestCreateTranslation:
    """Tests for POST /api/v1/content/{id}/translations endpoint."""
    
    def test_create_translation_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test successful translation creation."""
        data = {
            "language": "es",
            "title": "Artículo de Prueba",
            "body": "Este es el cuerpo del artículo.",
            "meta_description": "Descripción de prueba",
        }
        
        response = client.post(
            f"/api/v1/content/{sample_content.id}/translations",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["language"] == data["language"]
        assert result["title"] == data["title"]
        assert result["body"] == data["body"]
        assert result["content_id"] == str(sample_content.id)
        assert "id" in result
    
    def test_create_translation_without_auth(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test translation creation without authentication fails."""
        data = {
            "language": "es",
            "title": "Artículo de Prueba",
            "body": "Cuerpo del artículo",
        }
        
        response = client.post(
            f"/api/v1/content/{sample_content.id}/translations",
            json=data
        )
        
        assert response.status_code == 401
    
    def test_create_translation_duplicate_language(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
        sample_translation: Translation,
    ):
        """Test creating translation with duplicate language fails."""
        data = {
            "language": sample_translation.language,
            "title": "Another Translation",
            "body": "Another body",
        }
        
        response = client.post(
            f"/api/v1/content/{sample_content.id}/translations",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_create_translation_invalid_language(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test creating translation with invalid language fails."""
        data = {
            "language": "invalid_lang",
            "title": "Test Title",
            "body": "Test body",
        }
        
        response = client.post(
            f"/api/v1/content/{sample_content.id}/translations",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_create_translation_for_nonexistent_content(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test creating translation for non-existent content fails."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        data = {
            "language": "es",
            "title": "Test Title",
            "body": "Test body",
        }
        
        response = client.post(
            f"/api/v1/content/{fake_id}/translations",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestGetTranslations:
    """Tests for GET /api/v1/content/{id}/translations endpoint."""
    
    def test_get_translations_success(
        self,
        client: TestClient,
        sample_content: Content,
        multiple_translations: list[Translation],
    ):
        """Test successful retrieval of all translations."""
        response = client.get(
            f"/api/v1/content/{sample_content.id}/translations"
        )
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == len(multiple_translations)
    
    def test_get_translations_empty(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test getting translations when none exist."""
        response = client.get(
            f"/api/v1/content/{sample_content.id}/translations"
        )
        
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_get_translations_for_nonexistent_content(
        self,
        client: TestClient,
    ):
        """Test getting translations for non-existent content."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/content/{fake_id}/translations")
        
        assert response.status_code == 404


class TestGetTranslationByLanguage:
    """Tests for GET /api/v1/content/{id}/translations/{language} endpoint."""
    
    def test_get_translation_by_language_success(
        self,
        client: TestClient,
        sample_content: Content,
        sample_translation: Translation,
    ):
        """Test successful retrieval of translation by language."""
        response = client.get(
            f"/api/v1/content/{sample_content.id}/translations/{sample_translation.language}"
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["language"] == sample_translation.language
        assert result["title"] == sample_translation.title
    
    def test_get_translation_by_language_not_found(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test getting non-existent translation by language."""
        response = client.get(
            f"/api/v1/content/{sample_content.id}/translations/de"
        )
        
        assert response.status_code == 404
    
    def test_get_translation_by_language_invalid_language(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test getting translation with invalid language code."""
        response = client.get(
            f"/api/v1/content/{sample_content.id}/translations/invalid_lang"
        )
        
        assert response.status_code in [400, 404, 422]


class TestGetTranslationById:
    """Tests for GET /api/v1/translations/{id} endpoint."""
    
    def test_get_translation_by_id_success(
        self,
        client: TestClient,
        sample_translation: Translation,
    ):
        """Test successful retrieval of translation by ID."""
        response = client.get(f"/api/v1/translations/{sample_translation.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == str(sample_translation.id)
        assert result["language"] == sample_translation.language
        assert result["title"] == sample_translation.title
    
    def test_get_translation_by_id_not_found(
        self,
        client: TestClient,
    ):
        """Test getting non-existent translation by ID."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/translations/{fake_id}")
        
        assert response.status_code == 404


class TestUpdateTranslation:
    """Tests for PUT /api/v1/translations/{id} endpoint."""
    
    def test_update_translation_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_translation: Translation,
    ):
        """Test successful translation update."""
        update_data = {
            "title": "Título Actualizado",
            "body": "Cuerpo actualizado",
        }
        
        response = client.put(
            f"/api/v1/translations/{sample_translation.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == update_data["title"]
        assert result["body"] == update_data["body"]
        assert result["language"] == sample_translation.language  # Unchanged
    
    def test_update_translation_without_auth(
        self,
        client: TestClient,
        sample_translation: Translation,
    ):
        """Test translation update without authentication fails."""
        update_data = {"title": "Updated Title"}
        
        response = client.put(
            f"/api/v1/translations/{sample_translation.id}",
            json=update_data
        )
        
        assert response.status_code == 401
    
    def test_update_translation_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test updating non-existent translation."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"title": "Updated Title"}
        
        response = client.put(
            f"/api/v1/translations/{fake_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_update_translation_partial(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_translation: Translation,
    ):
        """Test partial translation update."""
        original_body = sample_translation.body
        update_data = {"title": "Only Title Updated"}
        
        response = client.put(
            f"/api/v1/translations/{sample_translation.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["title"] == update_data["title"]
        # Body should remain unchanged
        assert result["body"] == original_body


class TestDeleteTranslation:
    """Tests for DELETE /api/v1/translations/{id} endpoint."""
    
    def test_delete_translation_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_translation: Translation,
    ):
        """Test successful translation deletion."""
        response = client.delete(
            f"/api/v1/translations/{sample_translation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify translation is deleted
        get_response = client.get(
            f"/api/v1/translations/{sample_translation.id}"
        )
        assert get_response.status_code == 404
    
    def test_delete_translation_without_auth(
        self,
        client: TestClient,
        sample_translation: Translation,
    ):
        """Test translation deletion without authentication fails."""
        response = client.delete(
            f"/api/v1/translations/{sample_translation.id}"
        )
        
        assert response.status_code == 401
    
    def test_delete_translation_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent translation."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.delete(
            f"/api/v1/translations/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestChangeTranslationStatus:
    """Tests for POST /api/v1/translations/{id}/status endpoint."""
    
    def test_change_status_to_in_progress(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_translation: Translation,
    ):
        """Test changing translation status to in_progress."""
        response = client.post(
            f"/api/v1/translations/{sample_translation.id}/status",
            json={"status": "in_progress"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "in_progress"
    
    def test_change_status_to_completed(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_translation: Translation,
    ):
        """Test changing translation status to completed."""
        # First move to in_progress
        client.post(
            f"/api/v1/translations/{sample_translation.id}/status",
            json={"status": "in_progress"},
            headers=auth_headers
        )
        
        # Then to completed
        response = client.post(
            f"/api/v1/translations/{sample_translation.id}/status",
            json={"status": "completed"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "completed"
    
    def test_change_status_to_reviewed(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_translation: Translation,
    ):
        """Test changing translation status to reviewed."""
        # Move through workflow: pending -> in_progress -> completed -> reviewed
        statuses = ["in_progress", "completed", "reviewed"]
        
        for status in statuses:
            response = client.post(
                f"/api/v1/translations/{sample_translation.id}/status",
                json={"status": status},
                headers=auth_headers
            )
            assert response.status_code == 200
        
        final_response = client.get(
            f"/api/v1/translations/{sample_translation.id}"
        )
        assert final_response.json()["status"] == "reviewed"
    
    def test_change_status_invalid_transition(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_translation: Translation,
    ):
        """Test invalid status transition."""
        # Try invalid status
        response = client.post(
            f"/api/v1/translations/{sample_translation.id}/status",
            json={"status": "invalid_status"},
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_change_status_without_auth(
        self,
        client: TestClient,
        sample_translation: Translation,
    ):
        """Test changing status without authentication fails."""
        response = client.post(
            f"/api/v1/translations/{sample_translation.id}/status",
            json={"status": "in_progress"}
        )
        
        assert response.status_code == 401
    
    def test_change_status_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test changing status of non-existent translation."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.post(
            f"/api/v1/translations/{fake_id}/status",
            json={"status": "in_progress"},
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestGetAvailableLanguages:
    """Tests for GET /api/v1/content/{id}/languages endpoint."""
    
    def test_get_available_languages_success(
        self,
        client: TestClient,
        sample_content: Content,
        multiple_translations: list[Translation],
    ):
        """Test successful retrieval of available languages."""
        response = client.get(
            f"/api/v1/content/{sample_content.id}/languages"
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "original" in result
        assert "translations" in result
        assert result["original"] == sample_content.language
        assert len(result["translations"]) == len(multiple_translations)
    
    def test_get_available_languages_no_translations(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test getting languages when no translations exist."""
        response = client.get(
            f"/api/v1/content/{sample_content.id}/languages"
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["original"] == sample_content.language
        assert len(result["translations"]) == 0
    
    def test_get_available_languages_not_found(
        self,
        client: TestClient,
    ):
        """Test getting languages for non-existent content."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/content/{fake_id}/languages")
        
        assert response.status_code == 404


class TestBulkCreateTranslations:
    """Tests for POST /api/v1/content/{id}/translations/bulk endpoint."""
    
    def test_bulk_create_translations_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test successful bulk translation creation."""
        data = {
            "translations": [
                {
                    "language": "es",
                    "title": "Título en Español",
                    "body": "Cuerpo en español",
                },
                {
                    "language": "fr",
                    "title": "Titre en Français",
                    "body": "Corps en français",
                },
                {
                    "language": "pt-br",
                    "title": "Título em Português",
                    "body": "Corpo em português",
                },
            ]
        }
        
        response = client.post(
            f"/api/v1/content/{sample_content.id}/translations/bulk",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert "created" in result
        assert len(result["created"]) == 3
    
    def test_bulk_create_translations_without_auth(
        self,
        client: TestClient,
        sample_content: Content,
    ):
        """Test bulk translation creation without authentication fails."""
        data = {
            "translations": [
                {
                    "language": "es",
                    "title": "Título",
                    "body": "Cuerpo",
                }
            ]
        }
        
        response = client.post(
            f"/api/v1/content/{sample_content.id}/translations/bulk",
            json=data
        )
        
        assert response.status_code == 401
    
    def test_bulk_create_translations_partial_failure(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
        sample_translation: Translation,
    ):
        """Test bulk creation with some failures (duplicate language)."""
        data = {
            "translations": [
                {
                    "language": sample_translation.language,  # Duplicate
                    "title": "Duplicate",
                    "body": "Duplicate",
                },
                {
                    "language": "fr",
                    "title": "Valid Translation",
                    "body": "Valid body",
                },
            ]
        }
        
        response = client.post(
            f"/api/v1/content/{sample_content.id}/translations/bulk",
            json=data,
            headers=auth_headers
        )
        
        # Should handle partial failures gracefully
        # May return 207 (Multi-Status) or other appropriate code
        assert response.status_code in [201, 207, 400]
    
    def test_bulk_create_translations_empty_list(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test bulk creation with empty translations list."""
        data = {"translations": []}
        
        response = client.post(
            f"/api/v1/content/{sample_content.id}/translations/bulk",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_bulk_create_translations_for_nonexistent_content(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test bulk creation for non-existent content."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        data = {
            "translations": [
                {
                    "language": "es",
                    "title": "Título",
                    "body": "Cuerpo",
                }
            ]
        }
        
        response = client.post(
            f"/api/v1/content/{fake_id}/translations/bulk",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestTranslationWorkflow:
    """Tests for translation workflow management."""
    
    def test_complete_translation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_content: Content,
    ):
        """Test complete translation workflow from creation to review."""
        # Create translation
        create_response = client.post(
            f"/api/v1/content/{sample_content.id}/translations",
            json={
                "language": "es",
                "title": "Artículo",
                "body": "Cuerpo",
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        translation_id = create_response.json()["id"]
        
        # Move to in_progress
        status_response = client.post(
            f"/api/v1/translations/{translation_id}/status",
            json={"status": "in_progress"},
            headers=auth_headers
        )
        assert status_response.status_code == 200
        
        # Update content
        update_response = client.put(
            f"/api/v1/translations/{translation_id}",
            json={"body": "Cuerpo actualizado"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # Move to completed
        completed_response = client.post(
            f"/api/v1/translations/{translation_id}/status",
            json={"status": "completed"},
            headers=auth_headers
        )
        assert completed_response.status_code == 200
        
        # Move to reviewed
        reviewed_response = client.post(
            f"/api/v1/translations/{translation_id}/status",
            json={"status": "reviewed"},
            headers=auth_headers
        )
        assert reviewed_response.status_code == 200
        
        # Verify final state
        final_response = client.get(f"/api/v1/translations/{translation_id}")
        assert final_response.status_code == 200
        assert final_response.json()["status"] == "reviewed"
