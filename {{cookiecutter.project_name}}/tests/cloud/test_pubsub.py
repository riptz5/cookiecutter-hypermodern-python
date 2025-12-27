{%- if cookiecutter.use_google_cloud == 'y' %}
"""Tests for Pub/Sub client."""
import pytest
from unittest.mock import MagicMock, patch
import json


class TestPubSubMessage:
    """Tests for PubSubMessage."""
    
    def test_message_to_bytes(self):
        """Test message serialization."""
        from {{cookiecutter.package_name}}.cloud.pubsub import PubSubMessage
        
        msg = PubSubMessage(
            data={"key": "value", "number": 123},
            attributes={"source": "test"},
        )
        
        raw = msg.to_bytes()
        
        assert isinstance(raw, bytes)
        parsed = json.loads(raw.decode("utf-8"))
        assert parsed["key"] == "value"
        assert parsed["number"] == 123
    
    def test_message_from_bytes(self):
        """Test message deserialization."""
        from {{cookiecutter.package_name}}.cloud.pubsub import PubSubMessage
        
        data = json.dumps({"key": "value"}).encode("utf-8")
        
        msg = PubSubMessage.from_bytes(data)
        
        assert msg.data["key"] == "value"
    
    def test_message_attributes_default(self):
        """Test message has default attributes."""
        from {{cookiecutter.package_name}}.cloud.pubsub import PubSubMessage
        
        msg = PubSubMessage(data={"test": True})
        
        assert msg.attributes == {}


class TestPubSubClient:
    """Tests for PubSubClient."""
    
    def test_topic_path(self):
        """Test topic path construction."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            from {{cookiecutter.package_name}}.cloud.pubsub import PubSubClient
            
            client = PubSubClient()
            
            path = client._topic_path("my-topic")
            
            assert path == "projects/test-project/topics/my-topic"
    
    def test_subscription_path(self):
        """Test subscription path construction."""
        with patch.dict("os.environ", {"GOOGLE_CLOUD_PROJECT": "test-project"}):
            from {{cookiecutter.package_name}}.cloud.pubsub import PubSubClient
            
            client = PubSubClient()
            
            path = client._subscription_path("my-sub")
            
            assert path == "projects/test-project/subscriptions/my-sub"
    
    def test_genesis_prefix(self):
        """Test GENESIS topic prefix."""
        from {{cookiecutter.package_name}}.cloud.pubsub import PubSubClient
        
        assert PubSubClient.GENESIS_PREFIX == "genesis-"
{%- endif %}
