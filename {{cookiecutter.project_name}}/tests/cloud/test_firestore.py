{%- if cookiecutter.use_google_cloud == 'y' %}
"""Tests for Firestore client."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestFirestoreClient:
    """Tests for FirestoreClient."""
    
    def test_initialization_without_project(self):
        """Test client initializes without explicit project."""
        with patch.dict("os.environ", {}, clear=True):
            from {{cookiecutter.package_name}}.cloud.firestore import FirestoreClient
            
            client = FirestoreClient()
            
            assert client._project_id is None
            assert client._client is None
    
    def test_initialization_with_project(self):
        """Test client initializes with project."""
        from {{cookiecutter.package_name}}.cloud.firestore import FirestoreClient
        
        client = FirestoreClient(project_id="test-project")
        
        assert client._project_id == "test-project"
    
    def test_initialization_from_env(self):
        """Test client uses environment variable."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "env-project"}):
            from {{cookiecutter.package_name}}.cloud.firestore import FirestoreClient
            
            client = FirestoreClient()
            
            assert client._project_id == "env-project"
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing client."""
        from {{cookiecutter.package_name}}.cloud.firestore import FirestoreClient
        
        client = FirestoreClient(project_id="test")
        
        await client.close()
        
        assert client._client is None
        assert client._initialized is False
{%- endif %}
